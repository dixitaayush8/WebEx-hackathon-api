from flask import Blueprint
from flask import request
from flask import jsonify
from flask import Flask
from flask_cors import CORS, cross_origin
import collections
import urllib
import requests
from datetime import datetime, timedelta
from src.utils import responses as resp
from src.utils.responses import response_with


main = Blueprint('main', __name__)
CORS(main)

@main.route('/namerecommendations', methods=['GET'])
def recommendations():
    try:
        test_date = str(datetime.today().replace(second=0, microsecond=0))
        test_date_str = datetime.strptime(test_date, '%Y-%m-%d %H:%M:%S')

        headers = {
            "Authorization": "Bearer YzMxNTJmNjYtZTI1Mi00MmFlLWFmNDgtYzAxMzNmZWIxMGFmZmZiOGVkNTktNDU1_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f",
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







