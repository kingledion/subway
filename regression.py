#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 20:30:19 2017

@author: dhartig
"""

import pandas as pd


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