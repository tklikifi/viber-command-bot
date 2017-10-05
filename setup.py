#!/usr/bin/env python3

import grp
import os
import pwd
from distutils import log
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import check_call, check_output


bot_user = 'viber'
bot_group = 'viber'


class BuildCommand(build_py):

    def run(self):
        branch = check_output('git rev-parse --abbrev-ref HEAD'.split())
        with open('viber_command_bot/git.py', 'w') as f:
            f.write("# THIS FILE IS GENERATED -- DO NOT EDIT!!!\n"
                    "branch = '{}'\n".format(branch.decode().strip()))
        build_py.run(self)


class DevelopCommand(develop):

    def run(self):
        develop.run(self)


class InstallCommand(install):

    def run(self):
        install.run(self)

        try:
            uid = pwd.getpwnam(bot_user).pw_uid
        except KeyError:
            log.info('creating viber command bot user {}'.format(bot_user))
            try:
                check_call('useradd -M -s /usr/sbin/nologin {}'.format(
                    bot_user).split())
            except Exception as e:
                print('ERROR: {}'.format(e))
            try:
                uid = pwd.getpwnam(bot_user).pw_uid
            except KeyError:
                uid = 0

        try:
            gid = grp.getgrnam(bot_group).gr_gid
        except KeyError:
            log.info('creating viber command bot group {}'.format(bot_group))
            try:
                check_call('groupadd {}'.format(bot_group).split())
            except Exception as e:
                print('ERROR: {}'.format(e))
            try:
                gid = grp.getgrnam(bot_group).gr_gid
            except KeyError:
                gid = 0

        log.info('setting viber command bot file permissions')
        os.chown('/etc/viber', uid, gid)
        os.chmod('/etc/viber', 0o750)
        os.chown('/etc/viber/viber-command-bot.conf', uid, gid)
        os.chmod('/etc/viber/viber-command-bot.conf', 0o640)
        os.chown('/etc/viber/viber-command-bot.ini', uid, gid)
        os.chmod('/etc/viber/viber-command-bot.ini', 0o640)


exec(open('viber_command_bot/version.py').read())
setup(name='viber_command_bot',
      version=__version__,
      description='Python Viber Command Bot',
      author='Tommi Linnakangas',
      author_email='tkl@iki.fi',
      url='https://github.com/tklikifi/viber/',
      install_requires=['certifi', 'chardet', 'click', 'Flask', 'future',
                        'idna', 'itsdangerous', 'Jinja2', 'MarkupSafe',
                        'requests', 'urllib3', 'viberbot', 'Werkzeug', ],
      packages=['viber_command_bot', 'viber_command_bot.flask', ],
      scripts=['scripts/viber-command-bot-register',
               'scripts/viber-send-message'],
      data_files=[('/etc/viber',
                   ['config/viber-command-bot.conf',
                    'config/viber-command-bot.ini']),
                  ('/usr/lib/systemd/system',
                   ['config/viber-command-bot.service', ])],
      cmdclass={'build_py': BuildCommand,
                'develop': DevelopCommand,
                'install': InstallCommand, },
      )
