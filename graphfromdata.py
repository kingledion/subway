#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 15 14:25:10 2018

@author: dhartig
"""
import csv
from matplotlib import pyplot as plt

x = [i for i in range(25)]
ylinsys = []
ylinsta = []

with open ('/opt/school/subway/working_reports/lin_reg_dat.csv', 'r') as csvfile:
    rdr = csv.reader(csvfile)
    for idx, sys, sta in rdr:
        ylinsys.append(sys)
        ylinsta.append(sta)
        
ylogsys = []
ylogsta = []

with open ('/opt/school/subway/working_reports/pois_reg_dat.csv', 'r') as csvfile:
    rdr = csv.reader(csvfile)
    for idx, sys, sta in rdr:
        ylogsys.append(sys)
        ylogsta.append(sta)

yladsys = []
yladsta = []       
with open ('/opt/school/subway/working_reports/lad_reg_dat.csv', 'r') as csvfile:
    rdr = csv.reader(csvfile)
    for idx, sys, sta in rdr:
        yladsys.append(sys)
        yladsta.append(sta)
        
        
       
plt.plot(x, ylinsys, 'k-', x, ylinsta, 'k:')
plt.plot(x, ylogsys, 'b-', x, ylogsta, 'b:')
plt.plot(x, yladsys, 'r-', x, yladsta, 'r:')
plt.xlabel("Number of features used")
plt.ylabel("Error score")
plt.show()      