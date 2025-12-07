# 생활 인프라 지도 플랫폼🏡

## Project Overview

**생활 인프라 지도 플랫폼**은 사용자가 선택한 위치를 기반으로 주변 생활 편의 시설(인프라)의 접근성을 분석하고 시각화해주는 서비스입니다.

- **📍 최단 거리 분석:** 클릭한 위치에서 가장 가까운 인프라(지하철, 마트, 병원 등)까지의 거리를 분석합니다.
- **⏱️ 등시선(Isochrone) 시각화:** 도보 기준으로 5분, 10분, 15분 내 도달 가능한 범위를 지도 위에 다각형으로 표현합니다.
- **📊 접근성 점수 산출:** 인프라별 거리와 사용자가 설정한 가중치를 반영하여 '종합 생활 인프라 접근성 점수'(0~100점)를 계산합니다.

## How to use

1. 아래 나오는 오픈 소스 소프트웨어들을 다운로드합니다.
   
   ```tsx
    pip install osmnx
    pip install shapely
    pip install folium
    pip install streamlit
    pip install scikit-learn
    ```

2. 명령 프롬포트에서 프로젝트 폴더로 이동합니다. (예시)

    ```tsx
    cd C:\Users\Username\Downloads\oss_project-main\codes
    ```

3. 다음 명령어를 입력하여 Streamlit 앱을 실행합니다.

    ```tsx
    streamlit run main.py
    ```

Tip: 실행을 종료하려면 터미널에서 Ctrl + C를 누르세요.

## 💻Results

![images](https://github.com/minho-05/oss_project/blob/main/images/result%201.png)

### 1️⃣ 사이드바 설정

- 연령대별 추천: 청년층, 중장년층 등 맞춤형 가중치 프리셋 제공
- 직접 설정: 슬라이더를 통해 각 시설별 중요도(가중치)를 사용자가 정의 가능

![images](
![images](

### 2️⃣ 지역 이동 및 보행 속도 설정

- 지역 검색: 특정 지역명(예: Yeouido, Seoul)을 입력하여 지도 이동
- 보행 속도: 본인의 걷는 속도에 맞춰 등시선 범위 조정 (기본: 75m/min)

![images](
![images](

### 3️⃣ 위치 분석

- 지도상의 특정 지점을 클릭하면 해당 좌표(위도, 경도)를 기준으로 분석을 시작합니다.

![images](

### 4️⃣ 분석 결과(예시)

- 종합 점수 및 인프라별 최단 거리 표기
- 시각화: 등시선(5/10/15분) 및 시설물 마커 표시

![images](
![images](

## Major Functions

### 등시선 계산 함수

- 도로망 네트워크를 기반으로 도보 이동 가능 범위를 다각형(Polygon)으로 계산합니다.

    ```tsx
    def get_isochrone(Graph, center_node, trip_times=[5, 10, 15], speed=75):
        ...
        return isochrone_polys
    ```

### 최단거리 분석 함수

- 선택된 지점과 특정 인프라 간의 최단 도보 거리를 계산합니다.

    ```tsx
    def get_nearest_distance(Graph_proj, center_node, points_proj, target_key, target_val):
        ...
        return min_dist, best_node
    ```

### 점수 측정 함수

- 거리 데이터와 가중치를 종합하여 최종 접근성 점수를 도출합니다.

    ```tsx
    def get_score(lat, lon, user_weights=None, dist=3000):
        ...
        return final_score_data
    '''

## Reference

- https://www.openstreetmap.org
- https://wiki.openstreetmap.org/wiki/OSMnx
- https://osmnx.readthedocs.io/en/stable

## Made by

- 24100706 김민호
