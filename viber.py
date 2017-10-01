import configparser
import os
import sys
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage


MAX_TEXT_MESSAGE_SIZE = 7 * 1000  # 7K


def create_text_messages(long_text):
    """
    Split long text into a list of max size text messages.
    """
    messages = list()
    if not long_text:
        return messages
    for text in [long_text[i:i + MAX_TEXT_MESSAGE_SIZE] for i in range(
            0, len(long_text), MAX_TEXT_MESSAGE_SIZE)]:
        messages.append(TextMessage(text=text))
    return messages


class ConfigError(Exception):
    pass


def parse_bot_config(config_file):
    bot_config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        raise ConfigError('ERROR: Configuration file not found: {}'.format(
            config_file))
    bot_config.read(config_file)

    if 'Viber' not in bot_config:
        raise ConfigError('ERROR: Configuration block "Viber" is missing')
    for k in ['authentication_token', 'name', 'avatar', 'webhook',
              'notify_user_id', 'trusted_user_ids',]:
        if k not in bot_config['Viber']:
            raise ConfigError('ERROR: Viber "{}" is not configured'.format(k))

    return bot_config


try:
    config = parse_bot_config(os.getenv('VIBER_CONF'))
except ConfigError as e:
    print(str(e))
    sys.exit(1)

viber = Api(BotConfiguration(
    auth_token=config['Viber']['authentication_token'],
    name=config['Viber']['name'], avatar=config['Viber']['avatar']))
