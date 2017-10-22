# -*- coding: utf-8 -*-
"""
Created on Sat Sep 16 13:51:56 2017

@author: dhartig
"""
import csv, re, shapefile

# Based on BP_2015_00CZ1.tzt from American Factfinder; used for Employment_by_zip_15
translate = {'a': 10, 'b': 60, 'c': 175, 'e': 375, 'f': 750, 'g': 1750, 'h': 3750, 'i': 7500, 'j': 17500, 'k': 37500, 'l': 75000}


# Helper function to parse zip code out of US Census bureau GEO.id
def zip_from_geoid(geoid):
    mtch = re.match("\d+US(\d{5})", geoid)
    if mtch:
        return mtch.group(1)
    return None



# All parse functions must start with 'read_'. All functions must return a dict with key = zipcode
# and val = another dict with key, vals of whatever data. There is no checking to ensure keys on the inner 
# dict do not collide. 
def read_population():
    data = {}
    with open('./sourcedata/Population_by_zip_15.csv', 'r') as f: 
        rdr = csv.reader(f, delimiter = ',', quotechar = '"')
        next(rdr) # not using a dictreader, skip the column headers
    
        for line in rdr:
            zcode = zip_from_geoid(line[0])
            data[zcode] = {'population': int(line[1]), 'pop_child': int(line[1]) - int(line[2]), 'pop_old': int(line[3])}
    
    return data
    
def read_employment():
    data = {}
    with open('./sourcedata/Employment_by_zip_15.csv', 'r') as f:
        rdr = csv.reader(f, delimiter = ',', quotechar = '"')
        next(rdr) # not using a dictreader, skip the column headers
        next(rdr) # Two lines of headers
        
        for line in rdr:
            zcode = zip_from_geoid(line[0])
            name = re.match("ZIP \d{5} \((.*)\)", line[1]).group(1)
                       
            if line[4] == 'D' or line[3] == 'S':
                emp = translate[line[3]]
                emp_pay = emp * 40
            else:
                emp = int(line[3])
                emp_pay = int(line[5])
           
            data[zcode] = {'name': name, 'employment': emp, 'emp_pay': emp_pay}
           
    return data
   
def read_geography():
    data = {}
    sf = shapefile.Reader("/opt/ziplfs/tl_2014_us_zcta510.shp")
    for r in sf.records():
        zcode, area, lat, lon = (r[i] for i in [0, 5, 7, 8])
        data[zcode] = {'area': float(area)/1000000, 'location': "ST_GEOMFROMTEXT('POINT({0} {1})')".format(float(lat), float(lon))} 
    return data


def read_households():
    data = {}
    with open('./sourcedata/Households_by_zip_15.csv', 'r') as f:
        rdr = csv.reader(f, delimiter = ',', quotechar = '"')
        next(rdr) # not using a dictreader, skip the column headers
        
        for line in rdr:
            zcode = zip_from_geoid(line[0])
            data[zcode] = {'household': int(line[1]), 'family': int(line[2]), 'house_w_child': int(line[3])}

    return data
    
def read_poverty():
    data = {}
    with open('./sourcedata/Poverty_by_zip_15.csv', 'r') as f:
        rdr = csv.reader(f, delimiter = ',', quotechar = '"')
        next(rdr) # not using a dictreader, skip the column headers
        
        for line in rdr:
            zcode = zip_from_geoid(line[0])
            data[zcode] = {'bachelors': int(line[2]), 
                            'labor_force': int(line[3]), 
                            'employed': int(line[4]),
                            'emp_full_time': int(line[5]),
                            'pop_poor': int(line[6]),
                            'pop_rich': int(line[1]) - int(line[7])}

    return data
    
    
    

def read_establishments():
    return parse_by_establishment('./sourcedata/Establishments_by_zip_15.csv', 'estab')
    
def read_universities():
    return parse_by_establishment('./sourcedata/University_by_zip_15.csv', 'uni')
    
def read_medical():
    return parse_by_establishment('./sourcedata/Medical_by_zip_15.csv', 'med')

def read_finance():
    return parse_by_establishment('./sourcedata/Finance_by_zip_15.csv', 'fin')
    
def read_business():
    return parse_by_establishment('./sourcedata/Business_by_zip_15.csv', 'bus')

def read_entertainment():
    return parse_by_establishment('./sourcedata/Entertainment_by_zip_15.csv', 'ent')
    
