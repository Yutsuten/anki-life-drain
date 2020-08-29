"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from operator import itemgetter

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT


class Form:
    """Generates a form.

    The form is consisted of a (fixed) layout and widget elements, may be used
    on places like dialogs and tabs.
    """
    widget = None

    _qt = None
    _row = None
    _layout = None

    def __init__(self, qt, widget=None):
        self._qt = qt
        self._row = 0
        self.widget = widget if widget is not None else qt.QWidget()
        self._layout = qt.QGridLayout(self.widget)

    def label(self, text, color=None):
        """Creates a label in the current row of the form.

        Args:
            text: The text to be shown by the label.
            color: Optional. The color of the text in hex format.
        """
        label = self._qt.QLabel(text)
        label.setWordWrap(True)
        if color:
            label.setStyleSheet('color: {}'.format(color))

        self._layout.addWidget(label, self._row, 0, 1, 4)
        self._row += 1

    def combo_box(self, cb_name, label_text, options):
        """Creates a combo box in the current row of the form.

        Args:
            cb_name: The name of the combo box. Not visible by the user.
            label_text: A text that describes what is the combo box for.
            options: A list of options.
        """
        label = self._qt.QLabel(label_text)
        combo_box = self._qt.QComboBox(self.widget)
        for option in options:
            combo_box.addItem(option)

        combo_box.get_value = combo_box.currentIndex
        combo_box.set_value = combo_box.setCurrentIndex

        setattr(self.widget, cb_name, combo_box)
        self._layout.addWidget(label, self._row, 0)
        self._layout.addWidget(combo_box, self._row, 2, 1, 2)
        self._row += 1

    def check_box(self, cb_name, label_text, tooltip=None):
        """Creates a check box in the current row of the form.

        Args:
            cb_name: The name of the check box. Not visible by the user.
            label_text: A text that describes what is the check box for.
        """
        check_box = self._qt.QCheckBox(label_text, self.widget)
        if tooltip is not None:
            check_box.setToolTip(tooltip)

        check_box.get_value = check_box.isChecked
        check_box.set_value = check_box.setChecked

        setattr(self.widget, cb_name, check_box)
        self._layout.addWidget(check_box, self._row, 0, 1, 4)
        self._row += 1

    def spin_box(self, sb_name, label_text, val_range, tooltip=None):
        """Creates a spin box in the current row of the form.

        Args:
            sb_name: The name of the spin box. Not visible by the user.
            label_text: A text that describes what is the spin box for.
            val_range: A list of two integers that are the range.
        """
        label = self._qt.QLabel(label_text)
        spin_box = self._qt.QSpinBox(self.widget)
        spin_box.setRange(val_range[0], val_range[1])
        if tooltip is not None:
            label.setToolTip(tooltip)
            spin_box.setToolTip(tooltip)

        spin_box.get_value = spin_box.value
        spin_box.set_value = spin_box.setValue

        setattr(self.widget, sb_name, spin_box)
        self._layout.addWidget(label, self._row, 0)
        self._layout.addWidget(spin_box, self._row, 2, 1, 2)
        self._row += 1

    def color_select(self, cs_name, label_text):
        """Creates a color select in the current row of the form.

        Args:
            cs_name: The name of the color select. Not visible by the user.
            label_text: A text that describes what is the color select for.
        """

        def choose_color():
            if not color_dialog.exec_():
                return
            color = color_dialog.currentColor().name()
            css = 'QLabel { background-color: %s; }' % color
            preview_label.setStyleSheet(css)

        label = self._qt.QLabel(label_text)
        select_button = self._qt.QPushButton('Select')
        preview_label = self._qt.QLabel('')
        color_dialog = self._qt.QColorDialog(select_button)
        color_dialog.setOption(self._qt.QColorDialog.DontUseNativeDialog)
        select_button.pressed.connect(choose_color)

        def set_value(color):
            css = 'QLabel { background-color: %s; }' % color
            color_dialog.setCurrentColor(self._qt.QColor(color))
            preview_label.setStyleSheet(css)

        color_dialog.get_value = lambda: color_dialog.currentColor().name()
        color_dialog.set_value = set_value

        setattr(self.widget, '%sPreview' % cs_name, preview_label)
        setattr(self.widget, '%sDialog' % cs_name, color_dialog)
        self._layout.addWidget(label, self._row, 0)
        self._layout.addWidget(select_button, self._row, 2)
        self._layout.addWidget(preview_label, self._row, 3)
        self._row += 1

    def fill_space(self):
        """Creates a spacer that will vertically fill all the free space."""
        spacer = self._qt.QSpacerItem(1, 1, self._qt.QSizePolicy.Minimum,
                                      self._qt.QSizePolicy.Expanding)
        self._layout.addItem(spacer, self._row, 0)
        self._row += 1

    def add_widget(self, widget):
        """Adds a widget to the form."""
        self._layout.addWidget(widget, self._row, 0, 1, 4)
        self._row += 1


