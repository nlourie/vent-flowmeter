#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 08:38:28 2020

pyqt realtime plot tutorial

source: https://www.learnpyqt.com/courses/graphics-plotting/plotting-pyqtgraph/


@author: nlourie
"""

from PyQt5 import QtWidgets, QtCore,uic
from pyqtgraph import PlotWidget, plot,QtGui
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
from datetime import datetime
import numpy as np
from scipy import signal
import board
import busio
import adafruit_lps35hw
import time
from scipy import interpolate

import adafruit_ads1x15.ads1115 as ADS

from adafruit_ads1x15.analog_in import AnalogIn

# Initialize the i2c bus
i2c = busio.I2C(board.SCL, board.SDA)


# Initialize the ADC
ads = ADS.ADS1115(i2c)
honeywell = AnalogIn(ads,ADS.P3)
# Read this in by calling honeywell.voltage

#import monitor_utils as mu

#Honeywell Volts to FLow calibration

f = [0.,0.,25.,50.,75.,100.,150.,200.]
v = [0.,1,2.99,3.82,4.3,4.58,4.86,5.0]
honeywell_v2f = interpolate.interp1d(v,f,kind = 'cubic')




# Using the adafruit_lps35hw class to read in the pressure sensor
    # note the address must be in decimal.
    # allowed addresses are: 
        # 92 (0x5c - if you put jumper from SDO to Gnd)
        # 93 (0x5d - default)
        
p2 = adafruit_lps35hw.LPS35HW(i2c, address = 92)
p1 = adafruit_lps35hw.LPS35HW(i2c, address = 93)

p1.data_rate = adafruit_lps35hw.DataRate.RATE_75_HZ
p2.data_rate = adafruit_lps35hw.DataRate.RATE_75_HZ
mbar2cmh20 = 1.01972


# Now read out the pressure difference between the sensors
print('p1_0 = ',p1.pressure,' mbar')
print('p1_0 = ',p1.pressure*mbar2cmh20,' cmH20')
print('p2_0 = ',p2.pressure,' mbar')
print('p2_0 = ',p2.pressure*mbar2cmh20,' cmH20')

print('')
print('Now zero the pressure:')
# Not sure why sometimes I have to do this twice??
p1.zero_pressure()
p1.zero_pressure()
time.sleep(1)
p2.zero_pressure()
p2.zero_pressure()
time.sleep(1)
print('p1_0 = ',p1.pressure,' mbar')
print('p1_0 = ',p1.pressure*mbar2cmh20,' cmH20')
print('p2_0 = ',p2.pressure,' mbar')
print('p2_0 = ',p2.pressure*mbar2cmh20,' cmH20')

print()

def breath_detect_coarse(flow,fs,plotflag = False):
    """
    %% This function detects peaks of flow signal
    
    % Inputs:
    %           flow:       flow signal
    %           fs:         sampling frequency
    %           plotflag:   set to 1 to plot
    
    % Output:
    %           peak (location, amplitude)
    
    % Written by: Chinh Nguyen, PhD
    % Email: c.nguyen@neura.edu.au
    
    % Updated on: 12 Nov 2015.
    % Ver: 1.0
    
    # Converted to python by: Nate Lourie, PhD
    # Email: nlourie@mit.edu
    # Updated on: April, 2020
    
    """
    # detect peaks of flow signal
    minpeakwidth = fs*0.3
    peakdistance = fs*1.5
    #print('peakdistance = ',peakdistance)
    minPeak = 0.05 # flow threshold = 0.05 (L/s)
    minpeakprominence = 0.05
    
    peak_index, _  = signal.find_peaks(flow, 
                                    height = minPeak,
                                    distance = peakdistance,
                                    prominence = minpeakprominence,
                                    width = minpeakwidth)
    """
    valley_index, _  = signal.find_peaks(-1*flow, 
                                    height = minPeak,
                                    distance = peakdistance,
                                    prominence = minpeakprominence,
                                    width = minpeakwidth)
    """
    #print('found peaks at index = ',peak_index)
    return peak_index


class MainWindow(QtWidgets.QMainWindow):
    
    # All we need for the calibration is two windows.
    # Plot 1 = deltaP (cm H20)
    # Plot 2 = honeywell Flow (L/s)

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Standalone Respiratory Monitor")
        
        self.graph1 = pg.PlotWidget()
        self.graph2 = pg.PlotWidget()
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.graph1)
        layout.addWidget(self.graph2)
        
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        
        # make the window with a graph widget
        #self.graph1 = pg.PlotWidget()
        self.setCentralWidget(widget)
        
        # set the plot properties
        self.graph1.setBackground('k')
        self.graph2.setBackground('k')
        self.graph1.showGrid(x = True, y = True)
        self.graph2.showGrid(x = True, y = True)


        
        # Set the label properties with valid CSS commands -- https://groups.google.com/forum/#!topic/pyqtgraph/jS1Ju8R6PXk
        labelStyle = {'color': '#FFF', 'font-size': '12pt'}
        self.graph1.setLabel('left','dP','cmH20',**labelStyle)
        self.graph2.setLabel('left','Flow','L/s',**labelStyle)
        self.graph2.setLabel('bottom', 'Time', 's', **labelStyle)

        # change the plot range
        #self.graph1.setYRange(-30,30,padding = 0.1)
        #self.graph2.setYRange(-2,2,padding = 0.1)

                                             
        self.x  = [0]
        self.t = [datetime.utcnow().timestamp()]
        self.dt = [0]

        self.x  = [0]
        self.dt = [0]
        self.dp = [(p1.pressure - p2.pressure)*mbar2cmh20]
        self.p1 = [(p1.pressure)*mbar2cmh20]
        self.p2 = [(p2.pressure)*mbar2cmh20]
        self.flow = [honeywell_v2f(honeywell.voltage)]
        
        #print('P1 = ',p1.pressure,' cmH20')
        #print('P2 = ',p2.pressure,' cmH20')


        # plot data: x, y values
        # make a QPen object to hold the marker properties
        pen = pg.mkPen(color = 'y',width = 1)
        pen2 = pg.mkPen(color = 'b',width = 2)
        #self.data_line11 = self.graph0.plot(self.dt,self.p1,pen = pen)
        #self.data_line12 = self.graph0.plot(self.dt,self.p2,pen = pen2)
        self.data_line1 = self.graph1.plot(self.dt,self.dp,pen = pen2)
        self.data_line2 = self.graph2.plot(self.dt, self.flow,pen = pen)
        
        # graph2
        
        #self.data_line21 = self.graph2.plot(self.dt,self.flow,pen = pen)
        #self.data_line22 = self.graph2.plot(self.dt,self.flow,pen = pen)
        # graph3
        
        
        #self.data_line3 = self.graph3.plot(self.dt,self.vol,pen = pen)

        self.calibrating = False

        
        """
        # Slower timer
        self.t_cal = 100
        self.cal_timer = QtCore.QTimer()
        self.cal_timer.setInterval(self.t_cal)
        self.cal_timer.timeout.connect(self.update_cal)
        self.cal_timer.start()
        """
        
        
        # Stuff with the timer
        self.t_update = 10 #update time of timer in ms
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.t_update)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()
        
        
        self.drift_model = [0,datetime.utcnow().timestamp()/1000*self.t_update]
        self.i_valleys = []
        self.time_to_show = 30 #s
        
         


    def update_plot_data(self):
        # This is what happens every timer loop
        
        if self.dt[-1] >= self.time_to_show:
            self.x = self.x[1:] # Remove the first element
            #self.y = self.y[1:] # remove the first element
            self.dp = self.dp[1:]
            self.t = self.t[1:] # remove the first element
            self.dt= self.dt[1:]
            self.p1 = self.p1[1:]
            self.p2 = self.p2[1:]
            self.flow = self.flow[1:]
        
        self.x.append(self.x[-1] + 1) # add a new value 1 higher than the last
        self.t.append(datetime.utcnow().timestamp())
        self.dt = [(ti - self.t[0]) for ti in self.t]
        dp_cmh20 = ((p1.pressure - p2.pressure))*mbar2cmh20
        self.dp.append(dp_cmh20)
        self.flow.append(honeywell_v2f(honeywell.voltage))
        
        self.p1.append(p1.pressure*mbar2cmh20)
        self.p2.append(p2.pressure*mbar2cmh20)

        self.data_line1.setData(self.dt,self.dp)
        self.data_line2.setData(self.dt,self.flow)


        




def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

