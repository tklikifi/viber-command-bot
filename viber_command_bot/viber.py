"""
Viber bot API configuration

It is possible to change bot configuration file by setting VIBER_CONF
environment variable.
"""

import os
import sys
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viber_command_bot.config import config


viber = Api(BotConfiguration(
    auth_token=config['Viber']['authentication_token'],
    name=config['Viber']['name'], avatar=config['Viber']['avatar']))
