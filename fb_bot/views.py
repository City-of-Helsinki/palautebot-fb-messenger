# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from chatbot import settings
from datetime import datetime
from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from fb_bot.models import Feedback
from pprint import pprint

import json
import pytz
import requests


class FbBotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == '123456789123456789':
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse("Error, invalid token")

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def init_feedback(self):
        # Function initializes feedback dictionary that holds user's feedback
        # while the script is running
        feedback = {}
        feedback['title'] = 'Facebook messenger feedback'
        feedback['address_string'] = ''
        feedback['description'] = ''
        feedback['phase'] = 0
        feedback['lat'] = ''
        feedback['long'] = ''
        feedback['media_url'] = ''
        feedback['timestamp'] = ''
        return feedback

    def is_yes(self, message):
        # Function checks if given message matches acceptable accept_answers
        message = message.lower()
        message = message.strip(',.-!?:;')
        accept_answers = ['kyllä', 'joo', 'juu', 'k']
        if any(message in s for s in accept_answers):
            return True
        else:
            return False

    def is_no(self, message):
        # Function checks if given message matches acceptable decline_answers
        message = message.lower()
        message = message.strip(',.-!?:;')
        decline_answers = ['ei', 'e']
        if any(message in s for s in decline_answers):
            return True
        else:
            return False

    def check_input(self, phase, message, user, bot_messages):
        # Function checks if aquired message is valid
        # Returns 0 (bad answer), 1 (Yes) or 2(No)

        # check if message contains the supported information
        # OR bot's own message
        pprint('Check_input...')
        try:
            user_input = message['message']['text']
            if any(user_input == s for s in bot_messages):
                return 0
        except (KeyError, TypeError) as e:
            if phase == 2 or phase == 4:
                try:
                    user_input = message['message']['attachments']
                except KeyError:
                    return 0
            else:
                return 0

        if isinstance(user_input, str) and phase > 0:
            message = user_input.lower()
            message = message.strip(',.-!?:;')
            if message == 'peruuta':
                return 3

        # PHASE 0 & PHASE 6: check if message is between 10 and 5000 marks
        if phase == 0 or phase == 6:
            string_length = len(user_input)
            if (string_length > 10) and (string_length < 5000):
                return 1
            return 0

        # PHASE 1,3,5: check if message contains 'yes', 'no' or invalid message
        elif phase == 1 or phase == 3 or phase == 5:
            if self.is_yes(user_input):
                return 1
            elif self.is_no(user_input):
                return 2
            else:
                return 0

        # PHASE 2: check if User has attached picture
        elif phase == 2:
            media_count = 0
            for attachment in user_input:
                try:
                    if (attachment['type'] == 'image'or
                            attachment['type'] == 'video'):
                        if 'url' in attachment['payload']:
                            media_count = media_count+1
                        else:
                            pass
                    else:
                        return 0
                except TypeError:
                    return 0
            if media_count != 0:
                return 1
            else:
                return 0

        # PHASE 4: check if user has attached location/map
        elif phase == 4:
            for attachment in user_input:
                try:
                    if ('lat' in attachment['payload']['coordinates']and
                            'long' in attachment['payload']['coordinates']):
                        return 1
                    else:
                        return 0
                except (TypeError, KeyError) as e:
                    return 0
            else:
                return 0

        # PHASE 9: Bot message doesn't need validating
        elif phase == 9:
            return 0

        # BAD PHASES
        # Bot accepts all messages in bad phases because
        # they are handled in POST function
        else:
            return 1

    def get_temp_row(self, message):
        # Function creates and returns a temporary database row
        # Temporary row is used in getting user_id and media_url
        # In facebook data, media_url and user_id are facebook objects
        # and temporary row in database was the easiest way around
        # when string formatted value couldn't be assigned to variable
        url = ''
        try:
            for attachment in message['message']['attachments']:
                url = attachment['payload']['url']
                temp_row, created = Feedback.objects.get_or_create(
                    user_id=message['sender']['id'],
                    message='temp',
                    phase=0,
                )
        except (KeyError, TypeError) as e:
            temp_row, created = Feedback.objects.get_or_create(
                user_id=message['sender']['id'],
                message='temp',
                phase=0,
            )
        if url != '':
            update_row_count = Feedback.objects.filter(
                                id=temp_row.id).update(media_url=url)
            print('UPDATED TEMP_ROW WITH URL')
        return temp_row

    def get_feedback_to_update(self, user):
        # Function returns a previous feedback information if feedback
        # giving is still in progress. Meaning that Feedback is not
        # complete, and less than 15 minutes has passed from the start
        # of feedback
        try:
            prev_row = Feedback.objects.filter(
                user_id=user).exclude(message='temp').latest(
                'source_created_at')
        except Feedback.DoesNotExist:
            return ''
        if prev_row.ready:
            return ''
        time_since_fb_started = datetime.now(
            settings.TIMEZONE) - prev_row.source_created_at.astimezone(
            settings.TIMEZONE)
        if time_since_fb_started.seconds > 900:
            Feedback.objects.filter(id=prev_row.id).delete()
            return ''
        return prev_row

    def get_phase(self, message):
        # Function returns phase of the feedback from database.
        # row.phase value is always 0
        row = self.get_temp_row(message)
        user = row.user_id
        if user == '204695756714834':
            Feedback.objects.filter(id=row.id).delete()
            return 9
        prev_row = self.get_feedback_to_update(user)
        if prev_row == '':
            pprint('No matches in DB')
            return row.phase
        if row.ready:
            return row.phase
        else:
            return prev_row.phase

    def init_answers(self):
        # Function initializes answer list
        # Order of items is important because these are being used with
        # index numbers. ---> bot_answers[currentPhase]
        answers = [
            'Kirjoita lyhyesti palautteesi (10-5000 merkkiä)',
            'Haluatko lisätä kuvan palautteeseen (kyllä/ei)?',
            'Liitä kuva',
            'Haluatko lisätä sijantitiedon palautteeseen (kyllä/ei)?',
            'Liitä sijainti puhelimestasi',
            'Haluatko lisätä osoitteen tai lisätietoja paikasta(kyllä/ei)?',
            'Kirjoita osoite tai lisätiedot paikasta', ]
        return answers

    def cancel_previous_step(self, phase, id):
        if phase == 0:
            Feedback.objects.filter(id=id).update(phase=phase, message='')
        elif phase == 1:
            Feedback.objects.filter(id=id).update(phase=phase)
        elif phase == 2:
            Feedback.objects.filter(id=id).update(phase=phase, media_url='')
        elif phase == 3:
            Feedback.objects.filter(id=id).update(phase=phase)
        elif phase == 4:
            Feedback.objects.filter(id=id).update(
                phase=phase,
                lat_coordinate='',
                long_coordinate='')
        elif phase == 5:
            Feedback.objects.filter(id=id).update(phase=phase)
        elif phase == 6:
            Feedback.objects.filter(id=id).update(phase=phase, address='')

    def save_to_hki_database(self, feedback):
        # Send information to HKI database and returns url to the feedback
        feedback['api_key'] = settings.HELSINKI_API_KEY
        feedback['service_code'] = settings.HELSINKI_API_SERVICE_CODE
        if settings.DEBUG:
            pprint('Information to the API: ', feedback)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response_new_ticket = requests.post(
            settings.HELSINKI_POST_API_URL,
            data=feedback,
            headers=headers)
        url_to_feedback = ''
        new_ticket = response_new_ticket.json()
        if settings.DEBUG:
            pprint(new_ticket)
        for entry in new_ticket:
            if 'code' in entry:
                pprint('ERROR: ', entry['code'])
                pprint('info: ', entry['description'])
                return url_to_feedback
            elif 'service_request_id' in entry:
                break
            else:
                pprint('something wrong with api data')
                pprint(entry)
                return url_to_feedback
        try:
            new_ticket_id = new_ticket[0]['service_request_id']
            if new_ticket_id == 'failureCode':
                return url_to_feedback
            else:
                url1 = 'https://www.hel.fi/helsinki/fi/kaupunki-ja-hallinto'
                url2 = '/osallistu-ja-vaikuta/palaute/nayta-palaute?fid='
                url_to_feedback = '%s%s%s' % (url1, url2, new_ticket_id)
        except KeyError as e:
            pprint('No service_request_id in new data: %s' % (new_ticket))
        return url_to_feedback

    def prepare_ticket(self, feedback, row):
        # Assigns information from database to feedback dictionary
        # and returns feedback dictionary
        feedback['address_string'] = row.street_address
        feedback['description'] = row.message
        feedback['lat'] = row.lat_coordinate
        feedback['long'] = row.long_coordinate
        feedback['media_url'] = row.media_url
        feedback['timestamp'] = row.source_created_at
        return feedback

    def post(self, request, *args, **kwargs):
        # Post function to handle Facebook messages
        feedback = self.init_feedback()
        bot_answers = self.init_answers()
        # Converts the text payload into a python dictionary
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events
                if 'message' in message:
                    bot_answer, query_response = '', ''
                    msg1, msg2, msg3 = '', '', ''
                    msg4, msg5, msg6 = '', '', ''
                    pprint("LET'S GET PHASE NOW!")
                    row = self.get_temp_row(message)
                    feedback['phase'] = self.get_phase(message)
                    pprint('BEFORE CHECK_INPUT PHASE = %s' % (
                        feedback['phase']))
                    pprint(message)
                    input_valid = self.check_input(
                        feedback['phase'],
                        message,
                        row.user_id,
                        bot_answers
                        )
                    if (input_valid == 1 or input_valid == 2 or
                            input_valid == 3):
                        pprint('check_input == true')
                        row = self.get_temp_row(message)
                        user = row.user_id
                        prev_row = self.get_feedback_to_update(user)
                        if input_valid == 3:
                            feedback['phase'] -= 1
                            self.cancel_previous_step(
                                feedback['phase'],
                                prev_row.id)
                            bot_answer = bot_answers[feedback['phase']]
                            post_facebook_message(
                                    message['sender']['id'],
                                    bot_answer)
                            break
                        if feedback['phase'] == 0:
                            pprint('THIS IS PHASE 0')
                            feedback['phase'] = feedback['phase']+1
                            feedback_start_at = datetime.fromtimestamp(
                                message['timestamp']/1000
                                )
                            query_response = Feedback.objects.create(
                                source_created_at=feedback_start_at,
                                user_id=message['sender']['id'],
                                message=message['message']['text'],
                                phase=feedback['phase']
                            )
                            bot_answer = bot_answers[feedback['phase']]

                        elif feedback['phase'] == 1:
                            pprint('THIS IS PHASE 1')
                            if input_valid == 1:
                                feedback['phase'] = feedback['phase']+1
                            elif input_valid == 2:
                                feedback['phase'] = feedback['phase']+2
                            bot_answer = bot_answers[feedback['phase']]
                            query_response = Feedback.objects.filter(
                                id=prev_row.id).update(phase=feedback['phase'])

                        elif feedback['phase'] == 2:
                            pprint('THIS IS PHASE 2')
                            for attachment in (message['message']
                                                      ['attachments']):
                                if 'url' in attachment['payload']:
                                    feedback['url'] = (attachment['payload']
                                                                 ['url'])
                                    break
                            feedback['phase'] = feedback['phase']+1
                            query_response = Feedback.objects.filter(
                                id=prev_row.id).update(
                                phase=feedback['phase'],
                                media_url=row.media_url
                                )
                            bot_answer = bot_answers[feedback['phase']]

                        elif feedback['phase'] == 3:
                            pprint('THIS IS PHASE 3')
                            if input_valid == 1:
                                feedback['phase'] = feedback['phase']+1
                            elif input_valid == 2:
                                feedback['phase'] = feedback['phase']+2
                            bot_answer = bot_answers[feedback['phase']]
                            query_response = Feedback.objects.filter(
                                id=prev_row.id).update(phase=feedback['phase'])

                        elif feedback['phase'] == 4:
                            pprint('THIS IS PHASE 4')
                            for attachment in (message['message']
                                                      ['attachments']):
                                if 'lat' in (attachment['payload']
                                                       ['coordinates']):
                                    feedback['lat'] = (attachment['payload']
                                                       ['coordinates']
                                                       ['lat'])
                                    feedback['long'] = (attachment['payload']
                                                        ['coordinates']
                                                        ['long'])
                                    feedback['phase'] = feedback['phase']+1
                                    break
                            query_response = Feedback.objects.filter(
                                id=prev_row.id).update(
                                phase=feedback['phase'],
                                lat_coordinate=feedback['lat'],
                                long_coordinate=feedback['long']
                                )
                            bot_answer = bot_answers[feedback['phase']]

                        elif feedback['phase'] == 5:
                            pprint('THIS IS PHASE 5')
                            if input_valid == 1:
                                feedback['phase'] = feedback['phase']+1
                                bot_answer = bot_answers[feedback['phase']]
                            elif input_valid == 2:
                                feedback['phase'] = feedback['phase']+2
                                feedback = self.prepare_ticket(
                                    feedback, prev_row)
                                url = self.save_to_hki_database(feedback)
                                if url != '':
                                    msg1 = 'Kiitos palautteestasi! Voit '
                                    msg2 = 'seurata palautteen käsittelyä '
                                    msg3 = 'oheisesta linkistä \n\nVoit '
                                    msg4 = 'aloittaa uuden palautteen '
                                    msg5 = 'kirjoittamalla sen lyhyesti tähän '
                                    msg6 = 'keskusteluun (10-5000 merkkiä)'
                                    bot_answer = '%s%s%s%s%s%s%s' % (
                                        msg1, msg2, url, msg3, msg4, msg5,
                                        msg6)
                                    query_response = Feedback.objects.filter(
                                        id=prev_row.id).update(
                                        phase=feedback['phase'],
                                        ready=True
                                        )
                                else:
                                    feedback['phase'] = 0
                                    msg1 = 'Palautteen tallentaminen epäonnist'
                                    msg2 = 'ui.\n\nVoit yrittää uudelleen kirj'
                                    msg3 = 'oittamalla palautteesi lyhyesti tä'
                                    msg4 = 'hän keskusteluun (10-5000 merkkiä)'
                                    bot_answer = '%s%s%s%s' % (
                                        msg1, msg2, msg3, msg4)
                                    query_response = Feedback.objects.filter(
                                        id=prev_row.id).update(
                                        phase=0,
                                        message='',
                                        lat_coordinate='',
                                        long_coordinate='',
                                        media_url='',
                                        street_address='',
                                        ready=False)
                            query_response = Feedback.objects.filter(
                                id=prev_row.id).update(phase=feedback['phase'])

                        elif feedback['phase'] == 6:
                            pprint('THIS IS PHASE 6')
                            feedback = self.prepare_ticket(feedback, prev_row)
                            feedback['address_string'] = (message['message']
                                                                 ['text'])
                            url = self.save_to_hki_database(feedback)
                            if url != '':
                                msg1 = 'Kiitos palautteestasi! Voit '
                                msg2 = 'seurata palautteen käsittelyä '
                                msg3 = 'oheisesta linkistä \n\nVoit '
                                msg4 = 'aloittaa uuden palautteen '
                                msg5 = 'kirjoittamalla sen lyhyesti tähän '
                                msg6 = 'keskusteluun (10-5000 merkkiä)'
                                bot_answer = '%s%s%s%s%s%s%s' % (
                                    msg1, msg2, url, msg3, msg4, msg5,
                                    msg6)
                                feedback['phase'] = 0
                                query_response = Feedback.objects.filter(
                                    id=prev_row.id).update(
                                    phase=feedback['phase'],
                                    ready=True,
                                    street_address=feedback['address_string']
                                    )
                            else:
                                feedback['phase'] = 0
                                msg1 = 'Palautteen tallentaminen epäonnistui.'
                                msg2 = '\n\nVoit yrittää uudelleen kirjoit'
                                msg3 = 'tamalla palautteesi lyhyesti tähän '
                                msg4 = 'keskusteluun (10-5000 merkkiä).'
                                bot_answer = '%s%s%s%s' % (
                                    msg1, msg2, msg3, msg4)
                                query_response = Feedback.objects.filter(
                                    id=prev_row.id).update(
                                    phase=0,
                                    message='',
                                    lat_coordinate='',
                                    long_coordinate='',
                                    media_url='',
                                    street_address='',
                                    ready=False)

                        elif feedback['phase'] == 9:
                            pprint('THIS IS PHASE 9')
                            pprint('Bot message ignored!')
                            continue

                        else:
                            pprint('PHASE 7 AND 8 ERROR')
                            query_response = Feedback.objects.filter(
                                id=prev_row.id).update(
                                phase=0,
                                message='',
                                lat_coordinate='',
                                long_coordinate='',
                                media_url='',
                                street_address='',
                                ready=False)
                            msg1 = 'Palautteen tallentaminen epäonnistui.'
                            msg2 = '\n\nVoit yrittää uudelleen kirjoit'
                            msg3 = 'tamalla palautteesi lyhyesti tähän '
                            msg4 = 'keskusteluun(10-5000 merkkiä).'
                            bot_answer = '%s%s%s%s' % (
                                msg1, msg2, msg3, msg4)
                        post_facebook_message(
                            message['sender']['id'],
                            bot_answer
                            )
                        Feedback.objects.filter(id=row.id).delete()
                        pprint(query_response)
                    else:
                        pprint('check_input == false')
                        if row.id == '204695756714834':
                            pprint('Bot cannot post to itself')
                        else:
                            if feedback['phase'] == 9:
                                pass
                            else:
                                if feedback['phase'] == 0:
                                    msg1 = 'Virheellinen syöte.'
                                else:
                                    msg1 = 'Virheellinen syöte, voit peruuttaa'
                                    msg2 = 'tämän vaiheen kirjoittamalla '
                                    msg3 = '\'peruuta\''
                                msg4 = bot_answers[feedback['phase']]
                                bot_answer = '%s %s%s\n\n %s' % (
                                    msg1, msg2, msg3, msg4)
                                post_facebook_message(
                                    message['sender']['id'],
                                    bot_answer
                                    )
        return HttpResponse()


def post_facebook_message(fbid, recevied_message):
    post_message_url = '''
    https://graph.facebook.com/v2.6/me/messages?access_token=%s''' % (
        settings.FACEBOOK_PAGE_ACCESS_TOKEN
        )
    response_msg = json.dumps({
        "recipient": {"id": fbid},
        "message": {"text": recevied_message}})
    status = requests.post(
        post_message_url,
        headers={"Content-Type": "application/json"},
        data=response_msg)
    pprint(status.json())
