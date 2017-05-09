import mysql.connector, csv, subway_utils as su
from subway_assignments import zip_assigns

translate = {'A': 10, 'B': 60, 'C': 175, 'E': 375, 'F': 750, 'G': 1750, 'H': 3750, 'I': 7500, 'J': 17500, 'K': 37500, 'L': 75000, 'M': 125000}

#################################################################
# NOTE
#   Requires mysql installed on your computer using the standard ports
#   For mysql, create a database named 'zipcode' and a user 
#   with username 'dbuser' and password 'dbpass'. This user must be 
#   given 'GRANT ALL ON zipcode'.
#   Alternately, make your own username, password, and database and 
#   enter into the connect statements (copy paste should suffice)

def main():
    sqlhaversine()
    data = read_files()
    data = assign_zips(data)
    insert_data(data)
    fix_no_geo_data()
    merge_smalls() 
    #gen_adjacents()
    
    
def sqlhaversine():

    zip_db = mysql.connector.connect(user='dbuser', password='dbpass', database='zipcode')
    zip_cursor = zip_db.cursor()
        
    zip_cursor.execute("DROP FUNCTION IF EXISTS haversine;")
    sql = "CREATE FUNCTION haversine(lat1 FLOAT, lon1 FLOAT, lat2 FLOAT, lon2 FLOAT) RETURNS FLOAT NO SQL DETERMINISTIC COMMENT "
    sql += "'Returns the distance in degrees on the Earth between two known points of latitude and longitude' BEGIN "
    sql += "RETURN DEGREES(ACOS(COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * COS(RADIANS(lon2) - RADIANS(lon1)) + SIN(RADIANS(lat1)) * SIN(RADIANS(lat2))));"
    sql += "END;"
    
    zip_cursor.execute(sql)
    zip_db.commit()
    
    
def read_files():
    data = {}
    
    # open the database
    zip_db = mysql.connector.connect(user='dbuser', password='dbpass', database='zipcode')
    zip_cursor = zip_db.cursor()
    
    try:
        zip_cursor.execute("DROP TABLE zipcodes;")
    except mysql.connector.errors.ProgrammingError as e:
        pass
        
    
    query = "CREATE TABLE zipcodes (zip_code VARCHAR(8) NOT NULL PRIMARY KEY, name VARCHAR(32), pop INT,"
    query += " emp INT, emp_pay INT, area FLOAT, location POINT, households INT)"
    zip_cursor.execute(query)
    
    with open('./sourcedata/zip_population.csv', 'r') as f: 
        rdr = csv.reader(f, delimiter=',')
        next(rdr) # not using a dictreader, skip the column headers
    
        for line in rdr:
            data[line[0]] = {'pop': int(line[1])}
        
    print('read population')
    
    	
    with open('./sourcedata/zip_employment.txt', 'r') as f:
        rdr = csv.reader(f, delimiter = ',', quotechar = '"')
        next(rdr) # not using a dictreader, skip the column headers
        
        for line in rdr:
    
            if line[3] == 'D' or line[3] == 'S':
                emp = translate[line[2]]
                emp_pay = emp * 60
            else:
                emp = int(line[4])
                emp_pay = int(line[8])
               
            d = data.get(line[0], {})
            d.update({'name': line[1], 'emp': emp, 'emp_pay': emp_pay})
            data[line[0]] = d
                
    print('read employment')    
    
    with open('./sourcedata/zip_geography.txt', 'r') as f:
        rdr = csv.reader(f, delimiter = '\t')
        next(rdr)
        
        for line in rdr:
            
            d = data.get(line[0], {})
            d.update({'area': float(line[1]) / 1000000, 'location': "GeomFromText('POINT({0} {1})')".format(line[6].rstrip("\n"), line[5])})
            data[line[0]] = d
            
    print('read geography')
    
    with open('./sourcedata/ACS_15_5YR_B11011_with_ann.csv', 'r') as f:
        rdr = csv.reader(f, delimiter = ',', quotechar = '"')
        next(rdr)
        next(rdr)
        
        for line in rdr:
            d = data.get(line[1], {})
            d.update({'households': int(line[3])})
            data[line[1]] = d
            
    print('read housholds')
    
    return data
        
    
