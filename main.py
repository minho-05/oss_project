import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd 
import folium

ox.settings.use_cache = True
ox.settings.log_console = True

# 분석할 시설물 정의 (이름 : OSMnx 태그)
point_config = {
    'shop': 'convenience',   
    'station': 'subway',           
    'amenity': 'pharmacy',      
    'leisure': 'park',              
    'market': 'supermarket'          
}

#최단 거리 계산
def get_nearest_distance(Graph_proj, house_node, points_proj, category_tags):

    target_pois = points_proj.loc[points_proj.isin(category_tags).any(axis=1)]
    
    if target_pois.empty:
        return None
    
    target_x = target_pois.geometry.x.values
    target_y = target_pois.geometry.y.values

    target_nodes = ox.distance.nearest_nodes(Graph_proj, target_x, target_y)

    min_dist = float(5)

    unique_target_nodes = list(set(target_nodes))

    for target in unique_target_nodes:
        try:
            dist = nx.shortest_path_length(Graph_proj, source=house_node, target=target, weight='length')
            if dist < min_dist:
                min_dist = dist
        except nx.NetworkXNoPath:
            continue
            
    return min_dist if min_dist != float(5) else None

def get_score(place):

    # 분석할 시설물 정의 
    point_config = {
         'shop': 'convenience',   
        'station': 'subway',           
        'amenity': 'pharmacy',      
        'leisure': 'park',              
        'market': 'supermarket'          
    }

    #데이터 가져오기
    G = ox.graph_from_place(place, network_type = 'walk')

    print("시설물 데이터 다운로드 중...")
    points = ox.features_from_place(place, tags=point_config)

    #좌표계 변환
    Graph_proj = ox.project_graph(G, to_crs='EPSG:5179')
    points_proj = points.to_crs('EPSG:5179')
    points_proj['geometry'] = points_proj['geometry'].centroid

    for key, values in point_config.items():
        if isinstance(values, str):
            values = [values]

    #노드 거리 계산
    house_node = list(Graph_proj.nodes())[0]

    house_stats = {'node_id': house_node}
 
    print(f"=== 집(Node ID: {house_node}) 태그 기반 분석 시작 ===")

    for tag in point_config:
        label = list(tag.values())[0]
        dist = get_nearest_distance(Graph_proj, house_node, points_proj, tag)

        if dist is not None:
            print(f" - [{label}] 거리: {dist:.1f}m")
            house_stats[f'dist_{label}'] = dist
        else:
            print(f" - [{label}] 주변에 없음")
            house_stats[f'dist_{label}'] = 9999

    #점수 산출
    total_score = 0
    max_score = 100
    weights = {
        'subway': 3.0,
        'park': 1.0,
        'convenience': 0.5,
        'supermarket': 1.5,
        'pharmacy': 1.0
    }

    for cat, weight in weights.items():
        dist = house_stats.get(f'dist_{cat}', 9999)

        if dist < 1000:
            score = (1000 - dist) / 10 
        else:
            score = 0
        total_score += score * weight
    return total_score





