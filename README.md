# Viber Command Bot

This is a small Python project to get familiar with Viber messaging service.

- [Viber](https://www.viber.com)

The project uses Viber Python Bot API to send and receive messages.

- [python-bot-api](https://developers.viber.com/docs/api/python-bot-api/)

Check API documentation about how to setup bot accounts.

- [get-started](https://developers.viber.com/docs/all/#lets-get-started)

## Viber command bot

Repository [viber-command-bot](https://github.com/tklikifi/viber-command-bot)
contains a simple Viber bot that receives commands from a trusted Viber user.
Bot executes the configured command and returns the answer. As a security
measure, the bot will not use any information received from the user as input to
the commands.

### Installation

The current implementation is tested in **Ubuntu 18.04** with **Python 3.6**.
First, install Python 3, nginx and uWSGI packages. Also, *redis* is needed for
cache:

```sh
sudo apt -y install python3 python3-setuptools python3-pip
sudo apt -y install nginx uwsgi uwsgi-plugin-python3
sudo apt -y install redis python3-redis
```

Install *viber-bot-python*:

```sh
pushd /tmp
git clone https://github.com/Viber/viber-bot-python.git
cd viber-bot-python
python3 ./setup.py build
sudo python3 ./setup.py install
popd
```

Install *viber-command-bot*:

```sh
pushd /tmp
git clone https://github.com/tklikifi/viber-command-bot.git
cd viber-command-bot
sudo pip3 install -r requirements.txt
python3 ./setup.py build
sudo python3 ./setup.py install
popd
```

``sudo python3 ./setup.py install`` command will do the following:

- Installs Python modules, scripts and configuration files.
- Creates user *viber*, if it does not exist.
- Creates group *viber*, if it does not exist.
- Sets directory */etc/viber* owner to *viber:viber*.
- Sets the owner of configuration files in */etc/viber* to *viber:viber*.
- Sets permissions of */etc/viber* directory to *750*.
- Sets permissions of configuration files in */etc/viber* directory to *640*.

The bot will run as user *viber*.

Edit bot configuration file */etc/viber/viber-command-bot.conf* to include the
following options in *Viber* configuration block:

- **authentication_token** - authentication token for the public Viber bot
  account
- **name** - bot name shown in the message
- **avatar** - image URL for bot avatar
- **webhook** - webhook URL of the bot
- **notify_user_id** - user id who receives notifications from the bot
- **trusted_user_ids** - list of user ids that are allowed to send messages
  to the bot
- **redis_channel** - channel used as message cache in Redis

Also, add the commands you want the bot to execute.

Add the following lines to */etc/nginx/nginx.conf*:

```sh
location = /viber-command-bot { rewrite ^ /viber-command-bot/; }
location /viber-command-bot { try_files $uri @viber-command-bot; }
location @viber-command-bot {
    include uwsgi_params;
    uwsgi_pass unix:/var/run/viber/viber-command-bot.sock;
}
```

Enable bot in *systemd* and start the service:

```sh
sudo systemctl enable viber-command-bot.service
sudo systemctl start viber-command-bot.service
sudo viber-command-bot-register
```

## Send Viber message

A small Python script *viber-send-message* can be used for sending messages to
Viber users that have subscribed to public Viber bot account, e.g.:

```sh
viber-send-message 'Hello there!'
viber-send-message --user-id userid 'Hello there!'
viber-send-message --media http://example.com/image.jpg 'Here is my image!'
```

If no *user-id* is given, the configured *notify_user_id* is used.

User account that wants to send Viber messages must belong to *viber* group:

```sh
sudo usermod -a -G viber user
```

## Receive Viber messages

A small Python script *viber-receive-messages* can be used for following message
to and from the bot:

```sh
viber-receive-messages
```

Daemon process *viber-command-executor* can be used for executing commands. It
is useful for example when *redis*, *nginx* and *viber-command-bot* are run in
separate docker containers.

```sh
viber-command-executor
```
