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

def scoreCV(plotfunc, pairs, cols, c):
    
    #print(c)
    scores = []  
    
    #print(cols)
    
    for df1, df2 in pairs:

        Xtrain = df1[cols]
        ytrain = df1['riders']
        
        Xtest = df2[cols]
        ytest = df2['riders']
        
        
        #print(cols)
        ypred = plotfunc(Xtrain, ytrain, Xtest) 
               
        #relerr = 1 - np.sum(np.divide(np.abs(np.subtract(y_pred, ytest)), ytest))/len(ytest)
        stat_err = np.sum(np.abs(ypred - ytest))/np.sum(ytest)
        sys_err = np.abs(np.sum(ypred)-np.sum(ytest))/np.sum(ytest)
        scores.append((sys_err, stat_err))

    return scores

        
def poissonF(Xtrain, ytrain, Xtest):
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest, has_constant='add')
   
    model = sm.GLM(ytrain, Xtrain, family=sm.families.Poisson())#, link =sm.families.links.identity())
    results = model.fit()
    
    maxs = pd.Series(np.amax(Xtrain, axis=0))
    Xtest = Xtest.clip(upper=maxs, axis=1)
    
    return results.predict(Xtest)


def poissIdentF(Xtrain, ytrain, Xtest):
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest, has_constant='add')
   
    model = sm.GLM(ytrain, Xtrain, family=sm.families.Poisson(), link =sm.families.links.identity())
    results = model.fit()
    
    return results.predict(Xtest)

def linearF(Xtrain, ytrain, Xtest):
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest, has_constant='add')
        
    model = sm.GLM(ytrain, Xtrain, family=sm.families.Gaussian())
    results = model.fit()
       
    return results.predict(Xtest)


def logF(Xtrain, ytrain, Xtest):
    
    ytrain = np.log(ytrain)
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest, has_constant='add')
    
        
    #model = sm.GLM(ytrain, Xtrain, family=sm.families.Gaussian(), link = sm.families.links.Log())
    model = sm.GLM(ytrain, Xtrain, family=sm.families.Gaussian())
    results = model.fit()
    
    maxs = pd.Series(np.amax(Xtrain, axis=0))
    Xtest = Xtest.clip(upper=maxs, axis=1)
     
    res = results.predict(Xtest)
    return np.exp(res)
    

def LADF(Xtrain, ytrain, Xtest):
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest, has_constant='add')
    
    #print(Xtrain.shape)
    #print(ytrain.shape)
    #print(Xtest.shape)
    
    model = QuantReg(ytrain, Xtrain)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results = model.fit(q=0.5)
    
    return results.predict(Xtest)

    
if __name__ == "__main__":
    # get all features
    df = loadData(citylist, droptransfer=True)    
    cols = list(df.columns.difference(['lat', 'lon', 'name', 'riders', '30net_students', '15net_students', 'near_students', 'near_hunits_renter'])) 
    
    # generate dataframes for all cross validation combinations
    pairs = []
    combs = list(itertools.combinations(citylist, r=5))
    for l1, l2 in zip(combs, [set(citylist) - set(c) for c in combs]):
        df1 = loadData(l1, droptransfer=True)
        df2 = loadData(l2, droptransfer=True)
        pairs.append((df1, df2))
        
    # greedily find the best set of n 
    used = []
    #used = ['15net_employed', 'near_hospitality', 'near_hunits_owner', '30net_population', 'near_university', 'parking',
     #       '30net_entertainment', '15net_household', 'near_medical', '15net_entertainment', 'near_finance', 'near_business', '15net_medical', 
      #      'near_hunits_attached', 'near_hunits_new', 'near_emp_full_time', '15net_hunits_large', 'near_household']
    for i in range(25):
        #print(used)
        touse = set(cols) - set(used)
        #print(touse)
        #print(list(used) + [list(touse)[0]])
        scoremap = [(c, scoreCV(LADF, pairs, list(used) + [c], c)) for c in set(cols) - set(used)]
        #for name, scores in sorted(scoremap, key=lambda x: np.mean(x[1]), reverse=True):
        #    print(name, np.mean([i[0] for i in scores]), np.mean([i[1] for i in scores]))
        name, scores = sorted(scoremap, key=lambda x: np.mean(x[1]))[0]
        print("{3},{0},{1:.4f},{2:.4f}".format(name, np.mean([x[0] for x in scores]), np.mean([x[1] for x in scores]), i+1))
        #print("Selected variable:", name)
        #print("station error: {0:.4f}  ".format(np.mean([x[1] for x in scores])), end='')
        #print("System error: {0:.4f}  ".format(np.mean([x[0] for x in scores])))
        used.append(name)
        #print(used)
        #input()
    
    
