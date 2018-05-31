#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 15 14:25:10 2018

@author: dhartig
"""
import csv
from matplotlib import pyplot as plt

x = [i for i in range(25)]
all_sys = []
all_sta = []

with open ('/opt/school/subway/working_reports/all_system_dat.csv', 'r') as csvfile:
    rdr = csv.reader(csvfile)
    for s in rdr:
        all_sys.append(s)
    

with open ('/opt/school/subway/working_reports/all_station_dat.csv', 'r') as csvfile:
    rdr = csv.reader(csvfile)
    for s in rdr:
        all_sta.append(s)

linsys, logsys, poisys, pidsys, ladsys = tuple(all_sys[i:i+25] for i in range(0,124, 25))
linsta, logsta, poista, pidsta, ladsta = tuple(all_sta[i:i+25] for i in range(0,124, 25))


        
       
plt.plot(x, linsys, 'bo-')
plt.plot(x, logsys, 'go-')
plt.plot(x, poisys, 'ro-')
plt.plot(x, pidsys, 'mo-')
plt.plot(x, ladsys, 'ko-')
plt.xlabel("Number of features used")
plt.ylabel("System Error score")
plt.show()  


plt.plot(x, linsta, 'bo-')
plt.plot(x, logsta, 'go-')
plt.plot(x, poista, 'ro-')
plt.plot(x, pidsta, 'mo-')
plt.plot(x, ladsta, 'ko-')
plt.xlabel("Number of features used")
plt.ylabel("Station Error score")
plt.show()  