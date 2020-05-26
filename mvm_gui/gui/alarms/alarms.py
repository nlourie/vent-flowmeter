#!/usr/bin/env python3
'''
Module containing the Alarms class
which mnages the alarm thresholds
'''
from PyQt5 import QtWidgets, uic
from PyQt5 import QtCore


class AlarmScrollBar(QtWidgets.QScrollBar):
    """
    Custom class to override QScrollBar parameters.
    """

    def __init__(self, *args):
        # QtWidgets.QScrollBar.init(self, parent, **kwargs)
        super(AlarmScrollBar, self).__init__(*args)
        self.setStyleSheet("""QScrollBar:horizontal {
                height: 15px;
                margin: 0px 40px 0 40px;
                background-color: #cccfca;
            }
            QScrollBar::handle:horizontal {
                min-width: 40px;
            }
            QScrollBar::add-line:horizontal {
                width: 40px;
                subcontrol-position: right;
                subcontrol-origin: margin;
            }

            QScrollBar::sub-line:horizontal {
                width: 40px;
                subcontrol-position: left;
                subcontrol-origin: margin;
            }""")


def clickable(widget):
    #pylint: disable=invalid-name
    """
    Creates a click event filter for widgets that are not normally clickable.
    The 'connect' function can be used to now attach a function to the click event.

    arguments:
    - widget: the widget to be made clickable
    """
    class Filter(QtCore.QObject):
        '''
        An extension of QObject that adds a 'clicked'
        pyqysignal.
        '''
        clicked = QtCore.pyqtSignal()

        def eventFilter(self, obj, event):
            '''
            Reimplementation of QObject eventFilter.

            arguments:
            - obj: the object
            - event: the event
            '''
            if obj == widget:
                if event.type() == QtCore.QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        return True
            return False
    clickable_filter = Filter(widget)
    widget.installEventFilter(clickable_filter)
    return clickable_filter.clicked