class GlobalSettings:
    """Creates the User Interfaces for Global Settings."""
    _qt = None
    _global_conf = None

    def __init__(self, qt, global_conf):
        self._qt = qt
        self._global_conf = global_conf

    def open(self):
        """Opens a dialog with the Global Settings."""
        conf = self._global_conf.get()
        dialog = self._qt.QDialog()
        dialog.setWindowTitle('Life Drain Global Settings')

        basic_tab = self._basic_tab()
        bar_style_tab = self._bar_style_tab()

        tab_widget = self._qt.QTabWidget()
        tab_widget.addTab(basic_tab, 'Basic')
        tab_widget.addTab(bar_style_tab, 'Bar Style')

        self._load_basic(basic_tab, conf)
        self._load_bar_style(bar_style_tab, conf)

        def save():
            self._global_conf.set({
                'enable': basic_tab.enableAddon.get_value(),
                'stopOnAnswer': basic_tab.stopOnAnswer.get_value(),
                'barPosition': bar_style_tab.positionList.get_value(),
                'barHeight': bar_style_tab.heightInput.get_value(),
                'barBorderRadius': bar_style_tab.borderRadiusInput.get_value(),
                'barText': bar_style_tab.textList.get_value(),
                'barStyle': bar_style_tab.styleList.get_value(),
                'barFgColor': bar_style_tab.fgColorDialog.get_value(),
                'barTextColor': bar_style_tab.textColorDialog.get_value(),
                'enableBgColor': bar_style_tab.enableBgColor.get_value(),
                'barBgColor': bar_style_tab.bgColorDialog.get_value()
            })
            return dialog.accept()

        button_box = self._qt.QDialogButtonBox(self._qt.QDialogButtonBox.Ok |
                                               self._qt.QDialogButtonBox.Cancel)
        button_box.rejected.connect(dialog.reject)
        button_box.accepted.connect(save)

        outer_form = Form(self._qt, dialog)
        outer_form.add_widget(tab_widget)
        outer_form.add_widget(button_box)

        dialog.setMinimumSize(400, 310)
        dialog.exec()

    def _basic_tab(self):
        tab = Form(self._qt)
        tab.check_box('enableAddon', 'Enable Life Drain')
        tab.check_box('stopOnAnswer', 'Stop drain on answer shown')
        tab.fill_space()
        return tab.widget

    def _bar_style_tab(self):
        tab = Form(self._qt)
        tab.combo_box('positionList', 'Position', POSITION_OPTIONS)
        tab.spin_box('heightInput', 'Height', [1, 40])
        tab.spin_box('borderRadiusInput', 'Border radius', [0, 20])
        tab.combo_box('textList', 'Text', map(itemgetter('text'), TEXT_FORMAT))
        tab.combo_box('styleList', 'Style', STYLE_OPTIONS)
        tab.color_select('fgColor', 'Bar color')
        tab.color_select('textColor', 'Text color')
        tab.check_box('enableBgColor', 'Enable custom background color')
        tab.color_select('bgColor', 'Background color')
        tab.fill_space()
        return tab.widget

    @staticmethod
    def _load_basic(widget, conf):
        widget.enableAddon.set_value(conf['enable'])
        widget.stopOnAnswer.set_value(conf['stopOnAnswer'])

    @staticmethod
    def _load_bar_style(widget, conf):
        widget.positionList.set_value(conf['barPosition'])
        widget.heightInput.set_value(conf['barHeight'])
        widget.borderRadiusInput.set_value(conf['barBorderRadius'])
        widget.textList.set_value(conf['barText'])
        widget.styleList.set_value(conf['barStyle'])
        widget.fgColorDialog.set_value(conf['barFgColor'])
        widget.textColorDialog.set_value(conf['barTextColor'])
        widget.enableBgColor.set_value(conf['enableBgColor'])
        widget.bgColorDialog.set_value(conf['barBgColor'])


