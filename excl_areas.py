#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 10 18:42:56 2018

@author: dhartig
"""

# Accidentally typed the points in backwards! This is how we reverse them
def rev_points(lst):   
    return [(lon, lat) for lat, lon in lst]

def getPoints(name):
    if name == 'Boston':
        return [rev_points(l) for l in bos_points]
    if name == 'Chicago':
        return [rev_points(l) for l in chi_points]
    return []

# Areas where there is no development (water, parks, etc)
chi_points  = [ # 60611, water and purification plant above navy pier
                [(41.9043, -87.6235), (41.9021, -87.6214), (41.9013, -87.6194), (41.8923, -87.6133),
                 (41.8924, -87.5950), (41.9050, -87.5984)],
            # Monroe Harbor and parks east of Columbus Drive
                [(41.8908, -87.6136), (41.8844, -87.6134), (41.8844, -87.6206), (41.8676, -87.6204),
                 (41.8677, -87.5923), (41.8908, -87.5923)],
            # Northerly Island and Burnham Harbor
                [(41.8634, -87.6131), (41.8562, -87.6131), (41.8501, -87.6092), (41.8501, -87.5969),
                 (41.8634, -87.5969)]
                ]
bos_points = [
            # Boston Harbor by aquarium
                [(42.3544, -71.0493), (42.3549, -71.0504), (42.3561, -71.0499), (42.3577, -71.0495),
                 (42.3589, -71.0502), (42.3630, -71.0508), (42.3640, -71.0494), (42.3672, -71.0509), 
                 (42.3678, -71.0541), (42.3683, -71.0576), (42.3715, -71.0529), (42.3694, -71.0441), 
                 (42.3552, -71.0453)]     
            ]