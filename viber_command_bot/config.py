import configparser
import os


class ParseError(Exception):
    pass


def parse(file_path):
    if not file_path:
        raise ParseError('Configuration file not specified')
    config = configparser.ConfigParser()
    if not os.path.exists(file_path):
        raise ParseError('Configuration file not found: {}'.format(file_path))
    config.read(file_path)

    if 'Viber' not in config:
        raise ParseError('Configuration block "Viber" is missing')
    for k in ['authentication_token', 'name', 'avatar', 'webhook',
              'notify_user_id', 'trusted_user_ids',]:
        if k not in config['Viber']:
            raise ParseError('Viber "{}" is not configured'.format(k))

    return config
