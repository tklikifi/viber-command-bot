# Project Viber

This is a small project to get familiar with Viber messaging service
(https://www.viber.com).

These tools use Viber Python Bot API
(https://developers.viber.com/docs/api/python-bot-api/) to send and receive
messages.


## Viber command bot

**command_bot** is a simple Viber bot that receives commands from a trusted
Viber user. Bot executes the configured command and returns the answer.

### Install

#### Nginx


    ...
    
    location = /viber-bot { rewrite ^ /viber-bot/; }   
    location /viber-bot { try_files $uri @viberbot; }  
    location @viberbot { 
        include uwsgi_params;                          
        uwsgi_pass unix:/var/run/viber/bot.sock;       
    }                   
    
    ...


#### Systemd

    # cp viber-command-bot.service /usr/lib/systemd/system
    # systemctl enable viber-command-bot.service
    # systemctl start viber-command-bot.service
    # /usr/local/viber/command_bot/bot.sh --register

## Send viber message

**send_message.py** is a small Python script that can be used for sending
messages to a trusted Viber user that has subscribed to public Viber bot
account.
