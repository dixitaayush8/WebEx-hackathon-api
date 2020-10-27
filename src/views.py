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


main = Blueprint('main', __name__)
CORS(main)

@main.route('/namerecommendations', methods=['GET'])
def recommendations():
    try:
        test_date = str(datetime.today().replace(second=0, microsecond=0))
        test_date_str = datetime.strptime(test_date, '%Y-%m-%d %H:%M:%S')

        headers = {
            "Authorization": "Bearer NWI3M2I0ZGUtNDYwZC00ZjUxLWI3YjYtZDMyY2U0NTA2ZGM2NzA5ZjE2NjQtODM0_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f",
            "Accept": "*/*"
        }
        params = {
            "from": (test_date_str - timedelta(days=28)).isoformat(),
            "to": test_date_str.isoformat()
        }
        list_of_data = []
        r = requests.get('https://webexapis.com/v1/meetings', headers=headers, params=params)
        if len(r.json()['items']) > 0:
            list_of_data.append(r.json()['items'])
        final_dict = collections.OrderedDict()
        for i in r.json()['items']:
            j = requests.get('https://webexapis.com/v1/meetingInvitees?meetingId=' + i['id'], headers=headers)
            for s in j.json()['items']:
                if s['displayName'] + ',' + s['email'] not in final_dict:
                    final_dict[s['displayName'] + ',' + s['email']] = 0
                final_dict[s['displayName'] + ',' + s['email']] = final_dict[s['displayName'] + ',' + s['email']] + 1
        final_dict = sorted(final_dict.items(), key=lambda x: x[1], reverse=True)
        c = 0
        final_list = []
        while c < len(final_dict):
            final_list.append(final_dict[c][0])
            c = c + 1
        jsonified_list = []
        for i in final_list:
            arr = i.split(',')
            json_dict = dict()
            json_dict['name'] = arr[0]
            json_dict['email'] = arr[1]
            jsonified_list.append(json_dict)
        if len(final_list) == 0:
            return response_with(resp.SUCCESS_200, value={"list": jsonified_list})
        elif len(final_list) < 7:
            return response_with(resp.SUCCESS_200, value={"list" : jsonified_list[0:len(final_list) - 1]})
        return response_with(resp.SUCCESS_200, value={"list" : jsonified_list[0:7]})
    except Exception:
        return response_with(resp.INVALID_INPUT_422)

@main.route('/addmeeting', methods=['POST'])
def add_meeting():
    try:
        headers = {
            "Authorization": "Bearer NWI3M2I0ZGUtNDYwZC00ZjUxLWI3YjYtZDMyY2U0NTA2ZGM2NzA5ZjE2NjQtODM0_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        title = request.json['title']
        password = request.json['password']
        start = request.json['start']
        iso_start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        end = request.json['end']
        iso_end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
        enabledAutoRecordMeeting = request.json['enabledAutoRecordMeeting']
        allowAnyUserToBeCoHost = request.json['allowAnyUserToBeCoHost']
        invitees = request.json['invitees']
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
        r = requests.post('https://webexapis.com/v1/meetings', headers=headers, json=json.dumps(body))
        room_title = r.json()['title']
        room_body = {"title": str(room_title)}
        create_room = requests.post('https://webexapis.com/v1/rooms', headers=headers, json=room_body, verify=True)
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
            create_membership = requests.post('https://webexapis.com/v1/memberships', headers=headers, json=membership_body)
        for i in meetingAgenda:
            iso_agenda_item = datetime.strptime(start, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=i['minutes']) - timedelta(hours=7)
            iso_agenda_item_hour = str(iso_agenda_item.hour)
            iso_agenda_item_min = str(iso_agenda_item.minute)
            if int(iso_agenda_item.hour) < 10:
                iso_agenda_item_hour = '0' + iso_agenda_item_hour
            if int(iso_agenda_item_min) < 10:
                iso_agenda_item_min = '0' + iso_agenda_item_min
            agenda_item_time = iso_agenda_item_hour + ':' + iso_agenda_item_min
            message_body = {"roomId": create_room.json()['id'], "text": i['message']}
            schedule.every().day.at(agenda_item_time).do(send_alert, message_body=message_body, headers=headers)
        t = Thread(target=run_schedule)
        t.start()
        return response_with(resp.SUCCESS_200)
    except Exception:
        return response_with(resp.INVALID_INPUT_422)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def send_alert(message_body, headers):
    create_message = requests.post('https://webexapis.com/v1/messages', headers=headers, json=message_body, verify=True)
    return schedule.CancelJob

