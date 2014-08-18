#!/usr/bin/env python

import opc
from PIL import Image, ImageFilter

import zulip
import requests
import re
import os

ZULIP_USERNAME = "led-bot@students.hackerschool.com"
api_file = open('API_KEY', 'r')
API_KEY = api_file.read()
BOT_EMAIL = "led-bot@students.hackerschool.com"
LED_SCREEN_ADDRESS = '10.0.5.184:7890'
zulipClient = zulip.Client(email=ZULIP_USERNAME, api_key=API_KEY)


class LedScreen:
    def __init__(self, address):
        self.matrixWidth = 64
        self.matrixHeight = 16
        self.matrix_size = self.matrixWidth * self.matrixHeight
        self.ADDRESS = address
        self.opcClient = opc.Client(self.ADDRESS)

    def loadImage(self, filename):
        try:
            self.image = Image.open(filename)
        except:
            print("unable to load image")
        self.imageWidth, self.imageHeight = self.image.size
        print("image loaded: ")
        print(self.image.format, self.image.size, self.image.mode)

    def showImage(self):
        print("showImage")
        if self.opcClient.can_connect():
            print('connected to %s' % self.ADDRESS)
            self._showImage(self.image, self.opcClient)

    def _showImage(self, ledImage, client):
        print("_showImage")
        # Test if it can connect
        my_pixels = []
        for i in xrange(0, self.matrix_size):
            x = i % 64
            y = int(i / 64)
            if (x < self.imageWidth) and (y < self.imageHeight):
                r, g, b, a = ledImage.getpixel((x, y))
                if a == 0:
                    r, g, b = 0, 0, 0
                my_pixels.append((b, g, r))
            else:
                my_pixels.append((0, 0, 0))

        # dump data to LED display
        self.opcClient.put_pixels(my_pixels, channel=0)

    def runCommand(self, command):
        print("running command ", command)
        self.loadImage('megaman.png')
        self.showImage()


def isBotMessage(senderEmail, msgContent):
    matchRule = '^(\\@\\*\\*)*led-bot(\\*\\*)*\s+show'

    # Check that bot is not talking to itself
    if senderEmail == BOT_EMAIL:
        return False

    # Check is message is meant for the bot
    content = msgContent.upper().split()
    print(content)
    if re.match(matchRule, msgContent, flags=re.I or re.X):
        return True

    return False


# Check if message is an undo-command
def isUndo(msgContent):
    content = msgContent.upper().split()
    if (content[0] == "UNDO"):
        return True
    return False


# Get response object for user sent message
def getResponseContent(msg):
    if msg["type"] == "stream":
        # user message was public
        msgTo = msg["display_recipient"]    # name of the stream
    elif msg["type"] == "private":
        # message sent by user is a private stream message
        msgTo = msg["sender_email"]

    msgText = """JUST GIVE ME A SEC I'LL SHOW YOUR STUFF WHEN I HAVE THE TIME
                WE'RE ALL UNDER A LOT OF PRESSURE HERE!!!"""
    resp = {
        "type": msg["type"],
        "subject": msg["subject"],              # topic within the stream
        "to": msgTo,                             # name of the stream
        "content": "%s" % msgText               # message to print to stream
    }

    return resp


# Undo-functionality, sends a patch-request to ZULIP-API, to edit (empty) a message
def undoLastMessage(msg, last_message):
    if not last_message.checkEmpty(msg['display_recipient'], msg['subject']):
        payload = {'message_id': last_message.getMsgId(msg['display_recipient'], msg['subject']),
                   'content': 'NOPE.'
                   }
        url = "https://api.zulip.com/v1/messages"
        return requests.patch(url, data=payload, auth=requests.auth.HTTPBasicAuth(os.environ['ZULIP_USERNAME'], os.environ['ZULIP_API_KEY']))


def parseCommand(content):
    return content


# call respond function when zulipClient interacts with gif bot
def respond(msg):
    # Check if message is meant for the bot
    if isBotMessage(msg['sender_email'], msg['content']):
        resp = getResponseContent(msg)
        print(resp)
        server_response = zulipClient.send_message(resp)

        screen = LedScreen(LED_SCREEN_ADDRESS)
        command = parseCommand(msg['content'])
        screen.runCommand(command)


        # puts messages sent by bot to stack to enable undo functionality
        # TODO: Push undo-message to queue.
        # TODO: If isUndo(msg) pop the latest message, create undo to LED


def main():
    # Get subscriptions to existing streams.
    # TODO: Fetch subscriptions dynamically
    f = open('subscriptions.txt', 'r')


    ZULIP_STREAM_SUBSCRIPTIONS = []

    try:
        for line in f:
            ZULIP_STREAM_SUBSCRIPTIONS.append(line.strip())
    finally:
        f.close()

    # Add subscriptions to bot
    zulipClient.add_subscriptions([{"name": stream_name} for stream_name in ZULIP_STREAM_SUBSCRIPTIONS])

    # This is a blocking call that will run forever, keepalive loop for the bot.
    print("Bot running... ")
    zulipClient.call_on_each_message(respond)

main()
