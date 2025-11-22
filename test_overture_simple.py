#!/usr/bin/env python3
"""
簡易テスト: 基本的な機能のみテスト（geopandasなしでも動作）
"""

import sys
import os

# ユーザーインストールのパッケージをパスに追加
user_site = os.path.expanduser('~/.local/lib/python3.12/site-packages')
if os.path.exists(user_site):
    sys.path.insert(0, user_site)

def test_basic_imports():
    """基本パッケージのインポートテスト"""
    print("=" * 60)
    print("基本パッケージインポートテスト")
    print("=" * 60)
    
    results = {}
    
    try:
        import numpy as np
        print(f"✓ numpy {np.__version__}")
        results['numpy'] = True
    except ImportError as e:
        print(f"✗ numpy: {e}")
        results['numpy'] = False
    
    try:
        import pandas as pd
        print(f"✓ pandas {pd.__version__}")
        results['pandas'] = True
    except ImportError as e:
        print(f"✗ pandas: {e}")
        results['pandas'] = False
    
    try:
        import scipy
        print(f"✓ scipy {scipy.__version__}")
        results['scipy'] = True
    except ImportError as e:
        print(f"✗ scipy: {e}")
        results['scipy'] = False
    
    try:
        from shapely.geometry import Point
        print(f"✓ shapely")
        results['shapely'] = True
    except ImportError as e:
        print(f"✗ shapely: {e}")
        results['shapely'] = False
    
    try:
        import joblib
        print(f"✓ joblib {joblib.__version__}")
        results['joblib'] = True
    except ImportError as e:
        print(f"✗ joblib: {e}")
        results['joblib'] = False
    
    try:
        from tqdm import tqdm
        print(f"✓ tqdm")
        results['tqdm'] = True
    except ImportError as e:
        print(f"✗ tqdm: {e}")
        results['tqdm'] = False
    
    return results


def test_project_modules():
    """プロジェクトモジュールのテスト"""
    print("\n" + "=" * 60)
    print("プロジェクトモジュールテスト")
    print("=" * 60)
    
    results = {}
    
    # 並列処理ユーティリティ（geopandasに依存しない）
    try:
        from src.utils.parallel_utils import get_optimal_n_jobs, parallel_map
        print("✓ src.utils.parallel_utils")
        
        # 機能テスト
        n_jobs = get_optimal_n_jobs(10)
        print(f"  → 最適なワーカー数 (10タスク): {n_jobs}")
        
        results['parallel_utils'] = True
    except Exception as e:
        print(f"✗ src.utils.parallel_utils: {e}")
        results['parallel_utils'] = False
    
    # PlaceExtent（pyprojに依存）
    try:
        from src.utils.overture_loader import PlaceExtent
        print("✓ src.utils.overture_loader.PlaceExtent")
        
        # 機能テスト
        extent = PlaceExtent(139.7, 35.6, 139.8, 35.7, crs="EPSG:4326")
        print(f"  → PlaceExtent作成: ({extent.minx}, {extent.miny}) - ({extent.maxx}, {extent.maxy})")
        
        results['overture_loader'] = True
    except Exception as e:
        print(f"✗ src.utils.overture_loader: {e}")
        results['overture_loader'] = False
    
    # その他のモジュール（geopandasに依存するためスキップ）
    print("\n注: geopandasがインストールされていないため、以下のモジュールはテストしません:")
    print("  - src.utils.hybrid_network")
    print("  - src.metrics.lacunarity")
    print("  - src.metrics.percolation")
    print("  - src.metrics.multifractal")
    print("  - src.pipeline")
    
    return results


def test_parallel_functionality():
    """並列処理機能のテスト"""
    print("\n" + "=" * 60)
    print("並列処理機能テスト")
    print("=" * 60)
    
    try:
        import numpy as np
        from src.utils.parallel_utils import parallel_map, vectorized_distance_matrix
        
        # テスト関数
        def square(x):
            return x ** 2
        
        # 並列マッピングテスト
        items = list(range(10))
        results = parallel_map(square, items, n_jobs=2, verbose=False)
        expected = [x**2 for x in items]
        
        if results == expected:
            print("✓ parallel_map: 正常に動作")
        else:
            print(f"✗ parallel_map: 結果が一致しません")
            return False
        
        # ベクトル化距離計算テスト
        coords1 = np.random.rand(100, 2) * 100
        coords2 = np.random.rand(50, 2) * 100
        
        distances, indices = vectorized_distance_matrix(
            coords1, coords2, max_distance=50.0
        )
        print(f"✓ vectorized_distance_matrix: {len(distances)} ペアを計算")
        
        return True
        
    except Exception as e:
        print(f"✗ 並列処理機能テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Overture 簡易テスト")
    print("=" * 60)
    
    # 基本パッケージテスト
    basic_results = test_basic_imports()
    
    # プロジェクトモジュールテスト
    project_results = test_project_modules()
    
    # 並列処理機能テスト
    if basic_results.get('numpy') and basic_results.get('joblib'):
        parallel_ok = test_parallel_functionality()
    else:
        parallel_ok = False
        print("\n並列処理テストをスキップ（必要なパッケージが不足）")
    
    # サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    all_basic = all(basic_results.values())
    all_project = all(project_results.values())
    
    if all_basic and all_project and parallel_ok:
        print("✓ すべてのテストが成功しました")
        print("\n次のステップ:")
        print("1. geopandasをインストール: pip install geopandas")
        print("2. 完全なテストを実行: python3 test_overture_single_location.py")
        sys.exit(0)
    else:
        print("一部のテストが失敗しました")
        print("\n不足しているパッケージ:")
        for name, ok in basic_results.items():
            if not ok:
                print(f"  - {name}")
        sys.exit(1)
