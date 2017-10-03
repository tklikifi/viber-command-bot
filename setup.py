#!/usr/bin/env python3

import grp
import os
import pwd
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import check_call


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)

        # Create viber user.
        username = 'viber'

        try:
            uid = pwd.getpwnam(username).pw_uid
        except KeyError:
            try:
                check_call('useradd {} -s /usr/sbin/nologin'.format(
                    username).split())
            except Exception as e:
                print('ERROR: {}'.format(e))
            try:
                uid = pwd.getpwnam(username).pw_uid
            except KeyError:
                uid = 0
        try:
            gid = grp.getgrnam('viber').gr_gid
        except KeyError:
            gid = 0

        # Set directory and file permissions.
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
      packages=['viber_command_bot', 'viber_command_bot.flask',],
      scripts=['scripts/viber-command-bot-register',
               'scripts/viber-send-message'],
      data_files=[('/etc/viber',
                   ['config/viber-command-bot.conf',
                    'config/viber-command-bot.ini']),
                  ('/usr/lib/systemd/system',
                   ['config/viber-command-bot.service',])],
      cmdclass={ 'develop': PostDevelopCommand,
                 'install': PostInstallCommand, },
      )