class Alarms(QtWidgets.QWidget):
    #pylint: disable=too-many-instance-attributes
    '''
    Allows to set the min and max alarms thresholds
    '''
    STORED_PER_COL = 7

    def __init__(self, *args):
        """
        Initialize the Alarms widget.

        Grabs child widgets.
        """
        super(Alarms, self).__init__(*args)
        uic.loadUi("alarms/alarms.ui", self)

        self.layout = self.findChild(QtWidgets.QGridLayout, "monitors_layout")
        self.label_alarmname = self.findChild(
            QtWidgets.QLabel, "label_alarmname")

        self.slider_alarmmin = self.findChild(
            QtWidgets.QScrollBar, "slider_alarmmin")
        self.alarmmin_min = self.findChild(
            QtWidgets.QLabel, "alarmmin_min")
        self.alarmmin_value = self.findChild(
            QtWidgets.QLabel, "alarmmin_value")
        self.alarmmin_max = self.findChild(
            QtWidgets.QLabel, "alarmmin_max")

        self.slider_alarmmax = self.findChild(
            QtWidgets.QScrollBar, "slider_alarmmax")
        self.alarmmax_min = self.findChild(
            QtWidgets.QLabel, "alarmmax_min")
        self.alarmmax_value = self.findChild(
            QtWidgets.QLabel, "alarmmax_value")
        self.alarmmax_max = self.findChild(
            QtWidgets.QLabel, "alarmmax_max")

        self.enabled = True

        self.mainparent = None
        self.monitors = None
        self.monitors_slots = None
        self.displayed_monitors = None
        self.selected = None

    def connect_monitors(self, mainparent):
        """
        Grabs monitors and their corresponding display slots from the main window.

        arguments:
        - mainparent: Reference to the main window.
        """
        self.mainparent = mainparent
        self.monitors = mainparent.monitors
        self.monitors_slots = mainparent.monitors_slots
        self.displayed_monitors = mainparent.config['displayed_monitors']

        # connect monitors to selection and alarm clearing slots
        for name, monitor in self.monitors.items():
            clickable(monitor).connect(lambda n=name: self.select_monitor(n))

    def set_enabled_state(self, isenabled):
        '''
        Sets the state to enabled

        arguments:
        - isenabled: True is enabled, false otherwise.
        '''
        self.enabled = isenabled

    def select_monitor(self, selected):
        """
        Selected a particular monitor widget by config name.

        arguments:
        - selected: config name
        """
        if not self.enabled:
            return

        for name, monitor in self.monitors.items():
            if name == selected:
                self.selected = name
                monitor.set_alarm_state(False)
                # if monitor.alarm is not None:
                #     monitor.alarm.clear_alarm()
                # Show configuration and highlight monitor
                if monitor.config_mode:
                    monitor.highlight()
                    self.show_settings(name)
            elif monitor.config_mode:
                monitor.unhighlight()

    def set_slider_range(self, slider, monitor):
        #pylint: disable=no-self-use
        """
        Sets the range for a slider given the current monitor being used.
        Range is set to the coarseness of the monitor.step.

        arguments:
        - slider: Reference to the slider to be set.
        - monitor: Reference to the monitor to set slider range.
        """
        alarm = monitor.gui_alarm
        if alarm.has_valid_minmax(monitor.configname):
            slider.setMinimum(0)
            slider.setMaximum(
                (alarm.get_max(
                    monitor.configname) -
                 alarm.get_min(
                     monitor.configname)) /
                monitor.step)
            slider.setSingleStep(monitor.step)
            slider.setPageStep(slider.maximum() / 2)
            slider.setEnabled(True)
        else:
            slider.setMinimum(0)
            slider.setMaximum(0)
            slider.setPageStep(slider.maximum())
            slider.setDisabled(True)

    def do_alarmmin_moved(self, slidervalue, monitor):
        """
        A slot for when the minimum alarm slider moves.

        arguments:
        - slidervalue: The physical value on the slider.
        - monitor: Reference to the monitor to set the slider value.
        """
        # Prevent min > max
        alarm = monitor.gui_alarm
        if alarm.has_valid_minmax(monitor.configname):
            slidervalue = min(
                self.slider_alarmmax.sliderPosition(), slidervalue)
            value = slidervalue * monitor.step + \
                alarm.get_min(monitor.configname)
            self.alarmmin_value.setText(str(value))
            self.slider_alarmmin.setValue(slidervalue)
            self.slider_alarmmin.setSliderPosition(slidervalue)

    def do_alarmmax_moved(self, slidervalue, monitor):
        """
        A slot for when the maximum alarm slider moves.

        arguments:
        - slidervalue: The physical value on the slider.
        - monitor: Reference to the monitor to set the slider value.
        """
        # Prevent max < min
        alarm = monitor.gui_alarm
        if alarm.has_valid_minmax(monitor.configname):
            slidervalue = max(
                self.slider_alarmmin.sliderPosition(), slidervalue)
            value = slidervalue * monitor.step + \
                alarm.get_min(monitor.configname)
            self.alarmmax_value.setText(str(value))
            self.slider_alarmmax.setValue(slidervalue)
            self.slider_alarmmax.setSliderPosition(slidervalue)

    def show_settings(self, name):
        """
        Display settins for a given named monitor.

        arguments:
        - name: The config name of the monitor.
        """
        monitor = self.monitors[name]
        alarm = monitor.gui_alarm
        unit = "" if monitor.units is None else monitor.units
        self.label_alarmname.setText(monitor.name + " " + unit)
        self.label_alarmname.setStyleSheet(
            "QLabel { color: " + monitor.color + "; background-color: black}")

        self.set_slider_range(self.slider_alarmmin, monitor)
        self.slider_alarmmin.valueChanged.connect(
            lambda value: self.do_alarmmin_moved(value, monitor))

        if alarm.has_valid_minmax(name):
            sliderpos = int(
                (alarm.get_setmin(name) - alarm.get_min(name)) / monitor.step)
            self.slider_alarmmin.setSliderPosition(sliderpos)
            self.do_alarmmin_moved(sliderpos, monitor)
            self.alarmmin_min.setText(str(alarm.get_min(name)))
            self.alarmmin_max.setText(str(alarm.get_max(name)))
        else:
            self.alarmmin_value.setText("-")
            self.alarmmin_min.setText("-")
            self.alarmmin_max.setText("-")

        self.set_slider_range(self.slider_alarmmax, monitor)
        self.slider_alarmmax.valueChanged.connect(
            lambda value: self.do_alarmmax_moved(value, monitor))
        if alarm.has_valid_minmax(name):
            sliderpos = int(
                (alarm.get_setmax(name) - alarm.get_min(name)) / monitor.step)
            self.slider_alarmmax.setSliderPosition(sliderpos)
            self.do_alarmmax_moved(sliderpos, monitor)
            self.alarmmax_min.setText(str(alarm.get_min(name)))
            self.alarmmax_max.setText(str(alarm.get_max(name)))
        else:
            self.alarmmax_value.setText("-")
            self.alarmmax_min.setText("-")
            self.alarmmax_max.setText("-")

    def apply_selected(self):
        """
        Applies the settings on screen for the selected monitor.
        A monitor is always selected.
        """
        monitor = self.monitors[self.selected]
        alarm = monitor.gui_alarm
        if alarm.has_valid_minmax(monitor.configname):
            alarm.update_min(
                monitor.configname,
                self.slider_alarmmin.sliderPosition() *
                monitor.step +
                alarm.get_min(
                    monitor.configname))
            alarm.update_max(
                monitor.configname,
                self.slider_alarmmax.sliderPosition() *
                monitor.step +
                alarm.get_min(
                    monitor.configname))
            # monitor.update_thresholds()

    def reset_selected(self):
        """
        Resets the settings on screen for the selected monitor.
        A monitor is always selected.
        """
        self.show_settings(self.selected)

    def move_selected_to_index(self, index=None):
        """
        Moves the selected monitor to the index location on the monitor bar

        arguments:
        - index: location on the monitor bar
            If None, monitor is removed from the bar
            If >= len(displayed_monitors), adds to end
        """

        if index is not None:
            index = max(0, min(len(self.displayed_monitors), index))
            # print("Moving " + self.selected + " to slot " + str(index))
        else:
            index = -1
            # print("Moving " + self.selected + " to alarms page")

        newmons = []
        for (i, name) in enumerate(self.displayed_monitors):
            if i == index:
                newmons.append(self.selected)
            if name != self.selected:
                newmons.append(name)
        if index >= len(self.displayed_monitors):
            newmons.append(self.selected)

        self.clear_monitors()
        self.displayed_monitors = newmons
        self.populate_monitors()

    def move_selected_down(self):
        """
        Moves a monitor down the monitor bar.
        If the object is not on the monitor bar, place on the top.
        """
        if self.selected in self.displayed_monitors:
            index = self.monitors_slots.indexOf(
                self.monitors[self.selected]) + 2
        else:
            index = 0
        self.move_selected_to_index(index=index)

    def move_selected_up(self):
        """
        Moves a monitor up the monitor bar.
        If the object is not on the monitor bar, place on the bottom.
        """
        if self.selected in self.displayed_monitors:
            index = self.monitors_slots.indexOf(
                self.monitors[self.selected]) - 1
        else:
            index = len(self.displayed_monitors)
        self.move_selected_to_index(index=index)

    def move_selected_off(self):
        """
        Removes a monitor from the monitor bar
        """
        self.move_selected_to_index()

    def clear_monitors(self):
        """
        Removes all monitors from monitor bar and alarms page.
        """
        for name in self.monitors:
            if name in self.displayed_monitors:
                self.monitors_slots.removeWidget(self.monitors[name])
            else:
                self.layout.removeWidget(self.monitors[name])

    def populate_monitors(self):
        """
        Populates monitors based on the ones assigned as displayed.
        If the monitor is not displayed, it is shown in the alarms page.
        """
        # Iterate through all monitors and either display on main bar, or put
        # on alarms page
        hidd = 0
        for name, monitor in self.monitors.items():
            if name not in self.displayed_monitors:
                # Monitor not displayed, so goes on Alarms page
                self.layout.addWidget(monitor,
                                      int(hidd % self.STORED_PER_COL),
                                      10 - int(hidd / self.STORED_PER_COL))
                hidd += 1

        for (disp, name) in enumerate(self.displayed_monitors):
            # Monitor displayed, so goes on Monitor Bar
            self.monitors_slots.insertWidget(disp, self.monitors[name])

        # Refresh monitors after populating
        for _name, monitor in self.monitors.items():
            monitor.refresh()

    def config_monitors(self):
        """
        Set all monitors into configuration mode.
        Always selects the last monitor as selected by default.
        """
        for name in self.monitors:
            self.monitors[name].config_mode = True
            self.selected = name
        self.select_monitor(self.selected)

    def deconfig_monitors(self):
        """
        Unsets all monitors out of configuration mode.
        """
        for name in self.monitors:
            self.monitors[name].unhighlight()
            self.monitors[name].config_mode = False
