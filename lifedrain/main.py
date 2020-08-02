"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from aqt import forms, mw, qt, gui_hooks
from aqt.editcurrent import EditCurrent
from aqt.overview import OverviewBottomBar
from aqt.preferences import Preferences
from aqt.progress import ProgressManager
from aqt.reviewer import Reviewer
from aqt.toolbar import BottomBar

from anki import hooks
from anki.collection import _Collection
from anki.hooks import wrap
from anki.lang import _
from anki.sched import Scheduler

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

    Generates the Preferences (Global Settings) User Interface. It also adds the
    triggers for loading and saving each setting.

    Args:
        lifedrain: A Lifedrain instance.
    """
    # Global Settings
    forms.preferences.Ui_Preferences.setupUi = wrap(
        forms.preferences.Ui_Preferences.setupUi,
        lambda *args: lifedrain.preferences_ui(args[0]))
    Preferences.__init__ = wrap(
        Preferences.__init__,
        lambda *args: lifedrain.preferences_load(args[0]))
    Preferences.accept = wrap(
        Preferences.accept, lambda *args: lifedrain.preferences_save(args[0]),
        'before')


def setup_shortcuts(lifedrain):
    """Configures the shortcuts provided by the add-on.

    Args:
        lifedrain: A Lifedrain instance.
    """

    # Global shortcuts
    mw.applyShortcuts([tuple(['Ctrl+l', lifedrain.global_settings])])

    # State shortcuts
    def state_shortcuts(state, shortcuts):
        if state == 'review':
            shortcuts.append(tuple(['p', lifedrain.toggle_drain]))
            shortcuts.append(tuple(['l', lifedrain.deck_settings]))
        elif state == 'overview':
            shortcuts.append(tuple(['l', lifedrain.deck_settings]))

    gui_hooks.state_shortcuts_will_change.append(state_shortcuts)


def setup_hooks(lifedrain):
    """Links events triggered on Anki to Life Drain methods.

    Args:
        lifedrain: A Lifedrain instance.
    """
    mw.addonManager.setConfigAction(__name__, lifedrain.global_settings)

    gui_hooks.state_will_change.append(
        lambda *args: lifedrain.screen_change(args[0]))
    gui_hooks.reviewer_did_show_question.append(
        lambda card: lifedrain.show_question())
    gui_hooks.reviewer_did_show_answer.append(
        lambda card: lifedrain.show_answer())
    gui_hooks.review_did_undo.append(lambda card_id: lifedrain.undo())
    hooks.card_did_leech.append(
        lambda *args: lifedrain.status.update({'card_new_state': True}))
    hooks.addHook('LifeDrain.recover', lifedrain.deck_manager.recover_life)

    # hack to add Life Drain button into the overview screen
    def bottom_bar_draw(*args, **kwargs):
        if isinstance(kwargs['web_context'], OverviewBottomBar):

            def update_buf(buf):
                attribute_list = [
                    'title="{}"'.format(_('Shortcut key: %s') % 'L'),
                    'onclick="pycmd(\'lifedrain\')"']
                attributes = ' '.join(attribute_list)
                text = 'Life Drain'
                button = '<button {}>{}</button>'.format(attributes, text)
                return '{}\n{}'.format(buf, button)

            def link_handler(url):
                if url == 'lifedrain':
                    lifedrain.deck_settings()
                default_link_handler(url=url)

            default_link_handler = kwargs['link_handler']

            new_kwargs = dict(kwargs)
            new_kwargs['buf'] = update_buf(kwargs['buf'])
            new_kwargs['link_handler'] = link_handler
            return default_bottom_bar_draw(*args, **new_kwargs)

        return default_bottom_bar_draw(*args, **kwargs)

    default_bottom_bar_draw = BottomBar.draw
    BottomBar.draw = bottom_bar_draw
    # end-of-hack

    Scheduler.buryNote = wrap(
        Scheduler.buryNote,
        lambda *args: lifedrain.status.update({'card_new_state': True}))
    Scheduler.buryCards = wrap(
        Scheduler.buryCards,
        lambda *args: lifedrain.status.update({'card_new_state': True}))
    Scheduler.suspendCards = wrap(
        Scheduler.suspendCards,
        lambda *args: lifedrain.status.update({'card_new_state': True}))
    _Collection.remCards = wrap(
        _Collection.remCards,
        lambda *args: lifedrain.status.update({'card_new_state': True}))
    EditCurrent.__init__ = wrap(
        EditCurrent.__init__,
        lambda *args: lifedrain.status.update({'reviewed': False}))
    Reviewer._answerCard = wrap(  # pylint: disable=protected-access
        Reviewer._answerCard,  # pylint: disable=protected-access
        lambda *args: lifedrain.status.update({'review_response': args[1]}),
        'before')
