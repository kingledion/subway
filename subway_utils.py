# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 18:14:33 2016

@author: dhartig
"""
from math import sqrt, radians, cos, sin, asin
import numpy as np, mysql.connector, warnings


# List of all data fields being filled with census data. MySQL data type is 'INT'.
feature_names = ['population', 
                  'pop_child', 
                  'pop_old', 
                  'household', 
                  'family', 
                  'house_w_child',
                  'bachelors',
                  'labor_force',
                  'employed',
                  'emp_full_time',
                  'pop_poor',
                  'pop_rich',
                  'employment', 
                  'emp_pay', 
                  'medical',
                  'hospitality', 
                  'university', 
                  'finance', 
                  'business', 
                  'entertainment',
                  'hunits',
                  'hunits_vacant',
                  'hunits_detached',
                  'hunits_attached', 
                  'hunits_medium',
                  'hunits_large',
                  'hunits_old',
                  'hunits_new',
                  'hunits_owner',
                  'hunits_renter']

def get_feature_names():
    return feature_names
                  
def get_zip_counts(zcodes):
    db, cursor = opendb()
    
    query= "SELECT zipcode, area, {0} from zipcodes where zipcode in ({1});"
    density_fields = ", ".join(feature_names)
    zip_list = ", ".join([str(z) for z in zcodes])
    
    counts, areas = {}, {}
    cursor.execute(query.format(density_fields, zip_list))
    for row in cursor.fetchall():
        zcode = row[0]
        areas[zcode] = row[1]
        counts[zcode] = {}
        for key, data in zip(feature_names, row[2:]):
            counts[zcode][key] = data
            
    # Format of results is a dictionary keyed by zipcode. The value of each zipcode
    # dictionary, keyed by field. A call to results[zcode][field_name] will yield
    # the density of field_name within that zipcode.
            
    return counts, areas
                    
    
        
def opendb():
    db = mysql.connector.connect(user='dbuser', password='dbpass', database='zipcode')
    cursor = db.cursor()
    return db, cursor


    
# vectorize!
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
                
                
    # convert to numpy arrays -> convets scalars to vectors
    lon1, lat1, lon2, lat2 = map(np.array, [lon1, lat1, lon2, lat2])
    
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(np.deg2rad, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.square(np.sin(dlat/2)) + np.cos(lat1) * np.cos(lat2) * np.square(np.sin(dlon/2))
    dist = 2 * np.arcsin(np.sqrt(a)) * r

    return dist
    
def std_features(X, mean, std):
    X = X - mean
    with warnings.catch_warnings():
        warnings.filterwarnings('error')
        try:
            X = X/std
        except Warning as warn:
            X = np.nan_to_num(X)
    return(X)
    

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




    
