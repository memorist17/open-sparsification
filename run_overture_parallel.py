#!/usr/bin/env python3
"""
Overture Mapsデータを使用した並列処理・高速化デモ

Overture MapsのParquetファイルから建物と道路データを取得し、
並列処理で指標計算を実行する。
"""

import argparse
from pathlib import Path
from typing import Dict, Optional
import geopandas as gpd

from src.pipeline import OpenSparsityAnalyzer, batch_analysis
from src.utils.overture_loader import (
    PlaceExtent,
    load_building_centroids,
    load_road_segments,
)
from src.utils.hybrid_network import build_hybrid_network
from src.utils.parallel_utils import get_optimal_n_jobs


def main():
    parser = argparse.ArgumentParser(
        description="Overture Mapsデータを使用した並列処理・高速化デモ"
    )
    parser.add_argument(
        '--buildings',
        type=str,
        required=True,
        help='Overture建物Parquetファイルのパス'
    )
    parser.add_argument(
        '--roads',
        type=str,
        help='Overture道路Parquetファイルのパス（オプション）'
    )
    parser.add_argument(
        '--extent',
        type=float,
        nargs=4,
        metavar=('MINX', 'MINY', 'MAXX', 'MAXY'),
        help='読み込む範囲（WGS84座標: minx miny maxx maxy）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='./overture_output',
        help='出力ディレクトリ'
    )
    parser.add_argument(
        '--cache-dir',
        type=str,
        help='キャッシュディレクトリ'
    )
    parser.add_argument(
        '--max-points',
        type=int,
        help='最大読み込み点数（サンプリング用）'
    )
    parser.add_argument(
        '--n-jobs',
        type=int,
        help='並列ワーカー数（Noneの場合は自動決定）'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='設定JSONファイル'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='詳細出力'
    )
    
    args = parser.parse_args()
    
    # 範囲設定
    extent = None
    if args.extent:
        extent = PlaceExtent(
            minx=args.extent[0],
            miny=args.extent[1],
            maxx=args.extent[2],
            maxy=args.extent[3],
            crs="EPSG:4326"
        )
        print(f"Extent: {extent}")
    
    # 建物データを読み込み
    print("=" * 60)
    print("Loading Overture Building Data")
    print("=" * 60)
    buildings = load_building_centroids(
        args.buildings,
        extent=extent,
        cache_dir=args.cache_dir,
        max_points=args.max_points,
        verbose=args.verbose
    )
    print(f"Loaded {len(buildings)} building centroids")
    
    # 道路データを読み込み（オプション）
    roads = None
    network = None
    if args.roads:
        print("\n" + "=" * 60)
        print("Loading Overture Road Data")
        print("=" * 60)
        roads = load_road_segments(
            args.roads,
            extent=extent,
            cache_dir=args.cache_dir,
            verbose=args.verbose
        )
        print(f"Loaded {len(roads)} road segments")
        
        # ハイブリッドネットワークを構築
        print("\n" + "=" * 60)
        print("Building Hybrid Network")
        print("=" * 60)
        network = build_hybrid_network(
            roads,
            buildings,
            verbose=args.verbose
        )
        print(f"Network: {len(network.nodes)} nodes, {len(network.edges)} edges")
    
    # 設定を読み込み
    config = {}
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # 並列ワーカー数を決定
    n_jobs = args.n_jobs
    if n_jobs is None:
        n_jobs = get_optimal_n_jobs(1)
        if args.verbose:
            print(f"\nUsing {n_jobs} parallel workers")
    
    # 解析を実行
    print("\n" + "=" * 60)
    print("Running OpenSparsity Analysis (Parallel)")
    print("=" * 60)
    
    analyzer = OpenSparsityAnalyzer(buildings, config, network=network)
    results = analyzer.run_all(verbose=args.verbose, n_jobs=n_jobs)
    
    # 結果を保存
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    analyzer.save(str(output_path), prefix='overture')
    
    # 可視化
    fig_dir = output_path / 'figures'
    fig_dir.mkdir(exist_ok=True)
    analyzer.visualize(output_dir=str(fig_dir), show=False)
    
    print("\n" + "=" * 60)
    print("Analysis Complete")
    print(f"Results saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
