#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 15 07:34:29 2018

@author: dhartig
"""

from regression import loadData
import numpy as np, numpy.linalg as ln
import matplotlib.pyplot as plt

colorlist= ['blue', 'red', 'green']#'#545454', 'green',  ]
citylist1 = ['boston', 'chicago', 'la']
citylist2 = ['atlanta', 'dallas', 'denver']      
xs = []
ys = []
ss = []

for name in citylist2:
    
    df = loadData([name], droptransfer=True)

#feat = [i for i in df if i.startswith("near_")]


#for f in feat:
#    a = np.column_stack((np.ones(len(df[f])), df[f]))
#    b = df['riders']
#    x, resid, rank, s = ln.lstsq(a, b)
    
#    print(f, "{0:.4f}, {1:.4f}".format(x[0], x[1]))

    xs.append(df['15net_population'])
    ys.append(df['15net_employment'])
    ss.append(df['riders']/200)
    
def getTrendLine(x0, y0):
    
    flatx = [item for sublist in x0 for item in sublist]
    flaty = [item for sublist in y0 for item in sublist]
    
    
    X = np.column_stack((np.ones(len(flatx)), flatx))
    results, resid, rank, s = ln.lstsq(X, flaty)
    a, b = results
    xr = [i for i in range(int(max(flatx)))]
    yr = [a + b * i for i in x0]
    
    return xr, yr


for x, y, size, clr in zip(xs, ys, ss, colorlist):
    plt.scatter(x, y, color=clr, s = size)
plt.xlabel("Total population near station")
plt.ylabel("Total employment near station")
plt.show()

#plt.plot(df['near_hunits_detached'], df['riders'], ro)
    