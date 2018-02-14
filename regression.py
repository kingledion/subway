#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 20:30:19 2017

@author: dhartig
"""

import pandas as pd, itertools
from sklearn import metrics
import numpy as np


def loadData(citylist):
    
    all_dfs = []
    for city in citylist:
        with open("./gendata/{0}_stations.csv".format(city)) as csvin:
            sdata = pd.read_csv(csvin)
        with open("./gendata/{0}_subway_ridership.csv".format(city)) as csvin:
            rdata = pd.read_csv(csvin, delimiter = ';', quotechar = "'", names = ['name', 'riders'])
            all_dfs.append(pd.merge(sdata, rdata, how = 'inner', on='name'))
            
    df = pd.concat(all_dfs)
    return df

citylist = ['boston', 'chicago', 'atlanta', 'dallas', 'denver', 'la']


def scoreAllCV(plotfunc, cols):
    scores = []
    combs = list(itertools.combinations(citylist, r=5))
    for l1, l2 in zip(combs, [set(citylist) - set(c) for c in combs]):
        print('Train:', l1, 'Test:', l2)
        df1 = loadData(l1)
        df2 = loadData(l2)
        
        Xtrain = df1[cols]
        ytrain = df1['riders']
        
        Xtest = df2[cols]
        ytest = df2['riders']
        
        unused, y_pred = plotfunc(cols, Xtrain, ytrain, Xtest, ytest) # unused is coefficients not used
        
        nearscore = [x + y for x, y in zip(df2['near_population'], df2['near_employment'])]
        
        for name, near, predicted, actual in zip(df2['name'], nearscore, y_pred, ytest):
            print("{0:28} {1:8} {2:8} {3:8}".format(name, int(near), int(predicted), actual))
        scores.append(metrics.r2_score(ytest, y_pred))
        print(scores[-1])
        
        input()
        
        #plt.plot(ytest, y_pred, 'bx')
        #plt.plot(ytest, ytest, 'r.')
        #plt.show()
        
    print("Summary score: ", np.mean(scores))
        
    return scores
