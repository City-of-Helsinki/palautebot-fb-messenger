
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

## Getting the keys

  - **Facebook**
    - Create a facebook page for the bot (if not already done)
      - You need the page id from url
    - Join to Facebook Developer on https://developers.facebook.com/
    - Select My Apps (upper right corner)
    - Select Add a New App
    - fill in the needed info
    - Head over to the Facebook Graph API Explorer https://developers.facebook.com/tools/explorer/
      - On the top right, select the FB App you created from the "Application" drop down list
      - Click "Get User Access Token"
      - Add the manage_pages and publish_pages permission in the checkbox list
      - Click info icon at the left side of generated token
      - Click open in Access Token Tool
      - Click Extend Access Token and Copy the extended token
      - Return to Graph API Explorer in another tab
      - Replace user access token in the access token field with the generated extended user access token
      - Select your page at the dropdown (right side of access token field)
      - Click info icon at the left side of generated token and open in access token tool
      - You should now see that token Expires=Never
      - **You need the following 2 keys**
        - Access Token (Page access token)
        - Page ID

## Issues

  - User can add multiple pictures (by selecting from album and sending all at once) but bot will only save the first picture's url.
  - It's not possible for user to manually reset the bot so that user could start giving new feedback. So there's no abort command but instead after 15 minutes from the start of previous feedback message bot will reset and then user is able to write a feedback again.

## Usage

  - Bot writes a welcome message when user starts a conversation for the first time.
  - User can focus in typing the answers bot is requesting.
  - Bot keeps user informed when information is handled and user is able to write new feedback.

## Code style

  PEP8

## License

[The MIT Licence](https://opensource.org/licenses/MIT)

