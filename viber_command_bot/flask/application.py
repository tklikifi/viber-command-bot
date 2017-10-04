#!/usr/bin/env python3

"""
Viber command bot Flask application
"""

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
def bot_request():
    """
    Receive bot request from Viber service.

    :return: Response(status=200), if request is successful
             Response(status=403), if request is not allowed
    """

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
                                command_help()))])
    elif isinstance(viber_request, ViberMessageRequest):
        if not check_user_id(viber_request):
            return Response(status=403)
        handle_viber_request(viber_request)
    elif isinstance(viber_request, ViberSubscribedRequest):
        logger.info('User "{}" subscribed as user id "{}"'.format(
            viber_request.user.name, viber_request.user.id))
        viber.send_messages(viber_request.user.id,
                            [TextMessage(text='Hello, {}!\n\n{}'.format(
                                viber_request.user.name,
                                command_help()))])
    elif isinstance(viber_request, ViberUnsubscribedRequest):
        logger.info('User id "{}" un-subscribed'.format(viber_request.user_id))
    elif isinstance(viber_request, ViberFailedRequest):
        logger.warning('Client failed receiving message, failure: '
                       '{0}'.format(viber_request))

    return Response(status=200)


def check_user_id(viber_request):
    """
    Check that the request comes from a trusted user id.

    :param viber_request: request from Viber service
    :return: True, if request is from trusted user id
             False, if request comes from un-trusted user id
    """
    if viber_request.sender.id not in config['Viber']['trusted_user_ids']:
        text = ('Received message from un-trusted user "{}" (user id "{}"): '
                '{}'.format(viber_request.sender.name, viber_request.sender.id,
                           viber_request.message.text))
        logger.warning(text)
        viber.send_messages(config['Viber']['notify_user_id'],
                            create_text_message_list(text))
        return False
    logger.info('Received message from trusted user "{}" (user id "{}"): '
                '{}'.format(viber_request.sender.name, viber_request.sender.id,
                            viber_request.message.text))
    return True


def handle_viber_request(viber_request):
    """
    Checks that Viber request is a command.

    :param viber_request: request from Viber service
    :return: None
    """
    text = viber_request.message.text.strip()
    if text.startswith('/'):
        execute_command(viber_request, text[1:])
    else:
        text = 'You did not send a command, try "/help".'
        viber.send_messages(viber_request.sender.id, [TextMessage(text=text)])


def execute_command(viber_request, command):
    """
    Executes command received in Viber request.

    :param viber_request: request from Viber service
    :param command: command found in request
    :return: None
    """
    logger.info('Received command "{}" from user "{}"'.format(
        command, viber_request.sender.name))
    if command == 'help':
        viber.send_messages(viber_request.sender.id,
                            [TextMessage(text=command_help())])
    elif command == 'echo':
        viber.send_messages(viber_request.sender.id, [TextMessage(text=':-)')])
    elif command.startswith('echo '):
        messages = create_text_message_list(command[len('echo '):])
        viber.send_messages(viber_request.sender.id, messages)
    elif command not in bot_commands:
        logger.warning('Un-supported command "{}" from user "{}"'.format(
            command, viber_request.sender.name))
        viber.send_messages(
            viber_request.sender.id,
            [TextMessage(text='Command "{}" is not supported, '
                              'try "/help".'.format(command))])
    elif 'execute' not in bot_commands[command]:
        logger.error('Execute parameter is not configured for command '
                     '"{}"'.format(command))
        viber.send_messages(viber_request.sender.id,
                            [TextMessage(text='Command "{}" is not properly '
                                              'configured.'.format(command))])
    elif bot_commands[command].get('output_format', 'text') not in [
        'text', 'json']:
        logger.error('Output format parameter is not properly configured for '
                     'command "{}" ("{}" should be "text" or "json")'.format(
            command, bot_commands[command].get('output_format')))
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
                  bot_commands[command].get('output_format', 'text'),
                  viber_request.sender.id,))
        command_thread.start()


def command_help():
    """
    Creates help text for the available commands.

    :return: help text
    """
    help = dict((k, bot_commands[k].get('help')) for k in bot_commands.keys())
    help['echo'] = 'Echo the text sent to the bot (internal command).'
    text = 'Available commands:\n\n'
    for k, v in sorted(help.items()):
        text += '/' + k + ' -- '
        if v is not None:
            text += v
        else:
            text += 'Help is not available for command "{}".'.format(k)
        text += '\n'
    return text


def command_thread_target(execute, output_format, user_id):
    """
    Local command is run in a separate thread.

    :param execute: local command to execute
    :param output_format: expected command output format specified in the bot
                          configuration
    :param user_id: user id who will receive the answer
    :return: None
    """
    text, media = execute_local_command(execute, output_format)
    messages = create_text_message_list(text)
    if media:
        messages.append(URLMessage(media=media))
    viber.send_messages(user_id, messages)


def execute_local_command(execute, output_format=None):
    """
    Execute local command in another process.

    :param execute: command found
    :param output_format:
    :return: (message text, optional media url)
    """
    logger.debug('Running command "{}"'.format(execute))
    p = subprocess.Popen(execute, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    output, error = p.communicate()
    rc = p.returncode
    if rc != 0:
        return 'Failed to execute command "{}": {}'.format(
            execute, output.decode().strip()), None
    if output_format == 'json':
        try:
            message = json.loads(output.decode().strip())
        except ValueError:
            logger.error('Command "{}" output was not JSON: {}'.format(
                execute, output.decode().strip()))
            return ('Failed to execute command "{}": Command output '
                    'was not JSON'.format(execute), None)
        return message.get('text'), message.get('media')
    return output.decode().strip(), None


def create_bot_commands():
    """
    Create bot commands dict from the bot configuration.

    :return: commands dict
    """
    commands = dict()
    prefix = 'Command '
    for section in [s for s in config.sections() if s.startswith(prefix)]:
        commands[section[len(prefix):].strip()] = dict(config[section])
    return commands


bot_commands = create_bot_commands()

log_level = config.get('Logger', 'level', fallback='INFO').upper()
use_syslog = config.getboolean('Logger', 'syslog', fallback=True)
log_file = config.get('Logger', 'file', fallback=None)

logger = logging.getLogger()
logger.setLevel(log_level)

if use_syslog:
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    formatter = logging.Formatter('viber-bot: %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

if log_file:
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: '
                                  '%(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def parse_command_line_arguments():
    """
    Parse command line arguments of the development server.

    :return: arguments
    """
    parser = argparse.ArgumentParser(description='Command bot using Viber')
    parser.add_argument('--debug', type=bool, default=False, help='debug')
    parser.add_argument('--listen-address', help='server listen address')
    parser.add_argument('--listen-port', type=int, help='server listen port')
    parser.add_argument('--tls-private-key', help='TLS private key file')
    parser.add_argument('--tls-certificate', help='TLS certificate file')
    parser.add_argument('--webhook', help='webhook for viber')
    parser.add_argument('--register', action='store_true', help='register bot')
    parser.add_argument('--un-register', action='store_true',
                        help='un-register bot')
    parser.set_defaults(webhook=config['Viber']['webhook'])
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
    app.run(host=args.listen_address, port=args.listen_port, debug=args.debug,
            ssl_context=(args.tls_certificate, args.tls_private_key))
