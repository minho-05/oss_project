import osmnx as ox
import networkx as nx

ox.settings.use_cache = True
ox.settings.log_console = True

def get_nearest_distance(Graph_proj, house_node, points_proj, target_key, target_val):
    
    #태그에 맞는 시설물 필터링
    if target_key not in points_proj.columns:
        return None
        
    target_pois = points_proj[points_proj[target_key] == target_val]
    
    if target_pois.empty:
        return None
    
    #좌표 추출
    target_x = target_pois.geometry.x.values
    target_y = target_pois.geometry.y.values

    #가장 가까운 노드 찾기
    target_nodes = ox.distance.nearest_nodes(Graph_proj, target_x, target_y)

    #최단 거리 계산
    min_dist = float('inf') 

    unique_target_nodes = list(set(target_nodes))

    for target in unique_target_nodes:
        try:
            dist = nx.shortest_path_length(Graph_proj, source=house_node, target=target, weight='length')
            if dist < min_dist:
                min_dist = dist
        except nx.NetworkXNoPath:
            continue
            
    return min_dist if min_dist != float('inf') else None