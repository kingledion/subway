#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 20:30:19 2017

@author: dhartig
"""

import pandas as pd, numpy as np, warnings
import sklearn.linear_model as lm, sklearn.svm as svm

def std_features(X, mean, std):
    X = X - mean
    with warnings.catch_warnings():
        warnings.filterwarnings('error')
        try:
            X = X/std
        except Warning as warn:
            X = np.nan_to_num(X)
    return(X)

# Read in data; merge into two datasets
with open("./gendata/boston_stations.csv") as csvin:
    sdata = pd.read_csv(csvin)
with open('./gendata/boston_subway_ridership.csv') as csvin:
    rdata = pd.read_csv(csvin, delimiter = ';', quotechar = "'", names = ['name', 'riders'])
data1 = pd.merge(sdata, rdata, how = 'inner', on='name')
    
with open("./gendata/chicago_stations.csv") as csvin:
    sdata = pd.read_csv(csvin)  
with open('./gendata/chicago_subway_ridership.csv') as csvin:
    rdata = pd.read_csv(csvin,  delimiter = ';', quotechar = "'", names = ['name', 'riders'])  
data2 = pd.merge(sdata, rdata, how = 'inner', on='name')
    
# Select columns for use in regression
fields = ['popnear', 'housenear', 'empnear', 'paynear', 'popwalk', 'housewalk', 'empwalk', 'paywalk', 'popdrive', 'housedrive', 'parking',
          '15empnet','30empnet','60empnet','15housenet','30housenet','60housenet','15paynet','30paynet','60paynet','15popnet','30popnet','60popnet']
X1 = data1.as_matrix(columns=fields)
X2 = data2.as_matrix(columns=fields)

# Standardize X values
xmn, xst = np.mean(X1, axis=0), np.std(X1, axis=0)
X1std = std_features(X1, xmn, xst)
X2std = std_features(X2, xmn, xst)

y1 = np.ravel(data1.as_matrix(columns=['riders']))
y2 = np.ravel(data2.as_matrix(columns=['riders']))

# Standardize y vlues
ymn, yst = np.mean(y1), np.std(y1)
y1std = std_features(y1, ymn, yst)
y2std = std_features(y2, ymn, yst)

def scoreLsq(Xtrain, ytrain, Xtest, ytest):

    coeff, resid, rank, s = np.linalg.lstsq(Xtrain, ytrain)
    
    predicted = np.dot(Xtrain, coeff)
    sstot = sum((ytrain - np.ones(ytrain.shape)*np.mean(ytrain))**2)
    ssres = sum((ytrain - predicted)**2)
    sc1 = 1-ssres/sstot
    
    predicted = np.dot(Xtest, coeff)
    sstot = sum((ytest - np.ones(ytest.shape)*np.mean(ytest))**2)
    ssres = sum((ytest - predicted)**2)
    sc2 = 1-ssres/sstot
    #print(["{0:.2f}".format(x) for x in coeff])
    return (sc1, sc2)
    
def scorePolyLsq(Xtrain, ytrain, Xtest, ytest):
    pass
    
def scoreRBFSVR(c, Xtrain, ytrain, Xtest, ytest):
    model = svm.SVR(kernel='rbf', C = c)
    model.fit(Xtrain, ytrain)
    #print(len(ytrain), len(model.support_))
    return (model.score(Xtrain, ytrain), model.score(Xtest, ytest))

def scoreRidge(a, Xtrain, ytrain, Xtest, ytest):
    model = lm.Ridge(alpha = a, fit_intercept = False, solver='svd')    
    model.fit(Xtrain, ytrain)   
    #print(["{0:.2f}".format(x) for x in model.coef_])
    return (model.score(Xtrain, ytrain), model.score(Xtest, ytest))
        
def scoreLASSO(a, Xtrain, ytrain, Xtest, ytest):
    model = lm.Lasso(alpha = a, fit_intercept=False, precompute=True, max_iter=100000)
    model.fit(Xtrain, ytrain)   
    #print(["{0:.2f}".format(x) for x in model.coef_])
    return (model.score(Xtrain, ytrain), model.score(Xtest, ytest))
    

print('\nLinear Least Squares Regression')   
print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreLsq(X1, y1, X2, y2)))
print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreLsq(X2, y2, X1, y1)))

for c in [1.5]:
    print('\nRadial Basis Function SVR (C = {0})'.format(c))
    print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreRBFSVR(c, X1std, y1std, X2std, y2std)))
    print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreRBFSVR(c, X2std, y2std, X1std, y1std)))

for a in [40]:
    print('\nRidge Regression (alpha = {0})'.format(a))
    print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreRidge(a, X1std, y1std, X2std, y2std)))
    print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreRidge(a, X2std, y2std, X1std, y1std)))

for a in [8]:
    print('\nLASSO Regression (alpha = {0})'.format(a))
    print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreLASSO(a, X1std, y1std, X2std, y2std)))
    print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreLASSO(a, X2std, y2std, X1std, y1std)))
