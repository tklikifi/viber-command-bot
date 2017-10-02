import os
import sys
from common.config import ConfigError, parse_config
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration


try:
    config = parse_config(os.getenv('VIBER_CONF'))
except ConfigError as e:
    print(str(e))
    sys.exit(1)

viber = Api(BotConfiguration(
    auth_token=config['Viber']['authentication_token'],
    name=config['Viber']['name'], avatar=config['Viber']['avatar']))
