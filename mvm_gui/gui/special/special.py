#!/usr/bin/env python3
"""
This module handles the Special Operations for the MVM GUI.
This includes country-specific-procedurings, pause functions, and freezing functions.
"""

from PyQt5 import QtWidgets, uic
from PyQt5 import QtCore
from messagebox import MessageBox


class SpecialBar(QtWidgets.QWidget):
    """
    A widget class for handling Special Operations.
    """
    def __init__(self, *args):
        """
        Initialize the SpecialBar container widget.

        Provides a passthrough to underlying widgets.
        """
        super(SpecialBar, self).__init__(*args)
        uic.loadUi("special/special.ui", self)

        self.button_expause.pressed.connect(
            lambda: self.paused_pressed('pause_exhale'))
        self.button_expause.released.connect(
            lambda: self.paused_released('pause_exhale'))

        self.button_inspause.pressed.connect(
            lambda: self.paused_pressed('pause_inhale'))
        self.button_inspause.released.connect(
            lambda: self.paused_released('pause_inhale'))
        self.button_lung_recruit.pressed.connect(self.toggle_lung_recruit)
        self._lung_recruit = False
        self._timer = {}

    def connect_datahandler_config_esp32(self, data_h, config, esp32, messagebar):
        """
        Passes the data handler and the confi dict to this class.

        arguments:
        - data_h: A reference to the data handler.
        - config: A dictionary of configuration parameters from default_settings.yaml
        - esp32: A reference to the esp32
        - messagebar: Reference to the MessageBar used for confirmation.
        """
        self._data_h = data_h
        self._config = config
        self._esp32 = esp32
        self._messagebar = messagebar

    def is_configured(self):
        """
        Returns whether or not the SpecialBar is configured.

        returns: true or false depending on whether or not SpecialBar is configured.
        """
        return hasattr(self, "_data_h") and hasattr(self, "_config")

    def _get_lung_recruit_eta(self):
        """
        Retrieves the Lungh Recruitment ETA from the esp32 and displays the result in Stop button
        """
        eta = float(self._esp32.get("pause_lg_time"))
        if eta == 0:
            self.stop_lung_recruit()
            self._lung_recruit_timer.stop()
        else:
            self.button_lung_recruit.setText(
                "Stop\nLung Recruitment\n%d" % int(eta))

    def start_lung_recruit(self):
        """
        Starts the lung recruitment procedure
        """
        self._lung_recruit = True
        lr_time = self._config["lung_recruit_time"]["current"]
        lr_pres = self._config["lung_recruit_pres"]["current"]
        self.button_lung_recruit.setText(
            "Stop\nLung Recruitment\n %d" % lr_time)

        self._esp32.set("pause_lg_p", lr_pres)
        self._esp32.set("pause_lg_time", lr_time)
        self._esp32.set("pause_lg", 1)

        self._lung_recruit_timer = QtCore.QTimer()
        self._lung_recruit_timer.timeout.connect(self._get_lung_recruit_eta)
        self._lung_recruit_timer.start(500)

    def stop_lung_recruit(self):
        """
        Stops the lung recruitment procedure
        """
        self._lung_recruit = False
        self._esp32.set("pause_lg", 0)
        self._lung_recruit_timer.stop()
        self.button_lung_recruit.setText("Country-Specific\nProcedures")

    def toggle_lung_recruit(self):
        """
        Toggles between starting and stopping the lung recruitment procedure
        """
        if self._lung_recruit:
            self.stop_lung_recruit()
        else:
            self._messagebar.get_confirmation(
                "Please confirm",
                "Do you wanted to start the Lung Recruitment procedure?",
                func_confirm=self.start_lung_recruit,
                color="#00FF00")

    def paused_pressed(self, mode):
        """
        Called when either the inspiration ot expiration pause
        buttons are pressed.

        arguments:
        - mode: The pause mode (either 'pause_exhale' or 'pause_inhale')
        """
        if not self.is_configured():
            raise Exception('Need to call connect_config_esp first.')
        if mode not in ['pause_exhale', 'pause_inhale']:
            raise Exception(
                'Can only call paused_pressed with pause_exhale or pause_inhale.')

        for other_pause in self._timer:
            self.paused_released(other_pause)

        self._timer[mode] = QtCore.QTimer(self)
        self._timer[mode].timeout.connect(
            lambda: self.send_signal(mode=mode, pause=True))
        self._timer[mode].start(self._config['expinsp_setinterval'] * 1000)

    def paused_released(self, mode):
        """
        Called when either the inspiration ot expiration pause
        buttons are released.

        arguments:
        - mode: The pause mode (either 'pause_exhale' or 'pause_inhale')
        """
        if not self.is_configured():
            raise Exception('Need to call connect_config_esp first.')
        if mode not in ['pause_exhale', 'pause_inhale']:
            raise Exception(
                'Can only call paused_pressed with pause_exhale or pause_inhale.')

        self.stop_timer(mode)

        self.send_signal(mode=mode, pause=False)

    def send_signal(self, mode, pause):
        """
        Sends signal the appropriate signal the ESP
        to pause inpiration or expiration.

        arguments:
        - mode: The pause mode (either 'pause_exhale' or 'pause_inhale')
        - pause: Boolean for paused or not paused
        """
        try:
            if not self._data_h.set_data(mode, int(pause)):
                raise Exception('Call to set_data failed.')
        except Exception as error:
            msg = MessageBox()
            confirm_func = msg.critical("Critical",
                                        "Severe hardware communication error",
                                        str(error),
                                        "Communication error",
                                        {msg.Ok: lambda: self.stop_timer(mode)})
            confirm_func()

    def stop_timer(self, mode):
        """
        Stops the QTimer which sends
        signals to the ESP

        arguments:
        - mode: The pause mode (either 'pause_exhale' or 'pause_inhale')
        """
        if hasattr(self, '_timer'):
            self._timer[mode].stop()
