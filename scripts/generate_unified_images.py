#!/usr/bin/env python3
"""
統一された画像生成スクリプト
実際の地理データ（GSI）から取得した建物データを使って、すべての画像を統一
"""

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import base64
import io

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_fetcher_corrected import fetch_real_geographic_data
from src.network_builder_corrected import create_urban_network
from src.app.satellite_cache import satellite_cache

def generate_unified_images():
    """統一された画像を生成"""
    
    # データを読み込み
    real_data_path = project_root / "data" / "processed" / "real_analysis_results.csv"
    if not real_data_path.exists():
        print("❌ 実際のデータファイルが見つかりません")
        return
    
    df = pd.read_csv(real_data_path)
    print(f"✅ 実際の地理データを読み込みました: {len(df)}地点")
    
    # 出力ディレクトリを作成
    unified_output_dir = project_root / "data" / "unified_images"
    unified_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔄 統一された画像生成開始: {len(df)}地点")
    
    successful = 0
    failed = 0
    
    for i, (idx, row) in enumerate(df.iterrows()):
        try:
            location_id = int(row['location_id'])
            lat, lon = row['latitude'], row['longitude']
            
            print(f"画像生成中: {i+1}/{len(df)} - 地点ID: {location_id} (緯度: {lat:.3f}, 経度: {lon:.3f})")
            
            # 実際の地理データを取得
            buildings_gdf, roads_gdf = fetch_real_geographic_data(lat, lon, 2000)
            
            if buildings_gdf.empty and roads_gdf.empty:
                print(f"⚠️ 地点 {location_id} でデータが見つかりませんでした - スキップ")
                failed += 1
                continue
            
            # ネットワークを構築
            network_graph = create_urban_network(buildings_gdf, roads_gdf)
            
            # 統一された画像を生成
            fig = create_unified_plot(
                buildings_gdf, roads_gdf, network_graph,
                row['sparsity'], row['resilience'], row['multi_nodality'],
                lat, lon
            )
            
            # 画像を保存
            output_path = unified_output_dir / f"unified_{location_id:03d}.png"
            fig.savefig(output_path, dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            successful += 1
            print(f"✅ 地点 {location_id} の画像生成完了")
            
            # 進捗表示
            if (i + 1) % 50 == 0:
                print(f"進捗: {i+1}/{len(df)} ({successful}成功, {failed}失敗)")
            
        except Exception as e:
            failed += 1
            print(f"❌ 地点 {location_id} の画像生成エラー: {e}")
            continue
    
    print(f"🎉 統一された画像生成完了: 成功 {successful}件, 失敗 {failed}件")
    print(f"📁 保存先: {unified_output_dir}")

def create_unified_plot(buildings_gdf, roads_gdf, network_graph, 
                       sparsity, resilience, multi_nodality, lat, lon):
    """統一された画像を作成（実際の地理データベース）"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 16))
    
    # 背景を白に設定
    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_facecolor('white')
        ax.set_xticks([])
        ax.set_yticks([])
    fig.patch.set_facecolor('white')
    
    # データの境界を取得
    if not buildings_gdf.empty:
        bounds = buildings_gdf.total_bounds
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
        building_color = '#FF6B6B'  # 高密度（低疎性）
    elif sparsity < 0.7:
        building_color = '#4ECDC4'  # 中密度
    else:
        building_color = '#96CEB4'  # 低密度（高疎性）
    
    # 1. 実際の建物のみの表示
    ax1.set_title(f'実際の建物データ - 疎性: {sparsity:.2f}', 
                  fontsize=14, fontfamily='Arial', pad=20)
    if not buildings_gdf.empty:
        buildings_gdf.plot(ax=ax1, color=building_color, edgecolor='darkgray', 
                         linewidth=0.5, alpha=0.8)
    
    ax1.set_xlim(x_min, x_max)
    ax1.set_ylim(y_min, y_max)
    ax1.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax1.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax1.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax1.set_aspect('equal')
    
    # 2. 実際の建物 + 道路の表示
    ax2.set_title('実際の建物 + 道路データ', fontsize=14, fontfamily='Arial', pad=20)
    if not roads_gdf.empty:
        roads_gdf.plot(ax=ax2, color='gray', alpha=0.7, linewidth=2)
    if not buildings_gdf.empty:
        buildings_gdf.plot(ax=ax2, color=building_color, edgecolor='darkgray', 
                         linewidth=0.5, alpha=0.6)
    
    ax2.set_xlim(x_min, x_max)
    ax2.set_ylim(y_min, y_max)
    ax2.set_xlabel('X (m)', fontsize=12, fontfamily='Arial')
    ax2.set_ylabel('Y (m)', fontsize=12, fontfamily='Arial')
    ax2.grid(True, color='lightgray', linewidth=0.5, alpha=0.5)
    ax2.set_aspect('equal')
    
    # 3. 実際の建物 + ネットワークの表示
    ax3.set_title(f'実際の建物 + ネットワーク - レジリエンス: {resilience:.2f}', 
                  fontsize=14, fontfamily='Arial', pad=20)
    if not buildings_gdf.empty:
        buildings_gdf.plot(ax=ax3, color=building_color, edgecolor='darkgray', 
                         linewidth=0.5, alpha=0.8)
    
    # ネットワークの描画
    if network_graph.number_of_nodes() > 0:
        # 建物の中心点をノード位置として使用
        pos = {}
        for i, (idx, building) in enumerate(buildings_gdf.iterrows()):
            centroid = building.geometry.centroid
            pos[i] = (centroid.x, centroid.y)
        
        # ノードの色を多中心性に基づいて設定
        node_colors = []
        for node in network_graph.nodes():
            if network_graph.degree(node) > 3:
                node_colors.append('#FF6B6B')  # 高次数ノード
            else:
                node_colors.append('#4ECDC4')  # 低次数ノード
        
        import networkx as nx
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
    
    # 4. 統合表示（実際のデータベース）
    ax4.set_title(f'統合表示 - 多中心性: {multi_nodality:.2f}', 
                  fontsize=14, fontfamily='Arial', pad=20)
    if not roads_gdf.empty:
        roads_gdf.plot(ax=ax4, color='gray', alpha=0.5, linewidth=1.5)
    if not buildings_gdf.empty:
        buildings_gdf.plot(ax=ax4, color=building_color, edgecolor='darkgray', 
                         linewidth=0.3, alpha=0.7)
    if network_graph.number_of_nodes() > 0 and pos:
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
    fig.suptitle(f'統一された地理データ分析\n緯度: {lat:.3f}, 経度: {lon:.3f} | '
                f'疎性: {sparsity:.2f}, レジリエンス: {resilience:.2f}, '
                f'多中心性: {multi_nodality:.2f}', 
                fontsize=16, fontfamily='Arial', y=0.95)
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    generate_unified_images()
