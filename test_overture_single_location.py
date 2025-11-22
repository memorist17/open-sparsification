#!/usr/bin/env python3
"""
1地点でのOvertureデータ取得・変換・指標計算のテスト

実際のOverture Parquetファイルがない場合は、サンプルデータを生成してテストします。
"""

import sys
import os
from pathlib import Path
import json

# ユーザーインストールのパッケージをパスに追加
user_site = os.path.expanduser('~/.local/lib/python3.12/site-packages')
if os.path.exists(user_site):
    sys.path.insert(0, user_site)

# 依存関係のチェック
try:
    import numpy as np
    import geopandas as gpd
    from shapely.geometry import Point, LineString
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"警告: 必要なパッケージがインストールされていません: {e}")
    print("テストを実行するには、以下のパッケージをインストールしてください:")
    print("  pip install numpy geopandas shapely pyproj networkx pyarrow")
    DEPENDENCIES_AVAILABLE = False
    sys.exit(1)

# テスト用のサンプルデータ生成
def generate_sample_buildings(extent, n_points=1000):
    """サンプル建物データを生成"""
    minx, miny, maxx, maxy = extent.minx, extent.miny, extent.maxx, extent.maxy
    
    # クラスタリングされたパターンで生成
    np.random.seed(42)
    n_clusters = 5
    points_per_cluster = n_points // n_clusters
    
    points = []
    for i in range(n_clusters):
        center_x = np.random.uniform(minx, maxx)
        center_y = np.random.uniform(miny, maxy)
        cluster_points = np.random.normal(
            [center_x, center_y],
            scale=[(maxx - minx) / 20, (maxy - miny) / 20],
            size=(points_per_cluster, 2)
        )
        points.extend(cluster_points)
    
    # 残りのポイントを追加
    remaining = n_points - len(points)
    if remaining > 0:
        random_points = np.random.uniform(
            [minx, miny], [maxx, maxy],
            size=(remaining, 2)
        )
        points.extend(random_points)
    
    geometry = [Point(x, y) for x, y in points[:n_points]]
    gdf = gpd.GeoDataFrame(
        {
            'id': [f'building_{i}' for i in range(len(geometry))],
            'name': [None] * len(geometry),
            'class': ['building'] * len(geometry),
        },
        geometry=geometry,
        crs='EPSG:4326'
    )
    
    return gdf.to_crs('EPSG:3857')


def generate_sample_roads(extent, n_segments=200):
    """サンプル道路データを生成"""
    minx, miny, maxx, maxy = extent.minx, extent.miny, extent.maxx, extent.maxy
    
    # WGS84からWeb Mercatorに変換
    import pyproj
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x1, y1 = transformer.transform(minx, miny)
    x2, y2 = transformer.transform(maxx, maxy)
    
    np.random.seed(42)
    segments = []
    
    # グリッド状の道路ネットワークを生成
    n_grid = int(np.sqrt(n_segments))
    x_coords = np.linspace(x1, x2, n_grid)
    y_coords = np.linspace(y1, y2, n_grid)
    
    for i in range(len(x_coords) - 1):
        # 縦の道路
        segments.append(LineString([
            (x_coords[i], y1),
            (x_coords[i], y2)
        ]))
        # 横の道路
        segments.append(LineString([
            (x1, y_coords[i]),
            (x2, y_coords[i])
        ]))
    
    # ランダムな道路も追加
    remaining = n_segments - len(segments)
    for _ in range(remaining):
        x_start = np.random.uniform(x1, x2)
        y_start = np.random.uniform(y1, y2)
        x_end = x_start + np.random.uniform(-(x2-x1)/10, (x2-x1)/10)
        y_end = y_start + np.random.uniform(-(y2-y1)/10, (y2-y1)/10)
        segments.append(LineString([(x_start, y_start), (x_end, y_end)]))
    
    gdf = gpd.GeoDataFrame(
        {
            'id': [f'road_{i}' for i in range(len(segments))],
            'name': [None] * len(segments),
            'class': ['road'] * len(segments),
            'level': [1] * len(segments),
        },
        geometry=segments[:n_segments],
        crs='EPSG:3857'
    )
    
    return gdf


