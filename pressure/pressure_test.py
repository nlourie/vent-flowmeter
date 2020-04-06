#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 11:53:17 2020

Sample script to read the LPS35HW pressure sensor from the adafruit
prototype board with a rasperry pi.



@author: nlourie
"""

import time
import board
import busio
import adafruit_lps35hw
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


# Initialize the i2c bus
i2c = busio.I2C(board.SCL, board.SDA)

# Using the adafruit_lps35hw class to read in the pressure sensor
    # note the address must be in decimal.
    # allowed addresses are: 
        # 92 (0x5c - if you put jumper from SDO to Gnd)
        # 93 (0x5d - default)
        
p1 = adafruit_lps35hw.LPS35HW(i2c, address = 92)
p2 = adafruit_lps35hw.LPS35HW(i2c, address = 93)

p1.data_rate = adafruit_lps35hw.DataRate.RATE_75_HZ
p2.data_rate = adafruit_lps35hw.DataRate.RATE_75_HZ


    



# Now read out the pressure difference between the sensors

# First: get the dp for zero flow from startup
dp_startup = p1.pressure - p2.pressure


t = []
p_cmH20    = [] # mouthpiece pressure, ie p1
dp_cmH20   = [] # pressure difference -- p1 = exhalation, p1=  inspiration

# set up the realtime plot
fig = plt.figure()
p_ax = fig.add_subplot(111)




# Define the loop
dt = 1000/75 #ms 
t_total = 60 #seconds
Npts = int(t_total*1000/dt)
mbar2cmh20 = 0.980665
i = 0

# This is a simple thing to check that stuff reads out
def animate(i,t,p_cmH20,dp_cmH20):
    try:
        pcur_cmH20 = p1.pressure*mbar2cmh20
        dpcur_cmH20 = (p1.pressure - p2.pressure)*mbar2cmh20
        
        t.append(datetime.utcnow())
        p_cmH20.append(pcur_cmH20)
        dp_cmH20.append(dpcur_cmH20)

        
        # limit the number of items in the vectors
        t  = t[-Npts:]
        p_cmH20  = p_cmH20[-Npts:]
        dp_cmH20 = dp_cmH20[-Npts:]
        dp_cmH20_cal = dp_cmH20 - dp_startup*mbar2cmh20
              
        """
        print('Reading P1:')
        print(f'   P1 = {p1.pressure} hPa')
        print(f'   T1 = {p1.temperature} C')
        
        print('Reading P2:')
        print(f'   P2 = {p2.pressure} hPa')
        print(f'   T2 = {p2.temperature} C')
        
        print(f'dP (cal) = {dp_cmH20_cal[-1]} cm H20')
        time.sleep(dt/1000)
        """
        # draw x and y lists
        p_ax.clear()
        p_ax.plot(t,dp_cmH20_cal)
        i+=1
      
    except KeyboardInterrupt:
        pass

# set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig,animate,fargs = (t,p_cmH20,dp_cmH20),interval = dt)
plt.show()
    
    
    
    
    
    
    
    
    