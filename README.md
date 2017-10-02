# Project Viber

This is a small project to get familiar with Viber messaging service
(https://www.viber.com).

These tools use Viber Python Bot API
(https://developers.viber.com/docs/api/python-bot-api/) to send and receive
messages.


## Viber bot command

Directory **bots/command** contains a simple Viber bot that receives commands
from a trusted Viber user. Bot executes the configured command and returns the
answer.

### Install

Here are instructions for installing the bot for NGINX in CentOS 7.

#### Bot

    $ sudo useradd viber -s /usr/sbin/nologin
    $ sudo mkdir /etc/viber
    $ sudo chown viber:viber /etc/viber 
    $ sudo chmod 700 /etc/viber 
    $ sudo cp bots/command/bot.conf /etc/viber/bot-command.conf
    $ sudo chown viber:viber /etc/viber/bot-command.conf
    $ sudo vi /etc/viber/bot-command.conf
    $ ./mkvirtualenv.sh

#### Nginx

Add the following lines to */etc/nginx/nginx.conf*:

    ...
    
    location = /viber/bot/command { rewrite ^ /viber/bot/command/; }   
    location /viber/bot/command { try_files $uri @viber-bot-command; }  
    location @viber-bot-command { 
        include uwsgi_params;                          
        uwsgi_pass unix:/var/run/viber/bot-command.sock;       
    }                   
    
    ...


#### Systemd

    $ sudo cp bots/command/systemd.service /usr/lib/systemd/system/viber-bot-command.service
    $ sudo systemctl enable viber-bot-command.service
    $ sudo systemctl start viber-bot-command.service
    $ scripts/viber-bot-command --register

## Send viber message

A small Pythob script **utils/send_message.py** can be used for sending messages
to a trusted Viber user that has subscribed to public Viber bot account. A shell
script **scripts/send-message** sets up the environment and sends the message,
e.g.:

    $ scripts/send-message 'Hello there!'
    $ scripts/send-message --user-id xxyyzz 'Hello there!'
    $ scripts/send-message --media http://example.com/image.jpg 'Here is my image!'
