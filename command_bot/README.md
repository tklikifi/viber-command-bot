# viber-command-bot
Viber bot for receiving commands on a computer

uwsgi -s /var/run/viber-bot/viber-bot.sock -C \
  --manage-script-name --mount /viber-bot=bot:app \
  --enable-threads
