"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from .defaults import DEFAULTS


class GlobalConf:
    """Manages lifedrain's global configuration."""
    fields = {'enable', 'stopOnAnswer', 'barPosition', 'barHeight',
              'barBorderRadius', 'barText', 'barStyle', 'barFgColor',
              'barTextColor', 'enableBgColor', 'barBgColor',
              'globalSettingsShortcut', 'deckSettingsShortcut',
              'pauseShortcut', 'recoverShortcut', 'behavUndo', 'behavBury',
              'behavSuspend'}
    _main_window = None

    def __init__(self, mw):
        self._main_window = mw

    def get(self):
        """Get global configuration from Anki's database."""
        conf = self._main_window.col.conf
        global_conf = conf.get('lifedrain', {})
        for field in self.fields:
            if field not in global_conf:
                global_conf[field] = DEFAULTS[field]
        return global_conf

    def set(self, new_conf):
        """Saves global configuration into Anki's database."""
        col = self._main_window.col
        conf = col.conf

        if 'lifedrain' not in conf:
            conf['lifedrain'] = {}
        for field in self.fields:
            conf['lifedrain'][field] = new_conf[field]
        col.setMod()


class DeckConf:
    """Manages each lifedrain's deck configuration."""
    fields = {'maxLife', 'recover', 'damage'}
    _main_window = None

    def __init__(self, mw):
        self._main_window = mw

    def get(self):
        """Get current deck configuration from Anki's database."""
        deck = self._main_window.col.decks.current()
        conf = deck.get('lifedrain', {})
        conf_dict = {
            'id': deck['id'],
            'name': deck['name'],
        }
        for field in self.fields:
            conf_dict[field] = conf.get(field, DEFAULTS[field])
        return conf_dict

    def set(self, new_conf):
        """Saves deck configuration into Anki's database."""
        col = self._main_window.col
        deck = col.decks.current()

        if 'lifedrain' not in deck:
            deck['lifedrain'] = {}
        for field in self.fields:
            deck['lifedrain'][field] = new_conf[field]
        col.decks.save(deck)
