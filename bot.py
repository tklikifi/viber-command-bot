#!/usr/bin/env python3

import json
import logging
import sched
import subprocess
import sys
import threading
import time
from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import URLMessage
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest
from config import ConfigError, parse_command_line_arguments, parse_config


args = parse_command_line_arguments()

try:
    config, commands = parse_config(args.config)
except ConfigError as e:
    print(str(e))
    sys.exit(1)

# Set logger.
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - '
                              '%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Configure Viber API.
viber = Api(BotConfiguration(
    auth_token=config['Viber bot']['authentication token'],
    name=config['Viber bot']['name'],
    avatar=config['Viber bot']['avatar']))

app = Flask(__name__)


def check_user_id(user_id, name=None):
    if user_id not in config['Viber bot']['trusted user ids']:
        notify = config['Viber bot']['notify user id']
        text = 'Message from untrusted user id: {} ({})'.format(user_id, name)
        logger.warning(text)
        viber.send_messages(notify, [TextMessage(text=text)])
        return False
    logger.info('Message from trusted user id: {} ({})'.format(user_id, name))
    return True


def handle_viber_request(viber_request):
    message = viber_request.message
    if message.text.startswith('/'):
        # We received a command.
        execute_command(viber_request, message.text[1:])
    else:
        text = 'You did not send a command.'
        viber.send_messages(viber_request.sender.id, [TextMessage(text=text)])


def execute_command(viber_request, command):
    if command == 'help':
        viber.send_messages(viber_request.sender.id,
                            [TextMessage(text=show_command_help())])
    elif command not in commands:
        viber.send_messages(viber_request.sender.id,
                            [TextMessage(text='Command "{}" is not '
                                              'supported.'.format(command))])
    else:
        # Execute local command in another thread.
        command_thread = threading.Thread(
            target=run_command, args=(commands[command]['execute'],
                                      commands[command]['output format'],
                                      viber_request.sender.id,))
        command_thread.start()


def run_command(command, output_format, user_id):
    text, media = execute_local_command(command, output_format)
    if media:
        viber.send_messages(user_id, [TextMessage(text=text),
                                      URLMessage(media=media)])
    else:
        viber.send_messages(user_id, [TextMessage(text=text)])


def show_command_help():
    text = 'Available commands:\n\n'
    for k, v in commands.items():
        text += '/' + k + ' -- '
        if v.get('help') is not None:
            text += v.get('help')
        else:
            text += 'Help is not available for command "{}".'.format(k)
        text += '\n'
    return text


def execute_local_command(command, output_format=None):
    logger.debug('Running command: "{}"'.format(command))
    p = subprocess.Popen(command, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    output, error = p.communicate()
    rc = p.returncode
    if rc != 0:
        return 'Failed to execute command "{}": {}'.format(
            command, error.decode().strip()), None
    if output_format == 'json':
        message = json.loads(output.decode().strip())
        return message.get('message'), message.get('media')
    return output.decode().strip(), None


@app.route('/', methods=['POST'])
def incoming():

    logger.debug('Received request, post data: {0}'.format(
        request.get_data()))

    if not viber.verify_signature(request.get_data(), request.headers.get(
            'X-Viber-Content-Signature')):
        return Response(status=403)

    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberConversationStartedRequest):
        viber.send_messages(viber_request.user.id,
                            [TextMessage(text='Hello, {}!\n\n{}'.format(
                                viber_request.user.name,
                                show_command_help()))])
    elif isinstance(viber_request, ViberMessageRequest):
        if not check_user_id(viber_request.sender.id,
                             name=viber_request.sender.name):
            return Response(status=403)
        handle_viber_request(viber_request)
    elif isinstance(viber_request, ViberSubscribedRequest):
        logger.info('User subscribed: {} ({})'.format(
            viber_request.user.id, viber_request.user.name))
        viber.send_messages(viber_request.user.id,
                            [TextMessage(text='Hello, {}!\n\n{}'.format(
                                viber_request.user.name,
                                show_command_help()))])
    elif isinstance(viber_request, ViberUnsubscribedRequest):
        logger.info('User un-subscribed: {}'.format(viber_request.user_id))
    elif isinstance(viber_request, ViberFailedRequest):
        logger.warning('Client failed receiving message, failure: '
                       '{0}'.format(viber_request))

    return Response(status=200)


if __name__ == '__main__':

    # Set webhook after the server has started.
    def set_webhook():
        viber.set_webhook(config['Viber bot']['webhook'])

    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(5, 1, set_webhook)
    thread = threading.Thread(target=scheduler.run)
    thread.start()

    # Start Flask server.
    app.run(host=config['Flask']['listen address'],
            port=int(config['Flask']['listen port']),
            debug=True, ssl_context=(config['Flask']['certificate'],
                                     config['Flask']['private key']))
