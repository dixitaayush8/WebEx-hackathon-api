from flask import Blueprint
from flask import request
from flask import jsonify
from flask import Flask
from flask_cors import CORS, cross_origin
import json
import collections
import urllib
import requests
import schedule
from datetime import datetime, timedelta
from src.utils import responses as resp
from src.utils.responses import response_with
from threading import Thread
import time
import sched


main = Blueprint('main', __name__)
CORS(main)

@main.route('/namerecommendations', methods=['GET'])
def recommendations(): #get top (or less) names user had meetings with during the past 28 days
    try:
        test_date = str(datetime.today().replace(second=0, microsecond=0))
        test_date_str = datetime.strptime(test_date, '%Y-%m-%d %H:%M:%S')

        headers = {
            "Authorization": "Bearer token for user",
            "Accept": "*/*"
        }
        params = {
            "from": (test_date_str - timedelta(days=28)).isoformat(),
            "to": test_date_str.isoformat()
        }
        list_of_data = []
        r = requests.get('https://webexapis.com/v1/meetings', headers=headers, params=params) #get info for meetings that happened during the past 28 days from today
        if len(r.json()['items']) > 0:
            list_of_data.append(r.json()['items'])
        final_dict = collections.OrderedDict() #ordered dictionary to map frequency count of "name,email" key
        for i in r.json()['items']: #loop through meetings
            j = requests.get('https://webexapis.com/v1/meetingInvitees?meetingId=' + i['id'], headers=headers) #get full meeting invitee info of each attendee to obtain their name and email
            for s in j.json()['items']:
                if s['displayName'] + ',' + s['email'] not in final_dict:
                    final_dict[s['displayName'] + ',' + s['email']] = 0
                final_dict[s['displayName'] + ',' + s['email']] = final_dict[s['displayName'] + ',' + s['email']] + 1
        final_dict = sorted(final_dict.items(), key=lambda x: x[1], reverse=True) #sort names by highest to lowest frequency count
        c = 0
        final_list = []
        while c < len(final_dict): #extract keys from dictionary
            final_list.append(final_dict[c][0])
            c = c + 1
        jsonified_list = []
        for i in final_list: #create list of dictionaries with name and email
            arr = i.split(',')
            json_dict = dict()
            json_dict['name'] = arr[0]
            json_dict['email'] = arr[1]
            jsonified_list.append(json_dict)
        if len(final_list) == 0:
            return response_with(resp.SUCCESS_200, value={"list": jsonified_list})
        elif len(final_list) < 7:
            return response_with(resp.SUCCESS_200, value={"list" : jsonified_list[0:len(final_list) - 1]})
        return response_with(resp.SUCCESS_200, value={"list" : jsonified_list[0:7]}) #return list of dictionaries with name and email
    except Exception:
        return response_with(resp.INVALID_INPUT_422)

@main.route('/addmeeting', methods=['POST'])
def add_meeting(): #add meeting, create Webex Teams room with meeting host + attendees, automatically send meeting alerts at specified minutes after start time of meeting
    try:
        headers = {
            "Authorization": "Bearer token for USER",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        title = request.json['title']
        password = request.json['password']
        start = request.json['start']
        iso_start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
        end = request.json['end']
        iso_end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
        enabledAutoRecordMeeting = request.json['enabledAutoRecordMeeting']
        allowAnyUserToBeCoHost = request.json['allowAnyUserToBeCoHost']
        invitees = request.json['invitees']
        get_headers = {
            "Authorization": "Bearer token for USER",
            "Accept": "*/*"
        }
        for i in invitees:
            email = i['email'].replace('@', '%40')
            email_endpoint = requests.get('https://webexapis.com/v1/people?email=' + email, headers=get_headers)  # get info for meetings that happened during the past 28 days from today
            for j in email_endpoint.json()['items']:
                i['name'] = j['displayName']
        meetingAgenda = request.json['meetingAgenda']
        body = {
            "title": str(title),
            "password": str(password),
            "start": iso_start.isoformat(),
            "end": iso_end.isoformat(),
            "enabledAutoRecordMeeting": enabledAutoRecordMeeting,
            "allowAnyUserToBeCoHost": allowAnyUserToBeCoHost,
            "invitees": invitees
        }
        r = requests.post('https://webexapis.com/v1/meetings', headers=headers, json=json.dumps(body)) #add meeting
        room_title = r.json()['title']
        room_body = {"title": str(room_title)}
        create_room = requests.post('https://webexapis.com/v1/rooms', headers=headers, json=room_body, verify=True) #create room out of meeting title
        ids = []
        ids.append(r.json()['hostEmail'])
        for i in invitees:
            ids.append(i['email'])
        for j in ids:
            if j == r.json()['hostEmail']:
                membership_body = {
                    "roomId": create_room.json()['id'],
                    "personEmail": j,
                    "isModerator": True
                }
            else:
                membership_body = {
                    "roomId": create_room.json()['id'],
                    "personEmail": j,
                    "isModerator": True
                }
            create_membership = requests.post('https://webexapis.com/v1/memberships', headers=headers, json=membership_body) #add meeting attendees to newly created room
        agenda_plan = ""
        s = sched.scheduler(time.time, time.sleep)
        for i in meetingAgenda:
            agenda_plan = agenda_plan + 'After ' + str(i['minutes']) + ' min(s), ' + i['message'] + '\n'
            iso_agenda_item = datetime.strptime(start, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=i['minutes']) - timedelta(hours=8) #for each meeting agenda item entered, generate exact time in ISO format and offset by minutes entered
            message_body = {"toPersonEmail": r.json()['hostEmail'], "text": i['message']}
            s.enterabs(iso_agenda_item.timestamp(), 1, send_alert, argument=(message_body,)) #schedule notification messages from bot
        send_agenda_to_all_users_body = {"roomId": create_room.json()['id'], "text": agenda_plan}
        send_agenda_to_all_users = requests.post('https://webexapis.com/v1/messages', headers=headers, json=send_agenda_to_all_users_body, verify=True) #send entire agenda to all users in room
        t = Thread(target=run_schedule, args=(s,)) #keep a single thread running to keep track of the scheduled jobs
        t.start()
        return response_with(resp.SUCCESS_200)
    except:
        return response_with(resp.INVALID_INPUT_422)


def run_schedule(s): #keep thread running during Flask session
    while True:
        s.run()
        time.sleep(1)

def send_alert(message_body):
    headers = {
        "Authorization": "Bearer token for BOT",
        "Content-Type": "application/json",
        "Accept": "*/*"
    }
    create_message = requests.post('https://webexapis.com/v1/messages', headers=headers, json=message_body, verify=True) #send message
















