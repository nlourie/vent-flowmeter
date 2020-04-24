#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 10:43:14 2020

@author: nlourie
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
from scipy import signal

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

#Honeywell Volts to FLow calibration

f = np.array([0.,0.,25.,50.,75.,100.,150.,200.])
v = np.array([0.,1,2.99,3.82,4.3,4.58,4.86,5.0])

plt.figure()
plt.plot(v,f,'ko',label = 'Cal Data from Honeywell')

plt.xlabel('Voltage (V)',fontsize = 14)
plt.ylabel('Flow (L/m)',fontsize = 14)
plt.title('Honeywell AWM700 Flowmeter',fontsize = 20)


v_fit = np.linspace(v[0],v[-1],1000)

honeywell_v2f = interpolate.interp1d(v,f,kind = 'cubic')
f_fit = honeywell_v2f(v_fit)

plt.plot(v_fit,f_fit,'r-',label = 'Cubic Spline Fit')
plt.legend()

t_raw,dp_raw,v_raw = np.loadtxt('lps33_flow_calibration - wide range no bag.txt',skiprows = 1,delimiter = '\t',unpack = True)
dt_raw = t_raw-t_raw[0]

plt.figure(figsize = (20,6))
plt.subplot(1,3,1)
plt.plot(dt_raw,dp_raw)
plt.ylabel('dP')
plt.subplot(1,3,2)

dpmin = 0.0
tmin = 0
tmax = 50
vmin = 1.1
vmax = 5.0


dp = dp_raw[(dp_raw>dpmin) & (dt_raw<tmax) & (dt_raw > tmin) & (v_raw > vmin) &(v_raw < vmax)]
v = v_raw[(dp_raw>dpmin) & (dt_raw<tmax) & (dt_raw > tmin)& (v_raw > vmin)&(v_raw < vmax)]
dt = dt_raw[(dp_raw>dpmin) & (dt_raw<tmax) & (dt_raw > tmin)& (v_raw > vmin)&(v_raw < vmax)]
dt_samp = dt[1] - dt[0]
print ('dt samples = ',dt_samp)
fs = 1/dt_samp


plt.figure(figsize = (20,6))
plt.subplot(1,3,1)
plt.plot(dt,dp,'o')
dp_filt = zerophase_lowpass(dp,lf = .3, fs = fs)
plt.plot(dt,dp_filt)
plt.ylabel('dP')
plt.subplot(1,3,2)
plt.plot(dt,v)
plt.ylabel('Flowmeter Voltage')
plt.plot(dt_raw,v_raw)
plt.subplot(1,3,3)
plt.plot(dt,honeywell_v2f(v))
plt.ylabel('Raw Flow (L/m)')
plt.subplot(1,3,3)


flow = honeywell_v2f(v)
flow_raw = flow

lps35hw_dp2f = np.polyfit(dp_filt,flow,1)
dp_fit = np.linspace(np.min(dp_filt),np.max(dp_filt),1000)
flow_fit = np.polyval( lps35hw_dp2f,dp_fit)



plt.figure()
plt.plot(dp_filt,flow,'ko',label = 'filtered realtime data')
plt.plot(dp_fit,flow_fit,'r-',label = '4-Deg Polynomial Fit')
plt.xlabel('dP (cm H20)',fontsize = 14)
plt.ylabel('Flow (L/m)',fontsize = 14)
plt.legend()

plt.figure()
plt.plot(dp_filt,flow - np.polyval(lps35hw_dp2f,dp),'bo')
plt.ylabel('Residual (L/m)')
plt.xlabel('dp cm H20')



"""
dp_raw,v_raw = np.loadtxt('lps33_flow_calibration - 2.txt',skiprows = 1,delimiter = '\t',unpack = True)

vmin = 1.1
vmax = 4.0
dp = dp_raw[(v_raw > vmin) & (v_raw < vmax)]
v = v_raw[(v_raw > vmin) & (v_raw < vmax)]

flow = honeywell_v2f(v)

plt.figure(figsize = (20,6))
plt.subplot(1,2,1)
plt.plot(dp)
plt.ylabel('dP')
plt.subplot(1,2,2)
plt.plot(v,'o')
plt.plot(v_raw)
plt.ylabel('Flowmeter Voltage')

dp_filt = zerophase_lowpass(dp,lf = .5, fs = fs)

plt.figure()
plt.plot(dp_filt,flow,'ko',label = 'filtered realtime data')
#plt.plot(dp_fit,flow_fit,'r-',label = '4-Deg Polynomial Fit')
plt.xlabel('dP (cm H20)',fontsize = 14)
plt.ylabel('Flow (L/m)',fontsize = 14)
plt.legend()


"""

# get a few points around some nice time ranges:
t_starts = np.array([0,14.7, 18.1,24.77,28.15,30.5, 33.7, 34.8, 38.3, 40.5, 46.5])
t_ends = np.array([8,16.5, 23,25.22,28.32,32.5, 34.5, 37.4, 39.2, 44.0, 48])

select_dp = 0*t_starts
select_flow = 0*t_starts
error_dp = 0*t_starts
error_flow = 0*t_starts
plt.figure(figsize = (20,8))
plt.subplot(1,2,1)
plt.plot(dt,dp)
plt.subplot(1,2,2)
plt.plot(dt,flow)
for i in range(len(t_starts)):
    t_range = dt[(dt > t_starts[i]) & (dt < t_ends[i])]
    dp_range = dp[(dt > t_starts[i]) & (dt < t_ends[i])]
    flow_range = flow[(dt > t_starts[i]) & (dt < t_ends[i])]
    
    select_dp[i] = np.mean(dp_range)
    error_dp[i] = np.std(dp_range)/np.sqrt(len(select_dp))
    select_flow[i] = np.mean(flow_range)
    error_flow[i] = np.std(flow_range)/np.sqrt(len(select_flow))
    plt.subplot(1,2,1)
    plt.plot(t_range,dp_range,'o')
    plt.subplot(1,2,2)
    plt.plot(t_range,flow_range,'o')
    
N = 4
select_data_fit = np.polyfit(select_dp,select_flow,N)
dp_fit = np.linspace(np.min(select_dp),np.max(select_dp),1000)
dp_fit = np.linspace(0,0.6,1000)
select_flow_fit = np.polyval( select_data_fit,dp_fit)

plt.figure()
plt.title('Calibration Data: Averages Over Select Ranges')
plt.plot(select_dp,select_flow,'ko',label = 'filtered realtime data')
plt.errorbar(select_dp,select_flow,yerr = error_flow,xerr = error_dp,fmt = '.k')
plt.plot(dp_fit,select_flow_fit,'r-',label = '%i-Deg Polynomial Fit' %N)
"""
tmin = 27.7
tmax = 29.4
plt.plot(dp[(dt > tmin) & (dt<tmax)],flow[(dt > tmin) & (dt < tmax)],'bo')
"""
plt.xlabel('dP (cm H20)',fontsize = 14)
plt.ylabel('Flow (L/m)',fontsize = 14)
plt.legend()

np.savetxt('select_cal_data.txt',np.column_stack((select_dp,select_flow)),delimiter = '\t')

plt.figure(figsize = (20,6))
plt.subplot(1,3,1)
plt.plot(dt,flow_raw)
plt.plot(dt,np.polyval(select_data_fit,dp))


