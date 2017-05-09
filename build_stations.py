# -*- coding: utf-8 -*-

import subway_utils as su, csv , numpy as np, networkx as nx
from rtree import index
from math import cos, radians, pi
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
        
    def getDataDict(self): # Inelegant solution!
        return self._data

def near_station(station, idx, pts):
    return [next(idx.nearest((*p, *p), 1, objects='raw')) == station for p in pts]   
    
def in_shape(state, pts):
    return [state.contains(shpgeo.Point(*p)) for p in pts]
    
def build_station_index(filename):
    with open(filename, 'r') as csvin:
        rdr = csv.reader(csvin, delimiter = ';', quotechar = "'")
        
        idx = index.Index()
        stations = []
        
        for row in rdr:
            if len(row) == 4:
                d = su.est_density(cursor, float(row[2]), float(row[1]))
                s = station(row[1], row[2], {**d, **{'name': row[0]}, **{'parking': row[3]}})     
                stations.append(s)
                idx.insert(0, (s['lon'], s['lat'], s['lon'], s['lat']), s)
                
            elif row:
                print(row)
                            
    return stations, idx
       
def calculate_areas(stations, idx, shp):
    # calculate latitude degrees to 1 km
    ns_deg = 1.0/110.574

    for s in stations:
        n = 1000 # done 1000
        # calculate lon degrees to 1km
        ew_deg = 1.0/111.320/cos(radians(s['lat']))
    
        Theta = np.random.randn(n, 2)
        R = np.sqrt(np.random.rand(n))
        vectors = Theta * np.stack([R*ew_deg / np.linalg.norm(Theta, axis=1), R*ns_deg / np.linalg.norm(Theta, axis=1)], axis=1)
        
        # pts in a 1km area
        pts = [(v[0] + s['lon'], v[1] + s['lat']) for v in vectors]
        walk = [1 if a else 0 for a in in_shape(shp, pts)]
        wcount = sum(walk)
        near = sum(1 if a and b else 0 for a, b in zip(near_station(s, idx, pts), walk))

        s['narea'] = near*pi/n # area of a 1km radius circle is pi
        s['warea'] = wcount*pi/n
        
        # pts in 15km area
        pts = [(v[0]*15 + s['lon'], v[1]*15 + s['lat']) for v in vectors]
        drive = sum(1 if a and b else 0 for a, b in zip(near_station(s, idx, pts), in_shape(shp, pts)))
        s['darea'] = drive*225*pi/n
        
        print(s['name'], "{0:.2f}".format(wcount*pi/n), "{0:.2f}".format(near*pi/n), "{0:.2f}".format(drive*225*pi/n))
        
#def calculate_totals(stations):
#    fields = stations[0].getfields()
#    dfields = [f for f in fields if f.endswith('density')]
#    for s in stations:
#        for d in dfields:
#            name = d.split('density')[0]
#            
#            s[name + 'near'] = int(s[d] * s['narea'])
#            s[name + 'walk'] = int(s[d] * s['warea'])
#            s[name + 'drive'] = int(s[d] * s['darea'])
            
def to_dataframe(stations):
    list_of_dict = [s.getDataDict() for s in stations] # There must be a better way!
    df = pd.DataFrame(list_of_dict)
    dfields = [f for f in list(df) if f.endswith('density')]
    
    for d in dfields:
        name = d.split('density')[0]
        df[name + 'near'] = df[d] * df['narea']
        df[name + 'walk'] = df[d] * df['warea']
        df[name + 'drive'] = df[d] * df['darea']

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
                    #G.add_edges_from([(src_l + src_s, src_l + tar_s), (src_l + tar_s, tar_l + src_s)], weight=w)
                elif src_s == tar_s:
                    # This means transfer between lines on the same station
                    # Add only this one direction (other should be defined separate)
                    G.add_edge(src_l + ":" + src_s, tar_l + ":" + tar_s, weight = float(w))
                
            elif row:
                print(row)
                
    return G
    
def get_nearby_nodes(G, r, names):
    graphs = [nx.ego_graph(G, x, radius = r, distance='weight') for x in names]
    g =  graphs[0] if len(graphs) <= 1 else nx.compose_all(graphs) # should I be using compose or union?
    return set([x.split(":")[1] for x in g.nodes()])
    
            
def add_station_network(df, G):
    stations = df['name'] 
    
    dfields = [f for f in list(df) if f.endswith('near')]
    nfields = [(d, d.split("near")[0] + 'net') for d in dfields]
    
    for s in stations:
        nodenames = [x for x in G.nodes() if x.split(":")[1] == s]

        within15 = get_nearby_nodes(G, 15, nodenames)
        within30 = get_nearby_nodes(G, 30, nodenames)
        within60 = get_nearby_nodes(G, 60, nodenames)
        
        for old, new in nfields:
            
            df.set_value(df['name'] == s, '15' + new, df.loc[df['name'].isin(within15), old].sum())
            df.set_value(df['name'] == s, '30' + new, df.loc[df['name'].isin(within30), old].sum())
            df.set_value(df['name'] == s, '60' + new, df.loc[df['name'].isin(within60), old].sum())
 
            
#def write_stations(stations, filename):
#
#    with open(filename , 'w') as outfile:
#        wrtr = csv.writer(outfile) 
#        wrtr.writerow(fields)
#        for s in stations:
#            wrtr.writerow([s[f] for f in fields])

################################################
# Load station geo data; build station lists; build station geoindices
# Load station network
    
bstations, bidx = build_station_index('./gendata/boston_subwaygeo.csv')
cstations, cidx = build_station_index('./gendata/chicago_subwaygeo.csv')
print("Density estimate and index built")

# load station network maps
bnetwork = loadnetwork('./gendata/boston_network.csv')
cnetwork = loadnetwork('./gendata/chicago_network.csv')

#############################################
# Load shapefiles, calculate available walking (1km) and driving (15km) areas
    
# load shapefile of states in question (index 32 = MA, 19 = IL)
sf = shapefile.Reader('./shapes/cb_2015_us_state_20m')

calculate_areas(bstations, bidx, shpgeo.shape(sf.shape(32).__geo_interface__))
calculate_areas(cstations, cidx, shpgeo.shape(sf.shape(19).__geo_interface__))
print("Areas calculated")

###############################################
# Convert to datafram and multiply densities by#write_stations(bstations, "/opt/school/stat672/subway/boston_stations.csv")    
#write_stations(cstations, "/opt/school/stat672/subway/chicago_stations.csv")   areas to get counts

bframe = to_dataframe(bstations)
cframe = to_dataframe(cstations)
print("Converted to dataframes")

##############################################
# Add nearby stations on the network to station data

add_station_network(bframe, bnetwork)
add_station_network(cframe, cnetwork)
print("Station network data added")

        
###############################################
# Write staions to csv files
        
bframe.to_csv("./gendata/boston_stations.csv") 
cframe.to_csv("./gendata/chicago_stations.csv")     
           
