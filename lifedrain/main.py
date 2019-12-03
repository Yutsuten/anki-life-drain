"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from anki.hooks import addHook, wrap
from anki.sched import Scheduler
from anki.collection import _Collection
from aqt import appVersion, forms, mw, qt
from aqt.deckconf import DeckConf
from aqt.dyndeckconf import DeckConf as FiltDeckConf
from aqt.editcurrent import EditCurrent
from aqt.preferences import Preferences
from aqt.progress import ProgressManager
from aqt.reviewer import Reviewer

from .lifedrain import Lifedrain


def main():
    """Initializes the Life Drain add-on."""
    make_timer = ProgressManager(mw).timer
    lifedrain = Lifedrain(make_timer, mw, qt)

    setup_user_interface(lifedrain)
    setup_shortcuts(lifedrain)
    setup_hooks(lifedrain)


def setup_user_interface(lifedrain):
    """Generates the User Interfaces for configurating the add-on.

    Generates the Preferences (Global Settings), Deck Settings and Custom Deck
    Settings (Filtered Deck Settings) User Interface. It also adds the triggers
    for loading and saving each setting.

    Args:
        lifedrain: A Lifedrain instance.
    """
    # Global Settings
    forms.preferences.Ui_Preferences.setupUi = wrap(
        forms.preferences.Ui_Preferences.setupUi,
        lambda *args: lifedrain.preferences_ui(args[0])
    )
    Preferences.__init__ = wrap(
        Preferences.__init__,
        lambda *args: lifedrain.preferences_load(args[0])
    )
    Preferences.accept = wrap(
        Preferences.accept,
        lambda *args: lifedrain.preferences_save(args[0]),
        'before'
    )

    # Deck Settings
    forms.dconf.Ui_Dialog.setupUi = wrap(
        forms.dconf.Ui_Dialog.setupUi,
        lambda *args: lifedrain.deck_settings_ui(args[0])
    )
    DeckConf.loadConf = wrap(
        DeckConf.loadConf,
        lambda *args: lifedrain.deck_settings_load(args[0])
    )
    DeckConf.saveConf = wrap(
        DeckConf.saveConf,
        lambda *args: lifedrain.deck_settings_save(args[0]),
        'before'
    )

    # Filtered Deck Settings
    forms.dyndconf.Ui_Dialog.setupUi = wrap(
        forms.dyndconf.Ui_Dialog.setupUi,
        lambda *args: lifedrain.custom_deck_settings_ui(
            args[0],
            appVersion.startswith('2.1')
        )
    )
    FiltDeckConf.loadConf = wrap(
        FiltDeckConf.loadConf,
        lambda *args: lifedrain.deck_settings_load(args[0])
    )
    FiltDeckConf.saveConf = wrap(
        FiltDeckConf.saveConf,
        lambda *args: lifedrain.deck_settings_save(args[0]),
        'before'
    )


def setup_shortcuts(lifedrain):
    """Configures the shortcuts provided by the add-on.

    Args:
        lifedrain: A Lifedrain instance.
    """
    if appVersion.startswith('2.0'):
        Reviewer._keyHandler = wrap(  # pylint: disable=protected-access
            Reviewer._keyHandler,  # pylint: disable=protected-access
            lambda self, evt, _old:
            lifedrain.toggle_drain() if evt.text() == 'p' else _old(self, evt),
            'around'
        )
    elif appVersion.startswith('2.1'):
        addHook(
            'reviewStateShortcuts',
            lambda shortcuts: shortcuts.append(tuple(['p', lifedrain.toggle_drain]))
        )


def setup_hooks(lifedrain):
    """Links events triggered on Anki to Life Drain methods.

    Args:
        lifedrain: A Lifedrain instance.
    """
    addHook('beforeStateChange', lambda *args: lifedrain.screen_change(args[0]))
    addHook('showQuestion', lifedrain.show_question)
    addHook('showAnswer', lifedrain.show_answer)
    addHook('reset', lifedrain.undo)
    addHook('revertedCard', lambda cid: lifedrain.undo())
    addHook('leech', lambda *args: lifedrain.status.update({'card_new_state': True}))
    addHook('LifeDrain.recover', lifedrain.deck_manager.recover_life)

    Scheduler.buryNote = wrap(
        Scheduler.buryNote,
        lambda *args: lifedrain.status.update({'card_new_state': True})
    )
    Scheduler.buryCards = wrap(
        Scheduler.buryCards,
        lambda *args: lifedrain.status.update({'card_new_state': True})
    )
    Scheduler.suspendCards = wrap(
        Scheduler.suspendCards,
        lambda *args: lifedrain.status.update({'card_new_state': True})
    )
    _Collection.remCards = wrap(
        _Collection.remCards,
        lambda *args: lifedrain.status.update({'card_new_state': True})
    )
    EditCurrent.__init__ = wrap(
        EditCurrent.__init__,
        lambda *args: lifedrain.status.update({'reviewed': False})
    )
    Reviewer._answerCard = wrap(  # pylint: disable=protected-access
        Reviewer._answerCard,  # pylint: disable=protected-access
        lambda *args: lifedrain.status.update({'review_response': args[1]}),
        'before'
    )