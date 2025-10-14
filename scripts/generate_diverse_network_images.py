#!/usr/bin/env python3
"""
地理的特徴を反映した多様なネットワーク画像を生成するスクリプト
各地点の緯度経度に基づいて異なる地理的特徴を持つ画像を生成
"""

import sys
import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, Polygon
import contextily as ctx
import warnings
warnings.filterwarnings('ignore')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_processing import load_spatial_data, preprocess_building_data, preprocess_road_data
from src.network_builder import create_urban_network, visualize_network
from src.utils.logger import get_logger

logger = get_logger(__name__)

def generate_diverse_network_images():
    """地理的特徴を反映した多様なネットワーク画像を生成"""
    
    # 出力ディレクトリの作成
    real_output_dir = project_root / "data" / "real_network_images"
    network_output_dir = project_root / "data" / "network_images"
    real_output_dir.mkdir(parents=True, exist_ok=True)
    network_output_dir.mkdir(parents=True, exist_ok=True)
    
    # サンプルデータの読み込み
    sample_data_path = project_root / "data" / "processed" / "sample_analysis_results.csv"
    if not sample_data_path.exists():
        logger.error("サンプルデータが見つかりません")
        return
    
    df = pd.read_csv(sample_data_path)
    
    logger.info(f"全{len(df)}地点の多様なネットワーク画像生成開始")
    
    # 各地点のネットワーク画像を生成
    for i, (idx, row) in enumerate(df.iterrows()):
        try:
            location_id = int(row['location_id'])
            lat, lon = row['latitude'], row['longitude']
            
            # 既に画像が存在する場合はスキップ
            real_image_path = real_output_dir / f"real_network_{location_id:03d}.png"
            network_image_path = network_output_dir / f"network_{location_id:03d}.png"
            
            if real_image_path.exists() and network_image_path.exists():
                logger.info(f"地点 {location_id} の画像は既に存在します - スキップ")
                continue
            
            logger.info(f"多様なネットワーク画像生成中: {i+1}/{len(df)} - 地点ID: {location_id} (緯度: {lat:.3f}, 経度: {lon:.3f})")
            
            # 緯度経度に基づいて地理的特徴を生成
            building_gdf, road_gdf = create_geographic_features(lat, lon, row)
            network_graph = create_urban_network(building_gdf, road_gdf)
            
            # 1. 実際の地理データ対応画像を生成
            if not real_image_path.exists():
                fig_real = create_geographic_network_plot(
                    network_graph, building_gdf, road_gdf, 
                    row['sparsity'], row['resilience'], row['multi_nodality'],
                    lat, lon
                )
                
                fig_real.savefig(real_image_path, dpi=150, bbox_inches='tight', 
                               facecolor='white', edgecolor='none')
                plt.close(fig_real)
            
            # 2. 通常のネットワーク画像を生成
            if not network_image_path.exists():
                fig_network = create_diverse_network_plot(
                    network_graph, building_gdf, road_gdf, 
                    row['sparsity'], row['resilience'], row['multi_nodality'],
                    lat, lon
                )
                
                fig_network.savefig(network_image_path, dpi=150, bbox_inches='tight', 
                                  facecolor='white', edgecolor='none')
                plt.close(fig_network)
            
            logger.info(f"地点 {location_id} の画像生成完了")
            
        except Exception as e:
            logger.error(f"地点 {location_id} の画像生成エラー: {e}")
            continue
    
    logger.info("全地点の多様なネットワーク画像生成完了")

def create_geographic_features(lat, lon, row):
    """緯度経度に基づいて地理的特徴を生成"""
    
    # 緯度経度に基づいて地域特性を決定
    region_type = determine_region_type(lat, lon)
    urban_density = determine_urban_density(lat, lon, row['sparsity'])
    
    # 建物データの生成
    building_gdf = create_diverse_buildings(lat, lon, region_type, urban_density)
    
    # 道路データの生成
    road_gdf = create_diverse_roads(lat, lon, region_type, urban_density)
    
    return building_gdf, road_gdf

