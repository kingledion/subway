import mysql.connector, subway_utils as su
from subway_assignments import zip_assigns
import parse_functions as pf


#################################################################
# NOTE
#   Requires mysql installed on your computer using the standard ports
#   For mysql, create a database and a user 
#   with username and password as defined below. This user must be 
#   given 'GRANT ALL ON db_name'.


dbuser = 'dbuser'
dbpass = 'dbpass'
db = 'zipcode'

# List of all data fields being filled with census data. MySQL data type is 'INT'.
fields = ['pop', 'emp', 'emp_pay', 'households', 'hospital', 'university']

def main():

    zip_db = mysql.connector.connect(user='dbuser', password='dbpass', database='zipcode')
    zip_cursor = zip_db.cursor()   
        
    create_db(zip_db, zip_cursor)
    
    data = read_files()
    data = assign_zips(data)
    insert_data(zip_db, zip_cursor, data)
    fix_no_geo_data()
    #merge_smalls() 
    #gen_adjacents()
    

    
    
def create_db(zip_db, zip_cursor):
    
    zip_cursor.execute("DROP TABLE IF EXISTS zipcodes;")
    censusfields = [f + " INT DEFAULT 0" for f in fields]
    sql = "CREATE TABLE zipcodes (zipcode VARCHAR(8) NOT NULL PRIMARY KEY, name VARCHAR(32), "
    sql += "area FLOAT, {0}, location POINT)".format(", ".join(censusfields))
    zip_cursor.execute(sql)
        
    zip_cursor.execute("DROP FUNCTION IF EXISTS haversine;")
    sql = "CREATE FUNCTION haversine(lat1 FLOAT, lon1 FLOAT, lat2 FLOAT, lon2 FLOAT) RETURNS FLOAT NO SQL DETERMINISTIC COMMENT "
    sql += "'Returns the distance in degrees on the Earth between two known points of latitude and longitude' BEGIN "
    sql += "RETURN DEGREES(ACOS(COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * COS(RADIANS(lon2) - RADIANS(lon1)) + SIN(RADIANS(lat1)) * SIN(RADIANS(lat2))));"
    sql += "END;"
    zip_cursor.execute(sql)
    
    zip_db.commit()
    
    
def read_files():
    
    data = {}
   
    # Loop through all 'read_xxx' functions and run them all; combine the returned data    
    for fn in [func for func in dir(pf) if func.startswith("read_")]:   
        for key,val in getattr(pf, fn)().items():
            if key in data:
                data[key].update(val)
            else:
                data[key] = val
        print("Finished parsing", fn)
       
    # Ensure all values get the zipcode tag, no matter what source they were read from
    for key in data:
        data[key].update({'zipcode': key})
        
    # Loop through all 'postproc_xxx' functions and run them all; combine the returned data    
    for fn in [func for func in dir(pf) if func.startswith("postproc_")]:   
        data = getattr(pf, fn)(data)
        print("Finished post processing", fn)
    
    return data

def merge_data(primary, toadd):
    keys = list((set(primary.keys()) | set(toadd.keys())) - set(['zipcode', 'name', 'location']))
    for k in keys:
        if k in primary and k in toadd:
            primary[k] = primary[k] + toadd[k]
        elif k in toadd:
            primary[k] = toadd[k]
    
# Resolve high employment data with no geo location:
def assign_zips(data):
    for key in zip_assigns:
        if 'pop' in data[key]:
            print("This one has a pop! {0}".format(key))
            input()
        else:
            merge_data(data[zip_assigns[key]], data[key])
            del data[key]
            
    return data
            
        
def insert_data(zip_db, zip_cursor, data):
          
    key_names = ['zipcode', 'name', 'area'] + fields + ['location']       
    query = "INSERT INTO zipcodes ({0}) VALUES ({1});"

    count = 0  
    
    for key in data:
        
        count += 1
        
        d = data[key]
        vals = [d[k] if k in d else 0 for k in key_names]
        use_fields = [key_names[i] for i in range(len(key_names)) if vals[i]]
        use_vals = [v for v in vals if v]
        # USE BATCHING!!!! SO SLOW!!!
        zip_cursor.execute(query.format(", ".join(use_fields), ", ".join(["'" + str(v) + "'" for v in use_vals[:2]]+[str(v) for v in use_vals[2:]])))

        prog = count / len(data)
        print("\rInserting into database: [{0:10s}] {1:.1f}%".format('#' * int(prog * 10) , prog*100), end="", flush=True)

    print()
    zip_db.commit()
    


# Resolve data with no geo
def fix_no_geo_data():
    
    zip_db = mysql.connector.connect(user='dbuser', password='dbpass', database='zipcode')
    zip_cursor = zip_db.cursor()
    
    field_sums = ", ".join(["SUM({0})".format(f) for f in fields])
    
    zip_cursor.execute("SELECT name, {0} FROM zipcodes WHERE location IS NULL GROUP BY name;".format(field_sums))
    
    city_list = [(row[0], row[1:]) for row in zip_cursor.fetchall()]

    count = 0
    for name, field_vals in city_list:
        count += 1
        
        zip_cursor.execute("SELECT zipcode, emp / area AS density FROM zipcodes WHERE name = '{0}' and area IS NOT NULL ORDER BY density desc;".format(name))
        zip_list = zip_cursor.fetchall()
        
        if len(zip_list) > 0:
            i = 0
            while i < len(zip_list) and zip_list[i][1] > 1000:
                i+= 1
            if i > 0:
                zip_list = [z[0] for z in zip_list[:i]]
            else:
                zip_list = ["'" + z[0] + "'" for z in zip_list]

            updates = [(fld, val/len(zip_list)) for fld, val in zip(fields, field_vals)]
            update_string = ", ".join(["{0} = {0} + {1}".format(fld, val) for fld, val in updates])
            zip_cursor.execute("UPDATE zipcodes SET {0} WHERE zipcode in ({1});".format(update_string,  ", ".join(zip_list)))
        else:
            pass
            # WHAT ARE WE DOING HERE???? WE ARE LETTING THESE ZIP CODES JUST DROP

        prog = count/len(city_list)
        print("\rResolving null areas: [{0:10s}] {1:.1f}%".format('#' * int(prog * 10) , prog*100), end="", flush=True)
        
    print()
    zip_db.commit()
    
    zip_cursor.execute("DELETE FROM zipcodes WHERE location IS NULL;")
    zip_db.commit() 
       
    zip_db = mysql.connector.connect(user='root', password='city4533', database='zipcode')
    zip_cursor = zip_db.cursor()
    
    zip_cursor.execute("ALTER TABLE zipcodes MODIFY location POINT NOT NULL;")
    zip_cursor.execute("CREATE SPATIAL INDEX location_index ON zipcodes (location);")
    zip_db.commit()       

            

# Not going to use this any more due to use of zip shape files     
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


