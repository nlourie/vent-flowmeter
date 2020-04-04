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
import matplotlib.pyplot as plt

i2c = busio.I2C(board.SCL,board.SDA)

import adafruit_ads1x15.ads1115 as ADS

from adafruit_ads1x15.analog_in import AnalogIn

ads = ADS.ADS1115(i2c)

chan = AnalogIn(ads,ADS.P3)


v = []
index = []
fig = plt.figure()
ax = fig.add_subplot(111)

i = 0

while True:
    #print(chan.value, chan.voltage)
    index.append(i)
    v.append(chan.voltage)
    plt.plot(index,v)
    fig.canvas.draw()
    ax.set_xlim(lef = max(0,i-50),right = i+50)
    
    
    
    
    time.sleep(0.1)
    i+=1
    