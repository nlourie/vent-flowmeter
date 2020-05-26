#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 11:52:45 2020

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
import matplotlib.pyplot as plt
from scipy import interpolate

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
    #print('l_lfilter = ',l_lfilter)
    if np.mod(l_lfilter,2) == 0:
        l_lfilter = l_lfilter + 1
        #print('made odd: l_lfilter = ',l_lfilter)
    
    # filter flow signal
    x_filt = signal.savgol_filter(x,polyorder = N,window_length = l_lfilter)
    return x_filt


# import the data

time,flow = np.loadtxt('dataset_2.txt',skiprows = 100,delimiter = '\t',unpack = True)
fs = 1/(time[1] - time[0] )
print('fs = ',fs)
        
vol = signal.detrend(np.cumsum(flow))
negative_mean_subtracted_volume = [-1*(v-np.mean(vol)) for v in vol]
i_valleys = breath_detect_coarse(negative_mean_subtracted_volume,fs = fs,plotflag = False)


model = 'spline'

if model == 'linear':
    drift_model = np.polyfit(time[i_valleys],vol[i_valleys],1)
    v_drift = np.polyval(drift_model,time)

elif model == 'spline':

    
    drift_model = interpolate.interp1d(time[i_valleys],vol[i_valleys],kind = 'linear')
    v_drift_within_spline = drift_model(time[i_valleys[0]:i_valleys[-1]])
    v_drift = np.zeros(len(time))
    v_drift[0:i_valleys[1]] = np.polyval(np.polyfit(time[i_valleys[0:1]],vol[i_valleys[0:1]],1),time[0:i_valleys[1]],)
    v_drift[i_valleys[0]:i_valleys[-1]] = v_drift_within_spline
    v_drift[i_valleys[-1]:] = np.polyval(np.polyfit(time[i_valleys[-2:]],vol[i_valleys[-2:]],1),time[i_valleys[-1]:])

vol_corr = vol - v_drift

flow_filt = zerophase_lowpass(flow,0.5,fs)


plt.figure(figsize = (10,10))

plt.subplot(3,1,1)
plt.plot(time,flow,label = 'flow')
plt.plot(time,flow_filt,label = 'filtered flow')
plt.ylabel('Flow')

plt.subplot(3,1,2)
plt.plot(time,vol)
plt.plot(time[i_valleys],vol[i_valleys],'ro')
plt.plot(time,v_drift)
plt.ylabel('Raw Volume')

plt.subplot(3,1,3)
plt.plot(time,vol_corr)
plt.ylabel('Corrected Volume')
