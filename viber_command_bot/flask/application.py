#!/usr/bin/env python3

"""
Viber command bot Flask application
"""

import json
import logging
import re
import socket
import subprocess
import threading
from logging.handlers import SysLogHandler

from flask import Flask, request, Response
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

from viber_command_bot.info import info
from viber_command_bot.messages import send_message
from viber_command_bot.cache import cache
from viber_command_bot.config import config
from viber_command_bot.viber import viber


NOTE = re.compile('^note(?P<n>\d+)$')
REMOVENOTE = re.compile('^removenote(?P<n>\d+)$')


app = Flask(__name__)


@app.route('/', methods=['POST'])
def bot_request():
    """
    Receive bot request from Viber service.

    :return: Response(status=200), if request is successful
             Response(status=403), if request is not allowed
    :raises Exception: if message sending fails
    """

    logger.debug('Received request, post data: {0}'.format(
        request.get_data()))

    if not viber.verify_signature(request.get_data(), request.headers.get(
            'X-Viber-Content-Signature')):
        return Response(status=403)

    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberConversationStartedRequest):
        cache.conversation_started(viber_request.user.id,
                                   viber_request.user.name)
        send_message(viber_request.user.id,
                     'Hello, {}!\n\n{}'.format(
                         viber_request.user.name, command_help()))
    elif isinstance(viber_request, ViberMessageRequest):
        if not check_user_id(viber_request):
            return Response(status=403)
        handle_viber_request(viber_request)
    elif isinstance(viber_request, ViberSubscribedRequest):
        logger.info('User "{}" subscribed as user id "{}"'.format(
            viber_request.user.name, viber_request.user.id))
        cache.subscribe_user(viber_request.user.id, viber_request.user.name)
        send_message(viber_request.user.id,
                     'Hello, {}!\n\n{}'.format(
                         viber_request.user.name, command_help()))
    elif isinstance(viber_request, ViberUnsubscribedRequest):
        logger.info('User id "{}" un-subscribed'.format(viber_request.user_id))
        cache.unsubscribe_user(viber_request.user_id)
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
    :raises Exception: if message sending fails
    """
    if viber_request.sender.id not in config.get('Viber', 'trusted_user_ids'):
        text = ('Received message from un-trusted user "{}" (user id "{}"): '
                '{}'.format(viber_request.sender.name, viber_request.sender.id,
                            viber_request.message.text))
        logger.warning(text)
        send_message(config.get('Viber', 'notify_user_id'), text)
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
    :raises Exception: if message sending fails
    """
    text = viber_request.message.text.strip()
    cache.refresh_user(viber_request.sender.id, viber_request.sender.name)
    cache.publish(viber_request.sender.id, text,
                  name=viber_request.sender.name)
    if text.startswith('/'):
        execute_command(viber_request, text[len('/'):].strip())


