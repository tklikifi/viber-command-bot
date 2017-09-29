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


def parse_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    # Configuration parameters for Viber.
    if 'Viber' not in config:
        raise ConfigError('ERROR: Configuration block "Viber" is '
                          'missing')
    if 'authentication token' not in config['Viber']:
        raise ConfigError('ERROR: Viber "authentication token" is not '
                          'configured')
    if 'name' not in config['Viber']:
        raise ConfigError('ERROR: Viber "name" is not configured')
    if 'avatar' not in config['Viber']:
        config['Viber']['avatar'] = None
    if 'webhook' not in config['Viber']:
        raise ConfigError('ERROR: Viber "webhook" is not configured')
    if 'notify user id' not in config['Viber']:
        raise ConfigError('ERROR: Viber "notify user id" is not '
                          'configured')
    if 'trusted user ids' not in config['Viber']:
        raise ConfigError('ERROR: Viber "trusted user ids" is not '
                          'configured')

    # Create commands dict from config.
    config_commands = dict()
    prefix = 'Command '
    sections = [s for s in config.sections() if s.startswith(prefix)]
    for section in sections:
        name = section[len(prefix):].strip()
        config_commands[name] = dict()
        for key in ['execute', 'output format', 'help']:
            if key in config[section]:
                config_commands[name][key] = config[section][key]
            else:
                config_commands[name][key] = None

    return config['Viber'], config_commands


# Parse Viber configuration.
try:
    viber_config, commands = parse_config('/etc/nginx/viber-bot.ini')
except ConfigError as e:
    print(str(e))
    sys.exit(1)

# Configure Viber API.
viber = Api(BotConfiguration(
    auth_token=viber_config['authentication token'],
    name=viber_config['name'], avatar=viber_config['avatar']))