class DeckSettings:
    """Creates the User Interface for Deck Settings."""
    _qt = None
    _deck_conf = None

    def __init__(self, qt, deck_conf):
        self._qt = qt
        self._deck_conf = deck_conf

    def open(self, life, set_deck_conf):
        """Opens a dialog with the Deck Settings."""
        conf = self._deck_conf.get()
        dialog = self._qt.QDialog()
        dialog.setWindowTitle('Life Drain options for {}'.format(conf['name']))

        basic_tab = self._basic_tab()
        damage_tab = self._damage_tab()

        tab_widget = self._qt.QTabWidget()
        tab_widget.addTab(basic_tab, 'Basic')
        tab_widget.addTab(damage_tab, 'Damage')

        self._load_basic(basic_tab, conf, life)
        self._load_damage(damage_tab, conf)

        def save():
            conf = self._deck_conf.get()

            enable_damage = damage_tab.enableDamageInput.isChecked()
            damage_value = damage_tab.damageInput.value()
            conf.update({
                'maxLife': basic_tab.maxLifeInput.value(),
                'recover': basic_tab.recoverInput.value(),
                'damage': damage_value if enable_damage else None,
                'currentValue': basic_tab.currentValueInput.value()
            })

            set_deck_conf(conf)
            self._deck_conf.set(conf)
            return dialog.accept()

        button_box = self._qt.QDialogButtonBox(self._qt.QDialogButtonBox.Ok |
                                               self._qt.QDialogButtonBox.Cancel)
        button_box.rejected.connect(dialog.reject)
        button_box.accepted.connect(save)

        outer_form = Form(self._qt, dialog)
        outer_form.add_widget(tab_widget)
        outer_form.add_widget(button_box)

        dialog.setMinimumSize(300, 210)
        dialog.exec()

    def _basic_tab(self):
        tab = Form(self._qt)
        tab.spin_box('maxLifeInput', 'Maximum life', [1, 10000], '''The time \
in seconds for the life bar go from full to empty.''')
        tab.spin_box('recoverInput', 'Recover', [0, 1000], '''The time in \
seconds that is recovered after answering a card.''')
        tab.spin_box('currentValueInput', 'Current life', [0, 10000], '''The \
current life, in seconds.''')
        tab.fill_space()
        return tab.widget

    def _damage_tab(self):
        tab = Form(self._qt)
        tab.check_box('enableDamageInput', 'Enable damage', '''Enable damage \
if a card is answered with 'Again'.''')
        tab.spin_box('damageInput', 'Damage', [-1000, 1000], '''The damage \
value to be dealt if answering with 'Again'.''')
        tab.fill_space()
        return tab.widget

    @staticmethod
    def _load_basic(widget, conf, life):
        widget.maxLifeInput.set_value(conf['maxLife'])
        widget.recoverInput.set_value(conf['recover'])
        widget.currentValueInput.set_value(life)

    @staticmethod
    def _load_damage(form, conf):
        def update_damageinput():
            damage_enabled = form.enableDamageInput.isChecked()
            form.damageInput.setEnabled(damage_enabled)
            form.damageInput.setValue(5)

        damage = conf['damage']
        form.enableDamageInput.set_value(damage is not None)
        form.enableDamageInput.stateChanged.connect(update_damageinput)
        form.damageInput.set_value(damage if damage is not None else 5)
        form.damageInput.setEnabled(conf['damage'] is not None)
