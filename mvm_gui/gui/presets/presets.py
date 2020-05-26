#!/usr/bin/env python3
"""
Widget for showing user some preset values for quickly changing
a setting.
"""

from PyQt5 import QtWidgets, uic

class Presets(QtWidgets.QWidget):
    """
    The Presets widget shows a set of buttons that will change the current
    value of a setting (and a cancel button).

    gui.settings.settings.Settings is responsible for setting up callbacks
    on all buttons.

    Class members:
    - button_cancel: Cancel QPushButton
    - button_preset: QPushButtons for selecting a value
    """
    def __init__(self, presets, *args):
        """
        Initialize the Presets widget.

        Grabs child widgets.

        Arguments:
        - presets: list of 2-element lists of [number, string]. The first element
            in each list is the actual value for the button, the second is any extra
            text to show on the button.
        - args: Other arguments for QtWidgets.QWidget
        """
        super(Presets, self).__init__(*args)
        uic.loadUi("presets/presets.ui", self)

        # get the buttons from the preset dialog
        self.button_cancel = self.findChild(QtWidgets.QPushButton, "button_cancel")
        self.button_preset = []

        for i in range(1, 7):
            btn = self.findChild(QtWidgets.QPushButton, "button_preset" + str(i))
            self.button_preset.append(btn)

        for preset, button in zip(presets, self.button_preset):
            if len(preset[1]) > 0:
                btn_txt = str(preset[0]) + ' (' + preset[1] + ')'
            else:
                btn_txt = str(preset[0])
            button.setText(btn_txt)

        # Hide the buttons that are not needed
        for i in range(len(presets), len(self.button_preset)):
            self.button_preset[i].hide()
