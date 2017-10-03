#!/usr/bin/env python3

import grp
import os
import pwd
from distutils import log
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import check_call


class DevelopCommand(develop):

    def run(self):
        develop.run(self)


class InstallCommand(install):

    user_options = install.user_options + [
        ('bot-user=', None,
         'Specify the user that will own the configuration files.'),
        ('bot-group=', None,
         'Specify the group that will be set to the configuration files.'),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.bot_user = 'viber'
        self.bot_group = 'viber'

    def finalize_options(self):
        install.finalize_options(self)

    def run(self):
        install.run(self)

        try:
            uid = pwd.getpwnam(self.bot_user).pw_uid
        except KeyError:
            log.info('creating viber command bot user {}'.format(
                self.bot_user))
            try:
                check_call('useradd -M -s /usr/sbin/nologin {}'.format(
                    self.bot_user).split())
            except Exception as e:
                print('ERROR: {}'.format(e))
            try:
                uid = pwd.getpwnam(self.bot_user).pw_uid
            except KeyError:
                uid = 0

        try:
            gid = grp.getgrnam(self.bot_group).gr_gid
        except KeyError:
            log.info('creating viber command bot group {}'.format(
                self.bot_group))
            try:
                check_call('groupadd {}'.format(self.bot_group).split())
            except Exception as e:
                print('ERROR: {}'.format(e))
            try:
                gid = grp.getgrnam(self.bot_group).gr_gid
            except KeyError:
                gid = 0

        log.info('setting viber command bot file permissions')
        os.chown('/etc/viber', uid, gid)
        os.chmod('/etc/viber', 0o750)
        os.chown('/etc/viber/viber-command-bot.conf', uid, gid)
        os.chmod('/etc/viber/viber-command-bot.conf', 0o640)
        os.chown('/etc/viber/viber-command-bot.ini', uid, gid)
        os.chmod('/etc/viber/viber-command-bot.ini', 0o640)


setup(name='viber_command_bot',
      version='0.1.0',
      description='Python Viber Command Bot',
      author='Tommi Linnakangas',
      author_email='tkl@iki.fi',
      url='https://github.com/tklikifi/viber/',
      install_requires=['certifi', 'chardet', 'click', 'Flask', 'future',
                        'idna', 'itsdangerous', 'Jinja2', 'MarkupSafe',
                        'requests', 'urllib3', 'uWSGI', 'viberbot',
                        'Werkzeug', ],
      packages=['viber_command_bot', 'viber_command_bot.flask', ],
      scripts=['scripts/viber-command-bot-register',
               'scripts/viber-send-message'],
      data_files=[('/etc/viber',
                   ['config/viber-command-bot.conf',
                    'config/viber-command-bot.ini']),
                  ('/usr/lib/systemd/system',
                   ['config/viber-command-bot.service', ])],
      cmdclass={'develop': DevelopCommand,
                'install': InstallCommand, },
      )
