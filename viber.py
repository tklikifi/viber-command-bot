import configparser
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
    for text in [long_text[i:i + MAX_TEXT_MESSAGE_SIZE] for i in range(
            0, len(long_text), MAX_TEXT_MESSAGE_SIZE)]:
        messages.append(TextMessage(text=text))
    return messages


class ConfigError(Exception):
    pass


def parse_bot_config(config_file):
    bot_config = configparser.ConfigParser()
    bot_config.read(config_file)

    # Configuration parameters for Viber.
    if 'Viber' not in bot_config:
        raise ConfigError('ERROR: Configuration block "Viber" is '
                          'missing')
    if 'authentication token' not in bot_config['Viber']:
        raise ConfigError('ERROR: Viber "authentication token" is not '
                          'configured')
    if 'name' not in bot_config['Viber']:
        raise ConfigError('ERROR: Viber "name" is not configured')
    if 'avatar' not in bot_config['Viber']:
        bot_config['Viber']['avatar'] = None
    if 'webhook' not in bot_config['Viber']:
        raise ConfigError('ERROR: Viber "webhook" is not configured')
    if 'notify user id' not in bot_config['Viber']:
        raise ConfigError('ERROR: Viber "notify user id" is not '
                          'configured')
    if 'trusted user ids' not in bot_config['Viber']:
        raise ConfigError('ERROR: Viber "trusted user ids" is not '
                          'configured')

    return bot_config


# Parse Viber configuration.
try:
    config = parse_bot_config('/etc/nginx/viber-bot.ini')
except ConfigError as e:
    print(str(e))
    sys.exit(1)

# Configure Viber bot API.
viber = Api(BotConfiguration(
    auth_token=config['Viber']['authentication token'],
    name=config['Viber']['name'], avatar=config['Viber']['avatar']))
