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
from scipy import signal
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def zerophase_lowpass(x,lf,fs):
    # filter flow using S-G filter
    
    # filter flow
    N = 2 # the higher the sharper the peak is
    # length = 1s (cut off frequency = 0.965 Hz)
    # Refer. Schafer, 2011, What is S-G filter.
    # fc_n = (N+1)/(3.2M - 4.6) (normalized unit)
    # fc(Hz) = fc_n*fs/2;
    # N: order: M length;
    # fc=lf(Hz) -> fc_n = 2*lf/fs;
    # M = [(N+1)*fs/(2*lf)+4.6]/3.2;
    
    # l_lfilter = round(fs*lf); % the longer, the smoother
    # l_lfilter = round(fs*lf); % the longer, the smoother
    
    l_lfilter = np.int(np.round(((N+1)*fs/(2*lf)+4.6)/3.2))
    print('l_lfilter = ',l_lfilter)
    if np.mod(l_lfilter,2) == 0:
        l_lfilter = l_lfilter + 1
        #print('made odd: l_lfilter = ',l_lfilter)
    
    # filter flow signal
    x_filt = signal.savgol_filter(x,polyorder = N,window_length = l_lfilter)
    return x_filt



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

p1_startup = p1.pressure
p2_startup = p2.pressure
dp_startup = p1_startup - p2_startup




# set up the realtime plot
fig, (p_ax,f_ax,v_ax) = plt.subplots(3, 1)
p_ax.set_ylabel('Pressure (cm H20)')

f_ax.set_ylabel('Flow (au)')

v_ax.set_ylabel('Tidal Volume (au)')
v_ax.set_xlabel('Time')



# Define the loop
dt = 1000/75 #ms 
t_total = 60 #seconds
Npts = 25 #int(t_total*1000/dt)
mbar2cmh20 = 0.980665
i = 0
indx = []

t = []
p_cmH20    = [] # mouthpiece pressure, ie p1
dp_cmH20   = [] # pressure difference -- p1 = exhalation, p1=  inspiration
v = []




# This is a simple thing to check that stuff reads out
def animate(i,indx,t,p_cmH20,dp_cmH20,v):
    try:
        pcur_cmH20 = (p1.pressure-p1_startup)*mbar2cmh20
        dpcur_cmH20 = ((p1.pressure - p2.pressure)-dp_startup)*mbar2cmh20
        

        
        t.append(datetime.utcnow())
        #print('t = ',t)
        p_cmH20.append(pcur_cmH20)
        dp_cmH20.append(dpcur_cmH20)
        indx.append(i)
        
        # limit the number of items in the vectors
        t  = t[-Npts:]
        p_cmH20  = p_cmH20[-Npts:]
        dp_cmH20 = dp_cmH20[-Npts:]
        indx = indx[-Npts:] 
        # remove the drift in the flow
        filter_len_sec = 2.0 #s
        filter_len_samples = int(filter_len_sec*1000/dt)
        
        if i > Npts:
            flow_drift = zerophase_lowpass(dp_cmH20,lf=2,fs = 1.0/((t[1]-t[0]).total_seconds()))
            #print('flow_drift',flow_drift)

            v_au = np.cumsum(dp_cmH20)
        
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
        f_ax.clear()
        v_ax.clear()
        
        p_ax.plot(indx,p_cmH20)
        f_ax.plot(indx,dp_cmH20)
        if i > Npts:
            f_ax.plot(indx,flow_drift)
            v_ax.plot(indx,v_au)
        
        i+=1
        print('i = ',i)
      
    except KeyboardInterrupt:
        pass

# set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig,animate,fargs = (indx,t,p_cmH20,dp_cmH20,v),interval = dt)
plt.tight_layout()
plt.show()
    
    
    
    
    
    
    
    
    