def read_hospitality():
    return parse_by_establishment('./sourcedata/Hospitality_by_zip_15.csv', 'hosp')
    

    
def parse_by_establishment(fname, tag):
    store_codes = {'260': '{0}_1k'.format(tag)}
    est_codes = {'212': 2, '220': 7, '230': 15, '241': 37, '242': 75, '251': 175, '252': 375, '254': 750}  
    
    data = {}
    
    with open(fname, 'r') as f:
        rdr = csv.reader(f, delimiter = ',', quotechar = '"')
        next(rdr) # not using a dictreader, skip the column headers
        
        last_zip = ""
        loop_data = {}
        
        for line in rdr:
            zcode = zip_from_geoid(line[0])
            if zcode != last_zip:
                if '{0}_sum'.format(tag) in loop_data and (loop_data['{0}_sum'.format(tag)] or loop_data['{0}_1k'.format(tag)]):
                    if last_zip in data:
                        data[last_zip].update(loop_data)
                    else:
                        data[last_zip] = loop_data
                # reset for next zip code
                last_zip = zcode
                loop_data = {}
            if line[1] in store_codes:
                loop_data[store_codes[line[1]]] = loop_data.get(store_codes[line[1]], 0) + int(line[2])
            elif line[1] in est_codes:
                loop_data['{0}_sum'.format(tag)] = loop_data.get('{0}_sum'.format(tag), 0) + int(line[2]) * est_codes[line[1]]
                
        if '{0}_sum'.format(tag) in loop_data and loop_data['{0}_sum'.format(tag)] > 0:
            if zcode in data:
                data[zcode].update(loop_data)
            else:
                data[zcode] = loop_data
        
    return data
    
def read_housing():
    data = {}
    with open('./sourcedata/Housing_by_zip_15.csv', 'r') as f:
        rdr = csv.reader(f, delimiter = ',', quotechar = '"')
        next(rdr) # not using a dictreader, skip the column headers
        
        for line in rdr:
            zcode = zip_from_geoid(line[0])
            data[zcode] = {'hunits': int(line[1]), 
                            'hunits_vacant': int(line[2]), 
                            'hunits_detached': int(line[3]),
                            'hunits_attached': int(line[4]) + int(line[5]),
                            'hunits_medium': int(line[6]) + int(line[7]), # 3-9 units per housing structure
                            'hunits_large': int(line[8]) + int(line[9]), # 10+ units per housing structure
                            'hunits_old': int(line[19]), # built 1939 or before
                            'hunits_new': int(line[10]) + int(line[11]) + int(line[12]), #built 2000 or later
                            'hunits_owner': int(line[20]),
                            'hunits_renter': int(line[21])}
                            #'hunits_mortgage': int(line[22])} Thats dumb

    return data
        



def postproc_establishments(old_data):
    new_data =  {}
    for zcode, vals in old_data.items():
            
        if 'name' in vals:
               
            estab_sum = vals.pop('estab_sum', 0)
            estab_1k = vals.pop('estab_1k', 0)
            hosp_sum = vals.pop('hosp_sum', 0)
            hosp_1k = vals.pop('hosp_1k', 0)
            uni_sum = vals.pop('uni_sum', 0)
            uni_1k = vals.pop('uni_1k', 0)
            fin_sum = vals.pop('fin_sum', 0)
            fin_1k = vals.pop('fin_1k', 0)
            bus_sum = vals.pop('bus_sum', 0)
            bus_1k = vals.pop('bus_1k', 0)
            ent_sum = vals.pop('ent_sum', 0)
            ent_1k = vals.pop('ent_1k', 0)
            med_sum = vals.pop('med_sum', 0)
            med_1k = vals.pop('med_1k', 0)
            
            onek_est = max(int((vals['employment'] - estab_sum)/estab_1k), 1000) if estab_1k else 0
            
            vals['hospitality'] = hosp_sum + hosp_1k * onek_est
            vals['university'] = uni_sum + uni_1k * onek_est   
            vals['finance'] = fin_sum + fin_1k * onek_est  
            vals['business'] = bus_sum + bus_1k * onek_est  
            vals['entertainment'] = ent_sum + ent_1k * onek_est  
            vals['medical'] = med_sum + med_1k * onek_est
            
            new_data[zcode] = vals
                        
    return new_data
        
        
            
            
        
        
        
    
    
    
    
    
    
    
            