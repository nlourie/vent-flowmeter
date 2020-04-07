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

i2c = busio.I2C(board.SCL,board.SDA)

import adafruit_ads1x15.ads1115 as ADS

from adafruit_ads1x15.analog_in import AnalogIn

ads = ADS.ADS1115(i2c)

chan = AnalogIn(ads,ADS.P3)

#Honeywell Volts to FLow calibration

f = [0.,0.,25.,50.,75.,100.,150.,200.]
v = [0.,1,2.99,3.82,4.3,4.58,4.86,5.0]
honeywell_v2f = interp1d(v,f,kind = 'cubic')



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
        self.graphWidget.setLabel('left', 'Flow (L/m)',**labelStyle)
        
        # change the plot range
        #self.graphWidget.setXRange(5,10,padding = 0.1)
        #self.graphWidget.setYRange(30,40,padding = 0.1)
                                             
        self.x  = [0]
        self.t = [datetime.utcnow()]
        self.dt = [0]
        self.y = [honeywell_v2f(chan.voltage)]

        # plot data: x, y values
        # make a QPen object to hold the marker properties
        pen = pg.mkPen(color = 'y',width = 1)
        self.data_line = self.graphWidget.plot(self.t, self.y,pen = pen)
        
        self.t_update = 10 #update time of timer in ms
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.t_update)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()
        
    def update_plot_data(self):
        # This is what happens every timer loop
        v = chan.voltage
        Npts_to_show = 1000
        if len(self.x) >= Npts_to_show:
            self.x = self.x[1:] # Remove the first element
            self.y = self.y[1:] # remove the first element
            self.t = self.t[1:] # remove the first element
            self.dt= self.dt[1:]
        self.x.append(self.x[-1] + 1) # add a new value 1 higher than the last
        self.t.append(datetime.utcnow())
        self.dt = [float((ti - self.t[0]).total_seconds()) for ti in self.t]
        self.y.append( honeywell_v2f(v) ) # add a new random value
        
        self.data_line.setData(self.t,self.y) #update the data
        
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

