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


def getData(fields, dataframe=False):
    # Read in data; merge into two datasets
    with open("./gendata/boston_stations.csv") as csvin:
        sdata = pd.read_csv(csvin)
    with open('./gendata/boston_subway_ridership.csv') as csvin:
        rdata = pd.read_csv(csvin, delimiter = ';', quotechar = "'", names = ['name', 'riders'])
    databos = pd.merge(sdata, rdata, how = 'inner', on='name')
        
    with open("./gendata/chicago_stations.csv") as csvin:
        sdata = pd.read_csv(csvin)  
    with open('./gendata/chicago_subway_ridership.csv') as csvin:
        rdata = pd.read_csv(csvin,  delimiter = ';', quotechar = "'", names = ['name', 'riders'])  
    datachi = pd.merge(sdata, rdata, how = 'inner', on='name')
        
    # Select columns for use in regression
    Xbos = databos.as_matrix(columns=fields)
    Xchi = datachi.as_matrix(columns=fields)
    
    ybos = np.ravel(databos.as_matrix(columns=['riders']))
    ychi = np.ravel(datachi.as_matrix(columns=['riders']))
    
    if dataframe:
        return databos, datachi
    else:
        return Xbos, ybos, Xchi, ychi

# Standardize X2 and y2 according to X1, y1
def standardize(X1, y1, X2, y2):

    # Standardize X values
    xmn, xst = np.mean(X1, axis=0), np.std(X1, axis=0)
    X1std = std_features(X1, xmn, xst)
    X2std = std_features(X2, xmn, xst)
    
    # Standardize y vlues
    ymn, yst = np.mean(y1), np.std(y1)
    y1std = std_features(y1, ymn, yst)
    y2std = std_features(y2, ymn, yst)
    
    return X1std, y1std, X2std, y2std, xmn, xst, ymn, yst


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
    return sc1, sc2, coeff
        
def scoreRBFSVR(c, Xtrain, ytrain, Xtest, ytest):
    model = svm.SVR(kernel='rbf', C = c)
    model.fit(Xtrain, ytrain)
    #print(len(ytrain), len(model.support_))
    return (model.score(Xtrain, ytrain), model.score(Xtest, ytest))

def scoreLinSVR(c, Xtrain, ytrain, Xtest, ytest):
    model = svm.SVR(kernel='linear', C = c)
    model.fit(Xtrain, ytrain)
    #print(len(ytrain), len(model.support_))
    return (model.score(Xtrain, ytrain), model.score(Xtest, ytest))

def scorePolySVR(c, Xtrain, ytrain, Xtest, ytest):
    model = svm.SVR(kernel='poly', C = c)
    model.fit(Xtrain, ytrain)
    #print(len(ytrain), len(model.support_))
    return (model.score(Xtrain, ytrain), model.score(Xtest, ytest))

def scoreSigSVR(c, Xtrain, ytrain, Xtest, ytest):
    model = svm.SVR(kernel='sigmoid', C = c)
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
    

def test1stOrder():
    
    fields = ['popnear', 'housenear', 'empnear', 'paynear', 'popwalk', 'housewalk', 'empwalk', 'paywalk', 'popdrive', 'housedrive', 'parking',
          '15empnet','30empnet','15housenet','30housenet','15paynet','30paynet','15popnet','30popnet']

    X1, y1, X2, y2 = getData(fields)
    X1std, y1std, X2std, y2std = standardize(X1, y1, X2, y2)[:4]

    print('\nLinear Least Squares Regression')   
    print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreLsq(X1, y1, X2, y2)))
    print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreLsq(X2, y2, X1, y1)))
    
    for c in [0.006]:
        print('\nLinear SVR (C = {0})'.format(c))
        print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreLinSVR(c, X1std, y1std, X2std, y2std)))
        print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreLinSVR(c, X2std, y2std, X1std, y1std)))
    
    for a in [350]:
        print('\nRidge Regression (alpha = {0})'.format(a))
        print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreRidge(a, X1std, y1std, X2std, y2std)))
        print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreRidge(a, X2std, y2std, X1std, y1std)))
    
    for a in [0.3]:
        print('\nLASSO Regression (alpha = {0})'.format(a))
        print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreLASSO(a, X1std, y1std, X2std, y2std)))
        print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreLASSO(a, X2std, y2std, X1std, y1std)))
        
    for c in [1.4]:
        print('\nRadial Basis Function SVR (C = {0})'.format(c))
        print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreRBFSVR(c, X1std, y1std, X2std, y2std)))
        print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreRBFSVR(c, X2std, y2std, X1std, y1std)))
        
    for c in [0.14]:
        print('\nPolynomial SVR (C = {0})'.format(c))
        print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scorePolySVR(c, X1std, y1std, X2std, y2std)))
        print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scorePolySVR(c, X2std, y2std, X1std, y1std)))
        
    for c in [0.08]:
        print('\nSigmoid SVR (C = {0})'.format(c)); 
        print("Train=Boston; Test=Chicago: {0:.3f}, {1:.3f}".format(*scoreSigSVR(c, X1std, y1std, X2std, y2std)))
        print("Train=Chicago; Test=Boston: {0:.3f}, {1:.3f}".format(*scoreSigSVR(c, X2std, y2std, X1std, y1std)))
    
    
