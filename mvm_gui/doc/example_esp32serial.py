"""
Example script on how to use the esp32serial library.

For the documentation. open a python and type:
>>> import esp32serial
>>> help(esp32serial.ESP32Serial)
"""

# import the library
import esp32serial

# create a connection
esp32 = esp32serial.ESP32Serial("/dev/ttyACM0")

# get an observable or parameter, converting it inline to float
pressure = float(esp32.get("pressure"))

# set a parameter to a value
result = esp32.set("intparameter", 3)

# this is just an example on what to expect and a possible reaction
if result != 'OK':
    raise Exception("setting intparameter failed")
