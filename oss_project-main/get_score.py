import osmnx as ox
import geopandas as gpd
from get_nearest_distance import get_nearest_distance 

ox.settings.use_cache = True
ox.settings.log_console = False

def get_score(lat, lon, dist=1500):

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
        total_score = 0
        weights = {
            'subway': 3.0,
            'park': 1.0,
            'convenience': 0.5,
            'supermarket': 1.5,
            'pharmacy': 1.0
        }

        for label, tag in point_config.items():
            key = list(tag.keys())[0]
            val = list(tag.values())[0]
            
            dist = get_nearest_distance(Graph_proj, center_node, points_proj, key, val)

            if dist is not None:
                print(f" - [{label}] 거리: {dist:.1f}m")
                center_stats[f'dist_{label}'] = dist
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
        return {
            'score': total_score,
            'stats': center_stats,
            'G_proj': Graph_proj,
            'center_node': center_node
        }
    except Exception as e:
        print(f"Error at {lat}, {lon}: {e}")
        return None