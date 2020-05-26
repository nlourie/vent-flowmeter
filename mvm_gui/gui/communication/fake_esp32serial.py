"""
A dummy class that can be used for testing the GUI when a real
ESP32 chip isn't available.
"""

import random
import time
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QTextCursor
from communication.peep import PEEP
from . import ESP32Alarm, ESP32Warning


class FakeMonitored(QtWidgets.QWidget):
    """
    A class widget for generating fake monitored MVM data.
    """
    def __init__(self, name, generator, value=0, is_random=True):
        """
        A constructor for the class.

        arguments:
        - name: The displayed text.
        - generator: The function for generating fake data.
        - value: The initiazlized Spin Box value.
        - is_random: Boolean to indicate using randomized data.
        """
        super(FakeMonitored, self).__init__()
        uic.loadUi('communication/input_monitor_widget.ui', self)

        self.generator = generator

        self.findChild(QtWidgets.QLabel, "label").setText(name)

        self.value_ib = self.findChild(QtWidgets.QDoubleSpinBox, "value")
        self.value_ib.setValue(value)

        self.random_cb = self.findChild(QtWidgets.QCheckBox, "random_checkbox")
        self.random_cb.setChecked(is_random)
        self.random_cb.toggled.connect(self._random_checkbox_fn)
        self._random_checkbox_fn()

    def _random_checkbox_fn(self):
        self.value_ib.setEnabled(not self.random_cb.isChecked())

    def generate(self):
        """
        Generate Fake data

        returns: An array of fake generated data
        """
        if self.random_cb.isChecked():
            return self.generator()
        return self.value_ib.value()


