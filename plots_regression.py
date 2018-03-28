#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 19 21:01:35 2018

@author: dhartig
"""

import itertools, numpy as np
from regression import loadData, citylist, poissonF, lstSqF, LADF, scoreCV
from matplotlib import pyplot as plt


REGRESSIONTYPE = poissonF

def errors_by_station(plotfunc, pairs, cols):  
    errpairs = []  
    
    
    for df1, df2 in pairs:

        Xtrain = df1[cols]
        ytrain = df1['riders']
        
        Xtest = df2[cols]
        ytest = df2['riders']
        
        
        #print(cols)
        y_pred = plotfunc(Xtrain, ytrain, Xtest, ytest) 
               
        errpairs.extend([(true, pred - true) for true, pred in zip(ytest, y_pred)])

    return errpairs

def ploterrs(errpairs):
    results = sorted(errpairs, key=lambda x: x[0])
    x, y = zip(*results)
    plt.plot(x, y, 'bx')
    plt.show()





if __name__ == "__main__":
    # get all features
    df = loadData(citylist, droptransfer=True)    
    cols = list(df.columns.difference(['lat', 'lon', 'name', 'riders'])) 
    
    # generate dataframes for all cross validation combinations
    pairs = []
    combs = list(itertools.combinations(citylist, r=5))
    for l1, l2 in zip(combs, [set(citylist) - set(c) for c in combs]):
        df1 = loadData(l1, droptransfer=True)
        df2 = loadData(l2, droptransfer=True)
        pairs.append((df1, df2))
    
    used = []
    for i in range(20):
        scoremap = [(c, scoreCV(REGRESSIONTYPE, pairs, list(used) + [c])) for c in set(cols) - set(used)]
        name, scores = sorted(scoremap, key=lambda x: np.mean(x[1]))[-1]
        used.append(name)
        print(name)
    
    results = errors_by_station(REGRESSIONTYPE, pairs, used)
    ploterrs(results)

