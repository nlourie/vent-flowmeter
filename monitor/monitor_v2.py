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
from random import randint
import board
import busio
from datetime import datetime
from scipy.interpolate import interp1d
import adafruit_lps35hw

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
mbar2cmh20 = 0.980665


# Now read out the pressure difference between the sensors
dp0 = p1.pressure - p2.pressure



"""
i2c = busio.I2C(board.SCL,board.SDA)

import adafruit_ads1x15.ads1115 as ADS

from adafruit_ads1x15.analog_in import AnalogIn

ads = ADS.ADS1115(i2c)

chan = AnalogIn(ads,ADS.P3)

#Honeywell Volts to FLow calibration

f = [0.,0.,25.,50.,75.,100.,150.,200.]
v = [0.,1,2.99,3.82,4.3,4.58,4.86,5.0]
honeywell_v2f = interp1d(v,f,kind = 'cubic')
"""



class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        # make the window with a graph widget
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        
        # set the plot properties
        self.graphWidget.setBackground('k')
        self.graphWidget.showGrid(x=True,y=True)
        
        # Set the label properties with valid CSS commands -- https://groups.google.com/forum/#!topic/pyqtgraph/jS1Ju8R6PXk
        labelStyle = {'color': '#FFF', 'font-size': '24pt'}
        self.graphWidget.setLabel('bottom', 'Time', 's', **labelStyle)
        self.graphWidget.setLabel('left', 'dp','cm H20',**labelStyle)
        
        # change the plot range
        #self.graphWidget.setXRange(5,10,padding = 0.1)
        #self.graphWidget.setYRange(30,40,padding = 0.1)
                                             
        self.x  = [0]
        self.t = [datetime.utcnow()]
        self.dt = [0]
        #self.y = [honeywell_v2f(chan.voltage)]
        self.dp = [((p1.pressure - p2.pressure)-dp0)*mbar2cmh20]
        self.p = [p1.pressure*mbar2cmh20]
        
        # plot data: x, y values
        # make a QPen object to hold the marker properties
        pen = pg.mkPen(color = 'y',width = 1)
        self.data_line = self.graphWidget.plot(self.dt, self.dp,pen = pen)
        
        self.t_update = 10 #update time of timer in ms
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.t_update)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()
        self.time_to_show = 60.0 #s
        
    def update_plot_data(self):
        # This is what happens every timer loop
        #v = chan.voltage
        
        if self.dt[-1] >= self.time_to_show:
            self.x = self.x[1:] # Remove the first element
            #self.y = self.y[1:] # remove the first element
            self.dp = self.dp[1:]
            self.t = self.t[1:] # remove the first element
            self.dt= self.dt[1:]
            self.p = self.p[1:]
            
        self.x.append(self.x[-1] + 1) # add a new value 1 higher than the last
        self.t.append(datetime.utcnow())
        self.dt = [float((ti - self.t[0]).total_seconds()) for ti in self.t]
        #self.y.append( honeywell_v2f(v) ) # add a new random value
        self.dp.append(((p1.pressure - p2.pressure)-dp0)*mbar2cmh20)
        self.p.append(p1.pressure*mbar2cmh20)
        
        self.data_line.setData(self.dt,self.dp) #update the data
        
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