def determine_region_type(lat, lon):
    """緯度経度に基づいて地域タイプを決定"""
    
    # 日本の主要地域の判定
    if 35.0 <= lat <= 36.0 and 139.0 <= lon <= 140.0:
        return "tokyo_metropolitan"  # 東京圏
    elif 34.0 <= lat <= 35.0 and 135.0 <= lon <= 136.0:
        return "osaka_metropolitan"  # 大阪圏
    elif 35.0 <= lat <= 36.0 and 136.0 <= lon <= 137.0:
        return "nagoya_metropolitan"  # 名古屋圏
    elif lat > 43.0:
        return "hokkaido"  # 北海道
    elif lat < 32.0:
        return "kyushu"  # 九州
    elif 35.0 <= lat <= 40.0 and 140.0 <= lon <= 141.0:
        return "tohoku"  # 東北
    else:
        return "regional"  # 地方都市

def determine_urban_density(lat, lon, sparsity):
    """都市密度を決定"""
    
    if sparsity < 0.3:
        return "high_density"  # 高密度
    elif sparsity < 0.7:
        return "medium_density"  # 中密度
    else:
        return "low_density"  # 低密度

def create_diverse_buildings(lat, lon, region_type, urban_density):
    """地域特性に基づいて多様な建物データを生成"""
    
    # 緯度経度をシードとして使用して再現可能な乱数を生成
    np.random.seed(int(lat * 1000 + lon * 1000) % 2**32)
    
    # 地域特性に基づいて建物密度を調整
    if urban_density == "high_density":
        num_buildings = np.random.randint(80, 120)
        building_size_range = (20, 60)
    elif urban_density == "medium_density":
        num_buildings = np.random.randint(40, 80)
        building_size_range = (30, 80)
    else:  # low_density
        num_buildings = np.random.randint(15, 40)
        building_size_range = (40, 100)
    
    # 地域特性に基づいて建物配置パターンを調整
    if region_type in ["tokyo_metropolitan", "osaka_metropolitan", "nagoya_metropolitan"]:
        # 大都市圏：格子状配置
        pattern = "grid"
    elif region_type == "hokkaido":
        # 北海道：散在型配置
        pattern = "scattered"
    else:
        # その他：ランダム配置
        pattern = "random"
    
    buildings = []
    center_x, center_y = 0, 0
    
    for i in range(num_buildings):
        if pattern == "grid":
            # 格子状配置
            grid_size = int(np.sqrt(num_buildings))
            row = i // grid_size
            col = i % grid_size
            x = center_x + (col - grid_size//2) * 80 + np.random.normal(0, 20)
            y = center_y + (row - grid_size//2) * 80 + np.random.normal(0, 20)
        elif pattern == "scattered":
            # 散在型配置
            angle = np.random.uniform(0, 2*np.pi)
            radius = np.random.uniform(50, 300)
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
        else:  # random
            # ランダム配置
            x = center_x + np.random.uniform(-200, 200)
            y = center_y + np.random.uniform(-200, 200)
        
        # 建物サイズ
        width = np.random.uniform(*building_size_range)
        height = np.random.uniform(*building_size_range)
        
        # 建物の形状を生成
        building = Polygon([
            (x - width/2, y - height/2),
            (x + width/2, y - height/2),
            (x + width/2, y + height/2),
            (x - width/2, y + height/2)
        ])
        
        buildings.append(building)
    
    # GeoDataFrameを作成
    building_gdf = gpd.GeoDataFrame({
        'geometry': buildings,
        'building_id': range(len(buildings)),
        'area': [geom.area for geom in buildings]
    }, crs='EPSG:4326')
    
    return building_gdf

def create_diverse_roads(lat, lon, region_type, urban_density):
    """地域特性に基づいて多様な道路データを生成"""
    
    # 緯度経度をシードとして使用
    np.random.seed(int(lat * 1000 + lon * 1000 + 1000) % 2**32)
    
    # 地域特性に基づいて道路密度を調整
    if urban_density == "high_density":
        num_roads = np.random.randint(20, 35)
        road_width_range = (8, 15)
    elif urban_density == "medium_density":
        num_roads = np.random.randint(12, 20)
        road_width_range = (6, 12)
    else:  # low_density
        num_roads = np.random.randint(6, 12)
        road_width_range = (4, 10)
    
    roads = []
    center_x, center_y = 0, 0
    
    for i in range(num_roads):
        # 道路の種類を決定
        if i < num_roads // 3:
            # 主要道路（直線的）
            start_x = center_x + np.random.uniform(-300, 300)
            start_y = center_y + np.random.uniform(-300, 300)
            end_x = center_x + np.random.uniform(-300, 300)
            end_y = center_y + np.random.uniform(-300, 300)
        else:
            # 細い道路（曲線的）
            start_x = center_x + np.random.uniform(-200, 200)
            start_y = center_y + np.random.uniform(-200, 200)
            end_x = start_x + np.random.uniform(-100, 100)
            end_y = start_y + np.random.uniform(-100, 100)
        
        # 道路の幅
        width = np.random.uniform(*road_width_range)
        
        # 道路の形状を生成（線形）
        from shapely.geometry import LineString
        road_line = LineString([(start_x, start_y), (end_x, end_y)])
        road = road_line.buffer(width/2)
        
        roads.append(road)
    
    # GeoDataFrameを作成
    road_gdf = gpd.GeoDataFrame({
        'geometry': roads,
        'road_id': range(len(roads)),
        'width': [np.random.uniform(*road_width_range) for _ in roads]
    }, crs='EPSG:4326')
    
    return road_gdf

def create_geographic_network_plot(network_graph, building_gdf, road_gdf, 
                                 sparsity, resilience, polycentricity, lat, lon):
    """地理的特徴を反映したネットワーク画像を作成"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 16))
    
    # 背景を白に設定
    for ax in [ax1, ax2, ax3, ax4]:
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
        x_min, y_min, x_max, y_max = -300, -300, 300, 300
    
    # 地域特性に基づいた色分け
    region_type = determine_region_type(lat, lon)
    if region_type == "tokyo_metropolitan":
        primary_color = '#FF6B6B'  # 赤系
    elif region_type == "osaka_metropolitan":
        primary_color = '#4ECDC4'  # 青緑系
    elif region_type == "nagoya_metropolitan":
        primary_color = '#45B7D1'  # 青系
    elif region_type == "hokkaido":
        primary_color = '#96CEB4'  # 緑系
    elif region_type == "kyushu":
        primary_color = '#FFEAA7'  # 黄系
    else:
        primary_color = '#DDA0DD'  # 紫系
    
    # 1. 建物のみの表示
    ax1.set_title(f'Buildings - {region_type.replace("_", " ").title()}', 
                  fontsize=14, fontfamily='Arial', pad=20)
    if not building_gdf.empty:
        building_gdf.plot(ax=ax1, color=primary_color, edgecolor='darkgray', 
                         linewidth=0.5, alpha=0.8)
    
    ax1.set_xlim(x_min, x_max)
    ax1.set_ylim(y_min, y_max)
    ax1.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax1.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax1.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax1.set_aspect('equal')
    
    # 2. 建物 + 道路の表示
    ax2.set_title('Buildings + Roads', fontsize=14, fontfamily='Arial', pad=20)
    if not road_gdf.empty:
        road_gdf.plot(ax=ax2, color='gray', alpha=0.7, linewidth=2)
    if not building_gdf.empty:
        building_gdf.plot(ax=ax2, color=primary_color, edgecolor='darkgray', 
                         linewidth=0.5, alpha=0.6)
    
    ax2.set_xlim(x_min, x_max)
    ax2.set_ylim(y_min, y_max)
    ax2.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax2.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax2.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax2.set_aspect('equal')
    
    # 3. ネットワーク構造の表示
    ax3.set_title('Network Structure', fontsize=14, fontfamily='Arial', pad=20)
    if network_graph.number_of_nodes() > 0:
        pos = nx.spring_layout(network_graph, k=1, iterations=50)
        
        # ノードの色を多中心性に基づいて設定
        node_colors = []
        for node in network_graph.nodes():
            if network_graph.degree(node) > 3:
                node_colors.append('#FF6B6B')  # 高次数ノード
            else:
                node_colors.append('#4ECDC4')  # 低次数ノード
        
        nx.draw_networkx_nodes(network_graph, pos, ax=ax3, 
                              node_color=node_colors, node_size=50, alpha=0.8)
        nx.draw_networkx_edges(network_graph, pos, ax=ax3, 
                              edge_color='gray', alpha=0.6, width=1)
    
    ax3.set_xlim(x_min, x_max)
    ax3.set_ylim(y_min, y_max)
    ax3.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax3.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax3.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax3.set_aspect('equal')
    
    # 4. 統合表示
    ax4.set_title('Integrated View', fontsize=14, fontfamily='Arial', pad=20)
    if not road_gdf.empty:
        road_gdf.plot(ax=ax4, color='gray', alpha=0.5, linewidth=1.5)
    if not building_gdf.empty:
        building_gdf.plot(ax=ax4, color=primary_color, edgecolor='darkgray', 
                         linewidth=0.3, alpha=0.7)
    if network_graph.number_of_nodes() > 0:
        pos = nx.spring_layout(network_graph, k=1, iterations=50)
        nx.draw_networkx_nodes(network_graph, pos, ax=ax4, 
                              node_color='red', node_size=30, alpha=0.8)
        nx.draw_networkx_edges(network_graph, pos, ax=ax4, 
                              edge_color='red', alpha=0.4, width=0.8)
    
    ax4.set_xlim(x_min, x_max)
    ax4.set_ylim(y_min, y_max)
    ax4.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax4.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax4.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax4.set_aspect('equal')
    
    # 全体のタイトル
    fig.suptitle(f'Geographic Network Analysis\nLat: {lat:.3f}, Lon: {lon:.3f} | '
                f'Sparsity: {sparsity:.2f}, Resilience: {resilience:.2f}, '
                f'Polycentricity: {polycentricity:.2f}', 
                fontsize=16, fontfamily='Arial', y=0.95)
    
    plt.tight_layout()
    return fig

def create_diverse_network_plot(network_graph, building_gdf, road_gdf, 
                               sparsity, resilience, polycentricity, lat, lon):
    """多様なネットワーク画像を作成"""
    
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
        x_min, y_min, x_max, y_max = -300, -300, 300, 300
    
    # 地域特性に基づいた色分け
    region_type = determine_region_type(lat, lon)
    if region_type == "tokyo_metropolitan":
        primary_color = '#FF6B6B'
    elif region_type == "osaka_metropolitan":
        primary_color = '#4ECDC4'
    elif region_type == "nagoya_metropolitan":
        primary_color = '#45B7D1'
    elif region_type == "hokkaido":
        primary_color = '#96CEB4'
    elif region_type == "kyushu":
        primary_color = '#FFEAA7'
    else:
        primary_color = '#DDA0DD'
    
    # 道路を描画
    if not road_gdf.empty:
        road_gdf.plot(ax=ax, color='gray', alpha=0.6, linewidth=2)
    
    # 建物を描画
    if not building_gdf.empty:
        building_gdf.plot(ax=ax, color=primary_color, edgecolor='darkgray', 
                         linewidth=0.5, alpha=0.8)
    
    # ネットワークを描画
    if network_graph.number_of_nodes() > 0:
        pos = nx.spring_layout(network_graph, k=1, iterations=50)
        
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
    ax.set_title(f'Network Analysis - {region_type.replace("_", " ").title()}\n'
                f'Lat: {lat:.3f}, Lon: {lon:.3f} | '
                f'Sparsity: {sparsity:.2f}, Resilience: {resilience:.2f}', 
                fontsize=16, fontfamily='Arial', pad=20)
    ax.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    generate_diverse_network_images()
