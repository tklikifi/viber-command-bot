#!/usr/bin/env python3

from setuptools import setup

setup(name='vibercommandbot',
      version='0.1.0',
      description='Python Viber Command Bot',
      author='Tommi Linnakangas',
      author_email='tkl@iki.fi',
      url='https://github.com/tklikifi/viber/',
      install_requires=['certifi', 'chardet', 'click', 'Flask', 'future',
                        'idna', 'itsdangerous', 'Jinja2', 'MarkupSafe',
                        'requests', 'urllib3', 'viberbot', 'Werkzeug', ],
      packages=['vibercommandbot', 'vibercommandbot.flask',],
      )
