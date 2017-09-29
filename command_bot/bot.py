#!/usr/bin/env python3

import argparse
import json
import logging
import sched
import subprocess
import threading
import time
from viber import commands, viber_config, viber
from flask import Flask, request, Response
from viberbot.api.messages import URLMessage
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

# Set logger.
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - '
                              '%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)


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


def check_user_id(user_id, name='<unknown>'):
    if user_id not in viber_config['trusted user ids']:
        text = 'Message from untrusted user id: {} ({})'.format(user_id, name)
        logger.warning(text)
        viber.send_messages(viber_config['notify user id'],
                            [TextMessage(text=text)])
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
            target=command_thread_target,
            args=(commands[command]['execute'],
                  commands[command]['output format'],
                  viber_request.sender.id,))
        command_thread.start()


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


def command_thread_target(command, output_format, user_id):
    text, media = execute_local_command(command, output_format)
    if media:
        viber.send_messages(user_id, [TextMessage(text=text),
                                      URLMessage(media=media)])
    else:
        viber.send_messages(user_id, [TextMessage(text=text)])


def execute_local_command(command, output_format=None):
    logger.debug('Running command: "{}"'.format(command))
    p = subprocess.Popen(command, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    output, error = p.communicate()
    rc = p.returncode
    if rc != 0:
        return 'Failed to execute command "{}": {}'.format(
            command, output.decode().strip()), None
    if output_format == 'json':
        message = json.loads(output.decode().strip())
        return message.get('message'), message.get('media')
    return output.decode().strip(), None


webhook = viber_config['webhook']


def set_webhook():
    viber.set_webhook(webhook)


# Set webhook after the server has started.
webhook_scheduler = sched.scheduler(time.time, time.sleep)
webhook_scheduler.enter(5, 1, set_webhook)
webhook_thread = threading.Thread(target=webhook_scheduler.run)
webhook_thread.start()


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Command bot using Viber')
    parser.add_argument('--debug', type=bool, default=False, help='debug')
    parser.add_argument('--log-level', help='log level')
    parser.add_argument('--listen-address', help='server listen address')
    parser.add_argument('--listen-port', type=int, help='server listen port')
    parser.add_argument('--tls-private-key', help='TLS private key file')
    parser.add_argument('--tls-certificate', help='TLS certificate file')
    parser.add_argument('--webhook', help='webhook for viber')
    parser.set_defaults(log_level='INFO')
    return parser.parse_args()


if __name__ == '__main__':

    # Start Flask development server.
    args = parse_command_line_arguments()
    logger.setLevel(args.log_level.upper())
    if args.webhook:
        webhook = args.webhook
    app.run(host=args.listen_address, port=args.listen_port, debug=args.debug,
            ssl_context=(args.tls_certificate, args.tls_private_key))