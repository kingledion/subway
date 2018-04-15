#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 08:20:19 2018

@author: dhartig
"""

from regression import loadData, citylist
from matplotlib import pyplot as plt
import statsmodels.api as sm, numpy as np, sklearn.linear_model as lm, sklearn.metrics as metrics, pandas as pd
from statsmodels.regression.quantile_regression import QuantReg
#from sklearn.preprocessing import StandardScaler
#from pyglmnet import GLM
import glmnet_python
from glmnet import glmnet; from glmnetPredict import glmnetPredict; from glmnetCoef import glmnetCoef
from cvglmnet import cvglmnet; from cvglmnetPredict import cvglmnetPredict; from cvglmnetCoef import cvglmnetCoef

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
#     linear regression
#     for i in range(10):
#         print("Pseudo-R^2:", i,  metrics.r2_score(ytest, y_pred[i]))
#     
#     plt.plot(ytest, y_pred[0], 'bx')
#     plt.plot(ytest, ytest, 'r.')
#     plt.show()
# =============================================================================

    
def poissonPlot(cols, Xtrain, ytrain, Xtest, ytest):
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest)
    
    model = sm.GLM(ytrain, Xtrain, family=sm.families.Poisson(), link =sm.families.links.identity())
    results = model.fit()
    
    return results.predict(Xtest)


def linearPlot(cols, Xtrain, ytrain, Xtest, ytest):
    
    Xtrain = sm.add_constant(Xtrain)
    Xtest = sm.add_constant(Xtest)
    
    #print(ytrain.shape, Xtrain.shape)
    
    #model = sm.GLM(ytrain, Xtrain, family=sm.families.Gaussian())
    #results = model.fit()
    model = QuantReg(ytrain, Xtrain)
    results = model.fit(q=0.5)
    
    #print("Coefficient:", results.params[cols].values)
       
    return results.predict(Xtest)


if __name__ == "__main__":
    
    df = loadData(citylist, droptransfer=True)    
    #cols = list(df.columns.difference(['lat', 'lon', 'name', 'riders'])) 
    cols = ['near_population', 'near_employment']
    
    l2 = set(['boston'])
    l1 = set(citylist) - l2
    print(l2)
    
    df1 = loadData(l1, droptransfer=True)
    df2 = loadData(l2, droptransfer=True)
    
    Xtrain = df1[cols]
    ytrain = df1['riders']
    
    Xtest = df2[cols]
    ytest = df2['riders']
    
    Xtrain = np.array(Xtrain, dtype='float64')
    ytrain = np.array(ytrain, dtype='float64')
    Xtest = np.array(Xtest, dtype='float64')
    
    fit = cvglmnet(x=Xtrain.copy(), y=ytrain.copy(), alpha=1, family = 'Poisson')
    coef = cvglmnetCoef(fit, s = "lambda_1se")
    
    #Xtrain = sm.add_constant(Xtrain)
    #Xtest = sm.add_constant(Xtest)
    
    #model = sm.GLM(ytrain, Xtrain, family=sm.families.Poisson())#, link =sm.families.links.identity())
    #results = model.fit()
    
    print("Parameters")
    print(coef)
    
    ## Replace maxima of test with maximum of train
    ('Xtrain')
    maxs = np.amax(Xtrain, axis=0)
    Xtest = np.clip(Xtest, 0, maxs)
    
    pred = cvglmnetPredict(fit, Xtest, ptype='response', s="lambda_1se")
    err = pred.flatten() - ytest
    
    names = df2['name']    
    out = pd.DataFrame({"Names": names, "Predicted": pred.flatten(), "Actual": ytest, "Error": err}, columns = ["Names", "Predicted", "Actual", "Error"])
    
    print(out)
    
    stat_err = np.sum(np.abs(pred.flatten() - ytest))/np.sum(ytest)
    sys_err = np.abs(np.sum(pred)-np.sum(ytest))/np.sum(ytest)
    print(sys_err, stat_err)
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    


    

    
    