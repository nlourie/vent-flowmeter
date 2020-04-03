#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 13:35:53 2020

breath_sim.py

Based off of this paper:
    Nguyen et al, 2017
    "An automated and reliable method for breath detection during
    variable mask pressures in awake and sleeping humans"
    https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0179030#sec021
    

@author: nlourie
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# Import data
t_flow,flow = np.loadtxt('flow_sim_data.txt',skiprows = 1,delimiter = '\t',unpack = True)
t_pepi,pepi = np.loadtxt('pepi_sim_data.txt',skiprows = 1,delimiter = '\t',unpack = True)


# Follow their algorithm to calculate the "corrected" volume

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
    
    
    volume = np.cumsum(flow)/fs

    return peak_index, volume


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


def Breath_detection(time,sig,fs,num,SmoothingParam,filterflag,plotflag = False):
    """
    % Inputs:
    %           sig:            flow signal
    %           fs:             sampling rate
    %           num:            number of the breath to plot (for quality control)
    %           SmoothParam:    smoothing parameters used to fitting the flow
    %                           shape, set between 0.85 to 0.95, the lower the
    %                           value, the smoother the signal.
    %           filterflag:     set to 1 if use low pass filter
    %           plotflag:       plot graphs
    
    % Output:
    %           out.infp            onsets of inspiration (sample)
    %           out.expp            onsets of expiration (sample) 
    %           out.inspiration     onsets of inspiration (s)
    %           out.expiration      onsets of expiration (s)
    %           out.Ti              Inspiratory time (s)
    %           out.Te              Expiratory time (s)
    %           out.Ttot            total breath time (s)
    %           out.PIF             Peak Inspiratory Flow (L/s)
    %           out.Vt              Tidal Volume (L)
    %           out.fb              Breathing frequency (bpm)
    %           out.Ve              Minute ventilation (L/min) 
    %
    % Written by: Chinh Nguyen, PhD, NeuroScience Research Australia (NeuRA)
    % Email: c.nguyen@neura.edu.au
    
    % Last Updated: 25/10/2016
    % Example:
    % out = Breath_detection(Flow.values,1/Flow.interval,2,0.9,1,1);
    # Converted to python by: Nate Lourie, PhD
    # Email: nlourie@mit.edu
    # Updated on: April, 2020
    """
    
    ## apply low-pass filter to the signal if desired
    if filterflag:
        lf = 2 #cutoff frequency (Hz)
        sig = zerophase_lowpass(sig,lf,fs)
    
    # remove mean
    sig = sig - np.mean(sig)
    
    ## detect onsets of inspiration/expiration based on inflection points
        
    # detect peaks in the flow signal
    i_peaks,volume = breath_detect_coarse(sig,fs,plotflag = False)
    infl_p_loc = np.zeros(len(i_peaks))
    
    # detect inflection points in the flow signal in each breath
    # loop through all the detected peaks
    for i in range(len(i_peaks)):
        # get the range of the indices between current peak and next peak (ie peak-to-peak = pp)
        if i<len(i_peaks):
            index_range_pp = np.arange(i_peaks[i],i_peaks[i+1])
        else:
            index_range_pp = np.arange(i_peaks[i],len(sig))
            
        # make a signal and time range peak2peak (pp)
        sig_range_pp  =  sig[index_range_pp]
        
        # find the valley between the 2 peaks
        i_min_pp = np.where([sig_range_pp == np.min(sig_range_pp)])[1][0]
        
        # get the range of the data between the valley and the peak (vp)
        print('i_min_pp = ',i_min_pp)
        print('index_range_pp[-1] = ',index_range_pp[-1])
        time_range_vp = time[i_min_pp:index_range_pp[-1]]
        sig_range_vp  =  sig[i_min_pp:index_range_pp[-1]]
        
        plt.plot(time_range_vp,sig_range_vp)

# Calculate the sampling frequency of the flow data
fs = 1.0/(t_flow[1] - t_flow[0])

# Detect the peaks in the flow signal
i_peaks, volume = breath_detect_coarse(flow,fs,False)
    
# Detect inflection points in the flow signal in each breath
flow_filt = zerophase_lowpass(flow,lf = 2,fs = fs)

plt.figure()
Breath_detection(t_flow,flow,fs,num=2,SmoothingParam = 0.9,filterflag=False,plotflag = False)




# Copy the plots from the paper
plt.figure(figsize = (6,10))

plt.subplot(4,1,1)
plt.plot(t_pepi,pepi)
plt.xlabel('time (s)')
plt.ylabel('pepi (L/s)')
plt.axis([20,60,0,22])
plt.grid('on')

plt.subplot(4,1,2)
plt.plot(t_flow,flow)
#plt.plot(t_flow,flow_filt)
plt.xlabel('time (s)')
plt.ylabel('flow (L/s)')
plt.axis([20,60,-1.25,0.6])
plt.grid('on')


plt.plot(t_flow[i_peaks],flow[i_peaks],'ro')

plt.subplot(4,1,3)
plt.plot(t_flow,volume)
plt.axis([20,60,0,2])
plt.grid('on')
plt.xlabel('time (s)')
plt.ylabel('volume (L)')



plt.tight_layout()