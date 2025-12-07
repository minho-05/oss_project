import osmnx as ox
import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from function import get_score, get_isochrone, point_config

st.set_page_config(layout="wide", page_title="생활 인프라 분석기")
st.title("🏡 생활 인프라 지도 플랫폼")
st.markdown("---")

# 사이드바 입력
with st.sidebar:
    st.header("⚙️ 설정")

    # 연령대 선택 기능
    age_group = st.selectbox(
        "당신의 연령대는?",
        ("청년층 (20~30대)", "중장년층 (40~50대)", "노년층 (60대 이상)", "직접 설정")
    )

    # 가중치 정의
    if age_group == "청년층 (20~30대)":
        custom_weights = {
            'subway': 4.0, 'bus': 2.0, 'convenience': 5.0,  'supermarket': 1.0, 'cafe': 4.0,
            'hospital': 1.0, 'public': 1.0, 'bank': 1.0, 'school': 0.0, 'park': 2.0
        }

    elif age_group == "중장년층 (40~50대)":
        custom_weights = {
            'subway': 3.0, 'bus': 3.0, 'convenience': 1.0,  'supermarket': 5.0, 'cafe': 3.0,
            'hospital': 3.0, 'public': 4.0, 'bank': 4.0, 'school': 4.0, 'park': 3.0
        }

    elif age_group == "노년층 (60대 이상)":
        custom_weights = {
            'subway': 2.0, 'bus': 4.0, 'convenience': 1.0,  'supermarket': 3.0, 'cafe': 1.0,
            'hospital': 5.0, 'public': 3.0, 'bank': 3.0, 'school': 0.0, 'park': 4.0
        }
        
    else: # 직접 설정
        st.write("가중치 직접 조정(0 ~ 5)")
        custom_weights = {
            'subway': st.slider("지하철 중요도", 0.0, 5.0, 2.5, key='w_subway'),
            'bus': st.slider("버스 중요도", 0.0, 5.0, 2.5, key='w_bus'),
            'convenience': st.slider("편의점 중요도", 0.0, 5.0, 2.5, key='w_conv'),  
            'supermarket': st.slider("마트 중요도", 0.0, 5.0, 2.5, key='w_mart'),
            'cafe': st.slider("카페 중요도", 0.0, 5.0, 2.5, key='w_cafe'),           
            'hospital': st.slider("병원 중요도", 0.0, 5.0, 2.5, key='w_hosp'),
            'public': st.slider("관공서 중요도", 0.0, 5.0, 2.5, key='w_public'),
            'bank': st.slider("은행 중요도", 0.0, 5.0, 2.5, key='w_bank'),
            'school': st.slider("학교 중요도", 0.0, 5.0, 2.5, key='w_school'),      
            'park': st.slider("공원 중요도", 0.0, 5.0, 2.5, key='w_park')
        }

    st.markdown("---")

    location_input = st.text_input("지역 이동 (검색)", value="Yeouido, Seoul")
    
    # 검색 버튼 기능
    if st.button("📍 이 지역으로 지도 이동"):
        try:
            coords = ox.geocode(location_input)
            st.session_state.center = coords
            st.session_state.zoom = 14
        except:
            st.error("지역을 찾을 수 없습니다.")

    st.markdown("---")
    speed = st.slider("보행 속도 (m/min)", 50, 100, 75, help="성인 평균 75m/min")
    st.caption("등시선 계산에 사용됩니다.")

# 지도 초기화
if 'center' not in st.session_state:
    st.session_state.center = [37.5665, 126.9780]

map_container = st.container()

# 세션 상태 초기화
if 'last_coords' not in st.session_state:
    st.session_state.last_coords = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# 지도 클릭 인터페이스
with map_container:
    st.subheader("1️⃣ 지도에서 분석하고 싶은 위치를 클릭하세요")
    m = folium.Map(location=st.session_state.center, zoom_start=14)
    output = st_folium(m, width="100%", height=500, returned_objects=["last_clicked"])

# 클릭 시 분석 실행
if output and output.get('last_clicked'):
    lat = output['last_clicked']['lat']
    lon = output['last_clicked']['lng']

    if (lat, lon) != st.session_state.last_coords:
            
        # 분석 시작 전에 좌표 기억해두기
        st.session_state.last_coords = (lat, lon)
    
        with st.spinner(f"📍 좌표({lat:.4f}, {lon:.4f}) 데이터 분석 중..."):
            data = get_score(lat, lon, user_weights=custom_weights)
            st.session_state.analysis_result = data

