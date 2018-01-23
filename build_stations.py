# -*- coding: utf-8 -*-

import subway_utils as su, csv , numpy as np, networkx as nx
from rtree import index
from math import cos, radians, pi
from collections import Counter
import shapely.geometry as shpgeo, shapefile, pandas as pd

db, cursor = su.opendb()

# Station class to use in conjunction with the rtree index
class station:
    
    def __init__(self, lat, lon, datadict = {}):
        self._data = datadict
        self._data['lat'] = float(lat)
        self._data['lon'] = float(lon)
        
    def __getitem__(self, key):
        if key not in self._data:
            raise IndexError(key)
        return self._data[key]
        
    def __setitem__(self, key, value):
        self._data[key] = value
        
    def __hash__(self):
        return hash((self._data['lat'], self._data['lon']))
        
    def __iter__(self):
        for key in self._data:
            yield key
        
    def __eq__(self, other):
        return True if self._data['lat'] == other._data['lat'] and  self._data['lon'] == other._data['lon'] else False
        
    def getfields(self):
        return [k for k in self._data]
        
    def setDataDict(self, newdict):
        self._data.update(newdict)
        
    def getDataDict(self): # Inelegant solution!
        return self._data

def near_station(station, idx, pts):
    return [next(idx.nearest((*p, *p), 1, objects='raw')) == station for p in pts]   
    
def which_shape(records, lon, lat):
    for zcode, s in records:
        if s.contains(shpgeo.Point(lon, lat)):
            return zcode
    return 0
    
#def in_shape(state, pts):
#    return [state.contains(shpgeo.Point(*p)) for p in pts]
       
def build_station_index(filename):
    with open(filename, 'r') as csvin:
        rdr = csv.reader(csvin, delimiter = ';', quotechar = "'")
        
        idx = index.Index()
        stations = []
        
        for row in rdr:
            if len(row) == 4:
                s = station(row[1], row[2], {'name': row[0], 'parking': row[3]})     
                stations.append(s)
                idx.insert(0, (s['lon'], s['lat'], s['lon'], s['lat']), s)
                
            elif row:
                print("Bad row in {0}:".format(filename), row)
                            
    return stations, idx
       
def calculate_areas(stations, idx, sf):
    
    # Get list of all station lats and lons
    coords = [(s['lon'], s['lat']) for s in stations]
    lons = [l[0] for l in coords]
    lats = [l[1] for l in coords]
    
    # Calculate lat and lon degrees to1 km of distance
    ns_deg = 1.0/110.574 
    ew_deg = 1.0/111.320/cos(radians(np.mean(lats))) # approximation is good enough
    
    # max box to select zipcodes from 
    min_lon, max_lon = min(lons) - 10 * ew_deg, max(lons) + 10 * ew_deg
    min_lat, max_lat = min(lats) - 10 * ns_deg, max(lats) + 10 * ns_deg
    print(min_lon, max_lon)
    print(min_lat, max_lat)
    
    # helper function to select zipcodes from box
    def nearby(lon, lat):
        return True if lon > min_lon and lon < max_lon and lat > min_lat and lat < max_lat else False

    shps = [(r[0], shpgeo.shape(sf.shape(i).__geo_interface__)) for i, r in enumerate(sf.records()) if nearby(float(r[8]), float(r[7]))] 
    
    # list of all feature names
    features = su.get_feature_names()
   
    for s in stations:
        n = 1000
        area = pi # 3.14 km^2 is area within 1km of a point
    
        # Creates random point within 1km of a central point
        Theta = np.random.randn(n, 2)
        R = np.sqrt(np.random.rand(n))
        vectors = Theta * np.stack([R*ew_deg / np.linalg.norm(Theta, axis=1), R*ns_deg / np.linalg.norm(Theta, axis=1)], axis=1)
        
        # pts in a 1km area    
        pts = [(v[0] + s['lon'], v[1] + s['lat']) for v in vectors]
        
        # walk determine which shape each point is in; if in no shape (such as in water) then zcode is 0
        # near further adds zeros for each zcode where the point is closer to some other station than s
        walk = [which_shape(shps, lon, lat) for lon, lat in pts]
        near = [zcode if is_near else 0 for zcode, is_near in zip(walk, near_station(s, idx, pts))]      
        
        # Count the number of time each zip code appears in walk or near
        walk = Counter(walk)
        near = Counter(near)
        
        # Remove counts for 0; the code for no zipcode found or another station is closer
        del walk[0]
        del near[0]
        
        # Get densities for zips of interest, along with list of all features
        all_zips = set(walk.keys() | near.keys())
        densities, maxima = su.get_zip_densities(all_zips)

        # Area for each zip cannot exceed the maximum area of that zipcode. This is particularly relevant for water surface area
        walk = {zcode: min(maxima[zcode], counts * area / n) for zcode, counts in walk.items()}
        near = {zcode: min(maxima[zcode], counts * area / n) for zcode, counts in near.items()}
        
        for f in features:
            s['walk_{0}'.format(f)] = sum([densities[zcode][f] * zarea for zcode, zarea in walk.items()])
            s['near_{0}'.format(f)] = sum([densities[zcode][f] * zarea for zcode, zarea in near.items()])
        
        print(s['name'])
        #print('Walking area', sum([v for k, v in walk.items()]))
        #for z in walk:
        #    print("\t{0}: {1}".format(z, walk[z]))
        print('Nearby area', sum([v for k, v in near.items()]))
        #for z in near:
        #    print("\t{0}: {1}".format(z, near[z]))
            

        
            
        
                
