#!/usr/bin/env python3

import argparse
import json
import logging
import sched
import subprocess
import threading
import time
from flask import Flask, request, Response
from logging.handlers import SysLogHandler
from viber import config, create_text_messages, viber
from viberbot.api.messages import URLMessage
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest


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
        if not check_user_id(viber_request):
            return Response(status=403)
        handle_viber_request(viber_request)
    elif isinstance(viber_request, ViberSubscribedRequest):
        logger.info('User subscribed: {} ({})'.format(
            viber_request.user.name, viber_request.user.id))
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


def check_user_id(viber_request):
    if viber_request.sender.id not in config['Viber']['trusted_user_ids']:
        text = 'Message from untrusted user {} ({}): {}'.format(
            viber_request.sender.name, viber_request.sender.id,
            viber_request.message.text)
        logger.warning(text)
        viber.send_messages(config['Viber']['notify_user_id'],
                            create_text_messages(text))
        return False
    logger.info('Message from trusted user {} ({}): {}'.format(
        viber_request.sender.name, viber_request.sender.id,
        viber_request.message.text))
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
    logger.info('Command from user {}: {}'.format(
        viber_request.sender.name, command))
    if command == 'help':
        viber.send_messages(viber_request.sender.id,
                            [TextMessage(text=show_command_help())])
    elif command not in bot_commands:
        logger.warning('Un-supported command from {}: {}'.format(
            viber_request.sender.name, command))
        viber.send_messages(viber_request.sender.id,
                            [TextMessage(text='Command "{}" is not '
                                              'supported.'.format(command))])
    elif 'execute' not in bot_commands[command]:
        logger.warning('Execute parameter not configured for command: '
                       '{}'.format(command))
        viber.send_messages(viber_request.sender.id,
                            [TextMessage(text='Command "{}" is not properly '
                                              'configured.'.format(command))])
    else:
        # Execute local command in another thread.
        command_thread = threading.Thread(
            target=command_thread_target,
            args=(bot_commands[command].get('execute'),
                  bot_commands[command].get('output_format'),
                  viber_request.sender.id,))
        command_thread.start()


def show_command_help():
    text = 'Available commands:\n\n'
    for k, v in bot_commands.items():
        text += '/' + k + ' -- '
        if v.get('help') is not None:
            text += v.get('help')
        else:
            text += 'Help is not available for command "{}".'.format(k)
        text += '\n'
    return text


def command_thread_target(command, output_format, user_id):
    text, media = execute_local_command(command, output_format)
    messages = create_text_messages(text)
    if media:
        messages.append(URLMessage(media=media))
    viber.send_messages(user_id, messages)


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


def create_bot_commands():
    commands = dict()
    prefix = 'Command '
    for section in [s for s in config.sections() if s.startswith(prefix)]:
        commands[section[len(prefix):].strip()] = dict(config[section])
    return commands


def set_webhook():
    viber.set_webhook(webhook)


bot_commands = create_bot_commands()

# Set loggers.
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(address = '/dev/log')
formatter = logging.Formatter('viber-bot: %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Set webhook after the server has started.
webhook = config['Viber']['webhook']
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
    debug_handler = logging.StreamHandler()
    debug_formatter = logging.Formatter('%(asctime)s: %(levelname)s: '
                                        '%(name)s: %(message)s')
    debug_handler.setFormatter(debug_formatter)
    logger.addHandler(debug_handler)
    logger.setLevel(args.log_level.upper())
    if args.webhook:
        webhook = args.webhook
    app.run(host=args.listen_address, port=args.listen_port, debug=args.debug,
            ssl_context=(args.tls_certificate, args.tls_private_key))