def bestFeaturesTest():
    
    # list of all fields
    fields = ['popnear', 'housenear', 'empnear', 'paynear', 'popwalk', 'housewalk', 'empwalk', 'paywalk', 'popdrive', 'housedrive', 'parking',
          '15empnet','30empnet','15housenet','30housenet','15paynet','30paynet','15popnet','30popnet']
    
    # get data
    Xbos, ybos, Xchi, ychi = getData(fields)
    Xbosstd, ybosstd, Xchistd, ychistd = standardize(Xbos, ybos, Xchi, ychi)[:4]
    
    featurescores = []
   
    # loop through all features selecting that feature from X
    for name, i in zip(fields, range(len(fields))):
        #print(i)
        
        Xb = np.reshape(Xbosstd[:,i], (-1,1)); Xc = np.reshape(Xchistd[:,i], (-1,1))
        
        b2cErr1, b2cErr2, b2cCoeff = scoreLsq(Xb, ybosstd, Xc, ychistd)
        c2bErr1, c2bErr2, c2bCoeff = scoreLsq(Xc, ychistd, Xb, ybosstd)
              
        featurescores.append((name, np.mean([b2cErr2,c2bErr2]), *[np.asscalar(i) for i in [b2cCoeff, c2bCoeff]]))

    return featurescores    
    
def simpleTest(): 
    
    fields = ['popnear', 'housenear', 'empnear', 'paynear', 'popwalk', 'housewalk', 'empwalk', 'paywalk', 'popdrive', 'housedrive', 'parking',
          '15empnet','30empnet','15housenet','30housenet','15paynet','30paynet','15popnet','30popnet']
 
    Xbos, ybos, Xchi, ychi = getData(fields)       
    bosFrame, chiFrame = getData(fields, dataframe=True)

     
    #predicted = np.dot(Xtrain, coeff)
    #sstot = sum((ytrain - np.ones(ytrain.shape)*np.mean(ytrain))**2)
    #ssres = sum((ytrain - predicted)**2)
    #sc1 = 1-ssres/sstot
    coeff, resid, rank, s = np.linalg.lstsq(Xbos, ybos)
    predicted = np.dot(Xchi, coeff)
#    sstot = sum((ychi - np.ones(ychi.shape)*np.mean(ychi))**2)
    ssres = sum((ychi - predicted)**2)
    chiFrame['predicted'] = predicted
    
    stationlist = []
    for row in chiFrame.iterrows():
        n, p, a, d1 = row[1]['name'], row[1]['predicted'], row[1]['riders'], row[1]['empnear']
        stationlist.append((n, p, a, (a-p)**2, d1))
        
    stationlist = sorted(stationlist, key=lambda x: x[3])
    for n, p, a, e, d1 in stationlist:
        print("{:<28}{:>8}{:>8}{:>12}{:>8}".format(n, int(p), a, int(e), int(d1)))
    
    #for p, a in zip(predicted, ytest):
    #    print(["{0:.0f}".format(x) for x in [a, np.mean(ytest), p, (a-np.mean(ytest))**2, (a-p)**2]], np.sign((a-p)**2 - (a-np.mean(ytest))**2))    
    
    #print(sum(np.sign((ytest - predicted)**2 - (ytest - np.ones(ytest.shape)*np.mean(ytest))**2)))
    #print(sstot)
    print(ssres)
    for n, c in zip(fields, coeff):
        print("{:<10}{}".format(n, c))
        
        

#simpleTest()
#bestFeaturesTest()
test1stOrder()