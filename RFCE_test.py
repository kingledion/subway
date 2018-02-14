#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 20 14:16:15 2018

@author: dhartig
"""

from regression import citylist, loadData
import numpy as np, scipy.stats as stats, math, sys
from sklearn.cluster import affinity_propagation, spectral_clustering
from sklearn.ensemble import RandomForestRegressor

def get_dataset():
    
    df = loadData(citylist)
    cols = list(df.columns.difference(['lat', 'lon', 'name', 'riders']))
    
    return df, cols

def makeAdj(df, cols):
    return np.square(np.corrcoef(df[cols], rowvar=False))

def remove_cols(to_remove, rcols, radj):
    i_to_remove = [rcols.index(name) for name in to_remove]
    radj = np.delete(radj, i_to_remove, axis = 0)
    radj = np.delete(radj, i_to_remove, axis = 1)
    rcols = [name for i, name in enumerate(rcols) if i not in i_to_remove]
    return rcols, radj  

# i = number of iterations
def RandomForestClusterSelection(df, cols, i=100):
    
    adj = makeAdj(df, cols)

    scores = {c: 0 for c in cols}
    
    for j in range(i):
          
        # Get scores for features
        rf = RandomForestRegressor(max_features='log2')
        rf.fit(df[cols], df['riders'])
        featScore = {name: score for score, name in zip(rf.feature_importances_, cols)}
        
        
        # Set up clusters
        clusters = {}
        centers, labels = affinity_propagation(adj)
        for name, c in zip(cols, labels):
            if c in clusters:
                clusters[c].append(name)
            else:
                clusters[c] = [name]
                

        # Select highest value in each cluster
        keep = []
        for c, names in clusters.items():
            name, maxval = max(zip(names, [featScore[n] for n in names]), key=lambda x: x[1])
            keep.append(name)
            
        for name in keep:
            scores[name] += 1
    
        sys.stdout.write("\r[{0}] {1:.1f}%".format('#'*math.floor(j/i*10)+' '*math.ceil(10-j/i*10), j/i*100))
        sys.stdout.flush()
    
    print()
    colwidth = max(len(name) for name in scores)
    outscores = sorted([(name, s/i) for name, s in scores.items()], key=lambda x: x[1], reverse=True)
    for name, score in outscores:
        print(name.ljust(colwidth), score)
        
RandomForestClusterSelection(*get_dataset())
