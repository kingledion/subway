# -*- coding: utf-8 -*-

import subway_utils as su, csv , numpy as np, networkx as nx, sys
from rtree import index
import shapely.geometry as shpgeo, shapely.vectorized as shpvec, shapefile, pandas as pd
from excl_areas import getPoints
from matplotlib import pyplot as plt

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
    
    n = 8 # Check up to n nearby stations

    nears = [list(idx.nearest((lon, lat, lon, lat), n, objects='raw')) for lon, lat in zip(lons, lats)]
    
    
    def getskey(stobj, key):
        return stobj.__getitem__(key)
    
    # lat and lon vectors for points and stations 
    vlon = np.reshape(np.repeat(lons, n), (-1, n))
    vlat = np.reshape(np.repeat(lats, n), (-1, n))
    
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
        n = max(1000, int((num_points - len(pts)) / (1 - success) * 1.5)) # always try at least 1000; cost is small
        tries += n
    
        lons = np.random.uniform(min_x, max_x, n)
        lats = np.random.uniform(min_y, max_y, n)
        valid = shpvec.contains(poly, lons, lats)
        #print(valid)
        excl = np.zeros(len(valid))
        for ply in excluded:
            ex = shpvec.contains(ply, lons, lats)
            excl = np.logical_or(excl, ex)
        
        newvalid = np.logical_and(valid, np.logical_not(excl))
               
        pts.extend([(lon, lat) for lon, lat, v in zip(lons, lats, newvalid) if v]) # do this part better!!
        
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
    

    shps = [(zcode, poly) for zcode, poly in shps if zcode in ziplist[name]]
   
    n = 100 # mutiplier by area (in km^2) for number of points to sample
    
    # Areas where there is no development (water, parks, etc)
    ex_points = getPoints(name)  
    exclusion = [shpgeo.Polygon(ptlist) for ptlist in ex_points]

    # list of all feature names
    features = su.get_feature_names()    
    # data for zipcodes
    zipdata, zipareas = su.get_zip_counts([z for z, s in shps])
    goodzips = []
    
    for i, d in enumerate(shps):
        
        zcode = d[0]
        poly = d[1]
        
        num_points = max(n*10,int(zipareas[zcode] * n)) # always a minimum of n*10 points, cost is small
        
        sys.stdout.write("{0} of {1}\r".format(i, len(shps)))
        sys.stdout.flush()
        #print('Processing zipcode', zcode, ' ... ', num_points, 'points',)
        
        lons, lats = random_points_in(poly, exclusion, num_points)
                   
        near_stat_dict = {}
        nears = near_stations(idx, lons, lats)
        for nlist in nears:
            for shash in nlist:
                near_stat_dict[shash] = near_stat_dict.get(shash, 0) + 1 / len(nlist)
                
        stassigns = [(shash, count) for shash, count in near_stat_dict.items()]
        
        # Printed summary for testing exclusion points! Keep in code!
        #for nlist, lon, lat in zip(nears, lons, lats):
        #    nlistnames = [stadict[shash]['name'] for shash in nlist]
        #    print(lon, lat, nlistnames)
        #    
        #for shash, cnt in sorted(stassigns, key=lambda x: x[1], reverse=True):
        #    print(stadict[shash]['name'], cnt)
        
        #print("Count", sum([x[1] for x in stassigns]))
        if sum([x[1] for x in stassigns]) > 0:
            goodzips.append(zcode)
            
               
        for shash, cnt in stassigns:
            prop = cnt/num_points
            s = stadict[shash]
            zd = zipdata[zcode]
            
            for f in features:
                s.increment('near_{0}'.format(f), zd[f] * prop)  
    #print(len(goodzips))
    #print({name: goodzips})
                
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
            
            
ziplist = {'Boston': ['02458', '02459', '02461', '02462', '02464', '02465', '02466', '02467', '02468', '02474', '02478', '02481', '02493', '02494', '02108', '02109', '02110', '02111', '02113', '02114', '02115', '02116', '02118', '02119', '02120', '02121', '02122', '02124', '02125', '02126', '02127', '02128', '02129', '02130', '02131', '02134', '02135', '02138', '02139', '02140', '02141', '02142', '02143', '02144', '02145', '02148', '02149', '02150', '02151', '02152', '02155', '02163', '02169', '02170', '02171', '02176', '02184', '02199', '02203', '02210', '02215', '02445', '02446'],
           'Chicago': ['60651', '60653', '60654', '60656', '60657', '60660', '60661', '60706', '60804', '60068', '60091', '60601', '60602', '60603', '60153', '60604', '60605', '60606', '60607', '60608', '60609', '60610', '60130', '60018', '60611', '60612', '60613', '60614', '60615', '60616', '60618', '60619', '60620', '60621', '60622', '60623', '60624', '60625', '60626', '60628', '60629', '60630', '60644', '60631', '60632', '60636', '60637', '60638', '60645', '60647', '60640', '60641', '60642', '60201', '60202', '60301', '60302', '60304', '60305', '60402'],
           'Atlanta': ['30303', '30305', '30307', '30308', '30309', '30310', '30311', '30312', '30313', '30314', '30315', '30316', '30317', '30318', '30319', '30324', '30326', '30328', '30334', '30337', '30338', '30340', '30341', '30342', '30344', '30346', '30354', '30360', '30363', '30083', '30002', '30030', '30032', '30035'],
           'Los Angeles': ['90831', '91030', '91101', '91103', '91104', '91105', '91106', '91107', '90723', '90755', '90802', '90805', '90806', '90807', '90810', '90813', '91601', '91602', '91604', '91608', '91754', '90001', '90002', '90004', '90005', '90006', '90007', '90008', '90010', '90011', '90012', '90013', '90014', '90015', '90016', '90017', '90018', '90019', '90020', '90021', '90022', '90023', '90026', '90027', '90028', '90029', '90031', '90033', '90034', '90037', '90038', '90039', '90042', '90044', '90045', '90046', '90047', '90062', '90063', '90065', '90068', '90071', '90079', '90089', '90090', '90220', '90221', '90057', '90058', '90059', '90061', '90222', '90232', '90242', '90245', '90249', '90250', '90255', '90260', '90262', '90266', '90278', '90303', '90304', '90650', '90706'],
           'Dallas': ['76051', '75006', '75007', '75019', '75023', '75038', '75039', '75040', '75042', '75062', '75063', '75067', '75074', '75075', '75080', '75081', '75082', '75088', '75089', '75208', '75210', '75211', '75214', '75215', '75270', '75390', '75216', '75217', '75218', '75219', '75220', '75223', '75224', '75225', '75226', '75227', '75229', '75230', '75231', '75233', '75234', '75235', '75238', '75241', '75243', '75201', '75202', '75246', '75247', '75251', '75203', '75204', '75205', '75206', '75207'],
           'Denver': ['80110', '80111', '80112', '80113', '80120', '80123', '80124', '80125', '80128', '80131', '80134', '80202', '80203', '80204', '80205', '80209', '80210', '80211', '80212', '80214', '80215', '80216', '80218', '80222', '80223', '80224', '80226', '80228', '80237', '80264', '80290', '80293', '80294', '80401', '80419', '80014', '80015'],
           }
            
            
