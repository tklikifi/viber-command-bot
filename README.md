# Project Viber

This is a small project to get familiar with Viber messaging service
(https://www.viber.com).

These tools use Viber Python Bot API
(https://developers.viber.com/docs/api/python-bot-api/) to send and receive
messages.


## Viber command bot

Directory **viber_command_bot** contains a simple Viber bot that receives
commands from a trusted Viber user. Bot executes the configured command and
returns the answer.

### Install

Here are instructions for installing the bot for NGINX in CentOS 7.

#### Bot

    $ sudo pip3.6 install setuptools
    $ python3.6 ./setup.py build
    $ sudo python3.6 ./setup.py install

Edit bot config file to include authentication token etc. and the commands you
want the bot to execute:

    $ sudo vi /etc/viber/viber-command-bot.conf


#### Nginx

Add the following lines to */etc/nginx/nginx.conf*:

    ...
    
    location = /viber-command-bot { rewrite ^ /viber-command-bot/; }   
    location /viber-command-bot { try_files $uri @viber-command-bot; }  
    location @viber-command-bot { 
        include uwsgi_params;                          
        uwsgi_pass unix:/var/run/viber/viber-command-bot.sock;       
    }                   
    
    ...


#### Systemd

    $ sudo cp config/viber-command-bot.service /usr/lib/systemd/system
    $ sudo systemctl enable viber-command-bot.service
    $ sudo systemctl start viber-command-bot.service
    $ sudo viber-command-bot-register

## Send Viber message

A small Python script **viber-send-message** can be used for sending messages to
Viber users that have subscribed to public Viber bot account, e.g.:

    $ viber-send-message 'Hello there!'
    $ viber-send-message --user-id xxyyzz 'Hello there!'
    $ viber-send-message --media http://example.com/image.jpg 'Here is my image!'

If no *user-id* is given, the Viber bot *notify_user_id* is used.

User account that wants to send Viber messages must belong to **viber** group:

    $ sudo usermod -a -G viber user
