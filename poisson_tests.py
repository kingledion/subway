#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 08:20:19 2018

@author: dhartig
"""

from regression import loadData, citylist, scoreAllCV
from matplotlib import pyplot as plt
import statsmodels.api as sm, numpy as np,  sklearn.metrics as metrics
#from sklearn.preprocessing import StandardScaler
#from pyglmnet import GLM
import glmnet_python
from glmnet import glmnet; from glmnetPlot import glmnetPlot; from glmnetCoef import glmnetCoef
from glmnetPredict import glmnetPredict; from glmnetPrint import glmnetPrint

def poissonNet(cols, Xtrain, ytrain, Xtest, ytest):
    
    Xtrain = np.array(Xtrain, dtype='float64')
    ytrain = np.array(ytrain, dtype='float64')
    Xtest = np.array(Xtest, dtype='float64')
    ytest = np.array(ytest, dtype='float64')
    
    fit = glmnet(x=Xtrain, y=ytrain, family='poisson')
    coef = glmnetCoef(fit, s = np.array([1.0], dtype='float64'))
    notcoef = [name for c, name in zip(coef, ['intercept'] + cols) if c == 0]
      
    y_pred = glmnetPredict(fit, Xtest, ptype='response', s = np.array([1.0], dtype='float64'))

    return notcoef, y_pred
    
    

# =============================================================================
# def poissonNet2(Xtrain, ytrain, Xtest, ytest):
#     scaler = StandardScaler().fit(Xtrain)
#        
#     glm = GLM(distr='poisson', alpha=1)
#     glm.fit(scaler.transform(Xtrain), ytrain)
#     y_pred = glm.predict(scaler.transform(Xtest))
#     
#     print(y_pred[0])
#     print(y_pred.size, ytest.size)
#     
#     for i in range(10):
#         print("Pseudo-R^2:", i,  metrics.r2_score(ytest, y_pred[i]))
#     
#     plt.plot(ytest, y_pred[0], 'bx')
#     plt.plot(ytest, ytest, 'r.')
#     plt.show()
# =============================================================================
    
    
def poissonPlot(cols, Xtrain, ytrain, Xtest, ytest):
    
    model = sm.GLM(ytrain, Xtrain, family=sm.families.Poisson())
    results = model.fit()
    
    return [],  results.predict(Xtest)


def linearPlot(cols, Xtrain, ytrain, Xtest, ytest):
    
    model = sm.GLM(ytrain, Xtrain, family=sm.families.Gaussian())
    results = model.fit()
    
    return [], results.predict(Xtest)

df = loadData(citylist)    
#cols = list(df.columns.difference(['lat', 'lon', 'name', 'riders']))  
cols = ['near_population', 'near_employment']  
scoreAllCV(linearPlot, cols)
    
    