#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 17 11:23:29 2018

@author: dhartig
"""

from matplotlib import pyplot as plt
import matplotlib

pois_score = [0.2162, 0.2671, 0.3107, 0.3426, 0.3691, 0.3729, 0.3754, 0.3750, 0.3804, 0.3875, 0.3893, 0.3961, 0.3989, 0.4006, 0.4022, 0.4070, 0.4243, 0.4312, 0.4441, 0.4474]
lstsq_score = [0.2890, 0.3145, 0.3515, 0.3828, 0.3922, 0.4094, 0.4189, 0.4329, 0.4346, 0.4358, 0.4392, 0.4416, 0.4358, 0.4320, 0.4290, 0.4372, 0.4366, 0.4336, 0.4302, 0.4245]
lad_score = [0.4676, 0.4859, 0.4819, 0.4847, 0.4878, 0.4933, 0.5030, 0.5037, 0.5040, 0.5064, 0.5069, 0.4989, 0.4937, 0.4875, 0.4840, 0.4838, 0.4851, 0.4768, 0.4676, 0.4841]
x = [i+1 for i in range(20)]

ax = plt.figure().gca()
ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
plt.xlabel("Number of variables added")
plt.ylabel("Error score")
plt.plot(x, pois_score, 'k-', x, lstsq_score, 'g-', x, lad_score, 'b-')
plt.show()
