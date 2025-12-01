import pandas as pd
import folium
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm  
from get_score import calculate_city_score

# CSV 파일 읽기
df = pd.read_csv('regions.csv')
df['full_address'] = df['district'] + ", " + df['city'] + ", " + df['country']

print("=== 분석 대상 목록 ===")
print(df[['district', 'full_address']].head())

results = []

# 주소 분석
for idx, row in tqdm(df.iterrows(), total=len(df)):
    address = row['full_address']
    region_name = row['district']

    score, lat, lon = calculate_city_score(address)

    if score is not None:
        results.append({
            'region': region_name,  
            'full_address': address,
            'score': score,
            'lat': lat,
            'lon': lon
        })

# 결과 저장 
result_df = pd.DataFrame(results)
result_df = result_df.sort_values(by='score', ascending=False)
result_df.to_csv('final_score_result.csv', index=False, encoding='utf-8-sig')

# 막대 그래프 제작
if not result_df.empty:
    plt.figure(figsize=(10, 6))
    sns.barplot(data=result_df, x='score', y='region', palette='viridis')
    plt.title("Living Infrastructure Score by Region")
    plt.xlabel("Score")
    plt.savefig("result_chart.png") 
    plt.show()

# 지도 제작
if not result_df.empty:
    m = folium.Map(location=[result_df.iloc[0]['lat'], result_df.iloc[0]['lon']], zoom_start=11)
    for idx, row in result_df.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=10 + (row['score'] / 10),
            popup=f"{row['region']}: {row['score']:.1f}",
            color='green' if row['score'] >= 80 else 'blue',
            fill=True
        ).add_to(m)
    m.save("result_map.html")
    print("저장 완료")