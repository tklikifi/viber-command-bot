"""
Viber bot configuration parsing
"""

import configparser
import os
import sys


class ParseError(Exception):
    """
    Error found during bot configuration parsing.
    """
    pass


def parse(file_path):
    """
    Parse bot configuration file.

    :param file_path: path to the configuration file
    :return: parsed configuration
    """
    if not file_path:
        raise ParseError('Configuration file not specified')
    config = configparser.ConfigParser()
    if not os.path.exists(file_path):
        raise ParseError('Configuration file not found: {}'.format(file_path))
    config.read(file_path)

    if 'Viber' not in config:
        raise ParseError('Configuration block "Viber" is missing')
    for k in ['authentication_token', 'name', 'avatar', 'webhook',
              'notify_user_id', 'trusted_user_ids', ]:
        if k not in config['Viber']:
            raise ParseError('Viber "{}" is not configured'.format(k))

    return config


VIBER_CONF = '/etc/viber/viber-command-bot.conf'


try:
    config = parse(os.getenv('VIBER_CONF', VIBER_CONF))
except ParseError as e:
    # Configuration parsing error is fatal.
    print('FATAL: {}'.format(e))
    sys.exit(1)
