import osmnx as ox
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point

ox.settings.use_cache = True
ox.settings.log_console = False

# 분석할 시설물 정의 
point_config = {
    'subway': {'station': 'subway'},
    'bus': {'highway': 'bus_stop'}, 
    'convenience': {'shop': 'convenience'},  
    'supermarket': {'shop': 'supermarket'}, 
    'cafe': {'amenity': 'cafe'},           
    'hospital': {'amenity': 'clinic'},
    'public': {'amenity': 'community_centre'},
    'bank': {'amenity': 'bank'}, 
    'school': {'amenity': 'school'},      
    'park': {'leisure': 'park'},                
}

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
            bounding_poly = gpd.GeoSeries(node_points).union_all().convex_hull
            isochrone_polys.append((trip_time, bounding_poly))
            
    return isochrone_polys

def get_nearest_distance(Graph_proj, center_node, points_proj, target_key, target_val):
    
    #태그에 맞는 시설물 필터링
    if points_proj.empty or target_key not in points_proj.columns:
        return None, None
        
    if isinstance(target_val, list):
        target_pois = points_proj[points_proj[target_key].isin(target_val)]
    else:
        target_pois = points_proj[points_proj[target_key] == target_val]
    
    if target_pois.empty:
        return None, None
    
    #좌표 추출
    target_x = target_pois.geometry.x.values
    target_y = target_pois.geometry.y.values

    #가장 가까운 노드 찾기
    target_nodes = ox.distance.nearest_nodes(Graph_proj, target_x, target_y)

    #최단 거리 계산
    min_dist = float('inf')

    nearest_node = None
    unique_target_nodes = list(set(target_nodes))

    for target in unique_target_nodes:
        try:
            dist = nx.shortest_path_length(Graph_proj, source=center_node, target=target, weight='length')
            if dist < min_dist:
                min_dist = dist
                nearest_node = target
        except nx.NetworkXNoPath:
            continue
    if min_dist != float('inf'):
        return min_dist, nearest_node 
    else:
        return None, None   

def get_score(lat, lon, user_weights=None, dist=3000):

    # 다운로드용 태그 제작
    download_tags = {}
    for conf in point_config.values():
        for k, v in conf.items():
            if k in download_tags:
                if isinstance(download_tags[k], list): download_tags[k].append(v)
                else: download_tags[k] = [download_tags[k], v]
            else:
                download_tags[k] = v

    try:
        # 데이터 가져오기
        G = ox.graph_from_point((lat, lon), dist=dist, network_type='walk')
        
        try:
            points = ox.features_from_point((lat, lon), tags=download_tags, dist=dist)
        except:
            points = gpd.GeoDataFrame()

        # 좌표계 변환
        Graph_proj = ox.project_graph(G, to_crs='EPSG:5179')

        if not points.empty:
            points_proj = points.to_crs('EPSG:5179')
            # 건물(Polygon)인 경우 중심점(Centroid)으로 변환
            points_proj['geometry'] = points_proj['geometry'].centroid
        else:
            points_proj = points

        # 중심 노드 찾기 (클릭한 좌표와 가장 가까운 도로 교차로)
        center_node = ox.distance.nearest_nodes(G, lon, lat)

        center_stats = {} 
        nearest_locs = {}
        total_score = 0
        total_weight_sum = 0

        if user_weights is None:
            weights = {key: 1.0 for key in point_config.keys()}
        else:
            weights = user_weights

        for label, tag in point_config.items():
            key = list(tag.keys())[0]
            val = list(tag.values())[0]
            
            dist, node = get_nearest_distance(Graph_proj, center_node, points_proj, key, val)

            if dist is not None:
                print(f" - [{label}] 거리: {dist:.1f}m")
                center_stats[f'dist_{label}'] = dist
                if node is not None:
                    node_data = G.nodes[node]
                    nearest_locs[label] = [node_data['y'], node_data['x']]
            else:
                print(f" - [{label}] 없음")
                center_stats[f'dist_{label}'] = 9999

        # 점수 산출
        for cat, weight in weights.items():
            dist = center_stats.get(f'dist_{cat}', 9999)

            if dist < 1000:
                score = (1000 - dist) / 10 
            else:
                score = 0
            total_score += score * weight
            total_weight_sum += weight
        
        if total_weight_sum > 0:
            final_score = total_score / total_weight_sum
        else:
            final_score = 0

        return {
            'score': final_score,
            'stats': center_stats,
            'nearest_locs': nearest_locs,
            'G_proj': Graph_proj,
            'center_node': center_node
        }
    except Exception as e:
        print(f"Error at {lat}, {lon}: {e}")
        return None

