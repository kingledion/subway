#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 20:30:19 2017

@author: dhartig
"""

import pandas as pd, itertools, numpy as np, statsmodels.api as sm
from statsmodels.regression.quantile_regression import QuantReg
import warnings



def loadData(citylist, droptransfer = False):
    
    all_dfs = []
    for city in citylist:
        with open("./gendata/{0}_stations.csv".format(city)) as csvin:
            sdata = pd.read_csv(csvin)
        with open("./gendata/{0}_subway_ridership.csv".format(city)) as csvin:
            rdata = pd.read_csv(csvin, delimiter = ';', quotechar = "'", names = ['name', 'riders'])
            all_dfs.append(pd.merge(sdata, rdata, how = 'inner', on='name'))
            
    df = pd.concat(all_dfs)
    if droptransfer:
        df = df[~df['name'].isin(transferstations)]
        
    return df

citylist = ['boston', 'chicago', 'atlanta', 'dallas', 'denver', 'la']

transferstations = set(['Five Points', 'Willowbrook-Rosa Parks', '7th Street-Metro Center', 'Union Station'])

def scoreCV(plotfunc, pairs, cols):  
    scores = []  
    
    #print(cols)
    
    for df1, df2 in pairs:

        Xtrain = df1[cols]
        ytrain = df1['riders']
        
        Xtest = df2[cols]
        ytest = df2['riders']
        
        
        #print(cols)
        y_pred = plotfunc(Xtrain, ytrain, Xtest, ytest) 
               
        err = 1 - np.sum(np.abs(np.subtract(y_pred, ytest)))/np.sum(ytest)
        relerr = 1 - np.sum(np.divide(np.abs(np.subtract(y_pred, ytest)), ytest))/len(ytest)
        syserr = 1 - np.abs(np.sum(y_pred)-np.sum(ytest))/np.sum(ytest)
        scores.append((err, relerr, syserr))

    return scores

        
def poissonF(Xtrain, ytrain, Xtest, ytest):
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest, has_constant='add')
        # For the case of atlanta, the network is small enough that the 60net feature are equal for all stations
        # this will cause a second constant to be added, and a garbage result, unfortunately.
   
    model = sm.GLM(ytrain, Xtrain, family=sm.families.Poisson(), link =sm.families.links.identity())
    results = model.fit()
    
    return results.predict(Xtest)

def lstSqF(Xtrain, ytrain, Xtest, ytest):
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest, has_constant='add')
        
    model = sm.GLM(ytrain, Xtrain, family=sm.families.Gaussian())
    results = model.fit()
       
    return results.predict(Xtest)

def LADF(Xtrain, ytrain, Xtest, ytest):
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest, has_constant='add')
    
    model = QuantReg(ytrain, Xtrain)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results = model.fit(q=0.5)
    
    return results.predict(Xtest)
    

    
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
        
    # greedily find the best set of n    
    used = []
    for i in range(20):
        scoremap = [(c, scoreCV(LADF, pairs, list(used) + [c])) for c in set(cols) - set(used)]
        name, scores = sorted(scoremap, key=lambda x: np.mean(x[1]))[-1]
        print("&{4}&{0}&{1:.4f}&{2:.4f}&{3:.4f}\\\\".format(name, np.mean([x[0] for x in scores]), np.mean([x[1] for x in scores]), np.mean([x[2] for x in scores]), i+1))
        #print("Selected variable:", name)
        #print("Summed station error: {0:.4f}  ".format(np.mean([x[0] for x in scores])), end='')
        #print("MAPE error: {0:.4f}  ".format(np.mean([x[1] for x in scores])), end='')
        #print("System error: {0:.4f}  ".format(np.mean([x[2] for x in scores])))
        used.append(name)
    
    
