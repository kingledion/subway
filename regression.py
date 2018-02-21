#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 20:30:19 2017

@author: dhartig
"""

import pandas as pd, itertools, numpy as np, re
from sklearn import metrics
from matplotlib import pyplot as plt



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


def scoreAllCV(plotfunc, allcols):  
    
    for col in allcols:
        
        cols = [col]
        
        print("\n>>> Analyzing", cols, "\n")
        
        scores = []
        allscores = []
        allreal = []
        allpred = []
        
        
        combs = list(itertools.combinations(citylist, r=5))
        for l1, l2 in zip(combs, [set(citylist) - set(c) for c in combs]):
            print('Train:', l1, 'Test:', l2)
            df1 = loadData(l1)
            df2 = loadData(l2)
            
            if re.search(col, '*'):
                first, second = col.split('*')
                df1[col] = df1[first] * df1[second]
                df2[col] = df2[first] * df2[second]
            
            Xtrain = df1[cols]
            ytrain = df1['riders']
            
            Xtest = df2[cols]
            ytest = df2['riders']
            
    
            
            coeflist, y_pred = plotfunc(cols, Xtrain, ytrain, Xtest, ytest) # unused is coefficients not used
                   
    
    
            #for name, near, predicted, actual in zip(df2['name'], nearscore, y_pred, ytest):
            #    print("{0:28} {1:8} {2:8} {3:8}".format(name, int(near), int(predicted), actual))
            scores.append(metrics.r2_score(ytest, y_pred))
            print("Coeff {0:.4f}; Pseudo R^2: {1:.4f}".format(coeflist[0], scores[-1]))
            
            if len(cols) == 1:
                allscores.extend(df2[cols].values)
                allreal.extend(ytest)
                allpred.extend(y_pred)
                
        print("Summary score: ", np.mean(scores))
    
            
        if len(cols) == 1:
            diff = np.array(allpred) - np.array(allreal)
            plt.errorbar(allscores, allreal, yerr=[np.zeros(diff.shape), diff], fmt='bx', ecolor='r')
            plt.plot(allscores, allpred, 'rx')
            plt.show()
            

    
    
    
        
    return scores
