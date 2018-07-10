from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from slackclient import SlackClient
from apiclient import discovery 
from oauth2client.client import flow_from_clientsecrets
from events.models import slackUserModel  
from events.models import CredentialsModel 
from django.http import HttpResponseRedirect 
import httplib2
from datetime import datetime, timedelta
import requests
import json

SLACK_VERIFICATION_TOKEN = getattr(settings, 'SLACK_VERIFICATION_TOKEN', None)
SLACK_BOT_USER_TOKEN = getattr(settings,                          #2
'SLACK_BOT_USER_TOKEN', None)                                     #
Client = SlackClient(SLACK_BOT_USER_TOKEN)                        #3


FLOW = flow_from_clientsecrets(
    settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON,
    scope='https://www.googleapis.com/auth/calendar',
    redirect_uri=settings.GOOGLE_CALENDAR_REDIRECT_URL,
    prompt="consent")

def get_calendar_service(credential):
    credentials = credential
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service  


def get_mail_id_from_slack(token, user_id):
    """
    Get the user's mail id from slack
    """
    URL = "https://slack.com/api/users.info?token={}&user={}&include_locale=True&pretty=1".format(
        token, user_id)
    response = requests.get(URL)
    json_response = json.loads(response.text)
    email_id = json_response["user"]["profile"]["email"]
    return email_id



class Events(APIView):
    def post(self, request, *args, **kwargs):

        slack_message = request.data

        if slack_message.get('token') != SLACK_VERIFICATION_TOKEN:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # verification challenge
        if slack_message.get('type') == 'url_verification':
            return Response(data=slack_message,
                            status=status.HTTP_200_OK)
        # greet bot
        if 'event' in slack_message:                              #4
            event_message = slack_message.get('event')            #
            print('////',event_message,'/////','/n')
            # ignore bot's own message
            if event_message.get('subtype') == 'bot_message':     #5
                return Response(status=status.HTTP_200_OK)        #
            
            # process user's message
            userName = event_message.get('user')    
            # print(slackUserModel.objects.filter(user=userName))

            try:
                slack_user = slackUserModel.objects.get(user=userName)
            except:
                slackUserModel(user=userName).save()

            if slack_user:
                # for credential models
                auth_url = FLOW.step1_get_authorize_url()
                channel = event_message.get('channel') 

                if CredentialsModel.objects.all().first():
                    credential = CredentialsModel.objects.all().first()
                    service = get_calendar_service(credential.credential)
                    # print(service)
                else:
                    Client.api_call(method='chat.postMessage',        #8
                        channel=channel,                  #
                        text= auth_url)
                    return Response(status=status.HTTP_200_OK)

                text = event_message.get('text')
                try:  
                    task = text.split(':')[0]
                    if 'task' in  task.lower():
                        tail = text.split(':')[1]
                        assignee_user = tail.split(',')[0]
                        task_priority = tail.split(',')[1]
                        task_name = task_priority.split('|')[0]             #
                        priority = task_priority.split('|')[1]  
                        channel = event_message.get('channel') 
                        assignee_slack_id = assignee_user.split("<@")[1].split('>')[0]

                        mail_id = get_mail_id_from_slack(SLACK_BOT_USER_TOKEN,assignee_slack_id )

                        calender_list = service.calendarList().list().execute()
                        time_zone = calender_list['items'][0]['timeZone']
                        event = {
                            'summary': task_name,
                            # 'location': '800 Howard St., San Francisco, CA 94103',
                            'description': priority,
                            'start': {
                                'dateTime': str(datetime.now().isoformat()),
                                'timeZone': time_zone,
                            },
                            'end': {
                                'dateTime': str((datetime.now()+ timedelta(hours=24)).isoformat()),
                                'timeZone': time_zone,
                            },
                            # 'recurrence': [
                            #     'RRULE:FREQ=DAILY;COUNT=2'
                            # ],
                            'attendees': [
                                {'email': mail_id },
                            ],
                            'reminders': {
                                'useDefault': False,
                                'overrides': [
                                {'method': 'email', 'minutes': 24 * 60},
                                {'method': 'popup', 'minutes': 10},
                                ],
                            },
                            }

                        event = service.events().insert(calendarId='primary', body=event).execute()
                        # print ('Event created: %s' % (event.get('htmlLink')))
                        reply = 'Hi task is assigned successfully,' + (event.get('htmlLink')) 
                except:
                    reply = 'Please mention the task in correct format'

                Client.api_call(method='chat.postMessage',        #8
                                channel=channel,                  #
                                text= reply)
                return Response(status=status.HTTP_200_OK)


        return Response(status=status.HTTP_200_OK)
    

def auth_return(request):
    credential = FLOW.step2_exchange(request.GET)
    CredentialsModel(credential=credential).save()
    return HttpResponseRedirect("/")


        

