import configparser
import os
import sys
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage


MAX_TEXT_MESSAGE_SIZE = 7 * 1000  # 7K limit in Viber API
NUMBER_OF_TEXT_MESSAGES = 20


def create_text_messages(text):
    """
    Split text into a list of text messages. Also, lLimit the number of the
    text messages.
    """
    messages = list()
    if not text:
        return messages
    truncated_text = text[:(NUMBER_OF_TEXT_MESSAGES * MAX_TEXT_MESSAGE_SIZE)]
    for chunk in [truncated_text[i:i + MAX_TEXT_MESSAGE_SIZE] for i in range(
            0, len(truncated_text), MAX_TEXT_MESSAGE_SIZE)]:
        messages.append(TextMessage(text=chunk))
    if truncated_text != text:
        messages.append(TextMessage(text='<truncated>'))
    return messages


class ConfigError(Exception):
    pass


def parse_bot_config(config_file):
    if not config_file:
        raise ConfigError('ERROR: Configuration file not specified')
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
