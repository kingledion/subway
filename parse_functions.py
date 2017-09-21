# -*- coding: utf-8 -*-
"""
Created on Sat Sep 16 13:51:56 2017

@author: dhartig
"""
import csv, re

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
    with open('./sourcedata/zip_population.csv', 'r') as f: 
        rdr = csv.reader(f, delimiter=',')
        next(rdr) # not using a dictreader, skip the column headers
    
        for line in rdr:
            data[line[0]] = {'pop': int(line[1])}
    
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
           
            data[zcode] = {'name': name, 'emp': emp, 'emp_pay': emp_pay}
           
    return data
   
def read_geography():
    data = {}
    with open('./sourcedata/zip_geography.txt', 'r') as f:
        rdr = csv.reader(f, delimiter = '\t')
        next(rdr)
        
        for line in rdr:
            data[line[0]] = {'area': float(line[1]) / 1000000, 'location': "ST_GEOMFROMTEXT('POINT({0} {1})')".format(line[6].rstrip("\n"), line[5])}
    
    return data


def read_households():
    data = {}
    with open('./sourcedata/ACS_15_5YR_B11011_with_ann.csv', 'r') as f:
        rdr = csv.reader(f, delimiter = ',', quotechar = '"')
        next(rdr)
        next(rdr)
        
        for line in rdr:
            data[line[1]] = {'households': int(line[3])}

    return data

def read_establishments():
    return parse_by_establishment('./sourcedata/Establishments_by_zip_15.csv', 'estab')
    
def read_universities():
    return parse_by_establishment('./sourcedata/University_by_zip_15.csv', 'uni')
    
def read_hospitals():
    return parse_by_establishment('./sourcedata/Hospital_by_zip_15.csv', 'hosp')

def read_finance():
    return parse_by_establishment('./sourcedata/Finance_by_zip_15.csv', 'fin')
    
def read_business():
    return parse_by_establishment('./sourcedata/Business_by_zip_15.csv', 'bus')

def read_entertainment():
    return parse_by_establishment('./sourcedata/Entertainment_by_zip_15.csv', 'ent')
    

    
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
                loop_data[store_codes[line[1]]] = loop_data.get(store_codes[line[1]], 0) + int(line[3])
            elif line[1] in est_codes:
                loop_data['{0}_sum'.format(tag)] = loop_data.get('{0}_sum'.format(tag), 0) + int(line[3]) * est_codes[line[1]]
                
        if '{0}_sum'.format(tag) in loop_data and loop_data['{0}_sum'.format(tag)] > 0:
            if zcode in data:
                data[zcode].update(loop_data)
            else:
                data[zcode] = loop_data
        
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
            
            onek_est = max(int((vals['emp'] - estab_sum)/estab_1k), 1000) if estab_1k else 0
            
            vals['hospital'] = hosp_sum + hosp_1k * onek_est
            vals['university'] = uni_sum + uni_1k * onek_est   
            vals['finance'] = fin_sum + fin_1k * onek_est  
            vals['business'] = bus_sum + bus_1k * onek_est  
            vals['entertainment'] = ent_sum + ent_1k * onek_est  
            
            new_data[zcode] = vals
                        
    return new_data
        
        
            
            
        
        
        
    
    
    
    
    
    
    
            