def execute_command(viber_request, command):
    """
    Executes command received in Viber request.

    :param viber_request: request from Viber service
    :param command: command found in request
    :return: None
    :raises Exception: if message sending fails
    """
    destination = list()
    if '@' in command:
        # Destination is a comma separated list of hosts.
        command, destination = command.split('@', 1)
        destination = destination.split(',')
    logger.info('Received command "{}" from user "{}"'.format(
        command, viber_request.sender.name))
    if not command or command == 'help':
        send_message(viber_request.sender.id, command_help())
    elif command == 'version':
        send_message(viber_request.sender.id, info)
    elif command == 'echo':
        send_message(viber_request.sender.id, ':-)')
    elif command.startswith('echo '):
        send_message(viber_request.sender.id, command[len('echo '):])
    elif command.startswith('note '):
        cache.add_note(command[len('note '):].strip())
    elif command == 'note':
        send_message(viber_request.sender.id, cache.show_note(number=-1))
    elif command == 'notes':
        text = ''
        for k, v in sorted(cache.show_all_notes().items()):
            text += '{}: {}\n'.format(k, v)
        send_message(viber_request.sender.id, text.strip())
    elif command.startswith('note'):
        m = NOTE.match(command)
        if m:
            send_message(viber_request.sender.id,
                         cache.show_note(number=int(m.group('n')) - 1))
        else:
            send_message(viber_request.sender.id,
                         'Invalid "note" command, use "note" or "noteN", '
                         'where "N" is an integer.')
    elif command == 'removenotes':
        cache.remove_all_notes()
    elif command == 'removenote':
        cache.remove_note(number=-1)
    elif command.startswith('removenote'):
        m = REMOVENOTE.match(command)
        if m:
            cache.remove_note(number=int(m.group('n') - 1))
        else:
            send_message(viber_request.sender.id,
                         'Invalid "removenote" command, use "removenote" or '
                         '"removenoteN", where "N" is an integer.')
    elif command not in bot_commands:
        logger.warning('Un-supported command "{}" from user "{}"'.format(
            command, viber_request.sender.name))
        send_message(viber_request.sender.id,
                     'Command "{}" is not supported, '
                     'try "/help".'.format(command))
    elif 'execute' not in bot_commands[command]:
        logger.error('Execute parameter is not configured for command '
                     '"{}"'.format(command))
        send_message(viber_request.sender.id,
                     'Command "{}" is not properly '
                     'configured.'.format(command))
    elif bot_commands[command].get('output_format', 'text') not in [
            'text', 'json', 'none']:
        logger.error('Output format parameter is not properly configured for '
                     'command "{}" ("{}" should be "text" or "json")'.format(
                        command, bot_commands[command].get('output_format')))
        send_message(viber_request.sender.id,
                     'Command "{}" is not properly '
                     'configured.'.format(command))
    elif config.getboolean('Viber', 'command_executor', fallback=False):
        # There is another daemon that handles the messages. Just publish
        # the message.
        cache.refresh_user(viber_request.sender.id, viber_request.sender.name)
        cache.publish(viber_request.sender.id,
                      bot_commands[command].get('execute'),
                      destination=destination,
                      name=viber_request.sender.name,
                      message_type='execute',
                      output_format=bot_commands[command].get(
                          'output_format', 'text'))
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
    help_dict = dict((k, bot_commands[k].get('help')) for k in
                     bot_commands.keys())
    help_dict['echo'] = 'Echo the text sent to the bot (internal command).'
    help_dict['version'] = 'Show information about the bot (internal command).'
    help_dict['note'] = 'Create note or show the last note (internal command).'
    help_dict['notes'] = 'Show all notes (internal command).'
    help_dict['noteN'] = 'Show the Nth note (internal command).'
    help_dict['removenote'] = 'Remove the last note (internal command).'
    help_dict['removenoteN'] = 'Remove the Nth note (internal command).'
    help_dict['removenotes'] = 'Remove all notes (internal command).'
    width = max(len(k) for k in help_dict.keys())
    text = 'Available commands:\n\n'
    for k, v in sorted(help_dict.items()):
        text += '/{:<{width}} -- '.format(k, width=width)
        if v is not None:
            text += v
        else:
            text += 'Help is not available for command "{}".'.format(k)
        text += '\n'
    return text.strip()


def command_thread_target(execute, output_format, user_id, destination,
                          pretext=None):
    """
    Local command is run in a separate thread.

    :param execute: local command to execute
    :param output_format: expected command output format specified in the bot
                          configuration
    :param user_id: user id who will receive the answer
    :param destination: destination for the command
    :param pretext: text added to the beginning of message
    :return: None
    :raises Exception: if message sending fails
    """
    if destination and socket.gethostname() not in destination:
        # Command is not for this host.
        return
    text, media = execute_local_command(execute, output_format)
    if output_format == 'none':
        return
    if isinstance(pretext, str):
        text = pretext + text
    send_message(user_id, text, media=media)


def execute_local_command(execute, output_format='text'):
    """
    Execute local command in another process.

    :param execute: command found
    :param output_format: text | json | none
    :return: (message text, optional media url)
    """
    logger.info('Running command "{}"'.format(execute))
    p = subprocess.Popen(execute, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    output, error = p.communicate()
    rc = p.returncode
    if rc != 0:
        error_msg = 'Failed to execute command "{}": {}'.format(
            execute, error.decode().strip())
        logger.error(error_msg)
        return error_msg, None
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
log_stdout = config.getboolean('Logger', 'stdout', fallback=False)

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

if log_stdout:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: '
                                  '%(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == '__main__':
    #
    # Flask development server.
    #
    import argparse
    parser = argparse.ArgumentParser(description='Command bot using Viber')
    parser.add_argument('--debug', type=bool, default=False, help='debug')
    parser.add_argument('--listen-address', help='server listen address')
    parser.add_argument('--listen-port', type=int, help='server listen port')
    parser.add_argument('--tls-certificate', help='TLS certificate file')
    parser.add_argument('--tls-private-key', help='TLS private key file')
    args = parser.parse_args()
    app.run(host=args.listen_address, port=args.listen_port, debug=args.debug,
            ssl_context=(args.tls_certificate, args.tls_private_key))
