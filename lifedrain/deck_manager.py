'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from anki.hooks import runHook

from .defaults import DEFAULTS
from .progress_bar import ProgressBar


class DeckManager(object):
    '''
    Manages different Life Drain configuration for each deck.
    '''
    _progress_bar = None
    _barInfo = {}
    _current_deck = None
    _game_over = False

    def __init__(self, qt, mw):
        self._progress_bar = ProgressBar(qt, mw)

    def add_deck(self, deck_id, conf):
        '''
        Adds a deck to the manager.
        '''
        if str(deck_id) not in self._barInfo:
            self._barInfo[str(deck_id)] = {
                'maxValue': conf.get('maxLife', DEFAULTS['maxLife']),
                'currentValue': conf.get('maxLife', DEFAULTS['maxLife']),
                'recoverValue': conf.get('recover', DEFAULTS['recover']),
                'enableDamageValue': conf.get('enableDamage', DEFAULTS['enableDamage']),
                'damageValue': conf.get('damage', DEFAULTS['damage'])
            }

    def set_deck(self, deck_id):
        '''
        Sets the current deck.
        '''
        if deck_id:
            self._current_deck = str(deck_id)
            self._progress_bar.set_max_value(
                self._barInfo[self._current_deck]['maxValue']
            )
            self._progress_bar.set_current_value(
                self._barInfo[self._current_deck]['currentValue']
            )
        else:
            self._current_deck = None

    def get_deck_conf(self, deck_id):
        '''
        Get the settings and state of a deck.
        '''
        return self._barInfo[str(deck_id)]

    def set_deck_conf(self, deck_id, conf):
        '''
        Updates deck's current state.
        '''
        max_life = conf.get('maxLife', DEFAULTS['maxLife'])
        recover_value = conf.get('recover', DEFAULTS['recover'])
        enable_damage = conf.get('enableDamage', DEFAULTS['enableDamage'])
        damage = conf.get('damage', DEFAULTS['damage'])
        current_value = conf.get('currentValue', DEFAULTS['maxLife'])
        if current_value > max_life:
            current_value = max_life

        self._barInfo[str(deck_id)]['maxValue'] = max_life
        self._barInfo[str(deck_id)]['recoverValue'] = recover_value
        self._barInfo[str(deck_id)]['enableDamageValue'] = enable_damage
        self._barInfo[str(deck_id)]['damageValue'] = damage
        self._barInfo[str(deck_id)]['currentValue'] = current_value

    def set_progress_bar_style(self, config):
        '''
        Updates the AnkiProgressBar instance.
        '''
        self._progress_bar.dock_at(config['position'])
        self._progress_bar.set_style(config['progressBarStyle'])

        if self._current_deck is not None:
            self.recover(value=0)

    def recover(self, increment=True, value=None, damage=False):
        '''
        Abstraction for recovering life, increments the bar if increment is True (default).
        '''
        multiplier = 1
        if not increment:
            multiplier = -1
        if value is None:
            if damage and self._barInfo[self._current_deck]['enableDamageValue']:
                multiplier = -1
                value = self._barInfo[self._current_deck]['damageValue']
            else:
                value = self._barInfo[self._current_deck]['recoverValue']

        self._progress_bar.inc_current_value(multiplier * value)

        life = self._progress_bar.get_current_value()
        self._barInfo[self._current_deck]['currentValue'] = life
        if life == 0 and not self._game_over:
            self._game_over = True
            runHook('LifeDrain.gameOver')
        elif life > 0:
            self._game_over = False

    def bar_visible(self, visible):
        '''
        Sets the visibility of the Progress Bar
        '''
        if visible:
            self._progress_bar.show()
        else:
            self._progress_bar.hide()
