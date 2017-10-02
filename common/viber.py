import os
import sys
import common.config
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration


try:
    config = common.config.parse(os.getenv('VIBER_CONF'))
except common.config.ParseError as e:
    print(str(e))
    sys.exit(1)

viber = Api(BotConfiguration(
    auth_token=config['Viber']['authentication_token'],
    name=config['Viber']['name'], avatar=config['Viber']['avatar']))
