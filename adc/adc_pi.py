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
import matplotlib.animation as animation
from datetime import datetime
import numpy as np



i2c = busio.I2C(board.SCL,board.SDA)

import adafruit_ads1x15.ads1115 as ADS

from adafruit_ads1x15.analog_in import AnalogIn

ads = ADS.ADS1115(i2c)

chan = AnalogIn(ads,ADS.P3)


xs = []
ys = []
fig = plt.figure()
ax = fig.add_subplot(111)
i = 0

dt = 10 # ms
T = 10 # seconds

Nmax = np.int(T*100/dt)

def animate(i,xs,ys):
    v = chan.voltage
    t = datetime.utcnow()

    xs.append(t)
    ys.append(v)
    
    # limit the number of items in the vectors
    xs = xs[-Nmax:]
    ys = ys[-Nmax:]

    # draw x and y lists
    ax.clear()
    ax.plot(xs,ys)


# set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig,animate,fargs = (xs,ys),interval = dt)
plt.show()

"""
while True:
    print('loop = ',i, chan.voltage)
    index.append(i)
    v.append(chan.voltage)
    ax.plot(index,v)
    fig.canvas.draw()
    #ax.set_xlim(left = max(0,i-50),right = i+50)
    
    
    
    time.sleep(0.1)
    i+=1
"""    
