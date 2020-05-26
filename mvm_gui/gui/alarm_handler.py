"""
Tools for asking the ESP about any alarms that have been raised,
and telling the user about them if so.

The top alarmbar shows little QPushButtons for each alarm that is currently active.
If the user clicks a button, they are shown the message text and a "snooze" button
for that alarm.

There is a single physical snooze button which is manipulated based on which alarm
the user has selected.
"""

import sys
from PyQt5 import QtCore, QtWidgets

from messagebox import MessageBox
from communication.esp32serial import ESP32Exception

BITMAP = {1 << x: x for x in range(32)}
ERROR = 0
WARNING = 1

class SnoozeButton:
    """
    Takes care of snoozing alarms.

    Class members:
    - _esp32: ESP32Serial object for communication
    - _alarm_h: AlarmHandler
    - _alarmsnooze: QPushButton that user will press
    - _code: The alarm code that the user is currently dealing with
    - _mode: Whether the current alarm is an ERROR or a WARNING
    """
    def __init__(self, esp32, alarm_h, alarmsnooze):
        """
        Constructor

        Arguments: see relevant class members
        """
        self._esp32 = esp32
        self._alarm_h = alarm_h
        self._alarmsnooze = alarmsnooze

        self._alarmsnooze.hide()
        self._code = None
        self._mode = None

        self._alarmsnooze.clicked.connect(self._on_click_snooze)
        self._alarmsnooze.setStyleSheet(
            'background-color: rgb(0,0,205); color: white; font-weight: bold;')
        self._alarmsnooze.setMaximumWidth(150)

    def set_code(self, code):
        """
        Sets the alarm code

        Arguments:
        - code: Integer alarm code
        """
        self._code = code
        self._alarmsnooze.setText('Snooze %s' % str(BITMAP[self._code]))

    def set_mode(self, mode):
        """
        Sets the mode.

        Arguments:
        - mode: ALARM or WARNING
        """
        self._mode = mode

    def show(self):
        """
        Shows the snooze alarm button
        """
        self._alarmsnooze.show()

    def _on_click_snooze(self):
        """
        The callback function called when the alarm snooze button is clicked.
        """
        if self._mode not in [WARNING, ERROR]:
            raise Exception('mode must be alarm or warning.')

        # Reset the alarms/warnings in the ESP
        # If the ESP connection fails at this
        # time, raise an error box
        try:
            if self._mode == ERROR:
                self._esp32.snooze_hw_alarm(self._code)
                self._alarm_h.snooze_alarm(self._code)
            else:
                self._esp32.reset_warnings()
                self._alarm_h.snooze_warning(self._code)
        except ESP32Exception as error:
            msg = MessageBox()
            func = msg.critical("Critical",
                                "Severe hardware communication error",
                                str(error),
                                "Communication error",
                                {msg.Retry: lambda: None,
                                 msg.Abort: lambda: None})
            func()

class AlarmButton(QtWidgets.QPushButton):
    """
    The alarm and warning buttons shown in the top alarmbar.

    Class members:
    - _mode: Whether this alarm is an ERROR or a WARNING
    - _code: The integer code for this alarm.
    - _errstr: Test describing this alarm.
    - _label: The QLabel to populate with the error message, if the user
        clicks our button.
    - _snooze_btn: The SnoozeButton to manipulate if the user clicks our
        button.
    """
    def __init__(self, mode, code, errstr, label, snooze_btn):
        super(AlarmButton, self).__init__()
        self._mode = mode
        self._code = code
        self._errstr = errstr
        self._label = label
        self._snooze_btn = snooze_btn

        self.clicked.connect(self._on_click_event)

        if self._mode == ERROR:
            self._bkg_color = 'red'
        elif self._mode == WARNING:
            self._bkg_color = 'orange'
        else:
            raise Exception('Option %s not supported' % self._mode)

        self.setText(str(BITMAP[self._code]))

        style = """background-color: %s;
                   color: white; 
                   border: 0.5px solid white; 
                   font-weight: bold;
                """ % self._bkg_color

        self.setStyleSheet(style)

        self.setMaximumWidth(35)
        self.setMaximumHeight(30)

    def _on_click_event(self):
        """
        The callback function called when the user clicks on an alarm button
        """

        # Set the label showing the alarm name
        style = """QLabel {
                        background-color: %s; 
                        color: white; 
                        font-weight: bold;
                    }""" % self._bkg_color

        self._label.setStyleSheet(style)
        self._label.setText(self._errstr)
        self._label.show()

        self._activate_snooze_btn()

    def _activate_snooze_btn(self):
        """
        Activates the snooze button that will silence this alarm
        """
        self._snooze_btn.set_mode(self._mode)
        self._snooze_btn.set_code(self._code)
        self._snooze_btn.show()