# 저장된 데이터가 있으면 작동
if st.session_state.get('analysis_result'):
    data = st.session_state.analysis_result

    if data:
        st.markdown("---")
        st.subheader("2️⃣ 분석 결과")
        score = data['score']
        stats = data['stats']
        nearest_locs = data['nearest_locs']
        Graph_proj = data['G_proj']
        center_node = data['center_node']
    
        # 등시선 계산
        polys = get_isochrone(Graph_proj, center_node, speed=speed)
    
        # 결과 지도 
        result_map = folium.Map(location=[lat, lon], zoom_start=15)
    
        # 등시선 폴리곤 시각화
        colors = {5: '#d32f2f', 10: '#f57c00', 15: '#fbc02d'} 
    
        for trip_time, poly in polys:
            # 미터 좌표계를 위경도 좌표계 변환 
            poly_geo = gpd.GeoSeries([poly], crs='EPSG:5179').to_crs('EPSG:4326')
            folium.GeoJson(
                poly_geo,
                style_function=lambda x, color=colors[trip_time]: {
                    'fillColor': color, 'color': color, 'weight': 1, 'fillOpacity': 0.4
                },
                tooltip=f"{trip_time}분 이내 도달 가능"
            ).add_to(result_map)

        # 마커 추가
        icon_map = {
            'subway': 'subway',
            'bus': 'bus',
            'convenience': 'shopping-basket',
            'supermarket': 'shopping-cart',
            'cafe': 'coffee', 
            'hospital': 'medkit',
            'public': 'university',
            'bank': 'krw',
            'school': 'graduation-cap',
            'park': 'tree', 
        }

        display_items = {
            ('subway', '🚇 지하철'),
            ('bus', '🚏 버스'), 
            ('convenience', '🏪 편의점'),  
            ('supermarket', '🛒 마트'), 
            ('cafe', '☕ 카페'),           
            ('hospital', '🏥 병원'),
            ('public', '🏛️ 관공서'), 
            ('bank', '🏦 은행'),
            ('school', '🏫 학교'),      
            ('park', '🌳 공원')
        }

        name_map = dict(display_items)

        placed_counts = {}
    
        for label, coords in nearest_locs.items():
            icon_name = icon_map.get(label, 'info-sign')
            distance_val = stats.get(label, stats.get(f"dist_{label}", 0))
 
            korean_name = name_map.get(label, label)

            #아이콘 겹침 방지
            coord_key = tuple(coords)
            
            if coord_key in placed_counts:
                placed_counts[coord_key] += 1
                count = placed_counts[coord_key]

                offset = 0.0001

                adj_lat = coords[0] + (count * offset) 
                adj_lon = coords[1] + (count * offset)
            else:
                placed_counts[coord_key] = 0
                adj_lat = coords[0]
                adj_lon = coords[1]

            folium.Marker(
                location=[adj_lat, adj_lon],
                popup=f"{korean_name}: {distance_val:.0f}m",
                tooltip=korean_name, 
                icon=folium.Icon(color='blue', icon=icon_name, prefix='fa')
            ).add_to(result_map)

        folium.Marker(
            [lat, lon], 
            popup="내 위치", 
            icon=folium.Icon(color='black', icon='home')
        ).add_to(result_map)
    
        # 지도 생성
        st_folium(result_map, width="100%", height=500)
        st.markdown("### 📊 상세 접근성 점수")
        col_score, col_empty = st.columns([1, 2])
        with col_score:
            st.metric(label="🏆 종합 생활 인프라 접근성 점수", value=f"{score:.1f}점", delta="100점 만점")
    
        st.markdown("#### 📏 인프라별 최단 거리")

        grid_cols = st.columns(4)

        for idx, (key, name) in enumerate(display_items):

            dist = stats.get(f'dist_{key}', stats.get(key, 9999))

            if dist >= 9000:
                dist_text = "없음"
            else:
                dist_text = f"{dist:.0f} m"
        
            with grid_cols[idx % 4]:
                st.metric(label=name, value=dist_text)
            
        st.caption(" 거리는 도보 이동 기준 최단 거리입니다.")

    else:
        st.error("데이터를 불러오지 못했습니다. (도로망이 없는 곳일 수 있음)")