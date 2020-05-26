#!/usr/bin/env python3
'''
Runs the MVM GUI
'''

import sys
import os
import os.path
from PyQt5 import QtCore, QtWidgets

import yaml

from mainwindow import MainWindow
from communication.esp32serial import ESP32Serial, ESP32Exception
from communication.fake_esp32serial import FakeESP32Serial
from messagebox import MessageBox


def connect_esp32(config):
    """
    Establish a serial connection with the ESP32.

    arguments:
    - config: a dictionary like representing the program configuration.

    returns: a valid ESP32Serial object if connection has been
    established, a FakeESP32Serial object if has been requested to run the
    software mockup, 'None' on error.
    """

    try:
        if 'fakeESP32' in sys.argv:
            print('******* Simulating communication with ESP32')
            err_msg = "Cannot setup FakeESP32Serial"
            esp32 = FakeESP32Serial(config)
            esp32.set("wdenable", 1)
        else:
            err_msg = "Cannot communicate with port %s" % config['port']
            esp32 = ESP32Serial(config)
            esp32.set("wdenable", 1)
    except ESP32Exception as error:
        msg = MessageBox()
        answer = msg.critical("Do you want to retry?",
                              "Severe hardware communication error",
                              str(error) + err_msg, "Communication error",
                              {msg.Retry: lambda: connect_esp32(config),
                               msg.Abort: lambda: None})
        return answer()

    return esp32


def main():
    """
    Main function.
    """

    base_dir = os.path.dirname(__file__)
    settings_file = os.path.join(base_dir, 'default_settings.yaml')

    with open(settings_file) as fsettings:
        config = yaml.load(fsettings, Loader=yaml.FullLoader)
    print('Config:', yaml.dump(config), sep='\n')

    app = QtWidgets.QApplication(sys.argv)

    esp32 = connect_esp32(config)

    if esp32 is None:
        sys.exit(-1)

    watchdog = QtCore.QTimer()
    watchdog.timeout.connect(esp32.set_watchdog)
    watchdog.start(config["wdinterval"] * 1000)

    window = MainWindow(config, esp32)
    window.show()
    app.exec_()
    esp32.set("wdenable", 0)


if __name__ == "__main__":
    main()
