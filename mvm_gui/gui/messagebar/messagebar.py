#!/usr/bin/env python3
"""
Bottom message bar that asks for user confirmation.
"""

from PyQt5 import QtWidgets, uic
from PyQt5 import QtCore


class MessageBar(QtWidgets.QWidget):
    #pylint: disable=too-many-instance-attributes
    """
    The MessageBar widget.
    """

    def __init__(self, parent, *args):
        """
        Initialize the MessageBar widget.

        Grabs child widgets.
        """
        super(MessageBar, self).__init__(*args)
        uic.loadUi("messagebar/messagebar.ui", self)

        self.mainparent = parent
        self.bottombar = self.mainparent.bottombar

        self.button_confirm = self.findChild(
            QtWidgets.QPushButton, "button_confirm")
        self.button_cancel = self.findChild(
            QtWidgets.QPushButton, "button_cancel")
        self.confirm_msg = self.findChild(QtWidgets.QLabel, "confirm_msg")

        self.confirm_msg.blinkstate = False
        self.confirm_msg.bordercolor = "#ffffff"
        self.blinktimer = QtCore.QTimer(self)
        self.blinktimer.setInterval(500)  # .5 seconds
        self.blinktimer.timeout.connect(self.blink_confirm)
        self.blinktimer.start()

        self.func_confirm = None
        self.func_cancel = None
        self.button_confirm.pressed.connect(self.confirmed)
        self.button_cancel.pressed.connect(self.cancelled)
        self.prev_menu = None

    def get_confirmation(self, title, message,
                         func_confirm=None, func_cancel=None, color="red"):
        #pylint: disable=too-many-arguments
        """
        Shows the confirmation in the bottom bar.

        title: Title of the confirmation (in bold)
        message: Message in the confirmation
        func_confirm: Additional function to run when confirm is pressed.
        func_cancel: Additional function to run when cancel is pressed
        color: Flashing border color of confirmation box
        """
        current_widget = self.bottombar.currentWidget()
        if current_widget != self:
            self.prev_menu = current_widget

        self.func_confirm = func_confirm
        self.func_cancel = func_cancel

        self.confirm_msg.setText("<p><b>" + title + "</b></p>" + message)
        self.confirm_msg.bordercolor = color

        self.bottombar.setCurrentWidget(self)

    def blink_confirm(self):
        """
        Timed-out function to make border of confirmation box blink.
        """
        label = self.confirm_msg
        if label.blinkstate:
            color = "#ffffff"
            label.blinkstate = False
        else:
            color = label.bordercolor
            label.blinkstate = True

        label.setStyleSheet("QLabel { border: 3px solid " + color + "; }")

    def confirmed(self):
        """
        Confirm button is pressed
        """

        if self.func_confirm is not None:
            self.func_confirm()

        self.cleanup()
        self.return_menu()

    def cancelled(self):
        """
        Cancel button is pressed
        """

        if self.func_cancel is not None:
            self.func_cancel()

        self.cleanup()
        self.return_menu()

    def cleanup(self):
        """
        Remove cancel and confirm functions for safety
        """
        self.func_cancel = None
        self.func_confirm = None

    def return_menu(self):
        """
        Go back to the previously shown menu, hiding the MessageMenu.
        """

        self.bottombar.setCurrentWidget(self.prev_menu)
