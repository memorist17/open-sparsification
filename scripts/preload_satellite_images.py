#!/usr/bin/env python3
"""
衛星画像の事前取得スクリプト
"""

import sys
import pandas as pd
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.app.satellite_cache import satellite_cache

def preload_satellite_images():
    """衛星画像を事前に取得"""
    
    # データを読み込み
    real_data_path = project_root / "data" / "processed" / "real_analysis_results.csv"
    sample_data_path = project_root / "data" / "processed" / "sample_analysis_results.csv"
    
    if real_data_path.exists():
        df = pd.read_csv(real_data_path)
        print(f"✅ 実際の地理データを読み込みました: {len(df)}地点")
    elif sample_data_path.exists():
        df = pd.read_csv(sample_data_path)
        print(f"⚠️ サンプルデータを読み込みました: {len(df)}地点")
    else:
        print("❌ データファイルが見つかりません")
        return
    
    # 緯度経度のリストを作成
    locations = [(row['latitude'], row['longitude']) for _, row in df.iterrows()]
    
    # 衛星画像を事前取得
    print("🛰️ 衛星画像の事前取得を開始...")
    successful, failed = satellite_cache.preload_satellite_images(locations, zoom=15)
    
    print(f"✅ 事前取得完了: 成功 {successful}件, 失敗 {failed}件")
    print(f"📁 キャッシュディレクトリ: {satellite_cache.cache_dir}")

if __name__ == "__main__":
    preload_satellite_images()