# Resolve high employment data with no geo location:
def assign_zips(data):
    for key in zip_assigns:
        if 'pop' in data[key]:
            print("This one has a pop! {0}".format(key))
            input()
        else:
            data[zip_assigns[key]]['emp'] += data[key]['emp']
            data[zip_assigns[key]]['emp_pay'] += data[key]['emp_pay']
            del data[key]
            
    return data
            
        
def insert_data(data):
    
    zip_db = mysql.connector.connect(user='dbuser', password='dbpass', database='zipcode')
    zip_cursor = zip_db.cursor()
    
    key_names = ['name', 'pop', 'emp', 'emp_pay', 'area', 'location', 'households']    
    
    query = "INSERT INTO zipcodes ({0}) VALUES({1});"
    
    count = 0
    total = len(data)
    
    for key in data:
              
        count += 1
        print("Adding {0} of {1}".format(count, total))
        
        d = data[key]
        add_keys = ['zip_code'] + [k for k in key_names if k in d]
        add_vals = ["'" + str(key) + "'"] + ["'" + str(d[k]) + "'" if k != 'location' else str(d[k]) for k in key_names if k in d]
        
        #print(query.format(", ".join(add_keys), ", ".join(add_vals)))
        zip_cursor.execute(query.format(", ".join(add_keys), ", ".join(add_vals)))
        

    
    zip_db.commit()
    


# Resolve data with no geo
def fix_no_geo_data():
    
    zip_db = mysql.connector.connect(user='dbuser', password='dbpass', database='zipcode')
    zip_cursor = zip_db.cursor()
    
    zip_cursor.execute("SELECT name, SUM(emp), SUM(emp_pay) FROM zipcodes WHERE location IS NULL GROUP BY name ORDER BY sum(emp) DESC;")
    
    city_list = [x for x in zip_cursor.fetchall()]

    inc = 0
    for name, emp, emp_pay in city_list:
        inc += 1
        
        zip_cursor.execute("SELECT COUNT(name) FROM zipcodes WHERE name = '{0}';".format(name))
        count = zip_cursor.fetchone()[0]
        
        if count > 0:
            zip_list = get_zip_list(zip_cursor, name, 16000)   
        else:
            zip_list = []
                   
        if len(zip_list) != 0:
            print("{1}:{2}: Updating {0}".format(name, inc, len(city_list)))
            zip_cursor.execute("UPDATE zipcodes SET emp = emp + {0}, emp_pay = emp_pay + {1} WHERE zip_code in ({2});".format(int(emp/len(zip_list)), int(emp_pay/len(zip_list)), ", ".join(zip_list)))
        else:
            print("{0}:{1}".format(inc, len(city_list)))
        
    zip_db.commit()
    
    zip_cursor.execute("DELETE FROM zipcodes WHERE location IS NULL;")
    zip_db.commit() 
    
    zip_cursor.execute("UPDATE zipcodes SET emp = 0 WHERE emp IS NULL;")
    zip_db.commit()
    
    zip_cursor.execute("UPDATE zipcodes SET emp_pay = 0 WHERE emp_pay IS NULL;")
    zip_db.commit()
    
    zip_db = mysql.connector.connect(user='root', password='city4533', database='zipcode')
    zip_cursor = zip_db.cursor()
    
    zip_cursor.execute("ALTER TABLE zipcodes MODIFY location POINT NOT NULL;")
    zip_cursor.execute("CREATE SPATIAL INDEX location_index ON zipcodes (location);")
    zip_db.commit()       

            
def get_zip_list(zip_cursor, name, threshold):
    zip_cursor.execute("SELECT zip_code FROM zipcodes WHERE NAME = '{0}' AND (emp + pop) / area > {1}".format(name, threshold))
    zip_list = [x[0] for x in zip_cursor.fetchall()]
    if len(zip_list) == 0 and threshold > 100:
        return get_zip_list(zip_cursor, name, int(float(threshold)/4))
    else:
        return zip_list
        
