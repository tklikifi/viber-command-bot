import argparse
import configparser


class ConfigError(Exception):
    pass


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Command bot using Viber')
    parser.add_argument('--daemon', dest='daemon', action='store_true',
                        help='start as daemon process')
    parser.add_argument('--no-daemon', dest='daemon', action='store_false',
                        help='start as normal process')
    parser.add_argument('--config', dest='config', help='configuration file')
    parser.set_defaults(daemon=True, config='bot.ini')
    return parser.parse_args()


def parse_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    # Configuration parameters for Flask.
    if 'Flask' not in config:
        raise ConfigError('ERROR: Configuration block "Flask" is missing')
    if 'private key' not in config['Flask']:
        raise ConfigError('ERROR: Flask "private key" is not configured')
    if 'certificate' not in config['Flask']:
        raise ConfigError('ERROR: Flask "certificate" is not configured')
    if 'listen address' not in config['Flask']:
        config['Flask']['listen address'] = '0.0.0.0'
    if 'listen port' not in config['Flask']:
        config['Flask']['listen port'] = '443'
    try:
        int(config['Flask']['listen port'])
    except (ValueError, ):
        raise ConfigError('ERROR: "listen port" must be an integer')

    # Configuration parameters for Viber bot.
    if 'Viber bot' not in config:
        raise ConfigError('ERROR: Configuration block "Viber bot" is '
                          'missing')
    if 'authentication token' not in config['Viber bot']:
        raise ConfigError('ERROR: Viber bot "authentication token" is not '
                          'configured')
    if 'name' not in config['Viber bot']:
        raise ConfigError('ERROR: Viber bot "name" is not configured')
    if 'avatar' not in config['Viber bot']:
        config['Viber bot']['avatar'] = None
    if 'webhook' not in config['Viber bot']:
        raise ConfigError('ERROR: Viber bot "webhook" is not configured')
    if 'notify user id' not in config['Viber bot']:
        raise ConfigError('ERROR: Viber bot "notify user id" is not '
                          'configured')
    if 'trusted user ids' not in config['Viber bot']:
        raise ConfigError('ERROR: Viber bot "trusted user ids" is not '
                          'configured')

    # Create commands dict from config.
    commands = dict()
    prefix = 'Command '
    sections = [s for s in config.sections() if s.startswith(prefix)]
    for section in sections:
        name = section[len(prefix):].strip()
        commands[name] = dict()
        for key in ['execute', 'output format', 'help']:
            if key in config[section]:
                commands[name][key] = config[section][key]
            else:
                commands[name][key] = None

    return config, commands
