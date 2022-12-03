# Some logic in this file is copied from https://github.com/Mezuzi/Jeeves
# MIT License
# Copyright (c) 2020 Oliver Yin
import json
import re
import requests

NRDB_API = 'https://netrunnerdb.com/api/2.0/'
NRDB_CARD_URL_PREFIX = 'https://netrunnerdb.com/en/card/'


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
        self.cards = {x['title']: Card(x) for x in data['data']}
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


class Card:
    def __init__(self, data):
        self.data = data

    def format(self):
        card = self.data
        title = f'**{card["stripped_title"]}** ({NRDB_CARD_URL_PREFIX}{card["code"]})'
        has_rez_cost = card['type_code'] in ['asset', 'upgrade', 'ice']
        subtitle = card["type_code"].capitalize()
        if 'keywords' in card:
            subtitle += f': {card["keywords"]}'

        subtitles = [
            subtitle,
        ]

        automatic_pairs = (
            ('Rez' if has_rez_cost else 'Cost', 'cost'),
            ('MU', 'memory_cost'),
            ('Strength', 'strength'),
            ('Trash', 'trash_cost'),
            ('Link', 'base_link'),
            ('Minimum deck size', 'minimum_deck_size'),
            ('Inflence limit', 'influence_limit'),
        )

        subtitles.extend(
            (
                f'{pair[0]}: {card.get(pair[1], "X")}'
                for pair in automatic_pairs
                if pair[1] in card
            )
        )

        faction_text = card["faction_code"].capitalize()
        if card.get('faction_cost'):
            faction_text += (
                f' {"●" * card["faction_cost"]}{"○" * (5 - card["faction_cost"])}'
            )
        subtitles.append(faction_text)

        if 'advancement_cost' in card and 'agenda_points' in card:
            subtitles.append(
                f'{card["advancement_cost"] or "X"} / {card["agenda_points"]}'
            )

        message = [
            title,
            f'**{" • ".join(subtitles)}**',
            card['stripped_text'],
        ]
        return '\n'.join(message)
