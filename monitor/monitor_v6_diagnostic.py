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
#import monitor_utils as mu

# Initialize the i2c bus
i2c = busio.I2C(board.SCL, board.SDA)

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
    print('found peaks at index = ',peak_index)
    return peak_index


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Standalone Respiratory Monitor")
        
        self.graph0 = pg.PlotWidget()
        self.graph1 = pg.PlotWidget()
        self.graph2 = pg.PlotWidget()
        self.graph3 = pg.PlotWidget()
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.graph0)
        layout.addWidget(self.graph1)
        layout.addWidget(self.graph2)
        layout.addWidget(self.graph3)
        
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        
        # make the window with a graph widget
        #self.graph1 = pg.PlotWidget()
        self.setCentralWidget(widget)
        
        # set the plot properties
        self.graph1.setBackground('k')
        self.graph0.showGrid(x = True, y = True)
        self.graph1.showGrid(x=True,y=True)
        self.graph2.showGrid(x = True, y = True)
        self.graph3.showGrid(x = True, y = True)

        
        # Set the label properties with valid CSS commands -- https://groups.google.com/forum/#!topic/pyqtgraph/jS1Ju8R6PXk
        labelStyle = {'color': '#FFF', 'font-size': '12pt'}
        self.graph0.setLabel('left','P','cmH20',**labelStyle)
        self.graph1.setLabel('left','Flow','L/s',**labelStyle)
        self.graph3.setLabel('bottom', 'Time', 's', **labelStyle)
        #self.graph2.setLabel('left', 'V raw','L',**labelStyle)
        self.graph3.setLabel('left','V corr','L',**labelStyle)

        # change the plot range
        #self.graph0.setYRange(-30,30,padding = 0.1)
        #self.graph1.setYRange(-2,2,padding = 0.1)
        #self.graph3.setYRange(-0.5,1.5,padding = 0.1)
        #self.graph3.setYRange(200,200,padding = 0.1)
                                             
        self.x  = [0]
        self.t = [datetime.utcnow().timestamp()]
        self.dt = [0]

        self.x  = [0]
        self.dt = [0]
        #self.y = [honeywell_v2f(chan.voltage)]
        self.dp = [(p1.pressure - p2.pressure)*mbar2cmh20]
        self.p1 = [(p1.pressure)*mbar2cmh20]
        self.p2 = [(p2.pressure)*mbar2cmh20]
        self.flow = [0]
        self.vol = [0]
        
        print('P1 = ',p1.pressure,' cmH20')
        print('P2 = ',p2.pressure,' cmH20')


        # plot data: x, y values
        # make a QPen object to hold the marker properties
        pen = pg.mkPen(color = 'y',width = 1)
        pen2 = pg.mkPen(color = 'b',width = 2)
        self.data_line01 = self.graph0.plot(self.dt,self.p1,pen = pen)
        self.data_line02 = self.graph0.plot(self.dt,self.p2,pen = pen2)
        self.data_line1 = self.graph1.plot(self.dt, self.flow,pen = pen)
        
        # graph2
        
        self.data_line21 = self.graph2.plot(self.dt,self.flow,pen = pen)
        self.data_line22 = self.graph2.plot(self.dt,self.flow,pen = pen)
        # graph3
        
        
        self.data_line3 = self.graph3.plot(self.dt,self.vol,pen = pen)

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
            self.vol = self.vol[1:]
            self.flow = self.flow[1:]
        
        self.x.append(self.x[-1] + 1) # add a new value 1 higher than the last
        self.t.append(datetime.utcnow().timestamp())
        self.dt = [(ti - self.t[0]) for ti in self.t]
        dp_cmh20 = ((p1.pressure - p2.pressure))*mbar2cmh20
        self.dp.append(dp_cmh20)
        self.flow.append(dp_cmh20)
        
        self.p1.append(p1.pressure*mbar2cmh20)
        self.p2.append(p2.pressure*mbar2cmh20)
        # remove any linear trend in the volume data since it's just nonsense.
        # THis should zero it out okay if there's no noticeable "dips"
        self.vol = signal.detrend(np.cumsum(self.flow))
        
        self.fs = 1/(self.t[-1] - self.t[-2])
        print('Sample Freq = ',self.fs)

        negative_mean_subtracted_volume = [-1*(v-np.mean(self.vol)) for v in self.vol]
        i_valleys = breath_detect_coarse(negative_mean_subtracted_volume,fs = self.fs,plotflag = False)
        self.i_valleys = i_valleys
            
            #print('i_valleys = ',self.i_valleys)
            #print('datatype of i_valleys = ',type(self.i_valleys))

        
        if len(self.i_valleys) >= 2:
            t = np.array(self.t)
            vol = np.array(self.vol)
            dt = np.array(self.dt)
            print('found peaks at dt = ',dt[self.i_valleys])
            #self.drift_model = np.polyfit(t[self.i_valleys],vol[self.i_valleys],1)
            #self.v_drift = np.polyval(self.drift_model,t)
            #self.vol_corr = vol - self.v_drift
            #self.data_line22.setData(self.dt,self.v_drift)
            
            self.drift_model = interpolate.interp1d(t[i_valleys],vol[i_valleys],kind = 'linear')
            v_drift_within_spline = self.drift_model(t[i_valleys[0]:i_valleys[-1]])
            v_drift = np.zeros(len(t))
            v_drift[0:self.i_valleys[1]] = np.polyval(np.polyfit(t[i_valleys[0:1]],vol[self.i_valleys[0:1]],1),t[0:self.i_valleys[1]],)
            v_drift[self.i_valleys[0]:self.i_valleys[-1]] = v_drift_within_spline
            v_drift[self.i_valleys[-1]:] = np.polyval(np.polyfit(t[self.i_valleys[-2:]],vol[self.i_valleys[-2:]],1),t[self.i_valleys[-1]:])
            self.v_drift = v_drift
            self.vol_corr = vol - v_drift
            self.data_line22.setData(self.dt,self.v_drift)
            
        else:
            self.vol_corr = self.vol
        self.data_line01.setData(self.dt,self.p1)
        self.data_line02.setData(self.dt,self.p2)
        self.data_line1.setData(self.dt,self.flow) #update the data

        self.data_line21.setData(self.dt,self.vol)
        self.data_line3.setData(self.dt,self.vol_corr)
        


    """        
    def update_cal(self)   : 
        print ('len dt = ',len(self.dt))
        if len(self.dt) > 50:
            
            # try to run the monitor utils functions
            fs = 1000/self.t_update
            i_peaks,i_valleys,i_infl_points,vol_last_peak,flow,self.vol_corr,self.vol_offset,time,vol,drift_model = mu.get_processed_flow(np.array(self.t),np.array(self.y),fs,SmoothingParam = 0,smoothflag=True,plotflag = False)
            if len(i_peaks) > 2:
                self.drift_model = drift_model
                print('updating calibration')
                self.calibrating = True

        self.data_line2.setData(self.dt,vol)
        self.data_line5.setData(self.dt,np.polyval(self.drift_model,time))
        self.data_line3.setData(self.dt,vol - np.polyval(self.drift_model,time))
        print('drift model = ',self.drift_model)
    """


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

