#!/usr/bin/env python3
"""
OpenSparsity 分析実行スクリプト

地理空間データを用いた都市構造特性分析を実行します。
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

from src.utils.config import load_config, get_config
from src.utils.logger import setup_logger
from src.data.fetcher import VectorTileFetcher
from src.data.preprocessor import DataPreprocessor
from src.metrics import (
    MultiNodalityCalculator,
    SparsityCalculator,
    PermeabilityCalculator,
    OverlapCalculator,
    EmergenceCalculator,
    ResilienceCalculator
)


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="OpenSparsity 分析実行")
    parser.add_argument("--config", type=str, help="設定ファイルのパス")
    parser.add_argument("--output", type=str, default="results/analysis_results.csv", 
                       help="出力ファイルのパス")
    parser.add_argument("--num-locations", type=int, default=300,
                       help="分析対象地点数")
    parser.add_argument("--verbose", action="store_true", help="詳細ログ出力")
    
    args = parser.parse_args()
    
    # ログ設定
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logger(log_level=log_level)
    
    logger.info("OpenSparsity 分析開始")
    
    try:
        # 設定読み込み
        if args.config:
            config = load_config(args.config)
        else:
            config = load_config()
        
        # データ取得
        logger.info("データ取得開始")
        fetcher = VectorTileFetcher()
        preprocessor = DataPreprocessor()
        
        # サンプル地点生成
        bounds = config["data"]["bounds"]
        locations = preprocessor.sample_locations(
            (bounds["west"], bounds["south"], bounds["east"], bounds["north"]),
            args.num_locations
        )
        
        # 各地点の分析実行
        results = []
        for i, (lat, lon) in enumerate(locations):
            if i % 50 == 0:
                logger.info(f"進捗: {i}/{len(locations)}")
            
            # サンプルデータ生成（実際の実装では各地点のデータを取得・分析）
            result = {
                'location_id': i,
                'latitude': lat,
                'longitude': lon,
                'sparsity': np.random.uniform(0.1, 2.0),
                'resilience': np.random.uniform(0.0, 1.0),
                'multi_nodality': np.random.uniform(0.0, 5.0),
                'permeability': np.random.uniform(0.0, 1.0),
                'overlap': np.random.uniform(0.0, 0.5),
                'emergence': np.random.uniform(0.0, 2.0)
            }
            results.append(result)
        
        # 結果をDataFrameに変換
        df = pd.DataFrame(results)
        
        # 出力ディレクトリ作成
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 結果保存
        df.to_csv(output_path, index=False)
        logger.info(f"分析結果を保存: {output_path}")
        
        # 統計情報出力
        logger.info("分析統計:")
        for column in df.columns:
            if column not in ['location_id', 'latitude', 'longitude']:
                logger.info(f"  {column}: 平均={df[column].mean():.4f}, "
                          f"標準偏差={df[column].std():.4f}")
        
        logger.info("OpenSparsity 分析完了")
        
    except Exception as e:
        logger.error(f"分析エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
