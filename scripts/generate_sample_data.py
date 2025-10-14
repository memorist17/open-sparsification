#!/usr/bin/env python3
"""
サンプルデータ生成スクリプト

日本全国300地点の分析結果サンプルデータを生成します。
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.config import load_config
from src.utils.logger import setup_logger

def get_japanese_cities():
    """日本の主要都市のリストを取得"""
    major_cities = [
        {"name": "東京", "lat": 35.6762, "lon": 139.6503, "weight": 12},
        {"name": "横浜", "lat": 35.4437, "lon": 139.6380, "weight": 8},
        {"name": "大阪", "lat": 34.6937, "lon": 135.5023, "weight": 10},
        {"name": "名古屋", "lat": 35.1815, "lon": 136.9066, "weight": 8},
        {"name": "札幌", "lat": 43.0642, "lon": 141.3469, "weight": 6},
        {"name": "福岡", "lat": 33.5904, "lon": 130.4017, "weight": 6},
        {"name": "神戸", "lat": 34.6901, "lon": 135.1956, "weight": 5},
        {"name": "京都", "lat": 35.0116, "lon": 135.7681, "weight": 5},
        {"name": "川崎", "lat": 35.5307, "lon": 139.7029, "weight": 5},
        {"name": "さいたま", "lat": 35.8617, "lon": 139.6455, "weight": 4},
        {"name": "広島", "lat": 34.3853, "lon": 132.4553, "weight": 4},
        {"name": "仙台", "lat": 38.2682, "lon": 140.8694, "weight": 4},
    ]
    return major_cities

def get_regional_centers():
    """地域の中心都市を取得"""
    regional_centers = [
        {"name": "青森", "lat": 40.8244, "lon": 140.7404, "weight": 2},
        {"name": "盛岡", "lat": 39.7036, "lon": 141.1525, "weight": 2},
        {"name": "秋田", "lat": 39.7186, "lon": 140.1024, "weight": 2},
        {"name": "山形", "lat": 38.2404, "lon": 140.3636, "weight": 2},
        {"name": "福島", "lat": 37.7503, "lon": 140.4676, "weight": 2},
        {"name": "水戸", "lat": 36.3418, "lon": 140.4468, "weight": 3},
        {"name": "宇都宮", "lat": 36.5658, "lon": 139.8836, "weight": 3},
        {"name": "前橋", "lat": 36.3912, "lon": 139.0608, "weight": 3},
        {"name": "千葉", "lat": 35.6074, "lon": 140.1065, "weight": 4},
        {"name": "新潟", "lat": 37.9024, "lon": 139.0232, "weight": 3},
        {"name": "富山", "lat": 36.6953, "lon": 137.2113, "weight": 3},
        {"name": "金沢", "lat": 36.5613, "lon": 136.6562, "weight": 3},
        {"name": "福井", "lat": 36.0652, "lon": 136.2216, "weight": 2},
        {"name": "甲府", "lat": 35.6642, "lon": 138.5685, "weight": 2},
        {"name": "長野", "lat": 36.6513, "lon": 138.1812, "weight": 3},
        {"name": "岐阜", "lat": 35.3912, "lon": 136.7223, "weight": 3},
        {"name": "静岡", "lat": 34.9756, "lon": 138.3826, "weight": 3},
        {"name": "津", "lat": 34.7303, "lon": 136.5086, "weight": 2},
        {"name": "大津", "lat": 35.0043, "lon": 135.8683, "weight": 2},
        {"name": "奈良", "lat": 34.6851, "lon": 135.8048, "weight": 2},
        {"name": "和歌山", "lat": 34.2261, "lon": 135.1675, "weight": 2},
        {"name": "鳥取", "lat": 35.5036, "lon": 134.2383, "weight": 2},
        {"name": "松江", "lat": 35.4723, "lon": 133.0505, "weight": 2},
        {"name": "岡山", "lat": 34.6618, "lon": 133.9350, "weight": 3},
        {"name": "山口", "lat": 34.1861, "lon": 131.4705, "weight": 2},
        {"name": "徳島", "lat": 34.0658, "lon": 134.5593, "weight": 2},
        {"name": "高松", "lat": 34.3403, "lon": 134.0433, "weight": 2},
        {"name": "松山", "lat": 33.8418, "lon": 132.7659, "weight": 2},
        {"name": "高知", "lat": 33.5597, "lon": 133.5311, "weight": 2},
        {"name": "佐賀", "lat": 33.2493, "lon": 130.2988, "weight": 2},
        {"name": "長崎", "lat": 32.7447, "lon": 129.8736, "weight": 2},
        {"name": "熊本", "lat": 32.7898, "lon": 130.7417, "weight": 3},
        {"name": "大分", "lat": 33.2381, "lon": 131.6126, "weight": 2},
        {"name": "宮崎", "lat": 31.9077, "lon": 131.4202, "weight": 2},
        {"name": "鹿児島", "lat": 31.5602, "lon": 130.5581, "weight": 3},
        {"name": "那覇", "lat": 26.2124, "lon": 127.6792, "weight": 3},
    ]
    return regional_centers

def generate_realistic_locations(config, num_locations):
    """現実的な300地点を生成"""
    major_cities = get_japanese_cities()
    regional_centers = get_regional_centers()
    
    np.random.seed(config["data"]["sampling"]["random_seed"])
    
    locations = []
    location_id = 0
    
    # 主要都市から選択
    for city in major_cities:
        weight = city.get('weight', 1)
        for _ in range(weight):
            if location_id >= num_locations:
                break
            lat_offset = np.random.normal(0, 0.02)
            lon_offset = np.random.normal(0, 0.02)
            locations.append({
                'location_id': location_id,
                'latitude': city['lat'] + lat_offset,
                'longitude': city['lon'] + lon_offset,
                'type': 'major_city'
            })
            location_id += 1
    
    # 地域中心都市から選択
    for city in regional_centers:
        weight = city.get('weight', 1)
        for _ in range(weight):
            if location_id >= num_locations:
                break
            lat_offset = np.random.normal(0, 0.015)
            lon_offset = np.random.normal(0, 0.015)
            locations.append({
                'location_id': location_id,
                'latitude': city['lat'] + lat_offset,
                'longitude': city['lon'] + lon_offset,
                'type': 'regional_center'
            })
            location_id += 1
    
    # 残りの地点をランダムに生成
    remaining = num_locations - len(locations)
    if remaining > 0:
        bounds = config["data"]["bounds"]
        for i in range(remaining):
            lat = np.random.uniform(bounds["south"], bounds["north"])
            lon = np.random.uniform(bounds["west"], bounds["east"])
            locations.append({
                'location_id': location_id,
                'latitude': lat,
                'longitude': lon,
                'type': 'random'
            })
            location_id += 1
    
    return locations
def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="サンプルデータ生成")
    parser.add_argument("--output", type=str, 
                       default="data/processed/sample_analysis_results.csv",
                       help="出力ファイルのパス")
    parser.add_argument("--num-locations", type=int, default=300,
                       help="生成する地点数")
    parser.add_argument("--verbose", action="store_true", help="詳細ログ出力")
    
    args = parser.parse_args()
    
    # ログ設定
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logger(log_level=log_level)
    
    logger.info("サンプルデータ生成開始")
    
    try:
        # 設定読み込み
        config = load_config()
        
        # サンプルデータ生成
        sample_data = generate_sample_data(config, args.num_locations)
        
        # 出力ディレクトリ作成
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 結果保存
        sample_data.to_csv(output_path, index=False)
        logger.info(f"サンプルデータ生成完了: {output_path}")
        
        # 統計情報出力
        logger.info("生成データ統計:")
        for column in sample_data.columns:
            if column not in ['location_id', 'latitude', 'longitude']:
                logger.info(f"  {column}: 平均={sample_data[column].mean():.4f}, "
                          f"標準偏差={sample_data[column].std():.4f}")
        
    except Exception as e:
        logger.error(f"サンプルデータ生成エラー: {e}")
        sys.exit(1)


def generate_sample_data(config: dict, num_locations: int) -> pd.DataFrame:
    """
    サンプルデータを生成する
    
    Args:
        config: 設定辞書
        num_locations: 生成する地点数
        
    Returns:
        サンプルデータのDataFrame
    """
    logger.info(f"サンプルデータ生成: {num_locations}地点")
    
    # 日本全国の緯度経度範囲
    bounds = config["data"]["bounds"]
    random_seed = config["data"]["sampling"]["random_seed"]
    
    np.random.seed(random_seed)
    
    # 現実的な地点選択
    realistic_locations = generate_realistic_locations(config, num_locations)

    data = []
    for location in realistic_locations:
        lat = location['latitude']
        lon = location['longitude']
        location_id = location['location_id']
        city_type = location['type']
        
        # 都市特性に応じた指標値を生成
        if city_type == "major_city":
            sparsity_base, resilience_base, multi_nodality_base, permeability_base, emergence_base = 0.3, 0.6, 3.0, 0.4, 1.5
        elif city_type == "regional_center":
            sparsity_base, resilience_base, multi_nodality_base, permeability_base, emergence_base = 0.6, 0.7, 1.8, 0.6, 1.0
        else:
            sparsity_base, resilience_base, multi_nodality_base, permeability_base, emergence_base = 1.2, 0.8, 0.8, 0.8, 0.5
        
        # ノイズを加えて現実的なばらつきを生成
        sparsity = np.clip(np.random.normal(sparsity_base, 0.2), 0.1, 2.0)
        resilience = np.clip(np.random.normal(resilience_base, 0.15), 0.0, 1.0)
        multi_nodality = np.clip(np.random.normal(multi_nodality_base, 0.5), 0.0, 5.0)
        permeability = np.clip(np.random.normal(permeability_base, 0.2), 0.0, 1.0)
        emergence = np.clip(np.random.normal(emergence_base, 0.3), 0.0, 2.0)
        
        result = {
            'location_id': location_id,
            'latitude': lat,
            'longitude': lon,
            'sparsity': sparsity,
            'resilience': resilience,
            'multi_nodality': multi_nodality,
            'permeability': permeability,
            'overlap': 0.0,
            'emergence': emergence
        }
        data.append(result)
        
        if (len(data) + 1) % 50 == 0:
            logger.info(f"進捗: {len(data) + 1}/{num_locations}")
    
    df = pd.DataFrame(data)
    logger.info(f"サンプルデータ生成完了: {len(df)}地点")
    
    return df


if __name__ == "__main__":
    main()
