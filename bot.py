#!/usr/bin/env python

import simplematrixbotlib as botlib
import toml

from netrunnerdb import Cards
from fancier_bot import BotWithHTML

creds_data = toml.load('config.toml').get('simplematrixbotlib', {}).get('creds', {})
creds = botlib.Creds(
    creds_data['homeserver'], creds_data['username'], creds_data['password']
)
config = botlib.Config()
config.load_toml("config.toml")

cards = Cards()
bot = BotWithHTML(creds, config)


@bot.listener.on_message_event
async def echo(room, message):
    match = botlib.MessageMatch(room, message, bot)
    if match.is_not_from_this_bot():
        for card in cards.cards_from_message(message.body):
            await bot.api.send_html_message(room.room_id, card.__html__())


bot.run()
