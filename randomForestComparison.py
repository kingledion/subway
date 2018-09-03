#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 11:09:24 2018

@author: dhartig
"""

from regression import loadData, citylist
from sklearn.ensemble import RandomForestRegressor
import itertools, numpy as np

df = loadData(citylist, droptransfer=True)    
cols = list(df.columns.difference(['lat', 'lon', 'name', 'riders', '30net_students', '15net_students', 'near_students', 'near_hunits_renter'])) 

rfscores = np.zeros(len(cols))

combs = list(itertools.combinations(citylist, r=5))
for l1, l2 in zip(combs, [set(citylist) - set(c) for c in combs]):
    
    print(l2)
    
    for _ in range(100):
        
    
        df1 = loadData(l1, droptransfer=True)
        df2 = loadData(l2, droptransfer=True)
    
        Xtrain = df1[cols]
        ytrain = df1['riders']
        
        Xtest = df2[cols]
        ytest = df2['riders']
        
        forest = RandomForestRegressor(max_features = 5, n_jobs = -1)
        forest.fit(Xtrain, ytrain)
        
        rfscores = rfscores + forest.feature_importances_
        
        #ypred = forest.predict(Xtest)
        
        #stat_err = np.sum(np.abs(ypred - ytest))/np.sum(ytest)
        #sys_err = np.abs(np.sum(ypred)-np.sum(ytest))/np.sum(ytest)
        
        #rfscores.append((sys_err, stat_err))
        
featurescores = sorted(zip(cols, rfscores), key = lambda x: x[1], reverse=True)

print("\nRandom Forest Summary")
for j in range(20):
        print(featurescores[j])
