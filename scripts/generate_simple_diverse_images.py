#!/usr/bin/env python3
"""
簡易版：地理的特徴を反映した多様なネットワーク画像を生成するスクリプト
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
import warnings
warnings.filterwarnings('ignore')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.logger import get_logger

logger = get_logger(__name__)

def generate_simple_diverse_images():
    """簡易版：地理的特徴を反映した多様なネットワーク画像を生成"""
    
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
    
    logger.info(f"全{len(df)}地点の簡易多様ネットワーク画像生成開始")
    
    # 各地点のネットワーク画像を生成
    for i, (idx, row) in enumerate(df.iterrows()):
        try:
            location_id = int(row['location_id'])
            lat, lon = row['latitude'], row['longitude']
            
            logger.info(f"簡易多様ネットワーク画像生成中: {i+1}/{len(df)} - 地点ID: {location_id} (緯度: {lat:.3f}, 経度: {lon:.3f})")
            
            # 1. 実際の地理データ対応画像を生成
            real_image_path = real_output_dir / f"real_network_{location_id:03d}.png"
            fig_real = create_simple_geographic_plot(lat, lon, row)
            fig_real.savefig(real_image_path, dpi=150, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
            plt.close(fig_real)
            
            # 2. 通常のネットワーク画像を生成
            network_image_path = network_output_dir / f"network_{location_id:03d}.png"
            fig_network = create_simple_network_plot(lat, lon, row)
            fig_network.savefig(network_image_path, dpi=150, bbox_inches='tight', 
                              facecolor='white', edgecolor='none')
            plt.close(fig_network)
            
            logger.info(f"地点 {location_id} の画像生成完了")
            
        except Exception as e:
            logger.error(f"地点 {location_id} の画像生成エラー: {e}")
            continue
    
    logger.info("全地点の簡易多様ネットワーク画像生成完了")

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

def get_region_colors(region_type):
    """地域タイプに基づいて色を取得"""
    
    color_schemes = {
        "tokyo_metropolitan": {
            "primary": '#FF6B6B',    # 赤系
            "secondary": '#FF8E8E',  # 薄い赤
            "accent": '#FFB3B3'      # さらに薄い赤
        },
        "osaka_metropolitan": {
            "primary": '#4ECDC4',    # 青緑系
            "secondary": '#6ED5CD',  # 薄い青緑
            "accent": '#8EDDD6'      # さらに薄い青緑
        },
        "nagoya_metropolitan": {
            "primary": '#45B7D1',    # 青系
            "secondary": '#6BC5D9',  # 薄い青
            "accent": '#91D3E1'      # さらに薄い青
        },
        "hokkaido": {
            "primary": '#96CEB4',    # 緑系
            "secondary": '#A8D4C1',  # 薄い緑
            "accent": '#BADACE'      # さらに薄い緑
        },
        "kyushu": {
            "primary": '#FFEAA7',    # 黄系
            "secondary": '#FFEDB8',  # 薄い黄
            "accent": '#FFF0C9'      # さらに薄い黄
        },
        "regional": {
            "primary": '#DDA0DD',    # 紫系
            "secondary": '#E4B3E4',  # 薄い紫
            "accent": '#EBC6EB'      # さらに薄い紫
        }
    }
    
    return color_schemes.get(region_type, color_schemes["regional"])

def create_simple_geographic_plot(lat, lon, row):
    """簡易版：地理的特徴を反映した画像を作成"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 16))
    
    # 背景を白に設定
    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    # 地域特性を決定
    region_type = determine_region_type(lat, lon)
    colors = get_region_colors(region_type)
    
    # 緯度経度をシードとして使用して再現可能な乱数を生成
    np.random.seed(int(lat * 1000 + lon * 1000) % 2**32)
    
    # 地域特性に基づいて建物配置パターンを調整
    if region_type in ["tokyo_metropolitan", "osaka_metropolitan", "nagoya_metropolitan"]:
        # 大都市圏：格子状配置
        pattern = "grid"
        num_buildings = np.random.randint(60, 100)
    elif region_type == "hokkaido":
        # 北海道：散在型配置
        pattern = "scattered"
        num_buildings = np.random.randint(20, 50)
    else:
        # その他：ランダム配置
        pattern = "random"
        num_buildings = np.random.randint(30, 70)
    
    # 1. 建物のみの表示
    ax1.set_title(f'Buildings - {region_type.replace("_", " ").title()}', 
                  fontsize=14, fontfamily='Arial', pad=20)
    
    buildings = []
    center_x, center_y = 0, 0
    
    for i in range(num_buildings):
        if pattern == "grid":
            # 格子状配置
            grid_size = int(np.sqrt(num_buildings))
            row_idx = i // grid_size
            col_idx = i % grid_size
            x = center_x + (col_idx - grid_size//2) * 60 + np.random.normal(0, 15)
            y = center_y + (row_idx - grid_size//2) * 60 + np.random.normal(0, 15)
        elif pattern == "scattered":
            # 散在型配置
            angle = np.random.uniform(0, 2*np.pi)
            radius = np.random.uniform(40, 200)
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
        else:  # random
            # ランダム配置
            x = center_x + np.random.uniform(-150, 150)
            y = center_y + np.random.uniform(-150, 150)
        
        # 建物サイズ
        width = np.random.uniform(15, 40)
        height = np.random.uniform(15, 40)
        
        # 建物の色を決定
        if i < num_buildings // 3:
            color = colors["primary"]
        elif i < 2 * num_buildings // 3:
            color = colors["secondary"]
        else:
            color = colors["accent"]
        
        # 建物を描画
        rect = patches.Rectangle((x - width/2, y - height/2), width, height,
                               facecolor=color, edgecolor='darkgray', linewidth=0.5, alpha=0.8)
        ax1.add_patch(rect)
        buildings.append((x, y, width, height))
    
    ax1.set_xlim(-200, 200)
    ax1.set_ylim(-200, 200)
    ax1.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax1.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax1.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax1.set_aspect('equal')
    
    # 2. 建物 + 道路の表示
    ax2.set_title('Buildings + Roads', fontsize=14, fontfamily='Arial', pad=20)
    
    # 道路を描画
    num_roads = np.random.randint(8, 20)
    for i in range(num_roads):
        if i < num_roads // 3:
            # 主要道路（直線的）
            start_x = np.random.uniform(-180, 180)
            start_y = np.random.uniform(-180, 180)
            end_x = np.random.uniform(-180, 180)
            end_y = np.random.uniform(-180, 180)
            width = np.random.uniform(6, 12)
        else:
            # 細い道路（曲線的）
            start_x = np.random.uniform(-150, 150)
            start_y = np.random.uniform(-150, 150)
            end_x = start_x + np.random.uniform(-80, 80)
            end_y = start_y + np.random.uniform(-80, 80)
            width = np.random.uniform(3, 8)
        
        ax2.plot([start_x, end_x], [start_y, end_y], color='gray', linewidth=width, alpha=0.7)
    
    # 建物を描画
    for x, y, width, height in buildings:
        rect = patches.Rectangle((x - width/2, y - height/2), width, height,
                               facecolor=colors["primary"], edgecolor='darkgray', 
                               linewidth=0.5, alpha=0.6)
        ax2.add_patch(rect)
    
    ax2.set_xlim(-200, 200)
    ax2.set_ylim(-200, 200)
    ax2.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax2.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax2.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax2.set_aspect('equal')
    
    # 3. ネットワーク構造の表示
    ax3.set_title('Network Structure', fontsize=14, fontfamily='Arial', pad=20)
    
    # 簡易ネットワークを生成
    G = nx.Graph()
    
    # 建物をノードとして追加
    for i, (x, y, width, height) in enumerate(buildings):
        G.add_node(i, pos=(x, y))
    
    # 近接する建物間にエッジを追加
    for i in range(len(buildings)):
        for j in range(i+1, len(buildings)):
            x1, y1, _, _ = buildings[i]
            x2, y2, _, _ = buildings[j]
            distance = np.sqrt((x1-x2)**2 + (y1-y2)**2)
            if distance < 80:  # 近接判定
                G.add_edge(i, j)
    
    # ネットワークを描画
    if G.number_of_nodes() > 0:
        pos = {i: (x, y) for i, (x, y, _, _) in enumerate(buildings)}
        
        # ノードの色を次数に基づいて設定
        node_colors = []
        for node in G.nodes():
            if G.degree(node) > 3:
                node_colors.append('#FF6B6B')  # 高次数ノード
            else:
                node_colors.append('#4ECDC4')  # 低次数ノード
        
        nx.draw_networkx_nodes(G, pos, ax=ax3, node_color=node_colors, node_size=80, alpha=0.8)
        nx.draw_networkx_edges(G, pos, ax=ax3, edge_color='gray', alpha=0.6, width=1.5)
    
    ax3.set_xlim(-200, 200)
    ax3.set_ylim(-200, 200)
    ax3.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax3.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax3.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax3.set_aspect('equal')
    
    # 4. 統合表示
    ax4.set_title('Integrated View', fontsize=14, fontfamily='Arial', pad=20)
    
    # 道路を描画
    for i in range(num_roads):
        if i < num_roads // 3:
            start_x = np.random.uniform(-180, 180)
            start_y = np.random.uniform(-180, 180)
            end_x = np.random.uniform(-180, 180)
            end_y = np.random.uniform(-180, 180)
            width = np.random.uniform(4, 8)
        else:
            start_x = np.random.uniform(-150, 150)
            start_y = np.random.uniform(-150, 150)
            end_x = start_x + np.random.uniform(-80, 80)
            end_y = start_y + np.random.uniform(-80, 80)
            width = np.random.uniform(2, 5)
        
        ax4.plot([start_x, end_x], [start_y, end_y], color='gray', linewidth=width, alpha=0.5)
    
    # 建物を描画
    for x, y, width, height in buildings:
        rect = patches.Rectangle((x - width/2, y - height/2), width, height,
                               facecolor=colors["primary"], edgecolor='darkgray', 
                               linewidth=0.3, alpha=0.7)
        ax4.add_patch(rect)
    
    # ネットワークを描画
    if G.number_of_nodes() > 0:
        pos = {i: (x, y) for i, (x, y, _, _) in enumerate(buildings)}
        nx.draw_networkx_nodes(G, pos, ax=ax4, node_color='red', node_size=50, alpha=0.8)
        nx.draw_networkx_edges(G, pos, ax=ax4, edge_color='red', alpha=0.4, width=1)
    
    ax4.set_xlim(-200, 200)
    ax4.set_ylim(-200, 200)
    ax4.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax4.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax4.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax4.set_aspect('equal')
    
    # 全体のタイトル
    fig.suptitle(f'Geographic Network Analysis\nLat: {lat:.3f}, Lon: {lon:.3f} | '
                f'Sparsity: {row["sparsity"]:.2f}, Resilience: {row["resilience"]:.2f}, '
                f'Polycentricity: {row["multi_nodality"]:.2f}', 
                fontsize=16, fontfamily='Arial', y=0.95)
    
    plt.tight_layout()
    return fig

def create_simple_network_plot(lat, lon, row):
    """簡易版：多様なネットワーク画像を作成"""
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    
    # 背景を白に設定
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    # 地域特性を決定
    region_type = determine_region_type(lat, lon)
    colors = get_region_colors(region_type)
    
    # 緯度経度をシードとして使用
    np.random.seed(int(lat * 1000 + lon * 1000) % 2**32)
    
    # 地域特性に基づいて建物配置パターンを調整
    if region_type in ["tokyo_metropolitan", "osaka_metropolitan", "nagoya_metropolitan"]:
        pattern = "grid"
        num_buildings = np.random.randint(50, 80)
    elif region_type == "hokkaido":
        pattern = "scattered"
        num_buildings = np.random.randint(15, 35)
    else:
        pattern = "random"
        num_buildings = np.random.randint(25, 55)
    
    # 建物を生成
    buildings = []
    center_x, center_y = 0, 0
    
    for i in range(num_buildings):
        if pattern == "grid":
            grid_size = int(np.sqrt(num_buildings))
            row_idx = i // grid_size
            col_idx = i % grid_size
            x = center_x + (col_idx - grid_size//2) * 50 + np.random.normal(0, 12)
            y = center_y + (row_idx - grid_size//2) * 50 + np.random.normal(0, 12)
        elif pattern == "scattered":
            angle = np.random.uniform(0, 2*np.pi)
            radius = np.random.uniform(30, 150)
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
        else:  # random
            x = center_x + np.random.uniform(-120, 120)
            y = center_y + np.random.uniform(-120, 120)
        
        width = np.random.uniform(12, 30)
        height = np.random.uniform(12, 30)
        buildings.append((x, y, width, height))
    
    # 道路を描画
    num_roads = np.random.randint(6, 15)
    for i in range(num_roads):
        if i < num_roads // 3:
            start_x = np.random.uniform(-150, 150)
            start_y = np.random.uniform(-150, 150)
            end_x = np.random.uniform(-150, 150)
            end_y = np.random.uniform(-150, 150)
            width = np.random.uniform(5, 10)
        else:
            start_x = np.random.uniform(-120, 120)
            start_y = np.random.uniform(-120, 120)
            end_x = start_x + np.random.uniform(-60, 60)
            end_y = start_y + np.random.uniform(-60, 60)
            width = np.random.uniform(2, 6)
        
        ax.plot([start_x, end_x], [start_y, end_y], color='gray', linewidth=width, alpha=0.6)
    
    # 建物を描画
    for x, y, width, height in buildings:
        rect = patches.Rectangle((x - width/2, y - height/2), width, height,
                               facecolor=colors["primary"], edgecolor='darkgray', 
                               linewidth=0.5, alpha=0.8)
        ax.add_patch(rect)
    
    # ネットワークを生成・描画
    G = nx.Graph()
    for i, (x, y, width, height) in enumerate(buildings):
        G.add_node(i, pos=(x, y))
    
    for i in range(len(buildings)):
        for j in range(i+1, len(buildings)):
            x1, y1, _, _ = buildings[i]
            x2, y2, _, _ = buildings[j]
            distance = np.sqrt((x1-x2)**2 + (y1-y2)**2)
            if distance < 70:
                G.add_edge(i, j)
    
    if G.number_of_nodes() > 0:
        pos = {i: (x, y) for i, (x, y, _, _) in enumerate(buildings)}
        
        node_colors = []
        for node in G.nodes():
            if G.degree(node) > 3:
                node_colors.append('#FF6B6B')
            else:
                node_colors.append('#4ECDC4')
        
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=100, alpha=0.9)
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color='red', alpha=0.6, width=1.5)
    
    ax.set_xlim(-150, 150)
    ax.set_ylim(-150, 150)
    ax.set_xlabel('X (m)', fontsize=14, fontfamily='Arial')
    ax.set_ylabel('Y (m)', fontsize=14, fontfamily='Arial')
    ax.set_title(f'Network Analysis - {region_type.replace("_", " ").title()}\n'
                f'Lat: {lat:.3f}, Lon: {lon:.3f} | '
                f'Sparsity: {row["sparsity"]:.2f}, Resilience: {row["resilience"]:.2f}', 
                fontsize=16, fontfamily='Arial', pad=20)
    ax.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    generate_simple_diverse_images()