def to_dataframe(stations):
    list_of_dict = [s.getDataDict() for s in stations] # There must be a better way!
    df = pd.DataFrame(list_of_dict)
    return df
    
def loadnetwork(filename):
    G = nx.MultiDiGraph()    
    
    with open(filename, 'r') as csvin:
        rdr = csv.reader(csvin, delimiter = ';', quotechar = "'")
        
        for row in rdr:
            if len(row) == 5:
                src_l, src_s, tar_l, tar_s, w = row
                if not tar_l: 
                    # This means stations on the same line. Add both directions
                    # on the directed graph and  src_l = tar_l.
                    #print([(src_l + src_s, src_l + tar_s), (src_l + tar_s, src_l + src_s)])
                        G.add_edge(src_l + ":" + src_s, src_l + ":" + tar_s, weight = float(w))
                        G.add_edge(src_l + ":" + tar_s, src_l + ":" + src_s, weight = float(w))
                elif src_s == tar_s:
                    # This m0eans transfer between lines on the same station
                    # Add only this one direction (other should be defined separate)
                    try:
                        G.add_edge(src_l + ":" + src_s, tar_l + ":" + tar_s, weight = float(w))
                    except ValueError as e:
                        print(row)
                        raise e
            elif row:
                print(row)
                
    return G
    
def get_nearby_nodes(G, r, names):
    #print(names)
    graphs = [nx.ego_graph(G, x, radius = r, distance='weight') for x in names]
    g =  graphs[0] if len(graphs) <= 1 else nx.compose_all(graphs) # should I be using compose or union?
        
    return set([x.split(":")[1] for x in g.nodes()])
    
            
def add_station_network(df, G):
    stations = df['name'] 
    
    features = su.get_feature_names()
    
    for s in stations:
        print(s)
        nodenames = [x for x in G.nodes() if x.split(":")[1] == s]

        within15 = get_nearby_nodes(G, 15, nodenames)
        within30 = get_nearby_nodes(G, 30, nodenames)
        within60 = get_nearby_nodes(G, 60, nodenames)
        
        for fname in features:
            
            df.set_value(df['name'] == s, '15net_{0}'.format(fname), df.loc[df['name'].isin(within15), "near_{0}".format(fname)].sum())
            df.set_value(df['name'] == s, '30net_{0}'.format(fname), df.loc[df['name'].isin(within30), "near_{0}".format(fname)].sum())
            df.set_value(df['name'] == s, '60net_{0}'.format(fname), df.loc[df['name'].isin(within60), "near_{0}".format(fname)].sum())
 
            
#def write_stations(stations, filename):
#
#    with open(filename , 'w') as outfile:
#        wrtr = csv.writer(outfile) 
#        wrtr.writerow(fields)
#        for s in stations:
#            wrtr.writerow([s[f] for f in fields])
            


################################################          
# Format of filenames is (name, station geos csv input, station network and ridership csv input, station data output)  
#                        NOTE: name is only used for printing status updates to screen
in_city_list = [('Boston', './gendata/boston_subwaygeo.csv', './gendata/boston_network.csv', "./gendata/boston_stations.csv"),
                ('Chicago', './gendata/chicago_subwaygeo.csv', './gendata/chicago_network.csv', "./gendata/chicago_stations.csv"),
                ('Atlanta', './gendata/atlanta_subwaygeo.csv', './gendata/atlanta_network.csv', "./gendata/atlanta_stations.csv"),
                ('Los Angeles', './gendata/la_subwaygeo.csv', './gendata/la_network.csv', "./gendata/la_stations.csv"),
                ('Dallas', './gendata/dallas_subwaygeo.csv', './gendata/dallas_network.csv', "./gendata/dallas_stations.csv"),
                ('Denver', './gendata/denver_subwaygeo.csv', './gendata/denver_network.csv', "./gendata/denver_stations.csv")]

# load shapefile of all zipcodes in the US
sf = shapefile.Reader("/opt/ziplfs/tl_2014_us_zcta510.shp")

for name, geo_in, network_in, stations_out in in_city_list:
    
    # Load station geo data; build station lists; build station geoindices
    stations, idx = build_station_index(geo_in)
    print("{0} density estimate and index built".format(name))

    # load station network maps
    network = loadnetwork(network_in)
    print("{0} network built".format(name))

    # Calculate available walking and areas
    calculate_areas(stations, idx, sf)
    print("{0} station data calculated".format(name))

    # Convert to dataframe
    dframe = to_dataframe(stations)
    print("{0} converted to dataframe".format(name))

    # Add nearby stations on the network to station data
    add_station_network(dframe, network)
    print("Station network data added")
     
    # Write staions data to csv file      
    dframe.to_csv(stations_out, index=False) 
    print("Station data written; done with {0}".format(name))
  
           