class FakeESP32Serial(QtWidgets.QMainWindow):
    # pylint: disable=too-many-instance-attributes
    # These are appropriate instances for initialization of dictionaries
    """
    A widget class to emulate ESP32 functionality when not connected to hardware.
    """
    peep = PEEP()

    def __init__(self, config):
        super(FakeESP32Serial, self).__init__()

        uic.loadUi('communication/fakeesp32.ui', self)
        self.get_all_fields = config["get_all_fields"]
        self.observables = {name: None for name in self.get_all_fields}

        self._arrange_fields()
        self.alarms_checkboxes = {}
        self.warning_checkboxes = {}
        self._connect_alarm_and_warning_widgets()
        self._connect_status_widgets()
        self._lung_recruit_stop_time = 0

        self.set_params = {
            "run": 0,
            "mode": 0,
            "backup": 0,
            "alarm": 0,
            "warning": 0,
            "temperature": 40,
            "rate": 17.0,
            "ratio": 2 / 3,
            "ptarget": 37.7,
            "pcv_trigger_enable": 1,
            "pcv_trigger": 7,
            "assist_ptrigger": 7.0,
            "assist_flow_min": 47.0,
            "pressure_support": 27.,
            "backup_min_time": 17.0,
            "backup_enable": 1,
            "pause_lg_p": 37,
            "pause_lg_time": 7.0}

        self.event_log = self.findChild(QtWidgets.QPlainTextEdit, "event_log")
        self.event_log.setReadOnly(True)
        self.show()

    # pylint: disable=too-many-branches
    # The number of branches is appropriate given the different types of generators.
    def _arrange_fields(self):
        max_colums = 3  # you eventually need to edit the
        # input_monitor_widget.ui file to put more

        monitors_grid = self.findChild(QtWidgets.QGridLayout, "monitors_grid")

        row = 0
        column = 0
        for name in self.observables:
            if name == "pressure":
                generator = self.peep.pressure
            elif name == "flow":
                generator = self.peep.flow
            elif name == "battery_charge":
                generator = lambda: int(random.uniform(0, 100))
            elif name == "tidal":
                generator = lambda: random.uniform(1000, 1500)
            elif name == "peep":
                generator = lambda: random.uniform(4, 20)
            elif name == "temperature":
                generator = lambda: random.uniform(10, 50)
            elif name == "battery_powered":
                generator = lambda: int(random.uniform(0, 1.5))
            elif name == "bpm":
                generator = lambda: random.uniform(10, 100)
            elif name == "o2":
                generator = lambda: random.uniform(10, 100)
            elif name == "peak":
                generator = lambda: random.uniform(10, 100)
            elif name == "total_inspired_volume":
                generator = lambda: random.uniform(10, 100)
            elif name == "total_expired_volume":
                generator = lambda: random.uniform(10, 100)
            elif name == "volume_minute":
                generator = lambda: random.uniform(10, 100)
            else:
                generator = lambda: random.uniform(10, 100)

            fake_mon = FakeMonitored(name, generator)
            self.observables[name] = fake_mon

            monitors_grid.addWidget(fake_mon, row, column)

            column += 1
            if column == max_colums:
                column = 0
                row += 1

    def _compute_and_raise_alarms(self):
        number = 0
        for item in self.alarms_checkboxes:
            if self.alarms_checkboxes[item].isChecked():
                number += item
        self.set("alarm", number)

    def _compute_and_raise_warnings(self):
        number = 0
        for item in self.warning_checkboxes:
            if self.warning_checkboxes[item].isChecked():
                number += item
        self.set("warning", number)

    def _connect_alarm_and_warning_widgets(self):
        get_checkbox = lambda wname, alarm_code: (
            1 << alarm_code, self.findChild(QtWidgets.QCheckBox, wname))

        # for simplicity here the bit number is used. It will be converted
        # few lines below.

        # HW alarms
        alarm_check_boxes = {
            "low_input_pressure_alarm": 0,
            "high_input_pressure_alarm": 1,
            "low_inner_pressure_alarm": 2,
            "high_inner_pressure_alarm": 3,
            "battery_low_alarm": 4,
            "gas_leakage_alarm": 5,
            "gas_occlusion_alarm": 6,
            "partial_gas_occlusion_alarm": 7,
            "apnea_alarm": 22,
            "system_failure_alarm": 31}

        # HW warnings
        warning_check_boxes = {
            "o2_warning": 0,
            "power_warning": 1}

        for name in alarm_check_boxes:
            code, widget = get_checkbox(name, alarm_check_boxes[name])
            self.alarms_checkboxes[code] = widget

        self.raise_alarms_button = self.findChild(
            QtWidgets.QPushButton,
            "raise_alarm_btn")

        self.raise_alarms_button.pressed.connect(
            self._compute_and_raise_alarms)

        for name in warning_check_boxes:
            code, widget = get_checkbox(name, warning_check_boxes[name])
            self.warning_checkboxes[code] = widget

        self.raise_warnings_button = self.findChild(
            QtWidgets.QPushButton,
            "raise_warning_btn")

        self.raise_warnings_button.pressed.connect(
            self._compute_and_raise_warnings)

    def _connect_status_widgets(self):
        '''
        Connects the Change Status button to the
        appropriate callback
        '''
        self.btn_change_status.clicked.connect(self._update_status)

    def _update_status(self):
        '''
        Changes the run,mode,backup variables in the ESP
        '''
        self.set('run', int(self.status_run.isChecked()))
        self.set('mode', int(self.status_mode.isChecked()))
        self.set('backup', int(self.status_backup.isChecked()))

    def log(self, message):
        """
        Logs a given message.

        arguments:
        -message: The message to be logged
        """
        self.event_log.appendPlainText(message)
        cursor = self.event_log.textCursor()
        cursor.movePosition(QTextCursor.End)

    def set(self, name, value):
        """
        Set command wrapper

        arguments:
        - name           the parameter name as a string
        - value          the value to assign to the variable as any type
                         convertible to string

        returns: an "OK" string in case of success.
        """

        print("FakeESP32Serial-DEBUG: set %s %s" % (name, value))

        if name == 'pause_lg' and int(value) == 1:
            self._lung_recruit_stop_time = time.time(
            ) + self.set_params["pause_lg_time"]

        self.set_params[name] = value
        return "OK"

    def set_watchdog(self):
        """
        Set the watchdog polling command

        returns: an "OK" string in case of success.
        """

        return self.set("watchdog_reset", 1)

    def get(self, name):
        """
        Get command wrapper

        arguments:
        - name           the parameter name as a string

        returns: the requested value
        """

        print("FakeESP32Serial-DEBUG: get %s" % name)

        retval = 0

        if name in self.observables:
            retval = self.observables[name].generate()
        elif name == 'pause_lg_time':
            eta = self._lung_recruit_stop_time - time.time()
            if eta > 0:
                retval = eta
            else:
                retval = 0
        elif name in self.set_params:
            retval = self.set_params[name]
        else:
            retval = int(random.uniform(10, 100))

        return str(retval)

    def get_all(self):
        """
        Get the pressure, flow, o2, and bpm at once and in this order.

        returns: a dict with member keys as written above and values as
        strings.
        """

        print("FakeESP32Serial-DEBUG: get all")

        values = [self.get(field) for field in self.get_all_fields]

        return dict(zip(self.get_all_fields, values))

    def get_alarms(self):
        """
        Get the alarms from the ESP32

        returns: a ESP32Alarm instance describing the possible alarms.
        """

        return ESP32Alarm(int(self.get("alarm")))

    def get_warnings(self):
        """
        Get the warnings from the ESP32

        returns: a ESP32Warning instance describing the possible warnings.
        """

        return ESP32Warning(int(self.get("warning")))

    def reset_alarms(self):
        """
        Reset all the raised alarms in ESP32

        returns: an "OK" string in case of success.
        """

        self.log("alarms lowered")
        return self.set("alarm", 0)

    def reset_warnings(self):
        """
        Reset all the raised warnings in ESP32

        returns: an "OK" string in case of success.
        """

        self.log("warnings lowered")
        return self.set("warning", 0)

    def raise_gui_alarm(self):
        """
        Raises an alarm in ESP32

        arguments:
        - alarm_type      an integer representing the alarm type

        returns: an "OK" string in case of success.
        """

        self.log("GUI Alarm!")

        self.set_params["alarm"] = self.set_params["alarm"] | 1 << 29

        return "OK"

    def snooze_hw_alarm(self, alarm_type):
        """
        Function to snooze the corresponding alarm in ESP32

        arguments:
        - alarm_type      an integer representing the alarm type. One and
                          only one

        returns: an "OK" string in case of success.
        """

        self.log("Snooze HW alarm %d" % alarm_type)
        current_alarm = self.set_params["alarm"]
        if current_alarm & alarm_type:
            self.set_params["alarm"] = current_alarm ^ alarm_type
        return "OK"

    def snooze_gui_alarm(self):
        """
        Function to snooze the corresponding alarm in ESP32

        arguments:
        - alarm_type      an integer representing the alarm type. One and
                          only one

        returns: an "OK" string in case of success.
        """

        self.log("Snooze gui alarms")
        return self.snooze_hw_alarm(1 << 29)
