import osmnx as ox
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, Polygon

place = "Seoul, South Korea"
G = ox.graph_from_place(place, network_type='drive')
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

start_point = (37.5665, 126.9780) 
center_node = ox.nearest_nodes(G, start_point[1], start_point[0])


trip_times = [30, 60, 90] 
travel_speed = 4.5 

isochrone_polys = []
for minutes in trip_times:
    seconds = minutes * 60
    subgraph = nx.ego_graph(G, center_node, radius=seconds, distance='travel_time')

    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]

    bounding_poly = gpd.GeoSeries(node_points).unary_union.convex_hull
    isochrone_polys.append(bounding_poly)

gdf = gpd.GeoDataFrame(geometry=isochrone_polys, crs=G.graph['crs'])
gdf.explore() 