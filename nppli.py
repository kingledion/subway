#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 17:53:02 2018

@author: dhartig
"""

import numpy as np

def ipsolver(X, y, eps = 1e-10):
    
    
    def objective(X, y, beta):
        return np.sum(X @ beta) - np.sum(y @ np.log(X @ beta))

    def gradient(X, y, beta):
        #print("Grad in:", X.shape, y.shape, beta.shape)
        dinv = np.diag(1/(X @ beta))
        #print("dinv:", dinv.shape)
        return -1*np.sum(X.T @ (dinv * (y - X @ beta)), axis=1)
    
    def hessian(X, y, beta):
        dinv = np.diag(1/(X @ beta))
        return X.T @ (y * dinv**2 ) @ X
    
    # no error checking!
    X = np.array(X)
    y = np.array(y)
    
    p = X.shape[1] # number of columns
    n = X.shape[0] # number of rows
    if len(y) != n:
        print("X and y do not match in dimensions")
        return False
    
    #print(X.shape, y.shape)
    
    beta = np.array([i if i>= 0 else eps for i in X.T @ y])
    lamb = 1 / beta
    mu = 10   # why?
    sigma = 0.95
    kappa = 0.01
    eta = sum(beta * lamb) # = # columns of X = len(beta) = p
    
    CONVERGE = False
    
    while not CONVERGE:
        
        #print('Convergence Loop')
        #print("Beta:", beta)
        #print("Lambda:", lamb)
        
        
        
        gamma = p*mu/eta  # = mu while eta = p
        #print(X.shape, y.shape, beta.shape)
        rdual = gradient(X, y, beta) - lamb
        rcent = lamb * beta - 1/gamma
        #print(g.shape, rdual.shape, rcent.shape)
        normold = np.sqrt(np.sum([rdual**2, rcent**2]))
        hess = hessian(X, y, beta)
        hess = hess + np.diag(lamb/beta)
        
        rhs_beta = -1*rcent/beta - rdual
        DD = np.diag(1/np.diag(hess))
        hess = hess @ DD
        del_beta = np.linalg.solve(hess, rhs_beta) * np.diag(DD)
        
        del_lambda = (-rcent - lamb * del_beta)/beta
        
        FINISHED = False
        stepsize = -lamb / del_lambda
        #print("delta beta, delta lambda and stepsize")
        #print(del_beta)
        #print(del_lambda)

        if any([i > 0 for i in stepsize]):
            stepsize = 0.99 * min([i for i in stepsize if i > 0])
        else:
            stepsize = 0.99
        
        while (not all ([i > 0 for i in beta + stepsize * del_beta])):
            stepsize = stepsize * sigma
            
        #print(stepsize)
                
        while (not FINISHED):
            beta = beta + stepsize * del_beta
            rdual = gradient(X, y, beta) - lamb + stepsize * del_lambda
            rcent = (lamb + stepsize * del_lambda)*beta - 1/gamma
            normnew = np.sqrt(np.sum([rdual**2, rcent**2]))
            if normnew < (1 - kappa*stepsize) * normold:
                FINISHED = True
            else:
                stepsize = stepsize * sigma
            if stepsize < 0.5 * eps:
                print("Cancelled stepsize selection")
                FINISHED = True
                CONVERGE = True
                #exit()
                
            #print("Finished loop")
            #print(beta)
            #print(lamb + stepsize * del_lambda)
        
        lamb = lamb + stepsize * del_lambda
        
        eta = sum(beta * lamb)
        if np.sqrt(np.sum(rdual**2)) < eps and eta < eps:
            CONVERGE = True
    
    ret = np.array([b if b > eps else 0 for b in beta])
    #print(ret)
    return ret
            
            
        
        
        

    

if __name__ == "__main__":
    
    X =  np.array([[0.30921275, 0.1639936, 0.32987366, 0.1521676, 0.10684073],
          [0.17249929, 0.4750078, 0.17943217, 0.3836358, 0.28166518],
          [0.23319490, 0.1418882, 0.38561522, 0.1968013, 0.50590085],
          [0.50298512, 0.1779079, 0.38381037, 0.4568122, 0.20863101],
          [0.58547021, 0.3941782, 0.35733173, 0.2196384, 0.02525606],
          [0.37268724, 0.3931057, 0.38063653, 0.2595784, 0.46842405],
          [0.03192279, 0.4767289, 0.15030169, 0.2757356, 0.15306851],
          [0.20316094, 0.2770893, 0.29683695, 0.3696765, 0.33493901],
          [0.20653092, 0.2459795, 0.01397448, 0.3478179, 0.48448527],
          [0.02525816, 0.1456942, 0.42368594, 0.3646511, 0.13924143]])
    
    beta = np.array([10, 10, 0, 0, 0])
    
    y = np.array([2, 9, 4, 6, 20, 15, 4, 3, 5, 1])
    
    #print(X)
    #print()
    #print(y)
    #print()
    #print(beta)
    
    b = ipsolver(X, y, objective, gradient, hessian)
    print('Output')
    print(b)
