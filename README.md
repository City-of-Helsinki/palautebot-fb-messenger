
# Palaute-Bot

## Requirements

  - **for deploying**
    - Facebook Account and keys (with valid phone number)
    - Facebook page for palautebot with instant messaging enabled

  - **for facebook app review**
    - Link to the updated privacy policy
    - Icon (1024x1024)




FACEBOOK_PAGE_ID= ''
FACEBOOK_PAGE_ACCESS_TOKEN = ''
HELSINKI_API_KEY = ''

## Setting up Facebook Messenger Bot

- Create a facebook page for the bot (if not already done)
  - **You need the page id from url**
- Join to Facebook Developer on https://developers.facebook.com/
- Select My Apps (upper right corner)
- Select Add a New App
- fill in the name for your app
- Select Messenger as a product for your app
- Under Token Generation section
  - Select the facebook page that you created for the bot
  - Authorize the app from the pop up window
    - **You need the generated Page Access Token**

- From the next Section (Webhooks) click Setup Webhooks
  - **To the Callback URL field paste url you've gotten from the supplier (haltu)**
  - **To the Verify Token field paste url you've gotten from the supplier (haltu)**
  - Check following boxes
    - **messages**
    - **message_postbacks**
    - **message_deliveries**
    - **message_optins**

- From the next Section (App Review for Messenger) add to submission the following:
  - Pages_messaging
  - Pages-messaging-subscriptions

- From Current Submission section below click edit notes of pages_messaging
  - select the created page for bot
  - Select "your messenger experience includes automated replies"
  - Fill in following bot commands to the form:
    - Command: 'Peruuta'
      - Reply: 'bot goes backwards one step'
    - Command: 'kyllä'
      - Reply: 'Accept'
    - Command: 'ei'
      - Reply: 'Decline'
  - Add following text to Optional Notes for Reviewer:
    - "This bot designed to gather feedback for the City of Helsinki. It doesn't work with specific commands but it requests user input and sends user's messages to the database where they are handled. 
    Bot has few commands to make the user experience more smooth but none of them provide specific answer because user can type them in multiple situations."

- From left side of the screen click settings tab
  - Fill in privacy policy URL
  - Fill in correct Contact email (if not already set)
  - Add App Icon
  - Choose a app category

- After adding these you should be all set to send the app to the review
- From the left side menu click messenger
  - Scroll down and click "Submit For Review" from Current Submission section

## Issues

  - User can add multiple pictures (by selecting from album and sending all at once) but bot will only save the first picture's url.
  - It's not possible for user to manually reset the bot so that user could start giving new feedback. So there's no abort command but instead after 15 minutes from the start of previous feedback message bot will reset and then user is able to write a feedback again.
  - Desktop users cannot add location

## Usage

  - Bot writes a welcome message when user starts a conversation for the first time.
  - User can focus in typing the answers bot is requesting.
  - Bot keeps user informed when information is handled and user is able to write new feedback.

## Code style

  PEP8

## License

[The MIT Licence](https://opensource.org/licenses/MIT)

