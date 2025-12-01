import osmnx as ox
from get_nearest_distance import calculate_nearest_distance 

ox.settings.use_cache = True
ox.settings.log_console = True

def get_score(full_address):

    # 분석할 시설물 정의 
    point_config = {
        'convenience': {'shop': 'convenience'},   
        'subway': {'station': 'subway'},            
        'pharmacy': {'amenity': 'pharmacy'},      
        'park': {'leisure': 'park'},              
        'supermarket': {'shop': 'supermarket'}           
    }

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
        # 1. 데이터 가져오기
        place = full_address
        print(f"Downloading: {place}")
        G = ox.graph_from_place(place, network_type='walk')
        points = ox.features_from_place(place, tags=download_tags)

        # 2. 중심 좌표 구하기
        gdf_nodes = ox.graph_to_gdfs(G, edges=False)
        center_lat = gdf_nodes.y.mean() 
        center_lon = gdf_nodes.x.mean()

        #좌표계 변환
        Graph_proj = ox.project_graph(G, to_crs='EPSG:5179')
        points_proj = points.to_crs('EPSG:5179')
        points_proj['geometry'] = points_proj['geometry'].centroid

        #노드 거리 계산
        house_node = ox.distance.nearest_nodes(G, center_lon, center_lat)
        house_stats = {}
        print(f"=== {place} 분석 시작 ===")

        for label, tag in point_config.items():
            key = list(tag.keys())[0]
            val = list(tag.values())[0]
            
            dist = calculate_nearest_distance(Graph_proj, house_node, points_proj, key, val)

            if dist is not None:
                print(f" - [{label}] 거리: {dist:.1f}m")
                house_stats[f'dist_{label}'] = dist
            else:
                print(f" - [{label}] 없음")
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
        return total_score, center_lat, center_lon
    except Exception as e:
        print(f"Error in {place}: {e}")
        return None, None, None 