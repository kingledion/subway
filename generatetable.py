#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 15 18:37:28 2018

@author: dhartig
"""

import csv

with open("/opt/school/subway/final_report/featurereport.csv", "r") as csvin:
    
    rdr = csv.reader(csvin)
        
    for var, desc, linlas, linbf, loglas, logbf, ladlas, ladbf, extra in rdr:
        var = var.replace("_", "\\_")
        
        print("&".join([var, desc] + ["x" if x=="1" else "" for x in [linlas, linbf, loglas, logbf, ladlas, ladbf]]) + "\\\\")
    
    