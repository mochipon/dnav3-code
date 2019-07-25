#!/usr/bin/env python
#  -*- coding: utf-8 -*-
"""A simple bot script, built on Flask.

This sample script leverages the Flask web service micro-framework
(see http://flask.pocoo.org/).  By default the web server will be reachable at
port 5000 you can change this default if desired (see `flask_app.run(...)`).

ngrok (https://ngrok.com/) can be used to tunnel traffic back to your server
if your machine sits behind a firewall.

You must create a Webex Teams webhook that points to the URL where this script
is hosted.  You can do this via the WebexTeamsAPI.webhooks.create() method.

Additional Webex Teams webhook details can be found here:
https://developer.webex.com/webhooks-explained.html

A bot must be created and pointed to this server in the My Apps section of
https://developer.webex.com.  The bot's Access Token should be added as a
'WEBEX_TEAMS_ACCESS_TOKEN' environment variable on the web server hosting this
script.

This script supports Python versions 2 and 3.

Copyright (c) 2016-2019 Cisco and/or its affiliates.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


# Use future for Python v2 and v3 compatibility
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)
from builtins import *


__author__ = "Chris Lunsford"
__author_email__ = "chrlunsf@cisco.com"
__contributors__ = ["Brad Bester <brbester@cisco.com>"]
__copyright__ = "Copyright (c) 2016-2019 Cisco and/or its affiliates."
__license__ = "MIT"

import sys
import os

from flask import Flask, request
from ciscosparkapi import CiscoSparkAPI, Webhook
import requests


# Find and import urljoin
if sys.version_info[0] < 3:
    from urlparse import urljoin
else:
    from urllib.parse import urljoin


# Get the absolute path for the directory where this file is located "here"
here = os.path.abspath(os.path.dirname(__file__))

# Get the absolute path for the project / repository root
project_root = os.path.abspath(os.path.join(here, '../..'))

# Extend the system path to include the project root and import the env files
sys.path.insert(0, project_root)
import env_user     # noqa


# Module constants
WEATHER_FORCAST_URL = 'http://weather.livedoor.com/forecast/webservice/json/v1?city=200010'


# Initialize the environment
# Create the web application instance
flask_app = Flask(__name__)
# Create the Webex Teams API connection object
api = CiscoSparkAPI(access_token=env_user.SPARK_BOT_ACCESS_TOKEN)


# Helper functions
def get_forcasts():
    """Get weather forcasts from Weather Hack and return it as a list.

    Functions for Soundhound, Google, IBM Watson, or other APIs can be added
    to create the desired functionality into this bot.

    """
    response = requests.get(WEATHER_FORCAST_URL, verify=False)
    response.raise_for_status()
    json_data = response.json()
    return json_data['forecasts']


# Core bot functionality
# Your Webex Teams webhook should point to http://<serverip>:5000/events
@flask_app.route('/events', methods=['POST'])
def webex_teams_webhook_events():
    """Respond to inbound webhook JSON HTTP POST from Webex Teams."""

    # Get the POST data sent from Webex Teams
    json_data = request.json
    print("\n")
    print("WEBHOOK POST RECEIVED:")
    print(json_data)
    print("\n")

    # Create a Webhook object from the JSON data
    webhook_obj = Webhook(json_data)
    # Get the room details
    room = api.rooms.get(webhook_obj.data.roomId)
    # Get the message details
    message = api.messages.get(webhook_obj.data.id)
    # Get the sender's details
    person = api.people.get(message.personId)

    print("NEW MESSAGE IN ROOM '{}'".format(room.title))
    print("FROM '{}'".format(person.displayName))
    print("MESSAGE '{}'\n".format(message.text))

    # This is a VERY IMPORTANT loop prevention control step.
    # If you respond to all messages...  You will respond to the messages
    # that the bot posts and thereby create a loop condition.
    me = api.people.me()
    if message.personId == me.id:
        # Message was sent by me (bot); do not respond.
        print("THIS IS FROM ME!")
        return 'OK'

    else:
        # Message was sent by someone else; parse message and respond.
        if "today" in message.text:
            print("FOUND 'today'")
            # Get a forcast
            forcast = get_forcasts()[0]

            message = "今日の天気は{}".format(forcast['telop'])

            print("SENDING A MESSAGE '{}'".format(message))
            # Post the message to the room where the request was received
            api.messages.create(room.id, text=message)
        return 'OK'


if __name__ == '__main__':
    # Start the Flask web server
    flask_app.run(host='0.0.0.0', port=5000)