if __name__ == "__main__":
    # Format of filenames is (name, station geos csv input, station network and ridership csv input, station data output)  
    #                        NOTE: name is only used for printing status updates to screen
    #in_city_list = [('Boston', './gendata/boston_subwaygeo.csv', ),
    #                ('Chicago', './gendata/chicago_subwaygeo.csv'),
    #                ('Atlanta', './gendata/atlanta_subwaygeo.csv'),
    #                ('Los Angeles', './gendata/la_subwaygeo.csv'),
    #                ('Dallas', './gendata/dallas_subwaygeo.csv'),
    #                ('Denver', './gendata/denver_subwaygeo.csv')]
       
    
    # load shapefile of all zipcodes in the US
# =============================================================================
#     sf = shapefile.Reader("/opt/ziplfs/tl_2014_us_zcta510.shp")
#     
#     
#     allpops = []
#     
#     for i in range(100):
#         dflist = []
#         
#         print('>>>Loop', i)
#         
#         for name, geo_in in in_city_list:
#             
#             # Load station geo data; build station lists; build station geoindices
#             stations, idx = build_station_index(geo_in)
#         
#             # Calculate available walking and areas
#             calculate_areas(stations, idx, sf, name)
#             print("{0} station data calculated".format(name))
#             
#             # Convert to dataframe
#             dflist.append(to_dataframe(stations))
#             
#         df = pd.concat(dflist)
#         
#         allpops.append(df.as_matrix(["near_population"]))
#         
#     allpops = np.concatenate(allpops, axis = 1)
#     print(allpops.shape)
#         
#     mns = np.mean(allpops, axis=1)
#     varns = np.sqrt(np.var(allpops, axis=1))
#     
#     print(list(mns))
#     print(list(varns))
# 
#     
#     plt.plot(mns, varns, 'bx')
#     plt.show()
# =============================================================================
        
        



    allstdevs = [559.10839286150667, 563.38455811140045, 652.35681338441873, 569.54038362967196, 246.1331624360925, 173.52950207448367, 99.345677083828534, 36.302554088059203, 36.252284368851576, 62.937516539686541, 244.59099102181528, 301.31489580465944, 251.85364888336409, 232.32674241435382, 353.95588841982288, 400.8995471900904, 364.86367395630924, 408.03889202273655, 475.35379473006253, 495.46212242640433, 398.66425182906607, 568.71611826525418, 576.35145572605916, 500.14135276440135, 405.75508528059123, 173.55769131077571, 37.658762640277871, 96.891119264691113, 505.32952092469816, 622.66976015420437, 567.48391531318009, 455.67774106685732, 492.56790458295376, 532.92892961296832, 801.08914514670607, 264.73719596194843, 321.53016953198488, 346.36312689331794, 324.71702438663419, 151.58535375920937, 68.531196736004347, 55.173728750178597, 70.204257379342636, 376.4407695277585, 358.04882694093237, 432.98612849769006, 455.86715868936744, 301.26522244674533, 400.12067092669497, 290.66287364842992, 340.64447916089239, 251.50656861110923, 161.95926868368835, 80.306764137898185, 170.33391053337994, 234.05068601817246, 201.41665609586988, 171.12600458219134, 157.47826917980905, 189.38723835869052, 193.37113091239232, 177.35558052269241, 152.6599394808469, 143.60575610708585, 118.09653162570623, 146.51797375778801, 277.19530468675106, 359.34181189141327, 283.31079093414036, 219.04616356047367, 225.16991443755657, 186.22184590379987, 251.03637950585454, 134.07029055918207, 120.41498436522382, 277.84452985544715, 195.81556194900963, 142.34414024590725, 110.54416179431158, 115.21397180354941, 131.14817709707177, 127.40104449529117, 107.41468666099661, 99.166708342821181, 111.91840505222822, 157.65776391366899, 181.1570550240364, 154.46787064186421, 119.20202989028067, 125.42597889259845, 123.07792465970502, 106.95262213176353, 56.165551522872924, 63.753557120324992, 95.043524061817109, 170.93875695992079, 183.79106727292671, 152.8595265921885, 187.19115631666136, 158.70071801597931, 166.03964847876432, 162.11455726240311, 192.97497973314759, 198.67736620647133, 164.69568477524749, 157.74461174612139, 218.93210570020605, 205.63414301225941, 141.23577852037465, 256.08100014300334, 145.3493664563149, 284.28385830567794, 465.79746559421147, 270.05607176672231, 340.54901759883461, 276.54620664164719, 234.8928719759119, 312.70180905050978, 416.26030980895518, 342.23343189945916, 287.44948896681342, 502.47365755269971, 573.061947184053, 668.10019507187985, 596.20097358701264, 409.07848937032247, 389.21730295687144, 698.2273020268907, 623.7217022264864, 491.51508366493613, 477.88732007550936, 623.82320918441212, 592.14439071012737, 608.43531402676149, 545.35882731657011, 467.98240483681849, 581.76577447434568, 710.0845309735646, 616.94425719935168, 777.11086101464196, 396.23503347730616, 179.9284533449817, 85.103855236265929, 125.18284810256932, 60.96717154275894, 36.715312942199056, 133.22805667068025, 115.289839803124, 70.35127213178454, 87.906541700084375, 62.926258882892931, 42.047759573210797, 516.00026093446183, 534.31781413137855, 463.85743898031217, 327.99022613977678, 36.361634785209617, 220.82331517492875, 495.16947133899117, 456.85932313485955, 475.70987773813795, 400.42384317231569, 416.51237951073131, 334.73810224520162, 513.65079223027692, 631.60492781785672, 638.83937989496189, 553.22836004508576, 606.6261368988005, 611.33896585854416, 652.81905788211441, 664.89880950578208, 612.2056703378438, 679.25009100289969, 584.67850653398057, 593.73033794068624, 725.96446970865998, 531.8236286023913, 737.65611303951528, 112.45933155100012, 318.49199106616715, 434.57445092710356, 527.99150363406159, 720.67441782795822, 922.31206071552833, 907.38767968616844, 804.85804145013526, 910.5116041532159, 1128.8276008056173, 1057.2373415891821, 943.47620930403127, 826.83372191245189, 650.00609193941375, 306.22910796908798, 270.20424549197861, 158.28674488180408, 241.31500532106861, 317.79160154001977, 330.23882791070719, 384.31680405769259, 415.13111277304034, 598.86943800625932, 399.87723021997203, 662.24984085803294, 559.29481475340287, 291.32876638301605, 246.76442859073862, 229.42127998732281, 320.17775347112013, 350.3580388887641, 307.876778107429, 483.68916353917911, 488.11371805620121, 563.12315079430368, 613.76788333426236, 429.7624948231761, 335.70460128950822, 351.47317238910279, 478.84837996596093, 496.02995435455392, 309.78135528086227, 139.08513498504877, 590.5832181798645, 508.27869656810515, 366.8780994762605, 335.59085750367359, 378.36875690329612, 410.40194190734638, 452.61993224528845, 391.28768876217561, 538.96313086056466, 374.88945414685435, 490.28911527259464, 537.56829961627489, 546.3271579754595, 666.76377722091888, 632.89968086202691, 651.74202407341045, 626.50214579492501, 601.95104777212816, 496.08247444738441, 410.34523246350375, 490.23291411592015, 400.7420978659095, 734.335012981369, 758.17076461157831, 627.05039402712896, 622.54393553145019, 723.69825543775255, 815.49010870302277, 820.9912919979048, 162.13878215651391, 137.33334457105434, 123.88511106101052, 192.02977579263279, 163.74826406432183, 252.04338239320873, 284.88942726223002, 261.23892378012113, 266.8204075674808, 230.24875217834187, 131.31510803741975, 62.471158049621565, 211.19387003570563, 234.63763607708827, 211.76316234107873, 190.96271049333978, 188.13429084801942, 75.232114036285466, 64.270417024089937, 226.8893655405482, 236.15218824768448, 198.41180467273441, 185.26654039594339, 223.19407808946315, 192.51018813264912, 229.33690010528389, 217.88998452022878, 277.49883909248138, 227.23013973154303, 202.68596305235798, 290.09998048768369, 152.748803439272, 153.3045593598352, 192.24684381408326, 289.46700974772688, 321.12588468218479, 269.61176463352575, 180.86789300045592, 203.99729743453804, 475.16632410648077, 608.62811181989116, 592.83243534795861, 640.90719581951009, 544.56518127847687, 576.27834384633411, 427.73489779400103, 579.84710455737866, 723.82722361218111, 829.4216521945965, 916.53602207624044, 941.03914714325913, 1030.5557567260767, 1080.0049042862036, 795.21346130081531, 890.02331493956706, 377.65487118716379, 246.96144097566037, 404.13436397963818, 831.7560431021451, 747.6025777725464, 966.13799685655965, 996.94935581376501, 215.52002414285681, 307.47172991108647, 294.6425849836674, 540.55263293259372, 309.57945025757539, 605.66861435035219, 550.12809674121024, 557.27934058354981, 450.4622517904948, 535.00425904923918, 834.53694537077206, 798.65863086995375, 469.97496396304967, 205.37129216322759, 154.66934950958924, 433.47098931458476, 745.86587886118673, 805.10970541183542, 903.25894703142978, 577.87855986507475, 589.71336901704842, 860.60928133776383, 681.44742235200886, 726.91107832327555, 575.65207949773242, 438.67834736088395, 697.49494848653012, 899.50326843249161, 766.19514912154398, 436.71423096030361, 465.55274827198281, 288.47768710953608, 407.91758915777103, 497.16351758558034, 529.84407620872707, 660.7316417646515, 886.61091096349844, 396.71347169784116, 281.7456145878424, 258.57063664357469, 288.8034852805435, 471.57769166498753, 444.02496208913249, 253.23716560063258, 760.08197553935383, 664.70701668719914, 597.96500254905004, 497.72528679269453, 695.38805156875696, 769.37815995895483, 695.2940389068209, 495.71346311827153, 714.21973757459136, 423.63276784156869, 190.04796884569816, 205.74525699591152, 197.30452550612887, 261.59042043512977, 247.38224014528453, 240.97399526639506, 454.75395371650308, 358.45927525915124, 366.06720902033123, 361.55499605099754, 460.12603971323369, 476.04116514727122, 460.63425625502549, 203.95726082652246, 97.458293935079652, 64.863795528569327, 50.044394619522677, 86.1310018120938, 67.016600520162271, 121.79986526683183, 168.89413992097363, 203.08994450499753, 404.49205677760716, 346.38137465334592, 257.68475153099598, 150.41586817954393, 250.40648591320007, 343.44516327546569, 396.78616574083702, 346.860059098531, 403.27026540535621, 157.06211142385561, 204.57881286022038, 232.9376119708995, 204.52959359090633, 98.671631110168633, 219.28127925560597, 202.21472008680954, 319.8556217026578, 108.61830672137972, 101.31153805329708, 146.58000292399876, 200.79640390053797, 202.86799098180356, 197.23895179161357, 316.6945733677241, 170.96144640323732, 173.74782747183846, 148.4331657714803, 239.53968533038548, 200.12543707951437, 186.34027300526458, 180.40956825501777, 201.35296447366201, 222.4764031556667, 305.82598516438185, 249.51560752271394, 202.91665059489355, 152.58909782674397, 134.76510870315443, 168.31200400778462, 102.83191229149337, 252.93394048230741, 224.31928322152598, 170.51605354996926, 142.09328967693892, 229.89719555340216, 218.42819460357723, 246.89522551109357, 314.06299567551537, 264.99148222367972, 267.33876485106578, 203.66061423420328, 188.92752777848943, 238.24947213926501, 95.66895194863416, 49.38075762070693, 338.16249698108328, 259.45158786825959, 248.79943409169189, 277.43819750286809, 212.10637213330105, 183.05087019369572, 245.28215916319112, 217.61293078647688, 3.8865289991381453, 164.34672553751247, 101.66431390128322, 120.53649737207472, 224.86370969783556, 199.04027006220346, 170.86323473054944, 350.32711682843149, 305.79996870407876, 334.4354092110143, 322.81080149811567, 272.18285035142856, 337.68406215226685, 257.44939751007678, 353.73130243662212, 264.91529088506786, 197.98268592945371, 159.97994308713717, 115.11577131164464, 121.86908528883448, 115.94123590973508]
        
    allmeans = [9986.3161744087811, 12090.366098774883, 12915.009604090483, 14022.151525000001, 5901.7550875000024, 5457.3001425714265, 5708.189530523814, 1988.3353072380962, 1500.1548253214328, 1967.1829715238096, 4896.3820903571395, 7483.7394826547688, 6481.8360868333366, 6464.5467525000022, 8074.5519845000026, 7672.4053735714297, 7030.1501250000019, 8184.3976350000003, 9912.1963800000012, 15143.332125536159, 18800.598667992457, 15186.375580000002, 14713.671179999998, 20034.026379999992, 11095.830930166669, 6633.8692210714244, 1468.9033227142843, 3205.4143960952356, 11010.407162119045, 14613.866865000004, 10604.492604999999, 12217.170919999997, 9194.1721649999981, 11185.159994999996, 16409.514949999997, 4837.2039299999997, 9475.4617299999991, 6670.9349881188118, 5340.6292422683282, 3072.5485814606745, 2237.4041171309532, 2164.2238905714312, 2648.8116882280856, 5388.2470218407652, 5074.5753277600852, 7229.8142061358803, 6317.0956503641219, 4351.3159127091039, 5514.3425431656642, 4180.1471146245049, 4849.2575395256918, 8968.9915266666649, 4055.0521919047642, 2067.1519517619072, 5078.5228255952425, 7136.2590019166764, 5045.0752267142834, 4406.16971583333, 4051.3276654999972, 3944.3090684999975, 4266.4051089880923, 3736.49870304762, 3273.3886923809564, 2356.1353169880949, 1813.2212350833322, 2336.6362078809525, 3574.6420825000018, 7911.855821250002, 6292.0514495000025, 3646.3017669761916, 3714.0655264761917, 2343.2825762261909, 4698.9466326190459, 1611.5593129761919, 1714.7078102453643, 5012.583576497078, 4000.1910655858082, 3904.6000924074074, 4165.0391969178081, 3457.9747768493148, 3334.0019900000002, 3354.2831838168458, 1987.5418239285709, 1800.5949533095256, 2041.1385847500032, 2675.053749166666, 3292.7511385595189, 2932.594993035711, 2247.362536250002, 2132.2044809523832, 1555.9903389285712, 1231.0138567261904, 837.47868149999931, 937.21003797379217, 1264.8004891250894, 4701.3829254523771, 4137.4877672857174, 3591.1803276190522, 3570.0072415357149, 3152.3938398690457, 3652.9739225357143, 3575.4244469999999, 4009.4945167499995, 3332.8841377499989, 2748.7058096666669, 3029.5467347500007, 3228.081175000003, 2396.6505910952405, 1524.3245747738092, 2830.4371100893495, 1919.0094080751396, 3581.3305421554337, 6725.3844040041395, 4558.2991650702097, 5057.5644832743446, 3506.6727991278258, 3053.4574407195423, 3807.8961334968644, 5405.5208479095108, 5368.0858054783339, 5549.4400600000008, 10474.622230000001, 11931.385950000007, 15017.09173, 12840.556960000002, 11101.325763333351, 11064.797831666681, 12743.293054999998, 11175.583271666672, 9107.6335099999924, 9041.9558616666563, 11504.91751333333, 12341.723734166671, 9449.8419950000007, 8444.9352114999929, 7573.5248664999972, 9071.4127840000037, 12083.185405000002, 11432.555919999999, 13654.520003333337, 9083.6944303333312, 4014.0472954523802, 2162.8239465238112, 4059.8626434166613, 2544.7652888452349, 1320.0160078571437, 4985.3498746071355, 2079.5134997619052, 1202.8762536785705, 1523.3058198571432, 1344.1762933809528, 1460.5337845238112, 9434.8183266666692, 13899.748955000003, 13777.462609642851, 10938.376790988093, 797.19117473809456, 4118.7703547904393, 14588.929723675745, 7761.5968777099215, 7060.7947690595065, 6637.6518373374001, 7064.7022559390634, 5992.3495719565835, 9365.2741422570762, 12148.189428844875, 11054.891497865143, 9262.6559238168811, 8341.6457879999998, 9475.941022779898, 10198.807703894401, 10324.113982935067, 9024.7456057083964, 11572.539137170827, 9014.9438585181178, 8543.9704168783719, 8871.1058917906739, 8840.2079457200707, 13508.689946476619, 2146.2531283736212, 4669.4361974296162, 8625.8889676456165, 9946.4837299999999, 14441.702245145631, 16645.150285971526, 16733.287684734423, 15043.099517784947, 14938.236159351147, 17725.658628816793, 18498.167104007633, 16683.009014770993, 16957.762372366415, 14925.641944999999, 8568.6895543333321, 6095.5107083333332, 2711.6798163228841, 5162.5569515595244, 5627.4272358945964, 6067.4964428114399, 6344.3782733333319, 7942.6178724087613, 9142.1836682420053, 9665.07061187215, 13822.161088532921, 12668.21468122548, 9688.1624458424903, 5239.7676944139203, 4803.3550450000012, 6359.1573450000005, 6503.7843016666666, 6374.1868366666677, 6983.2047816666673, 8427.0234200000014, 9097.0288099999998, 10455.123380000001, 7476.9656000000014, 6202.0476050000007, 5394.8098550000004, 7054.6821766666681, 7603.9857461476067, 5850.9380357023829, 6661.3263244881, 8657.080986870229, 7119.7794229445235, 6085.9896024043173, 5073.0255640181686, 5736.0315979985889, 6652.9736977892098, 7433.8829825271068, 8188.9680156219183, 11052.101176643633, 6155.725418771779, 8728.0607483576114, 10579.779342237902, 8398.3923246589166, 10416.836860224261, 9118.1578767123283, 9068.0996575342451, 10081.280688347833, 9165.493952576966, 7177.8655515004057, 5201.1682167477675, 7560.3289938321177, 6348.8492065166247, 12570.946603858276, 11719.0232865013, 12036.164166941749, 11463.653052536314, 13676.340649350646, 14494.556177570301, 14690.505785005174, 2988.8370065458571, 3028.7916493755924, 4301.9502267441794, 3684.2364896582567, 5190.0402198818601, 5360.7790888513982, 5667.2561033845295, 4808.2403885494878, 6071.9367459215027, 5425.3529846786141, 2901.8858108333343, 1399.9357079135652, 4583.7818387786883, 4275.6653916236801, 3998.2270479296253, 3719.48812668151, 3325.695176248867, 1150.2818491449727, 1130.0463116223759, 5400.440938152442, 4523.4484232056529, 3833.9303424657533, 4037.5500280659485, 3845.1994327174157, 4218.7909915062291, 4285.6262661338069, 4302.7701480165779, 4884.2504017591591, 4143.8314114382401, 3938.0166440915496, 5781.5556323868477, 2622.678033333334, 3148.1356048302323, 3225.5562731617724, 5235.3049701668315, 5473.8007255565726, 3903.5212183778535, 3325.8878312542165, 2112.315901264642, 4572.9230134325981, 11849.420989019256, 12929.611780000003, 12213.325788042326, 9805.5626716590687, 11024.072602667415, 9309.9140780777852, 10198.500806962436, 15636.180719712233, 18702.999080000001, 18574.331344999999, 18037.093039999996, 16101.457446339853, 13886.741053479011, 9042.4442320874059, 13309.122626914412, 6950.5506781306331, 8246.1182891666558, 16216.081112484764, 25825.504786704736, 18804.505580000001, 27705.996569999996, 46367.277481819016, 10017.937713950334, 5173.3461365767816, 4151.5300383333324, 17802.015979999996, 5050.5009123300988, 13479.846700738131, 15855.814541601623, 13528.136864830143, 8744.128743115265, 23881.393702811147, 22227.399036995732, 14702.223758940976, 7234.740436760404, 2588.564072034852, 2362.0769304185392, 7268.4601724758395, 18977.985262873626, 16148.321522653532, 16467.539144548875, 10765.78025, 13617.884005, 17518.976618705034, 12267.206955780308, 13063.68904630848, 10650.702282755292, 7255.4450006540437, 12575.35402779638, 18513.443094323582, 13938.734699829372, 8588.771447748326, 8140.8646867215111, 6611.4338591666628, 7539.5688733333345, 9751.3323157351879, 8379.3703970592542, 11059.336053496441, 16437.33673290108, 9216.46731, 5788.7503433333341, 5170.7387039380856, 7370.4267530957541, 12719.725314999998, 8190.0620718667915, 4655.1886210131333, 14974.451875000002, 12854.688394999999, 10487.520795, 8251.9860099999987, 13742.021485000001, 19318.954075000001, 13879.142324999997, 10065.523156666664, 11744.788035495498, 9962.0208814639664, 3527.1036006149634, 3294.1320722417718, 3763.154178822851, 4268.3681347648635, 4840.1796515699207, 4811.174648742277, 7692.8747877524174, 7340.012732065411, 6138.8381209061863, 6286.2725473576857, 7561.7888659447399, 8361.088386756428, 13457.108140000002, 3690.492552333335, 2224.0868275000003, 1487.171682833334, 1093.5730998333329, 1321.7264028333334, 1373.258627633471, 2144.4173271685795, 3043.6755812895531, 3143.996489066235, 6523.5352294741642, 5934.5333985910229, 4990.0016266849016, 2739.8495474584943, 4742.0040266469296, 6572.9888693856483, 7155.2827042119598, 6863.5345495410465, 6116.7487702376766, 2419.7735711280761, 4050.8302883868218, 3956.6945059445179, 3467.2131339655216, 1506.9171836013247, 3545.3920845110238, 3537.3124457382783, 4909.6165223923772, 3392.8187225332726, 2204.2172736989446, 2966.6230740362553, 4623.9876070000009, 3215.946543333333, 4740.5428196666653, 6284.1291786781603, 2922.0213493103447, 2857.8738484482765, 3048.3198459793634, 4406.1976664431349, 3569.8472556892757, 3022.0442372881357, 3524.2466118789689, 3504.0576659038902, 3867.8956027226463, 4879.1839237799495, 4915.2892257390968, 3237.8875941233559, 2718.1025665637485, 2665.3027655889141, 2919.9559187361174, 1703.5718679495994, 7494.7329729363873, 3218.8056925305546, 2269.3696166032964, 1957.0283873706226, 3671.2610040509271, 3037.5777949074081, 3609.1863923611118, 4557.038588001803, 4888.1120763422823, 5377.7672294506747, 3729.0884295866731, 3649.0539364232136, 3781.7899099071178, 1421.8421663727954, 848.81947754014664, 5337.8241659156765, 4110.9638773102433, 4082.9516662219307, 5099.3659241024325, 3791.0116214677687, 3758.425030506407, 4258.8667531102292, 4172.6082119580178, 83.878501145632853, 3047.6518759298951, 2654.0358297177722, 2877.2035334904995, 4653.8155204267659, 3074.263697929292, 2568.9580680555546, 5119.8404292929326, 6026.9956694637713, 6481.3391725015917, 6294.1150733879031, 6070.174678362574, 6211.4814666490392, 4019.0181150446874, 5864.138336183637, 5436.2220986894072, 3276.6337737881504, 3004.7829528036964, 2068.6569295862932, 2247.527942192733, 2304.8996403140186]

    ratio = [s/m for m, s in zip (allmeans, allstdevs)]
    print(np.mean(ratio))
    
    plt.plot(allmeans, allstdevs, 'bx')
    plt.xlabel("Mean estimated population of zip code")
    plt.ylabel("SStandard deviation of population estimates")
    plt.show()
    
    plt.plot(allmeans, ratio, 'rx')
    plt.xlabel("Mean estimated population of zip code")
    plt.ylabel("Coefficient of variation of population estimtes")
    plt.show()
    
    
 
           
