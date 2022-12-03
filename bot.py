#!/usr/bin/env python

import simplematrixbotlib as botlib
import toml

creds_data = toml.load('config.toml').get('simplematrixbotlib', {}).get('creds', {})
creds = botlib.Creds(
    creds_data['homeserver'], creds_data['username'], creds_data['password']
)
config = botlib.Config()
config.load_toml("config.toml")

bot = botlib.Bot(creds, config)
PREFIX = '!'


@bot.listener.on_message_event
async def echo(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)
    if match.is_not_from_this_bot():
        for arg in match.args():
            # FIXME: replace logic with something looking at the whole message
            # instead of going through args, which are separated by a space, so
            # that's not what we want (we want to be able to lookup cards with
            # spaces in their names!)
            if arg.startswith('[[') and arg.endswith(']]'):
                await bot.api.send_text_message(
                    room.room_id, f'FIXME: Look up {arg[2:-2]} on netrunnerdb'
                )


bot.run()
