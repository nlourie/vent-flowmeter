#!/usr/bin/env python3
"""
Data management and dispatching back and forth the ESP32
"""

import sys
from PyQt5.QtCore import QTimer
from messagebox import MessageBox
from communication import ESP32Exception

class DataHandler():
    '''
    This class takes care of starting a new QTimer which
    is entirey dedicated to read data from the ESP32.
    '''

    def __init__(self, config, esp32, data_filler, gui_alarm):
        '''
        Initializes this class by creating a new QTimer

        arguments:
        - config: the config dictionary
        - esp32: the esp32serial instance
        - data_filler: the instance to the DataFiller class
        - gui_alarm: the alarm class
        '''

        self._config = config
        self._esp32 = esp32
        self._data_f = data_filler
        self._gui_alarm = gui_alarm

        self._timer = QTimer()
        self._timer.timeout.connect(self.esp32_io)
        self._start_timer()

    def __del__(self):
        '''
        Destructor
        Stops the timer
        '''

        self._stop_timer()

    def esp32_io(self):
        '''
        This is the main function that runs every time a QTimer times out.
        It runs the get_all to get the data from the ESP.
        '''

        try:
            # Get all params from ESP
            current_values = self._esp32.get_all()

            # Converting from str to float
            for name, value in current_values.items():
                current_values[name] = float(value)

            current_values = self._convert_values(current_values)

            self._gui_alarm.set_data(current_values)

            # finally, send values to the DataFiller
            for name, value in current_values.items():
                self._data_f.add_data_point(name, value)

        except ESP32Exception as error:
            self.open_comm_error(str(error))

    def _convert_values(self, values):
        '''
        '''

        conv = self._config['conversions']
        return {k: v * conv.get(k, 1.) for (k, v) in values.items()}
        # for n, v in values.items():
        #     values[n] = v * conv['pressure'] if 'pressure' in conv else v

    def open_comm_error(self, error):
        '''
        Opens a message window if there is a communication error.
        '''
        msg = MessageBox()

        # TODO: find a good exit point
        callbacks = {msg.Retry: self._restart_timer,
                     msg.Abort: lambda: sys.exit(-1)}

        msg.critical("COMMUNICATION ERROR",
                     "CANNOT COMMUNICATE WITH THE HARDWARE",
                     "Check cable connections then click retry.\n" + error,
                     "COMMUNICATION ERROR",
                     callbacks)()

    def _start_timer(self):
        '''
        Starts the QTimer.
        '''
        self._timer.start(self._config["sampling_interval"] * 1000)

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

    def set_data(self, param, value):
        '''
        Sets data to the ESP
        '''

        result = self._esp32.set(param, value)

        return result == self._config['return_success_code']
