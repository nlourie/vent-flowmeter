#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  4 14:13:34 2020


Testing out the ADS1115 ADC with the raspberry pi



@author: nlourie
"""

import board
import busio
import time

i2c = busio.I2C(board.SCL,board.SDA)

import adafruit_ads1x15.ads1115 as ADS

from adafruit_ads1x15.analog_in import AnalogIn

ads = ADS.ADS1115(i2c)

chan = AnalogIn(ads,ADS.P3)

while True:
    print(chan.value, chan.voltage)
    time.sleep(0.5)
