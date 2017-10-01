# viber-command-bot
Viber bot for receiving commands on a computer

    uwsgi -s /var/run/viber/bot.sock -C --manage-script-name --mount /viber-bot=command_bot.bot:app --enable-threads

