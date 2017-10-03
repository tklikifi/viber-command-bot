# Project Viber

This is a small project to get familiar with Viber messaging service
(https://www.viber.com).

These tools use Viber Python Bot API
(https://developers.viber.com/docs/api/python-bot-api/) to send and receive
messages.


## Viber command bot

Directory **vibercommandbot** contains a simple Viber bot that receives commands
from a trusted Viber user. Bot executes the configured command and returns the
answer.

### Install

Here are instructions for installing the bot for NGINX in CentOS 7.

#### Bot

    $ sudo useradd viber -s /usr/sbin/nologin
    $ sudo mkdir /etc/viber
    $ sudo chown viber:viber /etc/viber 
    $ sudo chmod 700 /etc/viber 
    $ sudo cp config/bot.conf /etc/viber/bot.conf
    $ sudo chown viber:viber /etc/viber/bot.conf
    $ sudo cp config/uwsgi.ini /etc/viber/uwsgi.ini
    $ sudo chown viber:viber /etc/viber/uwsgi.ini
    $ python3.6 ./setup.py build
    $ sudo python3.6 ./setup.py install

Edit bot config file to include authentication token etc. and the commands you
want the bot to execute:

    $ sudo vi /etc/viber/bot.conf


#### Nginx

Add the following lines to */etc/nginx/nginx.conf*:

    ...
    
    location = /viber-command-bot { rewrite ^ /viber-command-bot/; }   
    location /viber-command-bot { try_files $uri @viber-command-bot; }  
    location @viber-command-bot { 
        include uwsgi_params;                          
        uwsgi_pass unix:/var/run/viber/command-bot.sock;       
    }                   
    
    ...


#### Systemd

    $ sudo cp config/systemd.service /usr/lib/systemd/system/viber-command-bot.service
    $ sudo systemctl enable viber-command-bot.service
    $ sudo systemctl start viber-command-bot.service
    $ viber-command-bot-register

## Send viber message

A small Python script **viber-send-message** can be used for sending
messages to a trusted Viber user that has subscribed to public Viber bot
account, e.g.:

    $ viber-send-message 'Hello there!'
    $ viber-send-message --user-id xxyyzz 'Hello there!'
    $ viber-send-message --media http://example.com/image.jpg 'Here is my image!'
