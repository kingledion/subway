#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 20 14:16:15 2018

@author: dhartig
"""

from regression import citylist, loadData
import itertools, numpy as np, scipy.stats as stats, math, sys
from sklearn.cluster import affinity_propagation, spectral_clustering
from sklearn.ensemble import RandomForestRegressor

df = loadData(citylist)
cols = list(df.columns.difference(['lat', 'lon', 'name', 'riders']))

scores = {c: [] for c in cols}

for i in range(100):

    rf = RandomForestRegressor()#max_features='log2')
    rf.fit(df[cols], df['riders'])
    for name, score in zip(cols, rf.feature_importances_):
        scores[name].append(score)

    sys.stdout.write("\r[{0}] {1}%".format('#'*math.floor(i/10)+' '*math.ceil(10-i/10), i))
    sys.stdout.flush()

print()
colwidth = max(len(name) for name in scores)
outscores = sorted([(name, np.mean(s)) for name, s in scores.items()], key=lambda x: x[1], reverse=True)
for name, score in outscores:
    print(name.ljust(colwidth), score)
