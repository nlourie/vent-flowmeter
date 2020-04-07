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
from random import randint
import numpy as np

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
        self.graphWidget.setLabel('bottom', 'Label Text', 'Units', **labelStyle)
        self.graphWidget.setLabel('left', 'Temperature (°C)',**labelStyle)
        
        # change the plot range
        #self.graphWidget.setXRange(5,10,padding = 0.1)
        #self.graphWidget.setYRange(30,40,padding = 0.1)
                                             
        self.x  = [0]
        self.t = [datetime.utcnow()]
        self.dt = [0]
        self.y = [randint(0,100)]

        # plot data: x, y values
        # make a QPen object to hold the marker properties
        pen = pg.mkPen(color = 'y',width = 1)
        self.data_line = self.graphWidget.plot(self.dt, self.y,pen = pen)
        
        t_update = 10 #update time of timer in ms
        self.timer = QtCore.QTimer()
        self.timer.setInterval(t_update)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()
        
    def update_plot_data(self):
        # This is what happens every timer loop
        Npts_to_show = 1000
        if len(self.x) >= Npts_to_show:
            self.x = self.x[1:] # Remove the first element
            self.y = self.y[1:] # remove the first element
            self.t = self.t[1:]
            self.dt = self.dt[1:]
            
        self.x.append(self.x[-1] + 1) # add a new value 1 higher than the last
        self.y.append( randint(0,100)) # add a new random value
        self.t.append(datetime.utcnow())
        self.dt = [float((ti - self.t[0]).total_seconds()) for ti in self.t]
        
        self.data_line.setData(self.dt,self.y) #update the data
        
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

