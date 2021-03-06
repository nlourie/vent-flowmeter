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
import monitor_utils_test as mu
from scipy import signal


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
    print('peakdistance = ',peakdistance)
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
        self.graph1 = pg.PlotWidget()
        self.graph2 = pg.PlotWidget()
        self.graph3 = pg.PlotWidget()
        
        layout = QtWidgets.QVBoxLayout()
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
        self.graph1.showGrid(x=True,y=True)
        
        # Set the label properties with valid CSS commands -- https://groups.google.com/forum/#!topic/pyqtgraph/jS1Ju8R6PXk
        labelStyle = {'color': '#FFF', 'font-size': '24pt'}
        self.graph1.setLabel('bottom', 'Label Text', 'Units', **labelStyle)
        self.graph1.setLabel('left', 'Temperature (°C)',**labelStyle)
        
        # change the plot range
        #self.graph2.setYRange(-200,200,padding = 0.1)
        #self.graph3.setYRange(200,200,padding = 0.1)
                                             
        self.x  = [0]
        self.t = [datetime.utcnow().timestamp()]
        self.dt = [0]
        self.y = [0]

        # plot data: x, y values
        # make a QPen object to hold the marker properties
        pen = pg.mkPen(color = 'y',width = 1)
        self.data_line = self.graph1.plot(self.dt, self.y,pen = pen)
        
        # graph2
        self.flow = [0]
        self.data_line2 = self.graph2.plot(self.dt,self.flow,pen = pen)
        # graph3
        self.vol = [0]
        
        self.data_line3 = self.graph3.plot(self.dt,self.vol,pen = pen)
        self.data_line4 = self.graph3.plot(self.dt,self.vol,pen = pen)
        self.data_line5 = self.graph2.plot([0],[0],pen = pen)
        self.calibrating = False
        self.vol_offset = 0
        
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
        
    def update_plot_data(self):
        # This is what happens every timer loop
        Npts_to_show = 2000
        if len(self.x) >= Npts_to_show:
            self.x = self.x[1:] # Remove the first element
            self.y = self.y[1:] # remove the first element
            self.t = self.t[1:]
            self.dt = self.dt[1:]
            self.vol = self.vol[1:]
            
            
        self.x.append(self.x[-1] + 1) # add a new value 1 higher than the last
        self.y.append( np.sin(self.x[-1]*(1/(60)))+0.3*np.sin(self.x[-1]*(1/(6000))) )# add a new random value
        self.t.append(datetime.utcnow().timestamp())
        self.dt = [(ti - self.t[0]) for ti in self.t]
        
        self.vol = np.cumsum(self.y)
        try:
            negative_mean_subtracted_volume = [-1*(v-np.mean(self.vol)) for v in self.vol]
            i_valleys = breath_detect_coarse(negative_mean_subtracted_volume,fs = 1000/self.t_update,plotflag = False)
            self.i_valleys = i_valleys
            print('i_valleys = ',self.i_valleys)
            #print('datatype of i_valleys = ',type(self.i_valleys))
        except:
            pass
        
        if len(self.i_valleys) >= 2:
            t = np.array(self.t)
            vol = np.array(self.vol)
            dt = np.array(self.dt)
            print('found peaks at dt = ',dt[self.i_valleys])
            self.drift_model = np.polyfit(t[self.i_valleys],vol[self.i_valleys],1)
            self.v_drift = np.polyval(self.drift_model,t)
            self.vol_corr = vol - self.v_drift
            self.data_line5.setData(self.dt,self.v_drift)

            
        else:
            self.vol_corr = self.vol
        self.data_line.setData(self.dt,self.y) #update the data

        #self.data_line2.setData(self.dt,list(np.array(self.vol - np.polyval(self.drift_model,self.t))))
        self.data_line2.setData(self.dt,self.vol)
        self.data_line3.setData(self.dt,self.vol_corr)
        #self.data_line4.setData(self.dt,np.polyval(self.drift_model,self.t))
        #self.data_line3.setData(self.dt,self.vol - np.polyval(self.drift_model,self.t))


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

