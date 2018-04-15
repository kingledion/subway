#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 19 21:01:35 2018

@author: dhartig
"""

import numpy as np, sklearn.linear_model as lm
from sklearn.metrics import r2_score
from regression import loadData, citylist
from matplotlib import pyplot as plt



if __name__ == "__main__":
    # get all features
    df = loadData(citylist, droptransfer=True)    
    
    pops = df.as_matrix(['near_population'])
    emp = df.as_matrix(['near_employment'])
    riders = df.as_matrix(['riders'])
    
    xpop = np.array([x for x in range(1, int(max(pops)))]).reshape(-1,1)
    xemp = np.array([x for x in range(1, int(max(emp)))]).reshape(-1,1)
    
    
    # population regressions - Linear
    poplin = lm.LinearRegression().fit(pops, riders)
    xpoplin = poplin.predict(xpop)
    
    
    # Power
    lnpops = np.log(pops)
    lnriders = np.log(riders)
    lnxpop = np.log(xpop)
    poppow = lm.LinearRegression().fit(lnpops, lnriders)
    xpoppow = np.exp(poppow.predict(lnxpop))
    
    # log
    poplog = lm.LinearRegression().fit(lnpops, riders)
    xpoplog = poplog.predict(lnxpop)
    
    
    
    # plot pop regressions
    plt.plot(pops, riders, 'k.', alpha = 0.25)
    plt.plot(xpop, xpoplin, 'r-', xpop, xpoplog, 'b-')
    plt.xlabel("Nearby Population")
    plt.ylabel("Average Weekday Ridership")
    plt.show()
    
    
    # pop residuals
    linresid = riders - poplin.predict(pops)
    powresid = riders - np.exp(poppow.predict(lnpops))
    logresid = riders - poplog.predict(lnpops)
    
    print("Linear model:", r2_score(riders, poplin.predict(pops)))
    print("Power model:", r2_score(riders, np.exp(poppow.predict(lnpops))))
    print("Log model:", r2_score(riders, poplog.predict(lnpops)))
    print()
    
    
    plt.plot(pops, linresid, 'r.', alpha = 0.25)
    plt.plot(xpop, np.zeros(len(xpop)), 'k-', alpha = 0.5)
    plt.xlabel("Nearby Population")
    plt.ylabel("Residual from Linear Regression")
    plt.show()
    
    plt.plot(pops, logresid, 'b.',  alpha = 0.25)
    plt.plot(xpop, np.zeros(len(xpop)), 'k-', alpha = 0.5)
    plt.xlabel("Nearby Population")
    plt.ylabel("Residual from Log Regression")
    plt.show()
    
    #vals, base = np.histogram(linresid, bins=100)
    plt.hist(linresid, bins='auto')
    plt.xlabel("Distribution of Residuals from Population Linear Regression")
    plt.show()
    
    
    
    # employment regressions - Linear
    emplin = lm.LinearRegression().fit(emp, riders)
    xemplin = emplin.predict(xemp)
    
    
    # Power
    lnemp = np.log(emp)
    lnriders = np.log(riders)
    lnxemp = np.log(xemp)
    emppow = lm.LinearRegression().fit(lnemp, lnriders)
    xemppow = np.exp(emppow.predict(lnxemp))
    
    # log
    emplog = lm.LinearRegression().fit(lnemp, riders)
    xemplog = emplog.predict(lnxemp)
    
        # plot pop regressions
    plt.plot(emp, riders, 'k.', alpha = 0.25)
    plt.plot(xemp, xemplin, 'r-', xemp, xemplog, 'b-')
    plt.xlabel("Nearby Employment")
    plt.ylabel("Average Weekday Ridership")
    plt.show()
    
    
    # pop residuals
    linresid = riders - emplin.predict(emp)
    powresid = riders - np.exp(emppow.predict(lnemp))
    logresid = riders - emplog.predict(lnemp)
    
    print("Linear model:", r2_score(riders, emplin.predict(emp)))
    print("Power model:", r2_score(riders, np.exp(emppow.predict(lnemp))))
    print("Log model:", r2_score(riders, emplog.predict(lnemp)))
    print()
    
    
    plt.plot(emp, linresid, 'r.', xemp, np.zeros(len(xemp)), 'k-', alpha = 0.25)
    plt.plot( xemp, np.zeros(len(xemp)), 'k-', alpha = 0.5)
    plt.xlabel("Nearby Employment")
    plt.ylabel("Residual from Linear Regression ")
    plt.show()
    
    plt.plot(emp, logresid, 'b.', xemp, np.zeros(len(xemp)), 'k-', alpha = 0.25)
    plt.plot(xemp, np.zeros(len(xemp)), 'k-', alpha = 0.5)
    plt.xlabel("Nearby Employment")
    plt.ylabel("Residual from Log Regression")
    plt.show()
    
    plt.hist(linresid, bins='auto')
    plt.xlabel("Distribution of Residuals from Employment Linear Regression")
    plt.show()
    
    