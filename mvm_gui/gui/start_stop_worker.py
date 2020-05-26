'''
A file from class StartStopWorker
'''
import sys
from PyQt5.QtCore import QTimer
from messagebox import MessageBox
from communication.esp32serial import ESP32Exception


class StartStopWorker():
    #pylint: disable=too-many-instance-attributes
    '''
    A class entirely dedicated to start and stop
    the ventilator, and also to set the ventilator
    mode. For now, this is called only from the
    mainwindow.
    '''
    MODE_PCV = 0
    MODE_PSV = 1

    DO_RUN = 1
    DONOT_RUN = 0

    def __init__(self, main_window, config, esp32, button_startstop,
                 button_mode, toolbar, settings):
        #pylint: disable=too-many-arguments
        '''
        Constructor

        Arguments:
        - main_window: the main window
        - config: the config dictionary
        - esp32: the instance of the ESP32Serial class
        - button_startstop: The start/stop button
        - button_mode: The PCV/PSV button
        - toolbar: The toolbar
        - settings: The settings
        '''

        self._main_window = main_window
        self._config = config
        self._esp32 = esp32
        self._button_startstop = button_startstop
        self._button_mode = button_mode
        self._toolbar = toolbar
        self._settings = settings
        self._messagebar = self._main_window.messagebar

        self._mode_text = "PCV"

        self._mode = self.MODE_PCV
        self._run = self.DONOT_RUN

        self._backup_ackowledged = False

        self._esp32_io()

        self._init_settings_panel()

        self._timer = QTimer()
        self._timer.timeout.connect(self._esp32_io)
        self._start_timer()

    def _init_settings_panel(self):
        '''
        Initializes the settings values.
        If the ESP if running, read the current parameters
        and set them in the Setting panel.
        If the ESP is not running, don't do anything here,
        and leave the default behaviour.
        '''

        if self._run == self.DONOT_RUN:
            # If the ESP is NOT running, set the YAML parameters
            # in the settings panels, and also send those
            # values to the ESP
            self._settings.load_presets()
            self._settings.send_values_to_hardware()
        else:
            # If the ESP is running, read the current
            # parameters from the ESP and set those
            # values to the settings panels
            for param, esp_name in self._config['esp_settable_param'].items():
                value = float(self._esp32.get(esp_name))
                print('Reading Settings parameters from ESP:', param, value)
                if esp_name == 'ratio':
                    converted_value = (value**-1 - 1)**-1
                    self._settings.update_spinbox_value(param, converted_value)
                else:
                    self._settings.update_spinbox_value(param, value)

    def _esp32_io(self):
        '''
        The callback function called every time the
        QTimer times out.
        '''

        try:
            self._call_esp32()
        except ESP32Exception as error:
            self._raise_comm_error(str(error))

    def _call_esp32(self):
        '''
        Gets the run, mode and backup vairables
        from the ESP, and passes them to the
        StartStopWorker class.
        '''

        run = int(self._esp32.get('run'))
        mode = int(self._esp32.get('mode'))
        backup = int(self._esp32.get('backup'))

        if backup:
            if not self._backup_ackowledged:
                self._open_backup_warning()
                # TODO: Cannot have pop up window
        else:
            self._backup_ackowledged = False

        if run == self._run and mode == self._mode:
            return

        self.set_run(run)
        self.set_mode(mode)

    def _open_backup_warning(self):
        '''
        Opens a warning message if the ventilator
        changed from PSV to PCV ventilation.
        '''
        msg = MessageBox()

        callbacks = {msg.Ok: self._acknowlege_backup}

        msg.warning("CHANGE OF MODE",
                    "The ventilator changed from PSV to PCV mode.",
                    "The microcontroller raised the backup flag.",
                    "",
                    callbacks)()

    def _acknowlege_backup(self):
        '''
        Sets _backup_ackowledged to True
        '''
        self._backup_ackowledged = True

    def _raise_comm_error(self, message):
        """
        Opens an error window with 'message'.

        arguments:
        - message: the message to show in the error window
        """

        # TODO: find a good exit point
        msg = MessageBox()
        msg.critical('COMMUNICATION ERROR',
                     'Error communicating with the hardware', message,
                     '** COMMUNICATION ERROR **', {msg.Ok: lambda:
                                                           sys.exit(-1)})()

    def is_running(self):
        """
        A simple function that returns true if running.
        """
        return self._run == self.DO_RUN

    def mode(self):
        """
        Return the current mode
        """

        return self._mode

    def toggle_mode(self):
        """
        Toggles between desired mode (MODE_PCV or MODE_PSV).
        """
        if self._mode == self.MODE_PCV:
            result = self._esp32.set('mode', self.MODE_PSV)

            if result:
                self._mode_text = "PSV"
                self._button_mode.setText("Set\nPCV")
                self.update_startstop_text()
                self._mode = self.MODE_PSV
            else:
                self._raise_comm_error('Cannot set PSV mode.')

        else:
            result = self._esp32.set('mode', self.MODE_PCV)

            if result:
                self._mode_text = "PCV"
                self._button_mode.setText("Set\nPSV")
                self.update_startstop_text()
                self._mode = self.MODE_PCV
            else:
                self._raise_comm_error('Cannot set PCV mode.')

    def update_startstop_text(self):
        '''
        Updates the text in the Start/Stop button
        '''
        if self._run == self.DONOT_RUN:
            self._button_startstop.setText("Start\n" + self._mode_text)
            self._toolbar.set_stopped(self._mode_text)
        else:
            self._button_startstop.setText("Stop\n" + self._mode_text)
            self._toolbar.set_running(self._mode_text)

    def start_button_pressed(self):
        '''
        Callback for when the Start button is pressed
        '''
        # Send signal to ESP to start running
        result = self._esp32.set('run', self.DO_RUN)

        if result:
            self._run = self.DO_RUN
            self.show_stop_button()
        else:
            self._raise_comm_error('Cannot start ventilator.')

    def show_stop_button(self):
        '''
        Shows the stop button
        '''
        self._button_startstop.setDisabled(True)
        self._button_mode.setDisabled(True)
        self._button_startstop.repaint()
        self._button_mode.repaint()
        self.update_startstop_text()

        self._settings.disable_special_ops_tab()

        QTimer.singleShot(self.button_timeout(), lambda: (
            self.update_startstop_text(),
            self._button_startstop.setEnabled(True),
            self._button_startstop.setStyleSheet("color: red"),
            self._toolbar.set_running(self._mode_text)))

    def stop_button_pressed(self):
        '''
        Callback for when the Stop button is pressed
        '''
        # Send signal to ESP to stop running
        result = self._esp32.set('run', self.DONOT_RUN)

        if result:
            self._run = self.DONOT_RUN
            self.show_start_button()
        else:
            self._raise_comm_error('Cannot stop ventilator.')

    def show_start_button(self):
        '''
        Shows the start button
        '''
        self._button_startstop.setEnabled(True)
        self._button_mode.setEnabled(True)

        self.update_startstop_text()
        self._button_startstop.setStyleSheet("color: black")

        self._button_startstop.repaint()
        self._button_mode.repaint()

        self._toolbar.set_stopped(self._mode_text)
        self._settings.enable_special_ops_tab()

    def confirm_start_pressed(self):
        '''
        Opens a window which asks for confirmation
        when the Start button is pressed.
        '''
        self._button_mode.setDown(False)
        current_mode = self._mode_text.upper()
        self._messagebar.get_confirmation(
            "**STARTING %s MODE**" % current_mode,
            "Are you sure you want to START %s MODE?" % current_mode,
            func_confirm=self.start_button_pressed)

    def confirm_stop_pressed(self):
        '''
        Opens a window which asks for confirmation
        when the Stop button is pressed.
        '''
        self._button_mode.setDown(False)
        current_mode = self._mode_text.upper()
        self._messagebar.get_confirmation(
            "**STOPPING %s MODE**" % current_mode,
            "Are you sure you want to STOP %s MODE?" % current_mode,
            func_confirm=self.stop_button_pressed)

    def button_timeout(self):
        '''
        Waits for some time before making
        the Stop button visible
        '''
        timeout = 1000
        # Set timeout for being able to stop this mode
        if 'start_mode_timeout' in self._config:
            timeout = self._config['start_mode_timeout']
            # set maximum timeout
            if timeout > 3000:
                timeout = 3000
        return timeout

    def toggle_start_stop(self):
        """
        Toggles between desired run state (DO_RUN or DONOT_RUN).
        """

        if self._run == self.DONOT_RUN:
            self.confirm_start_pressed()
        else:
            self.confirm_stop_pressed()

    def set_run(self, run):
        '''
        Sets the run variable directly.
        Usually called at start up, when reading
        the run value from the ESP.

        arguments:
        - run: the run value (0 or 1) to set
        '''
        if self._run == run:
            return

        self._run = run

        if run == self.DONOT_RUN:
            # TODO: this should be an alarm
            msg = MessageBox()
            msg.critical('STOPPING VENTILATION',
                         'The hardware has stopped the ventilation.',
                         'The microcontroller has stopped the ventilation by sending run = ' +
                         str(run),
                         'The microcontroller has stopped the ventilation by sending run = ' +
                         str(run),
                         {msg.Ok: self.show_start_button})()

        else:
            self.show_stop_button()

    def _start_timer(self):
        '''
        Starts the QTimer.
        '''
        self._timer.start(self._config["status_sampling_interval"] * 1000)

    def _stop_timer(self):
        '''
        Stops the QTimer.
        '''
        self._timer.stop()

    def _restart_timer(self):
        '''
        Restarts the QTimer if the QTimer is active,
        or simply starts the QTimer
        '''
        if self._timer.isActive():
            self._stop_timer()

        self._start_timer()

    def set_mode(self, mode):
        '''
        Sets the mode variable directly.
        Usually called at start up, when reading
        the mode value from the ESP.

        arguments:
        - mode: the mode value (0 or 1) to set
        '''
        if self._mode != mode:
            self.toggle_mode()
