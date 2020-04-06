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



# Initialize the i2c bus
i2c = busio.I2C(board.SCL, board.SDA)

# Using the adafruit_lps35hw class to read in the pressure sensor
    # note the address must be in decimal.
    # allowed addresses are: 
        # 92 (0x5c - if you put jumper from SDO to Gnd)
        # 93 (0x5d - default)
        
p1 = adafruit_lps35hw.LPS35HW(i2c, address = 92)
p2 = adafruit_lps35hw.LPS35HW(i2c, address = 93)


# This is a simple thing to check that stuff reads out
while True:
    try:
        """
        print('Reading P1:')
        print(f'   P1 = {p1.pressure} hPa')
        print(f'   T1 = {p1.temperature} C')
        
        print('Reading P2:')
        print(f'   P2 = {p2.pressure} hPa')
        print(f'   T2 = {p2.temperature} C')
        """
        print(fdp = {p1.pressure - p2.pressure}')
        time.sleep(0.1)
    
    except KeyboardInterrupt:
        break
    



# Now read out the pressure difference between the sensors

# First: zero out the pressure sensors to the current ambient pressure
#p1.zero_pressure()
#p2.zero_pressure()

time = []
p    = [] # mouthpiece pressure, ie p1
dp   = [] # pressure difference -- p1 = exhalation, p1=  inspiration

# set up the realtime plot