def merge_smalls():
    
    zip_db = mysql.connector.connect(user='dbuser', password='dbpass', database='zipcode')
    zip_cursor = zip_db.cursor()
    
    # merge all below 0.25
    zip_cursor.execute("SELECT zip_code, pop, emp, emp_pay, area, households FROM zipcodes WHERE area < 0.25 ORDER BY area;")
    zip_list = zip_cursor.fetchall()
    
    update_str = "UPDATE zipcodes SET pop = {0}, emp = {1}, emp_pay = {2}, area = {3}, households = {5} WHERE zip_code = {4};"
    delete_str = "DELETE FROM zipcodes WHERE zip_code = {0};"
    
    while len(zip_list) > 0:
        
        zcode, pop, emp, emp_pay, area, households =  zip_list[0]
        nearest = su.get_adjacent(zip_cursor, zcode)[0]      
        
        pop_up = pop + nearest['pop']
        emp_up = emp + nearest['emp']
        emp_pay_up = emp_pay + nearest['pay']
        area_up = area + nearest['area']
        house_up = area + nearest['house']
        
        
        #print(update_str.format(pop_up, emp_up, emp_pay_up, area_up, nearest[0]))
        #print(delete_str.format(zcode))
        
        print("Delete {0} and add it to {1}".format(zcode, nearest['zipcode']))
              
        zip_cursor.execute(update_str.format(pop_up, emp_up, emp_pay_up, area_up, nearest['zipcode'], house_up))
        zip_cursor.execute(delete_str.format(zcode))
        
        zip_db.commit()
        
        zip_cursor.execute("SELECT zip_code, pop, emp, emp_pay, area, households FROM zipcodes WHERE area < 0.25 ORDER BY area LIMIT 1;")
        zip_list =  zip_cursor.fetchall()
         
    # Merge below 1 if no neighbor less than 5x  
    #zip_cursor.execute("SELECT zip_code, pop, emp, emp_pay, area, household FROM zipcodes ORDER BY area DESC;")
    #zip_list = zip_cursor.fetchall()
    
    #for zcode, pop, emp, emp_pay, area in zip_list:
        #nearest = process_zip(zip_cursor, zcode)
        #ran = sqrt(area/pi)
        
        #if len(nearest) == 1 or (len(nearest) > 0 and all([ran*5 < x['dist'] for x in nearest])):
                               
            #pop_up = pop + nearest[0]['pop']
            #emp_up = emp + nearest[0]['emp']
            #emp_pay_up = emp_pay + nearest[0]['emp_pay']
            #area_up = area + nearest[0]['area']
        
            #print('merge', zcode, 'into', nearest[0]['zcode'])
            
            #zip_cursor.execute(update_str.format(pop_up, emp_up, emp_pay_up, area_up, nearest[0]))
            #zip_cursor.execute(delete_str.format(zcode))
            
            #zip_db.commit()
            #input()
            
        
        # z[3] = area; evaluates to true if all neighbors more than 5x the size of z
        #if all([x[3] > z[3]*5 for x in nearest]):
        #    print("Too small, merge", z[0], "to", nearest[0][0])
        #else:
        #    print(z[0])
        
        
def gen_adjacents():
    
    zip_db = mysql.connector.connect(user='dbuser', password='dbpass', database='zipcode')
    zip_cursor = zip_db.cursor()
    
    try:
        zip_cursor.execute("DROP TABLE adjacent;")
    except mysql.connector.errors.ProgrammingError as e:
        pass
    
    zip_cursor.execute("CREATE TABLE adjacent (source VARCHAR(8) NOT NULL PRIMARY KEY, target VARCHAR(8))")
    
    zip_cursor.execute("SELECT zip_code FROM zipcodes WHERE name = 'LAWRENCE, MA';")
    zip_list = [x[0] for x in zip_cursor.fetchall()]
    
    for z in zip_list:
        print(z)
        adj = su.get_adjacent(zip_cursor, z)
        for a in adj:
            print(">>>", a)
        input()
        #print(z, adj)
        

            




main()


