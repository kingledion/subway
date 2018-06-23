#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 15 08:04:57 2018

@author: dhartig
"""

import itertools, numpy as np, pandas as pd, sys
import glmnet_python
from glmnet import glmnet; from glmnetPredict import glmnetPredict; from glmnetCoef import glmnetCoef
from cvglmnet import cvglmnet; from cvglmnetPredict import cvglmnetPredict; from cvglmnetCoef import cvglmnetCoef
from regression import loadData, citylist

from nppli import ipsolver, graddesc


def linearNet(Xtrain, ytrain, Xtest):
    
    Xtrain = np.array(Xtrain, dtype='float64')
    ytrain = np.array(ytrain, dtype='float64')
    Xtest = np.array(Xtest, dtype='float64')
    
    Xtrain, Xtest = normalize(Xtrain, Xtest)
    
    fit = cvglmnet(x=Xtrain, y=ytrain, alpha=1)
    coef = cvglmnetCoef(fit, s = "lambda_1se")
    
    pred = cvglmnetPredict(fit, Xtest, s="lambda_1se")
    
    print(coef.shape, pred.shape)
    
    return coef, pred

def logNet(Xtrain, ytrain, Xtest):
    
    
    Xtrain = np.array(Xtrain, dtype='float64')
    ytrain = np.array(ytrain, dtype='float64')
    Xtest = np.array(Xtest, dtype='float64')
    
    Xtrain, Xtest = standardize(Xtrain, Xtest)
    
    #beta = graddesc(Xtrain, ytrain)
    
    coef = ipsolver(Xtrain, ytrain, poisson = False)
    
    maxs = np.amax(Xtrain, axis=0)
    Xtest = np.clip(Xtest, 0, maxs)
    pred = Xtest @ coef
    
    print(coef.shape, pred.shape)
    
    return np.insert(coef, 0, 1), pred

    
 #   Xtrain = np.array(Xtrain, dtype='float64')
 #   ytrain = np.array(ytrain, dtype='float64')
 #   ytrain = np.log(ytrain)
 #   Xtest = np.array(Xtest, dtype='float64')
    
 #   Xtrain, Xtest = normalize(Xtrain, Xtest)
    
 #   fit = cvglmnet(x=Xtrain, y=ytrain, alpha=1)
 #   coef = cvglmnetCoef(fit, s = "lambda_1se")
    
 #   maxs = np.amax(Xtrain, axis=0)
 #   Xtest = np.clip(Xtest, 0, maxs)
    
 #   pred = cvglmnetPredict(fit, Xtest, s="lambda_1se")
 #   pred = np.exp(pred)
    
 #   print(coef.shape, pred.shape)
    
 #   return coef, pred


def poissonNet(Xtrain, ytrain, Xtest):
    
    Xtrain = np.array(Xtrain, dtype='float64')
    ytrain = np.array(ytrain, dtype='float64')
    Xtest = np.array(Xtest, dtype='float64')
    
    Xtrain, Xtest = poissonize(Xtrain, Xtest)
    
    fit = cvglmnet(x=Xtrain.copy(), y=ytrain.copy(), alpha=1, family = 'Poisson')
    coef = cvglmnetCoef(fit, s = "lambda_1se")
    
    maxs = np.amax(Xtrain, axis=0)
    Xtest = np.clip(Xtest, 0, maxs)
    
    pred = cvglmnetPredict(fit, Xtest, ptype='response', s="lambda_1se")
    
    #print(coef)
    #print(pred)
    
    print(coef.shape, pred.shape)
    
    
    return coef, pred


def poissIdentNet(Xtrain, ytrain, Xtest):
    
    Xtrain = np.array(Xtrain, dtype='float64')
    ytrain = np.array(ytrain, dtype='float64')
    Xtest = np.array(Xtest, dtype='float64')
    
    Xtrain, Xtest = standardize(Xtrain, Xtest)
    
    coef = ipsolver(Xtrain, ytrain)
    
    pred = Xtest @ coef
    
    print(coef.shape, pred.shape)
    
    return np.insert(coef, 0, 1), pred

def normalize(Xtrain, Xtest): 
    
    rowmean = np.mean(Xtrain, axis=0)
    rowstd = np.std(Xtrain, axis=0)
    
    return (Xtrain - rowmean)/rowstd, (Xtest - rowmean)/rowstd

def standardize(Xtrain, Xtest):
    
    rowstd = np.std(Xtrain, axis=0)
    
    return Xtrain/rowstd, Xtest/rowstd
    
    
def poissonize(Xtrain, Xtest):
    
    rowmean = np.mean(Xtrain, axis=0)
    
    return Xtrain/rowmean, Xtest/rowmean

if __name__ == "__main__":
    # get all features
    df = loadData(citylist, droptransfer=True)    
    cols = list(df.columns.difference(['lat', 'lon', 'name', 'riders', '30net_students', '15net_students', 'near_students'])) 
    
    # generate dataframes for all cross validation combinations
    pairs = []
    all_coefs = {}
    combs = list(itertools.combinations(citylist, r=5))
    for l1, l2 in zip(combs, [set(citylist) - set(c) for c in combs]):
        df1 = loadData(l1, droptransfer=True)
        df2 = loadData(l2, droptransfer=True)
     
        Xtrain = df1[cols]
        ytrain = df1['riders']
        
        Xtest = df2[cols]
        ytest = df2['riders']
        
        print(list(l2)[0])
        coef, ypred = logNet(Xtrain, ytrain, Xtest) 
        
        all_coefs[list(l2)[0]] =  [1 if i else 0 for i in coef[1:]]
                       
        #relerr = 1 - np.sum(np.divide(np.abs(np.subtract(y_pred, ytest)), ytest))/len(ytest)
        stat_err = np.sum(np.abs(ypred.flatten() - ytest))/np.sum(ytest)
        sys_err = np.abs(np.sum(ypred)-np.sum(ytest))/np.sum(ytest)
        print(sys_err, stat_err)
        
        #input()
        
    features = pd.DataFrame(all_coefs, index=cols)
    features.to_csv(sys.stdout)
    
        
        
        
        
        