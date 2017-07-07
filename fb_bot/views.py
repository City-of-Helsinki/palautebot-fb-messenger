# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from chatbot import settings
from datetime import datetime
from django.db.models import Q
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
import time

# Create your views here.
class FbBotView(generic.View):
    # WELCOME MESSAGE
    # post_message_url = 'https://graph.facebook.com/v2.6/me/thread_settings?access_token=%s' %(settings.FACEBOOK_PAGE_ACCESS_TOKEN)
    # response_msg = json.dumps({"setting_type":"greeting","greeting":{"text": "This is greeting text"}})
    # status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    # pprint(status.json())

    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == '123456789123456789':
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse("Error, invalid token")

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def init_feedback(self):
        #Function initializes feedback dictionary that holds user's feedback
        #while the script is running
        feedback = {}
        feedback['title'] = 'Facebook messenger feedback'
        feedback['address'] = ''
        feedback['description'] = ''
        feedback['phase'] = 0
        feedback['lat'] = ''
        feedback['long'] = ''
        feedback['media'] = ''
        feedback['timestamp'] = ''
        return feedback

    def is_yes(self, message):
        #Function checks if given message matches acceptable accept_answers
        message = message.lower()
        message = message.strip(',.-!?:;')
        accept_answers = ['kyllä', 'joo', 'juu', 'k']
        if any(message in s for s in accept_answers):
            return True
        else:
            return False

    def is_no(self, message):
        #Function checks if given message matches acceptable decline_answers
        message = message.lower()
        message = message.strip(',.-!?:;')
        decline_answers = ['ei', 'e']
        if any(message in s for s in decline_answers):
            return True
        else:
            return False

    def check_input(self, phase, message):
        #Function checks if aquired message is valid
        #Returns 0 (bad answer), 1 (Yes) or 2(No)

        #check if message has been sent within 15minutes from the start of feedback

        bot_messages = ['Facebook messenger feedback', 
                        'Check input didn\'t pass',
                        'Haluatko lisätä kuvan palautteeseen(kyllä/ei)?',
                        'Haluatko lisätä sijantitiedon palautteeseen(kyllä/ei)?',
                        'Liitä kuva',
                        'Haluatko lisätä osoitteen tai lisätietoja paikasta(kyllä/ei)?',
                        'Liitä sijainti',
                        'Kirjoita osoite tai lisätiedot paikasta']
        #check if message contains the supported information OR bot's own message
        try:
            user_input = message['message']['text']
            if any(user_input in s for s in bot_messages):
                pprint("check_input bot message detected and working")
                return 0
        except (KeyError, TypeError) as e:
            if phase == 2 or phase == 4:
                try:
                    user_input = message['message']['attachments']
                except KeyError:
                    return 0
            else:
                return 0

        #PHASE 0: check if message is between 10 and 5000 marks
        if phase == 0 or phase == 6:
            string_length = len(user_input)
            if (string_length > 10) and (string_length < 5000):
                return 1
            return 0
        #PHASE 1,3,5: check if message contains 'yes', 'no' or invalid message
        elif phase == 1 or phase == 3 or phase == 5:
            if self.is_yes(user_input):
                return 1
            elif self.is_no(user_input):
                return 2
            else:
                return 0

        #PHASE 2: check if User has attached picture
        elif phase == 2:
            for attachment in user_input:
                if 'url' in attachment['payload']:
                    pprint('Picture found in the post')
                    return 1
                else:
                    return 0
            else:
                return 0

        #PHASE 4: check if user has attached location/map
        elif phase == 4:
            for attachment in user_input:
                if 'lat' in attachment['payload']['coordinates'] and 'long' in attachment['payload']['coordinates']:
                    pprint('Location found in the post')
                    return 1
                else:
                    return 0
            else:
                return 0

        #PHASE 9: Bot message doesn't need validating
        elif phase == 9:
            return 0
        return 0

    def get_temp_row(self, message):
        for attachment in message['message']['attachments']:
            try:
                url = attachment['payload']['url']
                new_row, created = Feedback.objects.get_or_create(
                    user_id=message['sender']['id'],
                    message='temp',
                    phase=0,
                    media_url=url
                )
            except KeyError:
                new_row, created = Feedback.objects.get_or_create(
                    user_id=message['sender']['id'],
                    message='temp',
                    phase=0,
                )
        else:
            new_row, created = Feedback.objects.get_or_create(
                user_id=message['sender']['id'],
                message='temp',
                phase=0,
            )
        return new_row

    def get_feedback_to_update(self, user):
        try: 
            prev_row = Feedback.objects.filter(user_id=user).exclude(message='temp').latest('source_created_at')
        except Feedback.DoesNotExist:
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
            # pprint('id: %s\nphase: %s\nsource_created_at: %s\nuser_id: %s\nmessage: %s' % (prev_row.id, prev_row.phase, prev_row.source_created_at, prev_row.user_id, prev_row.message))
            return prev_row.phase

    def save_to_hki_database(self, feedback):
        #Send information to HKI database and return url to the feedback
        return 'www.google.fi'


    # Post function to handle Facebook messages
    def post(self, request, *args, **kwargs):
        feedback = self.init_feedback()
        # Converts the text payload into a python dictionary
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        # pprint(incoming_message)
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events 
                if 'message' in message:
                    bot_answer = ''
                    row = self.get_temp_row(message)
                    feedback['phase'] = self.get_phase(message)
                    pprint('BEFORE CHECK_INPUT PHASE: %s' %(feedback['phase']))
                    pprint(message)
                    user_input_valid = self.check_input(feedback['phase'], message)
                    if user_input_valid == 1 or user_input_valid == 2:
                        pprint('check_input == true')
                        row = self.get_temp_row(message)
                        user = row.user_id
                        prev_row = self.get_feedback_to_update(user)
                        if feedback['phase']== 0:
                            pprint('THIS IS PHASE 0')
                            feedback['phase'] = feedback['phase']+1
                            feedback_start_at = datetime.fromtimestamp(message['timestamp']/1000)
                            query_response = Feedback.objects.create(
                                source_created_at=feedback_start_at,
                                user_id=message['sender']['id'],
                                message=message['message']['text'],
                                phase= feedback['phase']
                            )
                            bot_answer = 'Haluatko lisätä kuvan palautteeseen(kyllä/ei)?'

                        elif feedback['phase'] == 1:
                            pprint('THIS IS PHASE 1')
                            if user_input_valid == 1:
                                feedback['phase'] = feedback['phase']+1
                                bot_answer = 'Liitä kuva'
                            elif user_input_valid == 2:
                                feedback['phase'] = feedback['phase']+2
                                bot_answer = 'Haluatko lisätä sijantitiedon palautteeseen(kyllä/ei)?'
                            query_response = Feedback.objects.filter(id=prev_row.id).update(phase=feedback['phase'])

                        elif feedback['phase'] == 2:
                            pprint('THIS IS PHASE 2')
                            for attachment in message['message']['attachments']:
                                if 'url' in attachment['payload']:
                                    feedback['url'] = attachment['payload']['url']
                                    break
                            feedback['phase'] = feedback['phase']+1
                            query_response = Feedback.objects.filter(id=prev_row.id).update(phase=feedback['phase'], media_url=feedback['media'])
                            bot_answer = 'Haluatko lisätä sijantitiedon palautteeseen(kyllä/ei)?'

                        elif feedback['phase'] == 3:
                            pprint('THIS IS PHASE 3')
                            if user_input_valid == 1:
                                feedback['phase'] = feedback['phase']+1
                                bot_answer = 'Liitä sijainti'
                            elif user_input_valid == 2:
                                feedback['phase'] = feedback['phase']+2
                                bot_answer = 'Haluatko lisätä osoitteen tai lisätietoja paikasta(kyllä/ei)?'
                            query_response = Feedback.objects.filter(id=prev_row.id).update(phase=feedback['phase'])

                        elif feedback['phase'] == 4:
                            pprint('THIS IS PHASE 4')
                            for attachment in message['message']['attachments']:
                                if 'lat' in attachment['payload']['coordinates']:
                                    feedback['lat'] = attachment['payload']['coordinates']['lat']
                                    feedback['long'] = attachment['payload']['coordinates']['long']
                                    break
                            query_response = Feedback.objects.filter(id=prev_row.id).update(phase=feedback['phase'], lat_coordinate=feedback['lat'], long_coordinate=feedback['long'])
                            bot_answer = 'Haluatko lisätä osoitteen tai lisätietoja paikasta(kyllä/ei)?'

                        elif feedback['phase'] == 5:
                            pprint('THIS IS PHASE 5')
                            if user_input_valid == 1:
                                feedback['phase'] = feedback['phase']+1
                                bot_answer = 'Kirjoita osoite tai lisätiedot paikasta'
                            elif user_input_valid == 2:
                                feedback['phase'] = feedback['phase']+2
                                bot_answer = 'Kiitos palautteestasi! Voit seurata palautteen käsittelyä oheisesta linkistä %s\n\n Voit antaa uuden palautteen kirjoittamalla sen lyhyesti tähän keskusteluun (10-5000 merkkiä)' % (url)
                                url = self.save_to_hki_database(feedback)
                                if  url != '':
                                    query_response = Feedback.objects.filter(id=prev_row.id).update(phase=feedback['phase'], ready=True)
                                else:
                                    post_facebook_message(message['sender']['id'], 'Viestin tallentaminen hki tietokantaan epäonnistui')
                            query_response = Feedback.objects.filter(id=prev_row.id).update(phase=feedback['phase'])

                        elif feedback['phase'] == 6:
                            pprint('THIS IS PHASE 6')
                            bot_answer = 'Kiitos palautteestasi! Voit seurata palautteen käsittelyä oheisesta linkistä %s\n\n Voit antaa uuden palautteen kirjoittamalla sen lyhyesti tähän keskusteluun (10-5000 merkkiä)' % (url)
                            feedback['address'] = message['message']['text']
                            url = self.save_to_hki_database(feedback)
                            if  url != '':
                                query_response = Feedback.objects.filter(id=prev_row.id).update(phase=feedback['phase'], ready=True, street_address=feedback['address'])
                            else:
                                post_facebook_message(message['sender']['id'], 'Viestin tallentaminen hki tietokantaan epäonnistui')

                        elif feedback['phase'] == 9:
                            pprint('THIS IS PHASE 9')
                            pprint('Bot message ignored!')
                            continue
                        else:
                            pprint('THIS IS PHASE 7-8 THAT SHOULD NOT HAPPEN')
                        post_facebook_message(message['sender']['id'], bot_answer)
                        Feedback.objects.filter(id=row.id).delete()
                        pprint(query_response)
                    else:
                        pprint('check_input == false')
                        if row.id == '204695756714834':
                            pprint('Bot cannot post to itself')
                        else:
                            post_facebook_message(message['sender']['id'], 'Check input didn\'t pass')
        return HttpResponse()

def post_facebook_message(fbid, recevied_message):
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=%s' %(settings.FACEBOOK_PAGE_ACCESS_TOKEN)
    response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":recevied_message}})
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    pprint(status.json())
