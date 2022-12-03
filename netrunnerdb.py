# Some logic in this file is copied from https://github.com/Mezuzi/Jeeves
# MIT License
# Copyright (c) 2020 Oliver Yin
import json
import re
import requests

NRDB_API = 'https://netrunnerdb.com/api/2.0/'


class Cards:
    def __init__(self):
        # FIXME: add way to refresh local cache (for now just delete
        # data/cards.json before starting the bot).
        filename = 'data/cards.json'
        try:
            with open(filename) as f:
                print(f'Loading cards from {filename}...')
                data = json.load(f)
        except FileNotFoundError:
            print('Loading cards from netrunnerdb...')
            data = requests.get(f'{NRDB_API}public/cards').json()
            with open(filename, 'w'):
                json.dump(data, f)
        self.cards = {x['title']: x for x in data['data']}
        print('Loaded netrunnerdb data!')

    def lookup_card_by_title(self, value):
        print(f'Looking up {value}')
        return self.cards.get(value)

    def cards_from_message(self, body):
        results = re.findall(r'\[\[(.*?)\]\]', body)
        return (
            filter(None, [self.lookup_card_by_title(value) for value in results])
            if results
            else []
        )
