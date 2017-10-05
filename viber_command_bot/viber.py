"""
Viber bot API configuration

It is possible to change bot configuration file by setting VIBER_CONF
environment variable.
"""

import os
import sys
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viber_command_bot.config import ParseError, parse


VIBER_CONF = '/etc/viber/viber-command-bot.conf'

try:
    config = parse(os.getenv('VIBER_CONF', VIBER_CONF))
except ParseError as e:
    # Configuration parsing error is fatal.
    print('FATAL: {}'.format(e))
    sys.exit(1)

viber = Api(BotConfiguration(
    auth_token=config['Viber']['authentication_token'],
    name=config['Viber']['name'], avatar=config['Viber']['avatar']))
