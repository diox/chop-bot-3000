#!/usr/bin/env python

import asyncio
import time

import simplematrixbotlib as botlib
import toml
from fancier_bot import BotWithHTML
from netrunnerdb import Cards


creds_data = toml.load('config.toml').get('simplematrixbotlib', {}).get('creds', {})
creds = botlib.Creds(
    creds_data['homeserver'], creds_data['username'], creds_data['password']
)
config = botlib.Config()
config.load_toml('config.toml')

cards = Cards()
bot = BotWithHTML(creds, config)


@bot.listener.on_message_event
async def card_lookup(room, message):
    match = botlib.MessageMatch(room, message, bot)
    if match.is_not_from_this_bot():
        tasks = []
        for line in message.body.split('\n'):
            if line.startswith('>'):
                continue
            for card in cards.cards_from_message(line):
                print(f'Found {card}, sending message to {room.room_id}')
                tasks.append(bot.api.send_html_message(room.room_id, card.__html__()))
        if tasks:
            await asyncio.gather(*tasks)


while True:
    try:
        print('Starting bot...')
        bot.run()
    except asyncio.exceptions.TimeoutError:
        print('Caught a TimeoutError, sleeping for one sec then restarting...')
        time.sleep(1)
