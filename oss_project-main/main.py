import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from get_score import get_score
from get_isochrone import get_isochrone

st.set_page_config(layout="wide", page_title="생활 인프라 분석기")
st.title("🏡 생활 편의성 지도 플랫폼")
st.markdown("---")

# 사이드바 입력
with st.sidebar:
    st.header("⚙️ 설정")
    location_input = st.text_input("지역 이동 (검색)", value="Yeouido, Seoul")
    
    # 검색 버튼 기능
    if st.button("📍 이 지역으로 지도 이동"):
        import osmnx as ox
        try:
            coords = ox.geocode(location_input)
            st.session_state.center = coords
            st.session_state.zoom = 14
        except:
            st.error("지역을 찾을 수 없습니다.")

    st.markdown("---")
    speed = st.slider("보행 속도 (km/h)", 3.0, 6.0, 4.5, help="성인 평균 4.5km/h")
    st.caption("등시선 계산에 사용됩니다.")

# 지도 초기화
if 'center' not in st.session_state:
    st.session_state.center = [37.5665, 126.9780]

map_container = st.container()

# 지도 클릭 인터페이스
with map_container:
    st.subheader("1️⃣ 지도에서 분석하고 싶은 위치를 클릭하세요")
    m = folium.Map(location=st.session_state.center, zoom_start=14)
    output = st_folium(m, width="100%", height=500)

# 클릭 시 분석 실행
if output['last_clicked']:
    lat = output['last_clicked']['lat']
    lon = output['last_clicked']['lng']

    st.markdown("---")
    st.subheader("2️⃣ 분석 결과 리포트")
    
    with st.spinner(f"📍 좌표({lat:.4f}, {lon:.4f}) 주변 데이터를 분석 중입니다..."):
        data = get_score(lat, lon)
        
        if data:
            score = data['score']
            stats = data['stats']
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
            folium.Marker([lat, lon], popup="내 위치", icon=folium.Icon(color='black', icon='home')).add_to(result_map)
            
            # 지도 생성
            st_folium(result_map, width="100%", height=500)
            st.markdown("### 📊 상세 접근성 점수")
            col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
            with col1:
                # 종합 점수 
                st.metric(label="🏆 종합 생활 편의 점수", value=f"{score:.1f}점", delta="100점 만점")
            
            labels = {
                'subway': '🚇 지하철역', 
                'park': '🌳 공원', 
                'convenience': '🏪 편의점',
                'supermarket': '🛒 대형마트',
                'pharmacy': '💊 약국'
            }

            cols = [col2, col3, col4, col2, col3]

            idx = 0
            for key, name in labels.items():
                dist = stats.get(key, 9999)
                
                # 거리 텍스트 포맷팅
                if dist >= 9000:
                    dist_text = "없음"
                else:
                    dist_text = f"{dist:.0f} m"
                
                # 적절한 컬럼에 배치
                if idx < len(cols):
                    with cols[idx]:
                        st.metric(label=name, value=dist_text)
                    idx += 1
        else:
            st.error("데이터를 불러오지 못했습니다. (도로망이 없는 곳일 수 있음)")