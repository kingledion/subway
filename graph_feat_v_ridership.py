#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 26 10:30:21 2018

@author: dhartig
"""

from regression import loadData, citylist, linearF
import matplotlib.pyplot as plt

df = loadData(citylist, droptransfer=True)

x = df['near_hospitality']
y = df['riders']

y_pred = linearF(x, y, x)

plt.plot(x, y, 'b.')
plt.plot(x, y_pred, 'k-')
plt.xlabel("Employment in hospitality industry near station")
plt.ylabel("Average weekday station ridership")
plt.show()