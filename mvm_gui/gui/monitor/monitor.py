#!/usr/bin/env python3
"""
Module that implements the widget for monitored values, with alarm
indication and snooze control.
"""

from PyQt5 import QtWidgets, uic
from PyQt5 import QtGui


class Monitor(QtWidgets.QWidget):
    #pylint: disable=too-many-instance-attributes
    """
    The Monitor class.

    This class provides visual display of monitored data as well as a way
    to display and snooze alarms.
    """

    def __init__(self, name, config, *args):
        """
        Initialize the Monitor widget.

        Grabs child widgets and sets alarm facility up.

        """
        super(Monitor, self).__init__(*args)
        uic.loadUi("monitor/monitor.ui", self)
        self.config = config
        self.configname = name

        self.label_name = self.findChild(QtWidgets.QLabel, "label_name")
        self.label_value = self.findChild(QtWidgets.QLabel, "label_value")
        self.label_min = self.findChild(QtWidgets.QLabel, "label_min")
        self.label_max = self.findChild(QtWidgets.QLabel, "label_max")
        self.stats_slots = self.findChild(QtWidgets.QGridLayout, "stats_slots")
        self.frame = self.findChild(QtWidgets.QFrame, "frame")

        monitor_default = {
            "name": "NoName",
            "init": 50,
            "units": None,
            "step": 1,
            "map": {},
            "dec_precision": 0,
            "color": "white",
            "alarmcolor": "red",
            "observable": "o2",
            "disp_type": None}
        entry = self.config['monitors'].get(name, monitor_default)

        self.entry = entry
        self.name = entry.get("name", monitor_default["name"])
        self.value = entry.get("init", monitor_default["init"])
        self.units = entry.get("units", monitor_default["units"])
        self.dec_precision = entry.get(
            "dec_precision", monitor_default["dec_precision"])
        self.color = entry.get("color", monitor_default["color"])
        self.alarmcolor = entry.get(
            "alarmcolor", monitor_default["alarmcolor"])
        self.step = entry.get("step", monitor_default["step"])
        self.map = entry.get("map", monitor_default["map"])
        self.observable = entry.get(
            "observable", monitor_default["observable"])
        self.disp_type = entry.get("disp_type", monitor_default["disp_type"])
        self.gui_alarm = None

        self.refresh()
        self.set_alarm_state(False)
        self.update_value(self.value)
        self.update_thresholds(None, None, None, None)
        self.label_value.resizeEvent = self.handle_resize

        # Get handles for display type
        self.display_opts = self.findChild(
            QtWidgets.QStackedWidget, "display_opts")
        self.shown_widget = self.findChild(QtWidgets.QWidget, "default_text")

        # bar type
        self.progress_bar = self.findChild(QtWidgets.QProgressBar, "bar_value")

        # Handle optional custom display type
        if self.disp_type is not None:
            if "bar" in self.disp_type:
                self.setup_bar_disp_type()
        self.display_opts.setCurrentWidget(self.shown_widget)

        # Setup config mode
        self.config_mode = False
        self.unhighlight()

    def setup_bar_disp_type(self):
        """
        Set a bar display, e.g. the battery charge.
        """

        (_, low, high) = self.disp_type.split(" ")
        self.shown_widget = self.findChild(QtWidgets.QWidget, "progress_bar")
        self.shown_widget.setStyleSheet(
            "QProgressBar {"
            "   background-color: rgba(0,0,0,0);"
            "   text-align: center;"
            "}"
            "QProgressBar::chunk {"
            "    background-color: #888888;"
            "}")
        showformat = "%p"
        if self.units is not None:
            showformat += " " + self.units
        self.progress_bar.setFormat(showformat)
        self.progress_bar.setMinimum(int(low))
        self.progress_bar.setMaximum(int(high))

    def get_name(self):
        '''
        Returns the configuration name
        for this monitor
        '''
        return self.configname

    def connect_gui_alarm(self, gui_alarm):
        '''
        Stores the GuiAlarm class
        '''
        self.gui_alarm = gui_alarm

    def update_thresholds(self, alarm_min, alarm_setmin,
                          alarm_max, alarm_setmax):
        '''
        Updates the labes showind the threshold values
        '''
        self.label_min.hide()
        self.label_max.hide()
        # if self.alarm is not None:
        print("Updating thresholds for " + self.configname)

        if alarm_min is not None:
            self.label_min.setText(str(alarm_setmin))
            self.label_min.show()

        if alarm_max is not None:
            self.label_max.setText(str(alarm_setmax))
            self.label_max.show()

    def refresh(self):
        """
        Update the monitor visuals (text and color) on new data in.
        """

        # Handle optional units
        if self.units is not None:
            self.label_name.setText(self.name + " " + str(self.units))
        else:
            self.label_name.setText(self.name)

        self.setStyleSheet("QWidget { color: " + str(self.color) + "; }")
        self.setAutoFillBackground(True)

    def handle_resize(self, event):
        #pylint: disable=unused-argument
        """
        Resize event callback function
        """

        # Handle font resize
        self.resize_font(self.label_value, minpx=10, maxpx=50, offset=23)
        self.resize_font(self.progress_bar, minpx=10, maxpx=16, offset=0)

    def resize_font(self, label, minpx=10, maxpx=50, offset=0):
        """
        Compute and update correct font size for the monitor size.
        """

        font = label.font()
        font.setPixelSize(max(min(self.height() - offset, maxpx), minpx))
        label.setFont(font)

    def set_alarm_state(self, isalarm):
        '''
        Sets or clears the alarm
        arguments:
        - isalarm: True is alarmed state
        '''
        if isalarm:
            color = self.alarmcolor
        else:
            color = QtGui.QColor("#000000")
            if self.gui_alarm is not None:
                self.gui_alarm.clear_alarm(self.configname)
        palette = self.palette()
        role = self.backgroundRole()
        palette.setColor(role, QtGui.QColor(color))
        self.setPalette(palette)

    def highlight(self):
        """
        Add a green contour on monitor.
        """

        self.frame.setStyleSheet("#frame { border: 5px solid limegreen; }")

    def unhighlight(self):
        """
        Remove the green contour on monitor.
        """

        self.frame.setStyleSheet("#frame { border: 0.5px solid white; }")

    def update_value(self, value):
        """
        Update the displayed value

        arguments:
        - value: the numeric value to be set.
        """

        if self.step is not None:
            self.value = round(value / self.step) * self.step
        else:
            self.value = value
        string_value = "%.*f" % (self.dec_precision, value)

        if self.map != {}:
            string_value = self.map.get(value, string_value)

        self.label_value.setText(string_value)
        self.bar_value.setValue(self.value)
