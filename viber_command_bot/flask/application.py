#!/usr/bin/env python3

import argparse
import json
import logging
import subprocess
import sys
import threading
from logging.handlers import SysLogHandler

from flask import Flask, request, Response
from viberbot.api.messages import URLMessage
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

from viber_command_bot.messages import create_text_message_list
from viber_command_bot.viber import config, viber

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
                            create_text_message_list(text))
        return False
    logger.info('Message from trusted user {} ({}): {}'.format(
        viber_request.sender.name, viber_request.sender.id,
        viber_request.message.text))
    return True


def handle_viber_request(viber_request):
    text = viber_request.message.text.strip()
    if text.startswith('/'):
        execute_command(viber_request, text[1:])
    else:
        text = 'You did not send a command.'
        viber.send_messages(viber_request.sender.id, [TextMessage(text=text)])


def execute_command(viber_request, command):
    logger.info('Command from user {}: {}'.format(
        viber_request.sender.name, command))
    if command == 'help':
        viber.send_messages(viber_request.sender.id,
                            [TextMessage(text=show_command_help())])
    elif command == 'echo':
        viber.send_messages(viber_request.sender.id, [TextMessage(text=':-)')])
    elif command.startswith('echo '):
        messages = create_text_message_list(command[len('echo '):])
        viber.send_messages(viber_request.sender.id, messages)
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
        # Viber bot API expects responses to be quick. The local command
        # might take longer that allowed, so execute them in another thread.
        # The answer is sent when the command is ready.
        command_thread = threading.Thread(
            target=command_thread_target,
            args=(bot_commands[command].get('execute'),
                  bot_commands[command].get('output_format'),
                  viber_request.sender.id,))
        command_thread.start()


def show_command_help():
    text = 'Available commands:\n\n'
    text += '/echo -- Echo the text sent to the bot (internal command).\n'
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
    messages = create_text_message_list(text)
    if media:
        messages.append(URLMessage(media=media))
    viber.send_messages(user_id, messages)


def execute_local_command(command, output_format=None):
    logger.debug('Running command: {}'.format(command))
    p = subprocess.Popen(command, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    output, error = p.communicate()
    rc = p.returncode
    if rc != 0:
        return 'Failed to execute command "{}": {}'.format(
            command, output.decode().strip()), None
    if output_format == 'json':
        message = json.loads(output.decode().strip())
        return message.get('text'), message.get('media')
    return output.decode().strip(), None


def create_bot_commands():
    commands = dict()
    prefix = 'Command '
    for section in [s for s in config.sections() if s.startswith(prefix)]:
        commands[section[len(prefix):].strip()] = dict(config[section])
    return commands


bot_commands = create_bot_commands()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(address='/dev/log')
formatter = logging.Formatter('viber-bot: %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Command bot using Viber')
    parser.add_argument('--debug', type=bool, default=False, help='debug')
    parser.add_argument('--log-level', help='log level')
    parser.add_argument('--listen-address', help='server listen address')
    parser.add_argument('--listen-port', type=int, help='server listen port')
    parser.add_argument('--tls-private-key', help='TLS private key file')
    parser.add_argument('--tls-certificate', help='TLS certificate file')
    parser.add_argument('--webhook', help='webhook for viber')
    parser.add_argument('--register', action='store_true', help='register bot')
    parser.add_argument('--un-register', action='store_true',
                        help='un-register bot')
    parser.set_defaults(log_level='INFO', webhook=config['Viber']['webhook'])
    return parser.parse_args()


if __name__ == '__main__':

    args = parse_command_line_arguments()
    if args.register:
        try:
            print('Registering webhook "{}" ... '.format(args.webhook),
                  end='', flush=True)
            viber.set_webhook(args.webhook)
            print('OK.')
        except Exception as e:
            print('\nERROR: Failed to register bot: {}'.format(e))
            sys.exit(1)
        sys.exit(0)
    if args.un_register:
        try:
            print('Un-registering webhook ... ', end='', flush=True)
            viber.unset_webhook()
            print('OK.')
        except Exception as e:
            print('\nERROR: Failed to un-register bot: {}'.format(e))
            sys.exit(1)
        sys.exit(0)

    # Start Flask development server.
    development_handler = logging.StreamHandler()
    development_formatter = logging.Formatter('%(asctime)s: %(levelname)s: '
                                              '%(name)s: %(message)s')
    development_handler.setFormatter(development_formatter)
    logger.addHandler(development_handler)
    logger.setLevel(args.log_level.upper())
    app.run(host=args.listen_address, port=args.listen_port, debug=args.debug,
            ssl_context=(args.tls_certificate, args.tls_private_key))
