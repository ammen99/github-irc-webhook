# Send notifications from GitHub to IRC

A very simple IRC bot. Requires `requests` and `python3`.
First adjust the port/server/etc in `src/config.py`, then start the bot by running `python3 src/bot.py`.

You also need to instruct GitHub to send events to the bot. Go to `Settings -> Webhooks` and add a new webhook with a type `application/json` to your server and the port you configured in `src/config.py`.
