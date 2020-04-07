#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 10:43:14 2020

@author: nlourie
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate

#Honeywell Volts to FLow calibration

f = np.array([0.,25.,50.,75.,100.,150.,200.])
v = np.array([1,2.99,3.82,4.3,4.58,4.86,5.0])

plt.figure()
plt.plot(v,f,'ko')

plt.xlabel('Voltage (V)',fontsize = 14)
plt.ylabel('Flow (L/m)',fontsize = 14)
plt.title('Honeywell AWM700 Flowmeter',fontsize = 20)


v_fit = np.linspace(v[0],v[-1],1000)

fit = interpolate.interp1d(v,f,kind = 'cubic')
f_fit = fit(v_fit)

plt.plot(v_fit,f_fit,'r-')