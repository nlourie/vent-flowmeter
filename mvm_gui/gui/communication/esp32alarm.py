"""
This module handles ESP32 alarms.
"""

class ESP32BaseAlarm():
    '''
    The base ESP Alarm Class
    '''

    alarm_to_string = {
        0: "Alarm name",
    }

    def __init__(self, number):
        '''
        Constructor

        arguments:
        - the number obtained from the ESP
        '''
        self.number = number
        self.unpack()

    def __bool__(self):
        return self.number != 0

    def __str__(self):
        return 'All alarms: ' + ' - '.join(self.strerror_all())

    def get_alarm_codes(self):
        """
        Gets the alarm codes.
        """

        return self.alarms

    def unpack(self):
        '''
        Unpacks the number obtained from the ESP
        '''

        self.alarms = list(x for x in [self.number & (1 << test) for test in range(32)] if x)

        print('Found alarms', self.alarms)

        return self.alarms

    def strerror(self, n_error):
        '''
        Returns a string with the error
        specified by n

        arguments:
        - n: the error number (unpacked)
        '''

        if n_error in self.alarm_to_string:
            return self.alarm_to_string[n_error]
        return 'Unknown error'

    def strerror_all(self, append_err_no=False):
        '''
        Same as strerror, but returns a list
        in case of multiple errors

        arguments:
        - append_err_no: if True, also adds the err number
        '''

        str_error = []
        for n_error in self.alarms:

            s_error = self.strerror(n_error)

            if append_err_no:
                s_error += ' (code: '
                s_error += str(n_error)
                s_error += ')'

            str_error.append(s_error)

        return str_error


class ESP32Alarm(ESP32BaseAlarm):
    """
    An ESP32 class for handling alarms, built on ESP32BaseAlarm
    """
    def __init__(self, number):
        if number & (1 << 29):
            number = number ^ (1 << 29)
        super(ESP32Alarm, self).__init__(number)

    alarm_to_string = {
        # From the ESP
        1 << 0: "Gas pressure too low",
        1 << 1: "Gas pressure too high",
        1 << 2: "Internal pressure too low (internal leakage)",
        1 << 3: "Internal pressure too high",
        1 << 4: "Out of battery power",
        1 << 5: "Leakage in gas circuit",
        1 << 6: "Obstruction in hydraulic circuit",
        1 << 7: "Partial obstruction in hydraulic circuit",
        # From the GUI
        1 << 8: "Pressure to patient mouth too low",
        1 << 9: "Pressure to patient mouth too high",
        1 << 10: "Inpiratory flux too low",
        1 << 11: "Inpiratory flux too high",
        1 << 12: "Expiratory flux too low",
        1 << 13: "Expiratory flux too high",
        1 << 14: "Tidal volume too low",
        1 << 15: "Tidal volume too high",
        1 << 16: "O2 too low",
        1 << 17: "O2 too high",
        1 << 18: "PEEP too low",
        1 << 19: "PEEP too high",
        1 << 20: "Respiratory rate too low",
        1 << 21: "Respiratory rate too high",

        # from the ESP
        1 << 22: "Apnea alarm",
        1 << 29: "GUI alarm raised",
        1 << 30: "GUI watchdog not reset",
        1 << 31: "System failure",
    }


class ESP32Warning(ESP32BaseAlarm):
    """
    ESP32Warning class
    """
    alarm_to_string = {
        # From the ESP
        1 << 0: "Oxygen sensor requires calibration",
        1 << 1: "Disconnected from power outlet",
    }
