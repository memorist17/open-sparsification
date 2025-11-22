#!/usr/bin/env python3
"""
最小限のテスト: インポートと基本機能の確認
"""

import sys
from pathlib import Path

def test_imports():
    """モジュールのインポートをテスト"""
    print("=" * 60)
    print("モジュールインポートテスト")
    print("=" * 60)
    
    errors = []
    
    # 基本パッケージ
    try:
        import numpy as np
        print("✓ numpy")
    except ImportError as e:
        print(f"✗ numpy: {e}")
        errors.append("numpy")
    
    try:
        import pandas as pd
        print("✓ pandas")
    except ImportError as e:
        print(f"✗ pandas: {e}")
        errors.append("pandas")
    
    try:
        import geopandas as gpd
        print("✓ geopandas")
    except ImportError as e:
        print(f"✗ geopandas: {e}")
        errors.append("geopandas")
    
    try:
        from shapely.geometry import Point
        print("✓ shapely")
    except ImportError as e:
        print(f"✗ shapely: {e}")
        errors.append("shapely")
    
    # プロジェクトモジュール
    print("\n" + "-" * 60)
    print("プロジェクトモジュール")
    print("-" * 60)
    
    try:
        from src.utils.overture_loader import PlaceExtent
        print("✓ src.utils.overture_loader")
    except ImportError as e:
        print(f"✗ src.utils.overture_loader: {e}")
        errors.append("overture_loader")
    
    try:
        from src.utils.hybrid_network import HybridNetwork
        print("✓ src.utils.hybrid_network")
    except ImportError as e:
        print(f"✗ src.utils.hybrid_network: {e}")
        errors.append("hybrid_network")
    
    try:
        from src.utils.parallel_utils import get_optimal_n_jobs
        print("✓ src.utils.parallel_utils")
    except ImportError as e:
        print(f"✗ src.utils.parallel_utils: {e}")
        errors.append("parallel_utils")
    
    try:
        from src.metrics.lacunarity import calculate_lacunarity
        print("✓ src.metrics.lacunarity")
    except ImportError as e:
        print(f"✗ src.metrics.lacunarity: {e}")
        errors.append("lacunarity")
    
    try:
        from src.pipeline import OpenSparsityAnalyzer
        print("✓ src.pipeline")
    except ImportError as e:
        print(f"✗ src.pipeline: {e}")
        errors.append("pipeline")
    
    # 結果サマリー
    print("\n" + "=" * 60)
    if errors:
        print(f"✗ {len(errors)}個のモジュールでエラーが発生しました")
        print("\n不足している依存関係:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("✓ すべてのモジュールが正常にインポートできました")
        return True


def test_basic_functionality():
    """基本機能のテスト"""
    print("\n" + "=" * 60)
    print("基本機能テスト")
    print("=" * 60)
    
    try:
        # PlaceExtentのテスト
        from src.utils.overture_loader import PlaceExtent
        
        extent = PlaceExtent(139.7, 35.6, 139.8, 35.7, crs="EPSG:4326")
        print(f"✓ PlaceExtent作成: {extent}")
        
        # 並列処理ユーティリティのテスト
        from src.utils.parallel_utils import get_optimal_n_jobs
        
        n_jobs = get_optimal_n_jobs(10)
        print(f"✓ 最適なワーカー数: {n_jobs}")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本機能テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Overture 1地点テスト: 最小限のチェック")
    print("=" * 60)
    
    # インポートテスト
    imports_ok = test_imports()
    
    if imports_ok:
        # 基本機能テスト
        functionality_ok = test_basic_functionality()
        
        if functionality_ok:
            print("\n" + "=" * 60)
            print("✓ すべてのテストが成功しました")
            print("=" * 60)
            print("\n次のステップ:")
            print("1. 必要な依存関係をインストール: pip install -r requirements.txt")
            print("2. 実際のデータでテスト: python test_overture_single_location.py")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("✗ 依存関係が不足しています")
        print("=" * 60)
        print("\nインストールコマンド:")
        print("  pip install -r requirements.txt")
        print("\nまたは個別に:")
        print("  pip install numpy pandas geopandas shapely pyproj joblib pyarrow")
        sys.exit(1)
