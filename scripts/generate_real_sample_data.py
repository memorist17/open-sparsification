#!/usr/bin/env python3
"""
実際の地理データから指標を計算してサンプルデータを生成するスクリプト
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
import time

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.real_metrics_calculator import calculate_real_metrics
from src.utils.logger import get_logger

logger = get_logger(__name__)

def generate_real_sample_data():
    """実際の地理データから指標を計算してサンプルデータを生成"""
    
    # 出力ディレクトリの作成
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 300地点の緯度経度を生成（日本の範囲内）
    locations = generate_japanese_locations(300)
    
    logger.info(f"実際の地理データから指標計算開始: {len(locations)}地点")
    
    # 各地点の指標を計算
    results = []
    successful_calculations = 0
    failed_calculations = 0
    
    for i, (lat, lon) in enumerate(locations):
        try:
            logger.info(f"指標計算中: {i+1}/{len(locations)} - 緯度: {lat:.3f}, 経度: {lon:.3f}")
            
            # 実際の地理データから指標を計算
            metrics = calculate_real_metrics(lat, lon)
            
            # 結果を保存
            result = {
                'location_id': i,
                'latitude': lat,
                'longitude': lon,
                'sparsity': metrics['sparsity'],
                'resilience': metrics['resilience'],
                'multi_nodality': metrics['multi_nodality'],
                'permeability': metrics['permeability'],
                'emergence': metrics['emergence'],
                'overlap': metrics['overlap']
            }
            
            results.append(result)
            successful_calculations += 1
            
            # 進捗表示
            if (i + 1) % 50 == 0:
                logger.info(f"進捗: {i+1}/{len(locations)} ({successful_calculations}成功, {failed_calculations}失敗)")
            
            # レート制限対策
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"地点 {i} の指標計算エラー: {e}")
            failed_calculations += 1
            
            # エラー時はデフォルト値を設定
            result = {
                'location_id': i,
                'latitude': lat,
                'longitude': lon,
                'sparsity': 0.5,
                'resilience': 0.5,
                'multi_nodality': 0.5,
                'permeability': 0.5,
                'emergence': 0.5,
                'overlap': 0.0
            }
            results.append(result)
            continue
    
    # DataFrameに変換
    df = pd.DataFrame(results)
    
    # CSVファイルに保存
    output_path = output_dir / "real_analysis_results.csv"
    df.to_csv(output_path, index=False)
    
    logger.info(f"実際の地理データから指標計算完了")
    logger.info(f"成功: {successful_calculations}件, 失敗: {failed_calculations}件")
    logger.info(f"結果を保存: {output_path}")
    
    # 統計情報を表示
    display_statistics(df)
    
    return df

def generate_japanese_locations(num_locations: int) -> List[Tuple[float, float]]:
    """日本の範囲内でランダムな地点を生成"""
    
    # 日本の境界
    japan_bounds = {
        'west': 129.0,
        'south': 30.0,
        'east': 146.0,
        'north': 46.0
    }
    
    # 主要都市の座標（重み付き）
    major_cities = [
        # 東京圏
        (35.6762, 139.6503, 0.3),  # 東京
        (35.4437, 139.6380, 0.2),  # 横浜
        (35.8617, 139.6455, 0.1),  # 川崎
        
        # 大阪圏
        (34.6937, 135.5023, 0.2),  # 大阪
        (34.6901, 135.1956, 0.1),  # 神戸
        (34.6851, 135.8048, 0.1),  # 京都
        
        # 名古屋圏
        (35.1815, 136.9066, 0.1),  # 名古屋
        
        # その他の主要都市
        (43.0642, 141.3469, 0.05),  # 札幌
        (38.2682, 140.8694, 0.05),  # 仙台
        (36.5658, 136.6566, 0.05),  # 金沢
        (34.3853, 132.4553, 0.05),  # 広島
        (33.5904, 130.4017, 0.05),  # 福岡
        (26.2124, 127.6792, 0.02),  # 那覇
    ]
    
    locations = []
    np.random.seed(42)  # 再現性のため
    
    # 主要都市から重み付きで選択
    city_weights = [weight for _, _, weight in major_cities]
    city_coords = [(lat, lon) for lat, lon, _ in major_cities]
    
    # 主要都市から選択
    num_major_cities = min(50, num_locations // 3)
    for _ in range(num_major_cities):
        idx = np.random.choice(len(city_coords), p=np.array(city_weights) / sum(city_weights))
        lat, lon = city_coords[idx]
        
        # 周辺に少しばらつきを追加
        lat += np.random.normal(0, 0.1)
        lon += np.random.normal(0, 0.1)
        
        locations.append((lat, lon))
    
    # 残りをランダムに生成
    remaining = num_locations - len(locations)
    for _ in range(remaining):
        lat = np.random.uniform(japan_bounds['south'], japan_bounds['north'])
        lon = np.random.uniform(japan_bounds['west'], japan_bounds['east'])
        locations.append((lat, lon))
    
    return locations

def display_statistics(df: pd.DataFrame):
    """統計情報を表示"""
    
    logger.info("=== 実際の地理データから計算された指標の統計 ===")
    
    metrics = ['sparsity', 'resilience', 'multi_nodality', 'permeability', 'emergence', 'overlap']
    
    for metric in metrics:
        if metric in df.columns:
            values = df[metric]
            logger.info(f"{metric}:")
            logger.info(f"  平均: {values.mean():.3f}")
            logger.info(f"  標準偏差: {values.std():.3f}")
            logger.info(f"  最小値: {values.min():.3f}")
            logger.info(f"  最大値: {values.max():.3f}")
            logger.info(f"  中央値: {values.median():.3f}")
    
    # 相関行列を表示
    logger.info("\n=== 指標間の相関 ===")
    correlation_matrix = df[metrics].corr()
    logger.info(correlation_matrix.round(3))

def main():
    """メイン関数"""
    try:
        df = generate_real_sample_data()
        logger.info("実際の地理データから指標計算が完了しました")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    main()
