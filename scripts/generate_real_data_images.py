#!/usr/bin/env python3
"""
実際の地理データを使用してネットワーク画像を生成するスクリプト
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import logging
from typing import Dict, List, Tuple
import time

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_fetcher import fetch_real_geographic_data
from src.network_builder import create_urban_network
from src.utils.logger import get_logger
from src.visualization.location_overview import (
    create_location_overview_figure,
    summarize_metrics,
)

logger = get_logger(__name__)

def generate_real_data_images():
    """実際の地理データを使用してネットワーク画像を生成"""
    
    # 出力ディレクトリの作成
    real_output_dir = project_root / "data" / "real_network_images"
    network_output_dir = project_root / "data" / "network_images"
    real_output_dir.mkdir(parents=True, exist_ok=True)
    network_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 実際の分析結果データを読み込み
    real_data_path = project_root / "data" / "processed" / "real_analysis_results.csv"
    if not real_data_path.exists():
        logger.error("実際の分析結果データが見つかりません。先に generate_real_sample_data.py を実行してください。")
        return
    
    df = pd.read_csv(real_data_path)
    
    logger.info(f"実際の地理データから画像生成開始: {len(df)}地点")
    
    metric_summary = summarize_metrics(
        df,
        ["sparsity", "resilience", "multi_nodality", "permeability"],
    )

    # 各地点のネットワーク画像を生成
    successful_generations = 0
    failed_generations = 0
    
    for i, (idx, row) in enumerate(df.iterrows()):
        try:
            location_id = int(row['location_id'])
            lat, lon = row['latitude'], row['longitude']
            
            logger.info(f"実際の地理データ画像生成中: {i+1}/{len(df)} - 地点ID: {location_id} (緯度: {lat:.3f}, 経度: {lon:.3f})")
            
            # 実際の地理データを取得
            building_gdf, road_gdf = fetch_real_geographic_data(lat, lon, 2000)
            
            # ネットワークを構築
            network_graph = create_urban_network(building_gdf, road_gdf)
            
            # 1. 実際の地理データ対応画像を生成
            real_image_path = real_output_dir / f"real_network_{location_id:03d}.png"
            fig_real, _ = create_location_overview_figure(
                row,
                metric_summary,
                radius_meters=2000,
                buildings_gdf=building_gdf,
                roads_gdf=road_gdf,
                network_graph=network_graph,
            )
            
            fig_real.savefig(real_image_path, dpi=150, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
            plt.close(fig_real)
            
            # 2. 通常のネットワーク画像を生成
            network_image_path = network_output_dir / f"network_{location_id:03d}.png"
            fig_network = create_real_network_plot(
                network_graph, building_gdf, road_gdf, 
                row['sparsity'], row['resilience'], row['multi_nodality'],
                lat, lon
            )
            
            fig_network.savefig(network_image_path, dpi=150, bbox_inches='tight', 
                              facecolor='white', edgecolor='none')
            plt.close(fig_network)
            
            successful_generations += 1
            logger.info(f"地点 {location_id} の画像生成完了")
            
            # 進捗表示
            if (i + 1) % 50 == 0:
                logger.info(f"進捗: {i+1}/{len(df)} ({successful_generations}成功, {failed_generations}失敗)")
            
            # レート制限対策
            time.sleep(0.2)
            
        except Exception as e:
            failed_generations += 1
            logger.error(f"地点 {location_id} の画像生成エラー: {e}")
            continue
    
    logger.info("実際の地理データから画像生成完了")
    logger.info(f"成功: {successful_generations}件, 失敗: {failed_generations}件")

def create_real_network_plot(network_graph, building_gdf, road_gdf, 
                            sparsity, resilience, polycentricity, lat, lon):
    """実際のデータを使用したネットワーク画像を作成"""
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    
    # 背景を白に設定
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    # データの境界を取得
    if not building_gdf.empty:
        bounds = building_gdf.total_bounds
        x_min, y_min, x_max, y_max = bounds
        margin = (x_max - x_min) * 0.1
        x_min -= margin
        y_min -= margin
        x_max += margin
        y_max += margin
    else:
        x_min, y_min, x_max, y_max = -1000, -1000, 1000, 1000
    
    # 指標に基づいた色分け
    if sparsity < 0.3:
        primary_color = '#FF6B6B'
    elif sparsity < 0.7:
        primary_color = '#4ECDC4'
    else:
        primary_color = '#96CEB4'
    
    # 道路を描画
    if not road_gdf.empty:
        road_gdf.plot(ax=ax, color='gray', alpha=0.6, linewidth=2)
    
    # 建物を描画
    if not building_gdf.empty:
        building_gdf.plot(ax=ax, color=primary_color, edgecolor='darkgray', 
                         linewidth=0.5, alpha=0.8)
    
    # ネットワークを描画
    if network_graph.number_of_nodes() > 0:
        pos = {}
        for i, (idx, building) in enumerate(building_gdf.iterrows()):
            centroid = building.geometry.centroid
            pos[i] = (centroid.x, centroid.y)
        
        # ノードの色を多中心性に基づいて設定
        node_colors = []
        for node in network_graph.nodes():
            if network_graph.degree(node) > 3:
                node_colors.append('#FF6B6B')
            else:
                node_colors.append('#4ECDC4')
        
        nx.draw_networkx_nodes(network_graph, pos, ax=ax, 
                              node_color=node_colors, node_size=100, alpha=0.9)
        nx.draw_networkx_edges(network_graph, pos, ax=ax, 
                              edge_color='red', alpha=0.6, width=1.5)
    
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel('X (m)', fontsize=14, fontfamily='Arial')
    ax.set_ylabel('Y (m)', fontsize=14, fontfamily='Arial')
    ax.set_title(f'Real Network Analysis\nLat: {lat:.3f}, Lon: {lon:.3f} | '
                f'Sparsity: {sparsity:.2f}, Resilience: {resilience:.2f}', 
                fontsize=16, fontfamily='Arial', pad=20)
    ax.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    return fig

def main():
    """メイン関数"""
    try:
        generate_real_data_images()
        logger.info("実際の地理データから画像生成が完了しました")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    main()
