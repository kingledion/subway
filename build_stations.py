# -*- coding: utf-8 -*-

import subway_utils as su, csv , numpy as np, networkx as nx
from rtree import index
import shapely.geometry as shpgeo, shapely.vectorized as shpvec, shapefile, pandas as pd
from excl_areas import getPoints

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
    
    def getLocation(self):
        return (self._data['lon'], self._data['lat'])
        
    def getfields(self):
        return [k for k in self._data]
        
    def setDataDict(self, newdict):
        self._data.update(newdict)
        
    def getDataDict(self): # Inelegant solution!
        return self._data
    
    def increment(self, key, value):
        self._data[key] = self._data.get(key, 0) + value


def near_stations(idx, lons, lats):

    nears = [list(idx.nearest((lon, lat, lon, lat), 4, objects='raw')) for lon, lat in zip(lons, lats)]
    
    def getskey(stobj, key):
        return stobj.__getitem__(key)
    
    # lat and lon vectors for points and stations 
    vlon = np.reshape(np.repeat(lons, 4), (-1, 4))
    vlat = np.reshape(np.repeat(lats, 4), (-1, 4))
    
    slon = np.vectorize(getskey)(nears, 'lon')
    slat = np.vectorize(getskey)(nears, 'lat')
           
    dists = su.haversine(vlon, vlat, slon, slat)
    
    #halfkm = np.sum(np.less(dists, 0.5), axis=0)
    #onekm = np.sum(np.less(dists, 1.0), axis=0)
    
    results = []   # better way, combine with out of loop processing
    for stalist, distlist in zip(nears, dists):
        sts = [s.__hash__ for s, d in zip(stalist, distlist) if d < 0.5]
        if not sts:
            sts = [s.__hash__ for s, d in zip(stalist, distlist) if d < 1.0]
        results.append(sts)
        
    
    return results
    
    

def random_points_in(poly, excluded, num_points):
    
    min_x, min_y, max_x, max_y = poly.bounds
    
    pts = []
    tries = 0
    
    while len(pts) < num_points:
        
        success = len(pts)/tries if tries else 0
        n = max(1000, int((num_points - len(pts)) / (1 - success) * 1.5)) # always try at least 100; cost is small
        tries += n
    
        lons = np.random.uniform(min_x, max_x, n)
        lats = np.random.uniform(min_y, max_y, n)
        valid = shpvec.contains(poly, lons, lats)
        
        pts.extend([(lon, lat) for lon, lat, v in zip(lons, lats, valid) if v]) # do this part better!!
        
    return zip(*pts[:num_points])
        
        
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
       
def calculate_areas(stations, idx, sf, name):
    
    # Get list of all station lats and lons
    coords = [(s['lon'], s['lat']) for s in stations]
    lons = [l[0] for l in coords]
    lats = [l[1] for l in coords]
    
    # build station directory
    stadict = {s.__hash__: s for s in stations}
    
    # Transform lat and lon degrees to km of distance
    ns_deg = 1.0/110.574 
    ew_deg = 1.0/111.320/np.cos(np.deg2rad(np.mean(lats))) # approximation is good enough
    
    # max box to select zipcodes from 
    min_lon, max_lon = min(lons) - 10 * ew_deg, max(lons) + 10 * ew_deg
    min_lat, max_lat = min(lats) - 10 * ns_deg, max(lats) + 10 * ns_deg
    
    # ONLY SELECT THE ONES THAT ARE CLOSE TO A STATION!!!!
    
    #print(min_lon, max_lon)
    #print(min_lat, max_lat)
    
    # helper function to select zipcodes from box
    def nearby(lon, lat):
        return True if lon > min_lon and lon < max_lon and lat > min_lat and lat < max_lat else False

    shps = [(r[0], shpgeo.shape(sf.shape(i).__geo_interface__)) for i, r in enumerate(sf.records()) if nearby(float(r[8]), float(r[7]))]  #asPolygon?
    

    
    n = 100 # mutiplier by area (in km^2) for number of points to sample
    
    # Areas where there is no development (water, parks, etc)
    ex_points = getPoints(name)   
    exclusion = [shpgeo.Polygon(ptlist) for ptlist in ex_points]

    # list of all feature names
    features = su.get_feature_names()    
    # data for zipcodes
    zipdata, zipareas = su.get_zip_counts([z for z, s in shps])
    
    for zcode, poly in shps:
               
        num_points = int(zipareas[zcode] * n)
        
        print('Processing zipcode', zcode, ' ... ', num_points, 'hectares')
        
        lons, lats = random_points_in(poly, exclusion, num_points)
       
        near_stat_dict = {}
        nears = near_stations(idx, lons, lats)
        for nlist in nears:
            for nhash in nlist:
                near_stat_dict[nhash] = near_stat_dict.get(nhash, 0) + 1 / len(nlist)
                
        stassigns = [(stadict[shash]['name'], shash, count) for shash, count in near_stat_dict.items()]
               
        for name, shash, cnt in stassigns:
            prop = cnt/num_points
            s = stadict[shash]
            zd = zipdata[zcode]
            
            for f in features:
                s.increment('near_{0}'.format(f), zd[f] * prop)  
                
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
                    # This means transfer between lines on the same station
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
        #within60 = get_nearby_nodes(G, 60, nodenames)
        
        for fname in features:
            
            df.set_value(df['name'] == s, '15net_{0}'.format(fname), df.loc[df['name'].isin(within15), "near_{0}".format(fname)].sum())
            df.set_value(df['name'] == s, '30net_{0}'.format(fname), df.loc[df['name'].isin(within30), "near_{0}".format(fname)].sum())
            #df.set_value(df['name'] == s, '60net_{0}'.format(fname), df.loc[df['name'].isin(within60), "near_{0}".format(fname)].sum())
 
            
            


################################################          
# Format of filenames is (name, station geos csv input, station network and ridership csv input, station data output)  
#                        NOTE: name is only used for printing status updates to screen
in_city_list = [('Boston', './gendata/boston_subwaygeo.csv', './gendata/boston_network.csv', "./gendata/boston_stations.csv")]#,
                #('Chicago', './gendata/chicago_subwaygeo.csv', './gendata/chicago_network.csv', "./gendata/chicago_stations.csv")],
                #('Atlanta', './gendata/atlanta_subwaygeo.csv', './gendata/atlanta_network.csv', "./gendata/atlanta_stations.csv"),
                #('Los Angeles', './gendata/la_subwaygeo.csv', './gendata/la_network.csv', "./gendata/la_stations.csv"),
                #('Dallas', './gendata/dallas_subwaygeo.csv', './gendata/dallas_network.csv', "./gendata/dallas_stations.csv"),
                #('Denver', './gendata/denver_subwaygeo.csv', './gendata/denver_network.csv', "./gendata/denver_stations.csv")]

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
    calculate_areas(stations, idx, sf, name)
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
  
           
