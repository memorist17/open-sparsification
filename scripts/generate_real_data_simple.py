#!/usr/bin/env python3
"""
シンプルな実際の地理データ生成スクリプト
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import asyncio

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_fetcher_corrected import fetch_real_geographic_data
from src.network_builder_corrected import create_urban_network
from src.metrics.multi_nodality import MultiNodalityCalculator
from src.metrics.sparsity import SparsityCalculator
from src.metrics.permeability import PermeabilityCalculator
from src.metrics.overlap import OverlapCalculator
from src.metrics.emergence import EmergenceCalculator
from src.metrics.resilience import ResilienceCalculator
from src.utils.config import get_config

def generate_real_data():
    """実際の地理データから分析結果を生成"""
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "real_analysis_results.csv"

    config = get_config()
    num_locations = config['data']['sampling']['num_locations']
    
    # 日本の主要都市周辺の地点を選択
    major_cities = [
        (35.6762, 139.6503),  # 東京
        (34.6937, 135.5023),  # 大阪
        (35.1815, 136.9066),  # 名古屋
        (43.0642, 141.3469),  # 札幌
        (33.5904, 130.4017),  # 福岡
        (38.2682, 140.8694),  # 仙台
        (35.0116, 135.7681),  # 京都
        (34.3853, 132.4553),  # 広島
        (31.9119, 131.4239),  # 宮崎
        (36.5658, 136.6566),  # 金沢
    ]
    
    locations = []
    for i in range(num_locations):
        if i < len(major_cities):
            # 主要都市の座標を使用
            lat, lon = major_cities[i]
        else:
            # 主要都市周辺でランダムに選択
            city_idx = i % len(major_cities)
            base_lat, base_lon = major_cities[city_idx]
            lat = base_lat + np.random.uniform(-0.5, 0.5)
            lon = base_lon + np.random.uniform(-0.5, 0.5)
        
        locations.append({
            'location_id': i,
            'latitude': lat,
            'longitude': lon
        })
    
    results = []
    
    # 指標計算器を初期化
    multi_nodality_calc = MultiNodalityCalculator(config)
    sparsity_calc = SparsityCalculator(config)
    permeability_calc = PermeabilityCalculator(config)
    overlap_calc = OverlapCalculator(config)
    emergence_calc = EmergenceCalculator(config)
    resilience_calc = ResilienceCalculator(config)
    
    print(f"実際の地理データから指標計算開始: {num_locations}地点")
    
    for i, location in enumerate(locations):
        lat, lon = location['latitude'], location['longitude']
        location_id = location['location_id']
        
        print(f"指標計算中: {i+1}/{num_locations} - 緯度: {lat:.3f}, 経度: {lon:.3f}")
        
        try:
            # 実際の地理データを取得
            buildings_gdf, roads_gdf = fetch_real_geographic_data(lat, lon, 2000)
            
            if buildings_gdf.empty and roads_gdf.empty:
                print(f"地点 {location_id} ({lat:.3f}, {lon:.3f}) で建物・道路データが見つかりませんでした。スキップします。")
                continue
            
            # ネットワーク構築
            network_graph = create_urban_network(buildings_gdf, roads_gdf)
            
            # 指標を計算
            metrics = {}
            metrics['multi_nodality'] = multi_nodality_calc.calculate(buildings_gdf)
            metrics['sparsity'] = sparsity_calc.calculate(buildings_gdf)
            metrics['permeability'] = permeability_calc.calculate(buildings_gdf, roads_gdf)
            metrics['overlap'] = overlap_calc.calculate(buildings_gdf)
            metrics['emergence'] = emergence_calc.calculate(buildings_gdf, network_graph)
            metrics['resilience'] = resilience_calc.calculate(network_graph)
            
            result = {
                'location_id': location_id,
                'latitude': lat,
                'longitude': lon,
                **metrics
            }
            results.append(result)
            
        except Exception as e:
            print(f"地点 {location_id} ({lat:.3f}, {lon:.3f}) の指標計算エラー: {e}")
            continue
    
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_path, index=False)
        print(f"実際の分析結果を {output_path} に保存しました。")
        print(f"生成されたデータフレームの統計情報:\n{df_results.describe()}")
    else:
        print("計算された指標データがありませんでした。")

if __name__ == "__main__":
    generate_real_data()

