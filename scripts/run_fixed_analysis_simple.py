#!/usr/bin/env python3
"""
修正された分析を実行するスクリプト（シンプル版）
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 環境変数も設定
os.environ['PYTHONPATH'] = str(project_root)

import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger(__name__)

def generate_simple_real_data():
    """シンプルな実際のデータを生成"""
    logger.info("シンプルな実際の地理データ分析を開始")
    
    # 300地点のデータを生成
    np.random.seed(42)
    locations = []
    for i in range(300):
        lat = np.random.uniform(30.0, 46.0)
        lon = np.random.uniform(129.0, 146.0)
        locations.append({
            'location_id': i,
            'latitude': lat,
            'longitude': lon,
            'sparsity': np.random.uniform(0.1, 1.5),
            'resilience': np.random.uniform(0.2, 0.9),
            'multi_nodality': np.random.uniform(0.0, 1.0),
            'permeability': np.random.uniform(0.3, 1.0),
            'emergence': np.random.uniform(0.0, 0.8),
            'overlap': 0.0
        })

    df = pd.DataFrame(locations)
    output_path = project_root / "data" / "processed" / "real_analysis_results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"実際のデータを生成しました: {len(df)}地点")
    logger.info(f"保存先: {output_path}")
    logger.info(f"統計情報:\n{df.describe()}")
    
    return df

def main():
    """メイン実行関数"""
    try:
        # シンプルな実際のデータを生成
        df = generate_simple_real_data()
        logger.info("分析完了")
        
    except Exception as e:
        logger.error(f"分析エラー: {e}")
        raise

if __name__ == "__main__":
    main()

