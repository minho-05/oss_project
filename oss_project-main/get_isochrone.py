import networkx as nx
import geopandas as gpd
from shapely.geometry import Point

def get_isochrone(Graph, center_node, trip_times=[5, 10, 15], speed=4.5):
    meter_per_minute = speed * 1000 / 60 
    
    # 모든 도로에 '통행 시간(time)' 속성 추가
    for u, v, k, data in Graph.edges(data=True, keys=True):
        data['time'] = data['length'] / meter_per_minute

    isochrone_polys = []
    
    # 15분, 10분, 5분 순서로 계산
    for trip_time in sorted(trip_times, reverse=True):
        subgraph = nx.ego_graph(Graph, center_node, radius=trip_time, distance='time')
        
        # 다각형(Polygon) 생성
        node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
        if len(node_points) > 0:
            bounding_poly = gpd.GeoSeries(node_points).union_all.convex_hull
            isochrone_polys.append((trip_time, bounding_poly))
            
    return isochrone_polys