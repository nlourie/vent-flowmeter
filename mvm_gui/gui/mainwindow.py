#!/usr/bin/env python3
"""
This module handles the main window.
"""

from PyQt5 import QtWidgets, uic

#from maindisplay.maindisplay import MainDisplay
from settings.settings import Settings
from settings.settingsfile import SettingsFile

#from toolbar.toolbar import Toolbar
#from menu.menu import Menu
#from settings.settingsbar import SettingsBar
#from alarms.alarms import Alarms
from alarms.guialarms import GuiAlarms
#from alarms.alarmsbar import AlarmsBar
#from special.special import SpecialBar

#from toolsettings.toolsettings import ToolSettings
from monitor.monitor import Monitor
from data_filler import DataFiller
from data_handler import DataHandler
from start_stop_worker import StartStopWorker
from alarm_handler import AlarmHandler
from numpad.numpad import NumPad
from frozenplots.frozenplots import Cursor
from messagebar.messagebar import MessageBar


class MainWindow(QtWidgets.QMainWindow):
    #pylint: disable=too-many-public-methods
    #pylint: disable=too-many-instance-attributes
    """
    The class taking care for the main window.
    It is top-level with respect to other panes, menus, plots and
    monitors.
    """

    def __init__(self, config, esp32, *args, **kwargs):
        #pylint: disable=too-many-statements
        """
        Initializes the main window for the MVM GUI. See below for subfunction setup description.
        """

        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi('mainwindow.ui', self)  # Load the .ui file

        self.config = config
        self.esp32 = esp32
        settings_file = SettingsFile(self.config["settings_file_path"])
        self.user_settings = settings_file.load()

        '''
        Start the alarm handler, which will check for ESP alarms
        '''
        self.alarm_h = AlarmHandler(self.config, self.esp32, self.alarmbar)

        '''
        Get the toppane and child pages
        '''
        self.toppane = self.findChild(QtWidgets.QStackedWidget, "toppane")
        self.main = self.findChild(QtWidgets.QWidget, "main")
        self.initial = self.findChild(QtWidgets.QWidget, "initial")
        self.startup = self.findChild(QtWidgets.QWidget, "startup")

        '''
        Get the center pane (plots) widgets
        '''
        self.centerpane = self.findChild(
            QtWidgets.QStackedWidget, "centerpane")
        self.plots_all = self.findChild(QtWidgets.QWidget, "plots_all")
        self.alarms_settings = self.findChild(
            QtWidgets.QWidget, "alarms_settings")

        '''
        Get the bottombar and child pages
        '''
        self.bottombar = self.findChild(QtWidgets.QStackedWidget, "bottombar")
        self.toolbar = self.findChild(QtWidgets.QWidget, "toolbar")
        self.menu = self.findChild(QtWidgets.QWidget, "menu")
        self.frozen_bot = self.findChild(
            QtWidgets.QWidget, "frozenplots_bottom")
        self.settingsbar = self.findChild(
            QtWidgets.QWidget, "settingsbar")
        self.specialbar = self.findChild(
            QtWidgets.QWidget, "specialbar")
        self.blank = self.findChild(QtWidgets.QWidget, "blank")
        self.settingsfork = self.findChild(
            QtWidgets.QWidget, "settingsforkbar")
        self.alarmsbar = self.findChild(QtWidgets.QWidget, "alarmsbar")
        self.numpadbar = self.findChild(QtWidgets.QWidget, "numpadbar")

        '''
        Get the stackable bits on the right
        '''
        self.rightbar = self.main.findChild(
            QtWidgets.QStackedWidget, "rightbar")
        self.monitors_bar = self.main.findChild(
            QtWidgets.QWidget, "monitors_bar")
        self.frozen_right = self.main.findChild(
            QtWidgets.QWidget, "frozenplots_right")

        '''
        Get initial and startup buttons
        '''
        self.button_new_patient = self.initial.findChild(
            QtWidgets.QPushButton, "button_new_patient")
        self.button_resume_patient = self.initial.findChild(
            QtWidgets.QPushButton, "button_resume_patient")
        self.button_resume_patient.setEnabled(self.user_settings != {})

        self.button_start_settings = self.startup.findChild(
            QtWidgets.QPushButton, "button_start_settings")
        self.button_start_vent = self.startup.findChild(
            QtWidgets.QPushButton, "button_start_vent")
        self.button_start_test = self.startup.findChild(
            QtWidgets.QPushButton, "button_start_test")

        '''
        Get toolbar widgets
        '''
        self.button_menu = self.toolbar.findChild(
            QtWidgets.QPushButton, "button_menu")
        self.button_unlockscreen = self.toolbar.findChild(
            QtWidgets.QPushButton, "button_unlockscreen")
        self.home_button = self.toolbar.findChild(
            QtWidgets.QWidget, "home_button")
        self.goto_menu = self.toolbar.findChild(QtWidgets.QWidget, "goto_menu")
        self.goto_unlock = self.toolbar.findChild(
            QtWidgets.QWidget, "goto_unlock")
        self.label_status = self.toolbar.findChild(
            QtWidgets.QLabel, "label_status")

        toolsettings_names = {"toolsettings_1",
                              "toolsettings_2", "toolsettings_3"}
        self.toolsettings = {}

        for name in toolsettings_names:
            toolsettings = self.toolbar.findChild(QtWidgets.QWidget, name)
            toolsettings.connect_config(config)
            self.toolsettings[name] = toolsettings

        # Get menu widgets and connect settings for the menu widget
        self.button_back = self.menu.findChild(
            QtWidgets.QPushButton, "button_back")
        self.button_settingsfork = self.menu.findChild(
            QtWidgets.QPushButton, "button_settingsfork")
        self.button_startstop = self.menu.findChild(
            QtWidgets.QPushButton, "button_startstop")
        self.button_autoassist = self.menu.findChild(
            QtWidgets.QPushButton, "button_autoassist")
        self.button_specialops = self.menu.findChild(
            QtWidgets.QPushButton, "button_specialops")

        self.button_alarms = self.settingsfork.findChild(
            QtWidgets.QPushButton, "button_alarms")
        self.button_settings = self.settingsfork.findChild(
            QtWidgets.QPushButton, "button_settings")
        self.button_lockscreen = self.settingsfork.findChild(
            QtWidgets.QPushButton, "button_lockscreen")
        self.button_backsettings = self.settingsfork.findChild(
            QtWidgets.QPushButton, "button_backsettings")

        self.button_backalarms = self.alarmsbar.findChild(
            QtWidgets.QPushButton, "button_backalarms")
        self.button_applyalarm = self.alarmsbar.findChild(
            QtWidgets.QPushButton, "button_applyalarm")
        self.button_resetalarm = self.alarmsbar.findChild(
            QtWidgets.QPushButton, "button_resetalarm")
        self.button_upalarm = self.alarmsbar.findChild(
            QtWidgets.QPushButton, "button_upalarm")
        self.button_downalarm = self.alarmsbar.findChild(
            QtWidgets.QPushButton, "button_downalarm")
        self.button_offalarm = self.alarmsbar.findChild(
            QtWidgets.QPushButton, "button_offalarm")

        self.button_freeze = self.specialbar.findChild(
            QtWidgets.QPushButton, "button_freeze")
        self.button_backspecial = self.specialbar.findChild(
            QtWidgets.QPushButton, "button_backspecial")

        # Get frozen plots bottom bar widgets and connect
        self.button_unfreeze = self.frozen_bot.findChild(
            QtWidgets.QPushButton, "button_unfreeze")

        # Connect initial startup buttons
        self.button_resume_patient.pressed.connect(self.goto_resume_patient)
        self.button_new_patient.pressed.connect(self.goto_new_patient)
        self.button_start_vent.pressed.connect(self.goto_main)
        # TODO: connect to circuit test on ESP
        # self.button_start_test.pressed.connect()
        self.button_start_settings.pressed.connect(self.goto_settings)

        # Connect back and menu buttons to toolbar and menu
        # This effectively defines navigation from the bottombar.

        # Toolbar
        self.button_menu.pressed.connect(self.show_menu)

        # Menu
        self.button_back.pressed.connect(self.show_toolbar)
        self.button_alarms.pressed.connect(self.goto_alarms)
        self.button_settingsfork.pressed.connect(self.show_settingsfork)
        self.button_specialops.pressed.connect(self.show_specialbar)

        # Settings
        self.button_settings.pressed.connect(self.goto_settings)
        self.button_lockscreen.pressed.connect(self.lock_screen)
        self.button_backsettings.pressed.connect(self.show_menu)

        # Special
        self.button_freeze.pressed.connect(self.freeze_plots)
        self.button_unfreeze.pressed.connect(self.unfreeze_plots)
        self.button_backspecial.pressed.connect(self.show_menu)

        # Confirmation bar
        self.messagebar = MessageBar(self)
        self.bottombar.insertWidget(self.bottombar.count(), self.messagebar)

        # Assign unlock screen button and setup state
        self.unlockscreen_interval = self.config['unlockscreen_interval']
        self.button_unlockscreen._state = 0
        self.button_unlockscreen.setAutoRepeat(True)
        self.button_unlockscreen.setAutoRepeatInterval(
            self.unlockscreen_interval)
        self.button_unlockscreen.clicked.connect(self.handle_unlock)

        self.numpad = NumPad(self)
        self.numpad.assign_code(
            self.config['unlockscreen_code'], self.unlock_screen)

        self.numpad.button_back.pressed.connect(self.lock_screen)
        self.button_backalarms.pressed.connect(self.exit_alarms)

        #Instantiate the DataFiller, which takes
        #care of filling plots data
        self.data_filler = DataFiller(config)

        #Set up tool settings (bottom bar)

        #self.toolsettings[..] are the objects that hold min, max values for a given setting as
        #as the current value (displayed as a slider and as a number).
        toolsettings_names = {"toolsettings_1",
                              "toolsettings_2", "toolsettings_3"}
        self.toolsettings = {}

        for name in toolsettings_names:
            toolsettings = self.toolbar.findChild(QtWidgets.QWidget, name)
            toolsettings.connect_config(config)
            self.toolsettings[name] = toolsettings

        # Set up data monitor/alarms (side bar) and plots

        #self.monitors[..] are the objects that hold monitor values and
        #thresholds for alarm min and max. The current value and
        #optional stats for the monitored value (mean, max) are set
        #here.
        # plot slot widget names
        self.plots = {}
        for name in config['plots']:
            plot = self.main.findChild(QtWidgets.QWidget, name)
            plot.setFixedHeight(130)
            self.data_filler.connect_plot(name, plot)
            self.plots[name] = plot

        # The monitored fields from the default_settings.yaml config file
        self.monitors = {}
        for name in config['monitors']:
            monitor = Monitor(name, config)
            self.monitors[name] = monitor
            self.data_filler.connect_monitor(monitor)

        # The alarms are from the default_settings.yaml config file
        # self.alarms = {}
        # for name in config['alarms']:
        #     alarm = GuiAlarm(name, config, self.monitors, self.alarm_h)
        #     self.alarms[name] = alarm
        self.gui_alarm = GuiAlarms(config, self.esp32, self.monitors)
        for monitor in self.monitors.values():
            monitor.connect_gui_alarm(self.gui_alarm)

        # Get displayed monitors
        self.monitors_slots = self.main.findChild(
            QtWidgets.QVBoxLayout, "monitors_slots")
        self.alarms_settings.connect_monitors(self)
        self.alarms_settings.populate_monitors()
        self.button_applyalarm.pressed.connect(
            self.alarms_settings.apply_selected)
        self.button_resetalarm.pressed.connect(
            self.alarms_settings.reset_selected)
        self.button_offalarm.pressed.connect(
            self.alarms_settings.move_selected_off)
        self.button_upalarm.pressed.connect(
            self.alarms_settings.move_selected_up)
        self.button_downalarm.pressed.connect(
            self.alarms_settings.move_selected_down)

        # Connect the frozen plots
        # Requires building of an ordered array to associate the correct
        # controls with the plot.
        active_plots = []
        for slotname in self.plots:
            active_plots.append(self.plots[slotname])
        self.cursor = Cursor(active_plots)
        self.frozen_bot.connect_workers(
            self.data_filler, active_plots, self.cursor)
        self.frozen_right.connect_workers(active_plots, self.cursor)

        #Instantiate DataHandler, which will start a new
        #thread to read data from the ESP32. We also connect
        #the DataFiller to it, so the thread will pass the
        #data directly to the DataFiller, which will
        #then display them.
        self._data_h = DataHandler(
            config, self.esp32, self.data_filler, self.gui_alarm)

        self.specialbar.connect_datahandler_config_esp32(self._data_h,
                                                         self.config, self.esp32, self.messagebar)

        #Connect settings button to Settings overlay.
        self.settings = Settings(self)
        self.toppane.insertWidget(self.toppane.count(), self.settings)

        #Set up start/stop auto/min mode buttons.

        #Connect each to their respective mode toggle functions.
        #The StartStopWorker class takes care of starting and stopping a run

        self._start_stop_worker = StartStopWorker(
            self,
            self.config,
            self.esp32,
            self.button_startstop,
            self.button_autoassist,
            self.toolbar,
            self.settings)

        if self._start_stop_worker.is_running():
            self.goto_main()

        self.button_startstop.released.connect(
            self._start_stop_worker.toggle_start_stop)
        self.button_autoassist.released.connect(
            self._start_stop_worker.toggle_mode)
        self.gui_alarm.connect_workers(self._start_stop_worker)

    def lock_screen(self):
        """
        Perform screen locking.
        """

        self.toppane.setDisabled(True)
        self.show_toolbar(locked_state=True)
        self.alarms_settings.set_enabled_state(False)

    def unlock_screen(self):
        """
        Perform screen unlocking.
        """

        self.toppane.setEnabled(True)
        self.show_toolbar(locked_state=False)
        self.alarms_settings.set_enabled_state(True)

    def handle_unlock(self):
        """
        Handle the screen unlock procedure.
        """

        button = self.button_unlockscreen
        if button.isDown():
            if button._state == 0:
                button._state = 1
                button.setAutoRepeatInterval(50)
            else:
                self.show_numpadbar()
                button._state = 0
                button.setAutoRepeatInterval(self.unlockscreen_interval)

    def goto_new_patient(self):
        """
        Go ahead with shallow set of operational parameters.
        """

        self.show_startup()

    def goto_resume_patient(self):
        """
        Go ahead with previously used operational parameters.
        """

        self.settings.update_config(self.user_settings)

        self.show_startup()

    def goto_settings(self):
        """
        Open the Settings pane.
        """

        self.show_settings()
        self.show_settingsbar()
        if self._start_stop_worker.mode() == self._start_stop_worker.MODE_PSV:
            self.settings.tabs.setCurrentWidget(self.settings.tab_psv)
        elif self._start_stop_worker.mode() == self._start_stop_worker.MODE_PCV:
            self.settings.tabs.setCurrentWidget(self.settings.tab_pcv)

    def goto_main(self):
        """
        Open the home ui
        """

        self.show_main()
        self.show_toolbar()

    def exit_settings(self):
        """
        Go back to home ui from the Settings pane.
        """

        self.show_main()
        self.show_menu()

    def goto_alarms(self):
        """
        Open the alarms settings pane.
        """

        self.show_alarms()
        self.show_alarmsbar()
        self.alarms_settings.config_monitors()

    def exit_alarms(self):
        """
        Go back to home ui from the alarms settings pane.
        """

        self.show_menu()
        self.show_plots()
        self.alarms_settings.deconfig_monitors()

    def show_settings(self):
        """
        Open the Settings pane.
        """

        self.toppane.setCurrentWidget(self.settings)
        self.settings.tabs.setFocus()

    def show_startup(self):
        """
        Show the startup pane.
        """

        self.toppane.setCurrentWidget(self.startup)

    def show_menu(self):
        """
        Open the menu on the bottom of the home pane.
        """

        self.bottombar.setCurrentWidget(self.menu)

    def show_numpadbar(self):
        """
        Shows the numeric pad in the bottom of the home pane.
        """
        self.bottombar.setCurrentWidget(self.numpadbar)

    def show_toolbar(self, locked_state=False):
        """
        Shows the toolbar in the bottom bar.

        arguments:
        - locked_state: If true, shows the unlock button. Otherwise
                        shows the menu button.
        """
        self.bottombar.setCurrentWidget(self.toolbar)
        if locked_state:
            self.home_button.setCurrentWidget(self.goto_unlock)
        else:
            self.home_button.setCurrentWidget(self.goto_menu)

    def show_settingsbar(self):
        """
        Open the settings submenu.
        """

        self.bottombar.setCurrentWidget(self.settingsbar)

    def show_specialbar(self):
        """
        Open the special operations submenu.
        """

        self.bottombar.setCurrentWidget(self.specialbar)

    def show_main(self):
        """
        Show the home pane.
        """

        self.toppane.setCurrentWidget(self.main)

    def show_settingsfork(self):
        """
        Show the intermediate settings submenu
        """

        self.bottombar.setCurrentWidget(self.settingsfork)

    def show_alarms(self):
        """
        Shows the alarm settings controls in the center of the alarm
        settings pane.
        """

        self.centerpane.setCurrentWidget(self.alarms_settings)

    def show_plots(self):
        """
        Shows the plots in the center of the home pane.
        """

        self.centerpane.setCurrentWidget(self.plots_all)

    def show_alarmsbar(self):
        """
        Shows the alarm settings controls in the bottom of the alarm
        settings pane.
        """

        self.bottombar.setCurrentWidget(self.alarmsbar)

    def freeze_plots(self):
        """
        Open the frozen plots pane.
        """

        self.data_filler.freeze()
        self.rightbar.setCurrentWidget(self.frozen_right)
        self.bottombar.setCurrentWidget(self.frozen_bot)

    def unfreeze_plots(self):
        """
        Go back to the home pane from the frozen plots pane.
        """

        self.data_filler.unfreeze()
        self.rightbar.setCurrentWidget(self.monitors_bar)
        self.show_specialbar()