def test_overture_pipeline():
    """Overtureパイプラインのテスト"""
    print("=" * 60)
    print("Overture 1地点テスト: データ取得・変換・指標計算")
    print("=" * 60)
    
    # テスト範囲を設定（東京23区の一部）
    from src.utils.overture_loader import PlaceExtent
    
    extent = PlaceExtent(
        minx=139.7,  # 東京の経度
        miny=35.6,   # 東京の緯度
        maxx=139.8,
        maxy=35.7,
        crs="EPSG:4326"
    )
    
    print(f"\nテスト範囲: {extent}")
    
    # サンプルデータを生成（実際のParquetファイルがない場合）
    print("\n" + "-" * 60)
    print("ステップ1: データ生成（サンプル）")
    print("-" * 60)
    
    buildings = generate_sample_buildings(extent, n_points=1000)
    print(f"✓ 建物データ生成: {len(buildings)} 点")
    
    roads = generate_sample_roads(extent, n_segments=100)
    print(f"✓ 道路データ生成: {len(roads)} セグメント")
    
    # ハイブリッドネットワークを構築
    print("\n" + "-" * 60)
    print("ステップ2: ハイブリッドネットワーク構築")
    print("-" * 60)
    
    from src.utils.hybrid_network import build_hybrid_network
    
    try:
        network = build_hybrid_network(
            roads,
            buildings,
            road_node_distance=50.0,
            building_to_road_distance=100.0,
            building_to_building_distance=200.0,
            verbose=True
        )
        print(f"✓ ネットワーク構築完了: {len(network.nodes)} ノード, {len(network.edges)} エッジ")
    except Exception as e:
        print(f"✗ ネットワーク構築エラー: {e}")
        network = None
    
    # 設定を読み込み
    print("\n" + "-" * 60)
    print("ステップ3: 設定読み込み")
    print("-" * 60)
    
    config_path = Path('config_example.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_raw = json.load(f)
        # 設定をフラット化（config_example.jsonの構造に対応）
        config = {
            'pixel_size': config_raw.get('lacunarity', {}).get('pixel_size', 5.0),
            'lacunarity_scales': config_raw.get('lacunarity', {}).get('window_sizes', [3, 5, 7, 11, 15, 21, 31, 41, 51]),
            'percolation_thresholds': config_raw.get('percolation', {}).get('thresholds', [10, 25, 50, 100, 200, 400]),
            'percolation_method': config_raw.get('percolation', {}).get('method', 'radius'),
            'multifractal_q': config_raw.get('multifractal', {}).get('q_values', [-5, -3, -2, -1, 0, 1, 2, 3, 5]),
            'box_sizes': config_raw.get('multifractal', {}).get('box_sizes', [10, 25, 50, 100, 200, 400, 800]),
        }
        print("✓ 設定ファイル読み込み完了")
    else:
        config = {
            'pixel_size': 5.0,
            'lacunarity_scales': [3, 5, 7, 11, 15, 21, 31, 41, 51],
            'percolation_thresholds': [10, 25, 50, 100, 200, 400],
            'percolation_method': 'radius',
            'multifractal_q': [-5, -3, -2, -1, 0, 1, 2, 3, 5],
            'box_sizes': [10, 25, 50, 100, 200, 400, 800],
        }
        print("✓ デフォルト設定を使用")
    
    # 指標計算（並列処理）
    print("\n" + "-" * 60)
    print("ステップ4: 指標計算（並列処理）")
    print("-" * 60)
    
    from src.pipeline import OpenSparsityAnalyzer
    from src.utils.parallel_utils import get_optimal_n_jobs
    
    n_jobs = get_optimal_n_jobs(1)
    print(f"並列ワーカー数: {n_jobs}")
    
    try:
        analyzer = OpenSparsityAnalyzer(buildings, config, network=network)
        
        print("\n[Lacunarity解析]")
        lac_result = analyzer.run_lacunarity(verbose=True, n_jobs=n_jobs)
        print(f"✓ Lacunarity完了: {len(lac_result)} スケール")
        
        print("\n[Percolation解析]")
        perc_result = analyzer.run_percolation(verbose=True)
        print(f"✓ Percolation完了: {len(perc_result)} 閾値")
        
        print("\n[Multifractal解析]")
        mf_result, mf_summary = analyzer.run_multifractal(verbose=True, n_jobs=n_jobs)
        print(f"✓ Multifractal完了: {len(mf_result)} q値")
        
        # サマリーを表示
        print("\n" + "-" * 60)
        print("ステップ5: 結果サマリー")
        print("-" * 60)
        
        summary = analyzer._compile_summary()
        print("\n主要指標:")
        if 'lacunarity_aggregation' in analyzer.results:
            print(f"  Lacunarity (small): {analyzer.results['lacunarity_aggregation'].get('small', 'N/A')}")
            print(f"  Lacunarity (medium): {analyzer.results['lacunarity_aggregation'].get('medium', 'N/A')}")
            print(f"  Lacunarity (large): {analyzer.results['lacunarity_aggregation'].get('large', 'N/A')}")
        
        if 'percolation_summary' in analyzer.results:
            perc_summary = analyzer.results['percolation_summary']
            print(f"  Percolation threshold (r_p): {perc_summary.get('r_p', 'N/A'):.2f} m")
            print(f"  Max connectivity: {perc_summary.get('max_S1_ratio', 'N/A'):.3f}")
        
        if 'multifractal_summary' in analyzer.results:
            mf_summary = analyzer.results['multifractal_summary']
            print(f"  Multifractal D0: {mf_summary.get('D0', 'N/A'):.3f}")
            print(f"  Multifractal D2: {mf_summary.get('D2', 'N/A'):.3f}")
            print(f"  Spectrum width (Δα): {mf_summary.get('Delta_alpha', 'N/A'):.4f}")
        
        # 結果を保存
        print("\n" + "-" * 60)
        print("ステップ6: 結果保存")
        print("-" * 60)
        
        output_dir = Path('./test_output_single')
        output_dir.mkdir(exist_ok=True)
        
        analyzer.save(str(output_dir), prefix='test_location')
        print(f"✓ 結果を保存: {output_dir}")
        
        # 可視化
        fig_dir = output_dir / 'figures'
        fig_dir.mkdir(exist_ok=True)
        analyzer.visualize(output_dir=str(fig_dir), show=False)
        print(f"✓ 可視化を保存: {fig_dir}")
        
        print("\n" + "=" * 60)
        print("✓ テスト完了！")
        print("=" * 60)
        print(f"\n結果ディレクトリ: {output_dir.absolute()}")
        print(f"  - CSV/JSON: {output_dir}")
        print(f"  - 図表: {fig_dir}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_overture_pipeline()
    sys.exit(0 if success else 1)
