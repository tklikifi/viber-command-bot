# Project Viber

This is a small project to get familiar with Viber messaging service
(https://www.viber.com).

These tools use Viber Python Bot API
(https://developers.viber.com/docs/api/python-bot-api/) to send and receive
messages.


## Viber bot command

**bot/command** is a simple Viber bot that receives commands from a trusted
Viber user. Bot executes the configured command and returns the answer.

### Install

#### Nginx


    ...
    
    location = /viber/bot/command { rewrite ^ /viber/bot/command/; }   
    location /viber/bot/command { try_files $uri @viber-bot-command; }  
    location @viber-bot-command { 
        include uwsgi_params;                          
        uwsgi_pass unix:/var/run/viber/bot-command.sock;       
    }                   
    
    ...


#### Systemd

    # cp systemd.service /usr/lib/systemd/system/viber-bot-command.service
    # systemctl enable viber-bot-command.service
    # systemctl start viber-bot-command.service
    # /usr/local/viber/viber-bot-command --register

## Send viber message

**send_message.py** is a small Python script that can be used for sending
messages to a trusted Viber user that has subscribed to public Viber bot
account. **send-message** is a shell script, which sets up the environment
and sends the message, e.g.:

    $ ./send-message 'Hello there!'
    $ ./send-message --user-id xxyyzz 'Hello there!'