class AlarmHandler:
    """
    This class starts a QTimer dedicated to checking is there are any errors
    or warnings coming from ESP32

    Class members:
    - _esp32: ESP32Serial object for communication
    - _alarm_time: Timer that will periodically ask the ESP about any alarms
    - _err_buttons: {int: AlarmButton} for any active ERROR alarms
    - _war_buttons: {int: AlarmButton} for any active WARNING alarms
    - _alarmlabel: QLabel showing text of the currently-selected alarm
    - _alarmstack: Stack of QPushButtons for active alarms
    - _alarmsnooze: QPushButton for snoozing an alarm
    - _snooze_btn: SnoozeButton that manipulates _alarmsnooze
    """

    def __init__(self, config, esp32, alarmbar):
        """
        Constructor

        Arguments: see relevant class members.
        """

        self._esp32 = esp32

        self._alarm_timer = QtCore.QTimer()
        self._alarm_timer.timeout.connect(self.handle_alarms)
        self._alarm_timer.start(config["alarminterval"] * 1000)

        self._err_buttons = {}
        self._war_buttons = {}

        self._alarmlabel = alarmbar.findChild(QtWidgets.QLabel, "alarmlabel")
        self._alarmstack = alarmbar.findChild(QtWidgets.QHBoxLayout, "alarmstack")
        self._alarmsnooze = alarmbar.findChild(QtWidgets.QPushButton, "alarmsnooze")

        self._snooze_btn = SnoozeButton(self._esp32, self, self._alarmsnooze)

    def handle_alarms(self):
        """
        The callback method which is called periodically to check if the ESP raised any
        alarm or warning.
        """

        # Retrieve alarms and warnings from the ESP
        try:
            esp32alarm = self._esp32.get_alarms()
            esp32warning = self._esp32.get_warnings()
        except ESP32Exception as error:
            esp32alarm = None
            esp32warning = None
            err_msg = "Severe hardware communication error. "
            err_msg += "Cannot retrieve alarm and warning statuses from hardware."
            msg = MessageBox()
            func = msg.critical("Critical",
                                err_msg,
                                str(error),
                                "Communication error",
                                {msg.Retry: lambda: None,
                                 msg.Abort: lambda: sys.exit(-1)})
            func()

        #
        # ALARMS
        #
        if esp32alarm:
            errors = esp32alarm.strerror_all()

            alarm_codes = esp32alarm.get_alarm_codes()

            for alarm_code, err_str in zip(alarm_codes, errors):
                if alarm_code not in self._err_buttons:
                    btn = AlarmButton(ERROR, alarm_code, err_str,
                                      self._alarmlabel, self._snooze_btn)
                    self._alarmstack.addWidget(btn)
                    self._err_buttons[alarm_code] = btn

        #
        # WARNINGS
        #
        if esp32warning:
            errors = esp32warning.strerror_all()

            warning_codes = esp32warning.get_alarm_codes()

            for warning_code, err_str in zip(warning_codes, errors):
                if warning_code not in self._war_buttons:
                    btn = AlarmButton(
                        WARNING, warning_code, err_str, self._alarmlabel, self._snooze_btn)
                    self._alarmstack.addWidget(btn)
                    self._war_buttons[warning_code] = btn

    def snooze_alarm(self, code):
        """
        Graphically snoozes alarm corresponding to 'code'

        Arguments:
        - code: integer alarm code
        """
        if code not in self._err_buttons:
            raise Exception('Cannot snooze code %s as alarm button doesn\'t exist.' % code)

        self._err_buttons[code].deleteLater()
        del self._err_buttons[code]
        self._alarmlabel.setText('')
        self._alarmlabel.setStyleSheet('QLabel { background-color: black; }')
        self._alarmsnooze.hide()

    def snooze_warning(self, code):
        """
        Graphically snoozes warning corresponding to 'code'

        Arguments:
        - code: integer alarm code
        """
        if code not in self._war_buttons:
            raise Exception('Cannot snooze code %s as warning button doesn\'t exist.' % code)

        self._war_buttons[code].deleteLater()
        del self._war_buttons[code]
        self._alarmlabel.setText('')
        self._alarmlabel.setStyleSheet('QLabel { background-color: black; }')
        self._alarmsnooze.hide()
