# Copyright (c) 2022 Mathieu Pillard, distributed under MIT License
# Some logic in this file is copied from https://github.com/Mezuzi/Jeeves
# which is Copyright (c) 2020 Oliver Yin, distributed under MIT License
import json
import re
import requests
import unicodedata

from rapidfuzz import fuzz


NRDB_API = 'https://netrunnerdb.com/api/2.0/'
NRDB_CARD_URL_PREFIX = 'https://netrunnerdb.com/en/card/'


class Cards:
    def __init__(self):
        mwls = self.load_data('mwl')['data']
        for mwl in mwls:
            if mwl.get('active'):
                self.active_mwl = mwl
                break
        self.packs = {x['code']: x for x in self.load_data('packs')['data']}
        self.cycles = {x['code']: x for x in self.load_data('cycles')['data']}
        cards_data = self.load_data('cards')
        self.cards = {
            self.normalize_text(card_data['title']): Card(
                card_data,
                # We only support NSG's ban list, so we only care about which
                # cards are in the MWL, assume they are all banned.
                is_banned=card_data['code'] in self.active_mwl['cards'],
                # For rotation we need to look up the pack, then the cycle,
                # then look at whether the cycle has rotated.
                # FIXME: maybe we should just have a way to look up the pack &
                # cycle from the Card, and figure out rotation and pack info
                # from there.
                has_rotated=self.cycles.get(
                    self.packs.get(card_data['pack_code'], {}).get('cycle_code'), {}
                ).get('rotated'),
            )
            for card_data in cards_data['data']
        }

    def load_data(self, type):
        # FIXME: add way to refresh local cache (for now just delete
        # data/cards.json before starting the bot).
        filename = f'data/{type}.json'
        try:
            with open(filename) as f:
                print(f'Loading {type} from {filename}...')
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f'Loading {type} from netrunnerdb...')
            data = requests.get(f'{NRDB_API}public/{type}').json()
            with open(filename, 'w') as f:
                json.dump(data, f)
        print(f'Loaded netrunnerdb {type}!')
        return data

    def normalize_text(self, value):
        return ''.join(
            c
            for c in unicodedata.normalize('NFKD', value)
            if unicodedata.category(c) not in ('Mn', 'Cc')
        ).lower()

    def score_card(self, value, card_title):
        if value == card_title:
            return 200
        else:
            return fuzz.ratio(value, card_title) + (70 if value in card_title else 0)

    def search_card(self, value):
        normalized_value = self.normalize_text(value)
        print(f'Searching for card "{value}" -> "{normalized_value}')
        return self.cards.get(
            max(
                [*self.cards.keys()], key=lambda x: self.score_card(normalized_value, x)
            )
        )

    def lookup_card_by_title(self, value):
        print(f'Looking up card "{value}"" by title')
        return self.cards.get(self.normalize_text(value))

    def cards_from_message(self, body):
        results = re.findall(r'\[\[(.*?)\]\]', body)
        return (
            filter(None, [self.search_card(value) for value in results])
            if results
            else []
        )


class Card:
    def __init__(self, data, *, is_banned=False, has_rotated=False):
        self.data = data
        self.is_banned = is_banned
        self.has_rotated = has_rotated

    def __str__(self):
        return self.data['stripped_title']

    def __html__(self):
        card = self.data
        title = (
            f'<strong>{"◆ " if card.get("uniqueness") else ""}'
            f'{card["title"]}</strong> ({NRDB_CARD_URL_PREFIX}{card["code"]})'
        )
        has_rez_cost = card['type_code'] in ['asset', 'upgrade', 'ice']
        subtitle = 'ICE' if card['type_code'] == 'ice' else card['type_code'].title()
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
                f'{pair[0]}: {card[pair[1]] if card[pair[1]] is not None else "X"}'
                for pair in automatic_pairs
                if pair[1] in card
            )
        )

        if 'advancement_cost' in card and 'agenda_points' in card:
            subtitles.append(
                f'{card["advancement_cost"] or "X"} / {card["agenda_points"]}'
            )

        faction_colors = {
            'anarch': 'orangered',
            'criminal': 'royalblue',
            'shaper': 'limegreen',
            'neutral': 'gray',
            'adam': 'olive',
            'sunny-lebeau': 'lightslategray',
            'apex': 'red',
            'weyland-consortium': 'darkgreen',
            'nbn': 'darkorange',
            'haas-bioroid': 'blueviolet',
            'jinteki': 'crimson',
        }
        faction_code = card["faction_code"].replace('-corp', '').replace('-runner', '')
        faction_color = faction_colors.get(faction_code, '')
        faction_title = 'NBN' if faction_code == 'nbn' else faction_code.title()
        faction_text = f'<font color="{faction_color}">{faction_title}</font>'
        if card.get('faction_cost'):
            faction_text += (
                f' {"●" * card["faction_cost"]}{"○" * (5 - card["faction_cost"])}'
            )
        subtitles.append(faction_text)
        if self.is_banned:
            subtitles.append('Banned!')
        if self.has_rotated:
            subtitles.append('Rotated!')

        replaces = {
            '[click]': '🕗',
            '[subroutine]': '↳',
            '[link]': '🔗',
            '[credit]': '🪙',
            '[interrupt]': '⚡',
            '[mu]': '🔋',
            '[recurring-credit]': '🪙↻',
            '[trash]': '🗑',
        }
        text = card['text']
        for key, value in replaces.items():
            text = text.replace(key, value)

        message = [
            title,
            f'<strong>{" • ".join(subtitles)}</strong>',
            f'<blockquote><p>{text}</p></blockquote>',
        ]
        return '\n'.join(message).replace('\n', '<br />')
