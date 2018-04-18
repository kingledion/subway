#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 17:53:02 2018

@author: dhartig
"""

import nump as np

def ols(X, y, intercept = True):
    
    # Verify that X can be transformed to a numpy array, and that it is a 2-d array (n x p)
    try:
        X = np.array(X)
    except Exception as e:
        raise TypeError('Unable to convert X to numpy array')
        
    # Verify that Y can be transformed to a numpy array, that it is 1-d, of size (p x 1)
    try:
        y = np.array(y)
    except Exception as e:
        raise TypeError('Unable to convert y to numpy array')
        
        