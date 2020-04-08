#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 14:39:32 2020

Breathsim v3

Still based off the paper, but tweaked algorithm so it works better


@author: nlourie
"""


import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy import interpolate
from scipy.misc import derivative



#t_flow,flow = np.loadtxt('flow_sim_data.txt',skiprows = 1,delimiter = '\t',unpack = True)
#t_pepi,pepi = np.loadtxt('pepi_sim_data.txt',skiprows = 1,delimiter = '\t',unpack = True)


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


def get_processed_flow(time,rawflow,fs,SmoothingParam,smoothflag = True,plotflag = False):
    
    
    """
    % Inputs:
    %           time:           time signal    
    %           flow:            flow signal
    %           fs:             sampling rate
    %           SmoothParam:    smoothing parameters used to fitting the flow
    %                           shape, set between 0.85 to 0.95, the lower the
    %                           value, the smoother the signal.
    %           smoothflag:     set to 1 if use low pass filter
    %           plotflag:       plot graphs
    """
    # Diagnostic Stuff
    print('num points in time = ',len(time))
    print('num points in flow = ',len(rawflow))
    
    
    ## Step 1: Smooth the data
    if smoothflag:
        lf = 2.0 #cutoff frequency (Hz)
        flow = zerophase_lowpass(rawflow,lf,fs)
    else:
        flow = rawflow
        
    # remove mean
    flow = flow - np.mean(flow)
    
    ## Step 2: fit a spline to the flow data
    # Fit a spline through the smoothed data    
    flow_model = interpolate.UnivariateSpline(time,flow,s = 0)
    
    ## Step 3: Get the second derivative
    d2 = derivative(flow_model,x0 = time,n = 2,dx = 15/fs)
    
    ## Step 4: Find the peaks
    i_peaks = breath_detect_coarse(flow,fs,plotflag = False)
    if len(i_peaks>=2):
        ## Step 5: Loop through the peaks
        i_valleys = [] #valleys
        i_infl_points = [] #inflection points
        for i in range(len(i_peaks)-1):
            # get the range of the indices between current peak and next peak (ie peak-to-peak = pp)
            if i < len(i_peaks):
                i_range_pp = np.arange(i_peaks[i],i_peaks[i+1])
                #print(f'looking at peak {i} at index {i_peaks[i]} and time {time[i_peaks[i]]}')
                #print(f'Index range = {i_range_pp}')
            else:
                i_range_pp = np.arange(i_peaks[i],len(flow))
            
            # 5a - find the minimum of the flow between the peak and next peak
            i_valley = i_range_pp[np.argmin(flow[i_range_pp])]
            #print(f'found valley at index {i_valley} and time {time[i_valley]}')
            i_valleys.append(i_valley)
            
            # 5b - find the maximum of the 2nd derivative between the valley and the peak
            # but only look between a certain min and max percentage of the breath
            min_pct = 0.5
            max_pct = 0.9
            len_range = i_range_pp[-1] - i_valley
            
            i_range_vp = np.arange(i_valley + int(min_pct*len_range),i_valley + int(max_pct*len_range))
            #print(f'found valley at index {i_valley} and time {time[i_valley]}')
    
            i_infl_point = i_range_vp[np.argmax(d2[i_range_vp])]
            i_infl_points.append(i_infl_point)
        
        ## Step 6: Fit a spline through the first and last points and all the inflection points
        i_to_fit = [0] + i_infl_points + [len(flow)-1]
        vol = np.cumsum(flow)/fs
        drift_model = interpolate.interp1d(time[i_to_fit],vol[i_to_fit],kind = 'cubic')
        vol_drift = drift_model(time)
            
        vol_corr = vol - vol_drift
        
        ## Step 7: Get the last tidal volume
        i_since_last_breath = np.arange(i_infl_points[-1],len(flow))
        
        print(f'index of last inflection point is: {i_infl_points[-1]}, and the most recent index is {len(flow)})')
        vol_last_peak = np.max(vol_corr[i_since_last_breath])
        i_last_peak = i_since_last_breath[np.argmax(vol_corr[i_since_last_breath])]
        print('Last Breath VT = %0.2f L'%vol_last_peak)
        
            
        if plotflag:    
            plt.figure(figsize = (10,10))
            plt.subplot(3,1,1)
            plt.title('On-the-fly Tidal Volume Correction',fontsize = 24)
            plt.plot(time,rawflow,label = 'Raw Flow Signal')
            plt.plot(time,flow, label = 'Smoothed Flow Signal')
            plt.plot(time[i_peaks],flow[i_peaks],'g^', label = 'Peak Exhalation')
            plt.plot(time[i_valleys],flow[i_valleys],'ro',label = 'Peak Inhalation')
            plt.plot(time[i_infl_points],flow[i_infl_points],'k*',label = 'Start of Breath')
            plt.ylabel('Flow (L/s)',fontsize = 14)
            plt.grid('on')
            plt.legend()
            
            plt.subplot(3,1,2)
            plt.plot(time,d2,label = 'Second Derivative')
            plt.plot(time[i_infl_points],d2[i_infl_points],'k*',label = 'Start of Breath')
            plt.ylabel('Second Derivative of Flow',fontsize = 14)
            plt.grid('on')
            plt.legend()
            
            plt.subplot(3,1,3)
            plt.plot(time,vol_corr,label = 'Corrected Volume')
            plt.plot(time[i_infl_points],vol_corr[i_infl_points],'k*',label = 'Start of Breath')
            plt.plot(time[i_last_peak],vol_corr[i_last_peak],'g^',label = 'Last VT = %0.2f L' %vol_last_peak)
            plt.plot(time[i_since_last_breath],vol_corr[i_since_last_breath],label = 'Last Breath')
            plt.xlabel('time (s)',fontsize = 14)
            plt.ylabel('Tidal Volume (L)',fontsize = 14)
            plt.legend()
            plt.grid('on')        
            
            plt.tight_layout()
    else:
        i_valleys = []
        i_infl_points =[]
        vol_last_peak = []
        vol_corr = np.cumsum(flow)/fs
    return i_peaks,i_valleys,i_infl_points,vol_last_peak,flow,vol_corr
  
if __name__ == '__main__':
    # Import data
    time,rawflow = np.loadtxt('data.txt',skiprows = 100,delimiter = '\t',unpack = True)
    fs = 1/(time[1] - time[0] )

    i_peaks,i_valleys,i_infl_points,vol_last_peak,flow,vol_corr = get_processed_flow(time,rawflow,fs,SmoothingParam = 0,smoothflag=True,plotflag = True)
    
