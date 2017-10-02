import configparser
import os


class ConfigError(Exception):
    pass


def parse_config(config_file):
    if not config_file:
        raise ConfigError('ERROR: Configuration file not specified')
    config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        raise ConfigError('ERROR: Configuration file not found: {}'.format(
            config_file))
    config.read(config_file)

    if 'Viber' not in config:
        raise ConfigError('ERROR: Configuration block "Viber" is missing')
    for k in ['authentication_token', 'name', 'avatar', 'webhook',
              'notify_user_id', 'trusted_user_ids',]:
        if k not in config['Viber']:
            raise ConfigError('ERROR: Viber "{}" is not configured'.format(k))

    return config
