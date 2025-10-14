#!/usr/bin/env python3
"""
実際の地理データから指標を計算するモジュール
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import networkx as nx
from sklearn.cluster import DBSCAN
from scipy.sparse import csgraph
from scipy.spatial.distance import pdist, squareform
import logging
from typing import Tuple, Dict, Any
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_fetcher import fetch_real_geographic_data
from src.network_builder import create_urban_network

logger = logging.getLogger(__name__)

class RealMetricsCalculator:
    """実際の地理データから指標を計算するクラス"""
    
    def __init__(self):
        self.analysis_radius = 2000  # メートル
        
    def calculate_all_metrics(self, lat: float, lon: float) -> Dict[str, float]:
        """
        指定された地点の全指標を計算
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            Dict[str, float]: 計算された指標値
        """
        try:
            # 実際の地理データを取得
            building_gdf, road_gdf = fetch_real_geographic_data(lat, lon, self.analysis_radius)
            
            # ネットワークを構築
            network_graph = create_urban_network(building_gdf, road_gdf)
            
            # 各指標を計算
            metrics = {
                'sparsity': self.calculate_sparsity(building_gdf),
                'resilience': self.calculate_resilience(network_graph),
                'multi_nodality': self.calculate_multi_nodality(building_gdf),
                'permeability': self.calculate_permeability(building_gdf, road_gdf),
                'emergence': self.calculate_emergence(building_gdf, network_graph),
                'overlap': self.calculate_overlap(building_gdf, road_gdf)
            }
            
            logger.info(f"指標計算完了: 緯度 {lat:.3f}, 経度 {lon:.3f}")
            logger.info(f"計算結果: {metrics}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"指標計算エラー: {e}")
            # エラー時はデフォルト値を返す
            return self._get_default_metrics()
    
    def calculate_sparsity(self, building_gdf: gpd.GeoDataFrame) -> float:
        """
        疎性指標を計算（フラクタル次元ベース）
        
        Args:
            building_gdf: 建物のGeoDataFrame
            
        Returns:
            float: 疎性指標値（0-2の範囲）
        """
        if building_gdf.empty:
            return 0.0
        
        try:
            # 建物の中心点を取得
            building_centroids = building_gdf.geometry.centroid
            
            # 座標を配列に変換
            coords = np.array([[p.x, p.y] for p in building_centroids])
            
            if len(coords) < 4:
                return 0.0
            
            # ボックスカウンティング法でフラクタル次元を計算
            fractal_dimension = self._calculate_fractal_dimension(coords)
            
            # 疎性指標に変換（フラクタル次元が低いほど疎）
            sparsity = max(0.0, min(2.0, 2.0 - fractal_dimension))
            
            return sparsity
            
        except Exception as e:
            logger.error(f"疎性計算エラー: {e}")
            return 0.0
    
    def calculate_resilience(self, network_graph: nx.Graph) -> float:
        """
        レジリエンス指標を計算（Fiedler値ベース）
        
        Args:
            network_graph: ネットワークグラフ
            
        Returns:
            float: レジリエンス指標値（0-1の範囲）
        """
        if network_graph.number_of_nodes() < 2:
            return 0.0
        
        try:
            # グラフの連結性を確認
            if not nx.is_connected(network_graph):
                # 連結していない場合は最小のFiedler値を計算
                components = list(nx.connected_components(network_graph))
                fiedler_values = []
                
                for component in components:
                    if len(component) >= 2:
                        subgraph = network_graph.subgraph(component)
                        fiedler_val = self._calculate_fiedler_value(subgraph)
                        fiedler_values.append(fiedler_val)
                
                if fiedler_values:
                    min_fiedler = min(fiedler_values)
                else:
                    min_fiedler = 0.0
            else:
                min_fiedler = self._calculate_fiedler_value(network_graph)
            
            # レジリエンス指標に変換（Fiedler値が高いほどレジリエント）
            resilience = max(0.0, min(1.0, min_fiedler / 10.0))  # 正規化
            
            return resilience
            
        except Exception as e:
            logger.error(f"レジリエンス計算エラー: {e}")
            return 0.0
    
    def calculate_multi_nodality(self, building_gdf: gpd.GeoDataFrame) -> float:
        """
        多中心性指標を計算（DBSCANベース）
        
        Args:
            building_gdf: 建物のGeoDataFrame
            
        Returns:
            float: 多中心性指標値（0-1の範囲）
        """
        if building_gdf.empty:
            return 0.0
        
        try:
            # 建物の中心点を取得
            building_centroids = building_gdf.geometry.centroid
            coords = np.array([[p.x, p.y] for p in building_centroids])
            
            if len(coords) < 5:
                return 0.0
            
            # DBSCANクラスタリング
            eps = 50.0  # メートル
            min_samples = 5
            
            clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
            labels = clustering.labels_
            
            # クラスター数を計算（ノイズを除く）
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            
            # 多中心性指標に変換
            max_expected_clusters = min(10, len(coords) // 10)  # 最大クラスター数
            multi_nodality = min(1.0, n_clusters / max_expected_clusters)
            
            return multi_nodality
            
        except Exception as e:
            logger.error(f"多中心性計算エラー: {e}")
            return 0.0
    
    def calculate_permeability(self, building_gdf: gpd.GeoDataFrame, road_gdf: gpd.GeoDataFrame) -> float:
        """
        透過性指標を計算（パーコレーション理論ベース）
        
        Args:
            building_gdf: 建物のGeoDataFrame
            road_gdf: 道路のGeoDataFrame
            
        Returns:
            float: 透過性指標値（0-1の範囲）
        """
        if building_gdf.empty or road_gdf.empty:
            return 0.0
        
        try:
            # グリッドベースのパーコレーション解析
            grid_resolution = 50  # メートル
            
            # 分析範囲を取得
            bounds = building_gdf.total_bounds
            x_min, y_min, x_max, y_max = bounds
            
            # グリッドを作成
            x_cells = int((x_max - x_min) / grid_resolution) + 1
            y_cells = int((y_max - y_min) / grid_resolution) + 1
            
            # 各グリッドセルで建物密度を計算
            grid_density = np.zeros((y_cells, x_cells))
            
            for idx, building in building_gdf.iterrows():
                centroid = building.geometry.centroid
                x_idx = int((centroid.x - x_min) / grid_resolution)
                y_idx = int((centroid.y - y_min) / grid_resolution)
                
                if 0 <= x_idx < x_cells and 0 <= y_idx < y_cells:
                    grid_density[y_idx, x_idx] += 1
            
            # パーコレーション閾値を設定
            threshold = 0.1  # 建物密度の閾値
            
            # パーコレーション確率を計算
            permeability = self._calculate_percolation_probability(grid_density, threshold)
            
            return permeability
            
        except Exception as e:
            logger.error(f"透過性計算エラー: {e}")
            return 0.0
    
    def calculate_emergence(self, building_gdf: gpd.GeoDataFrame, network_graph: nx.Graph) -> float:
        """
        創発性指標を計算（ネットワーク中心性と建物密度の関係）
        
        Args:
            building_gdf: 建物のGeoDataFrame
            network_graph: ネットワークグラフ
            
        Returns:
            float: 創発性指標値（0-1の範囲）
        """
        if building_gdf.empty or network_graph.number_of_nodes() == 0:
            return 0.0
        
        try:
            # 建物密度を計算
            total_area = building_gdf.total_bounds
            area = (total_area[2] - total_area[0]) * (total_area[3] - total_area[1])
            building_density = len(building_gdf) / area if area > 0 else 0
            
            # ネットワーク中心性を計算
            if network_graph.number_of_nodes() > 0:
                centrality = nx.degree_centrality(network_graph)
                avg_centrality = np.mean(list(centrality.values()))
            else:
                avg_centrality = 0.0
            
            # 創発性指標を計算（中心性と密度の相互作用）
            emergence = min(1.0, avg_centrality * building_density * 1000)  # 正規化
            
            return emergence
            
        except Exception as e:
            logger.error(f"創発性計算エラー: {e}")
            return 0.0
    
    def calculate_overlap(self, building_gdf: gpd.GeoDataFrame, road_gdf: gpd.GeoDataFrame) -> float:
        """
        重複指標を計算（機能的多様性）
        
        Args:
            building_gdf: 建物のGeoDataFrame
            road_gdf: 道路のGeoDataFrame
            
        Returns:
            float: 重複指標値（0-1の範囲）
        """
        # 現在は簡易実装（将来拡張予定）
        return 0.0
    
    def _calculate_fractal_dimension(self, coords: np.ndarray) -> float:
        """フラクタル次元を計算（ボックスカウンティング法）"""
        try:
            # 座標の範囲を取得
            x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
            y_min, y_max = coords[:, 1].min(), coords[:, 1].max()
            
            # ボックスサイズのリスト
            box_sizes = [10, 20, 40, 80, 160, 320]  # メートル
            
            counts = []
            for box_size in box_sizes:
                # グリッドを作成
                x_bins = int((x_max - x_min) / box_size) + 1
                y_bins = int((y_max - y_min) / box_size) + 1
                
                # 各ボックス内の点をカウント
                occupied_boxes = set()
                for x, y in coords:
                    x_idx = int((x - x_min) / box_size)
                    y_idx = int((y - y_min) / box_size)
                    occupied_boxes.add((x_idx, y_idx))
                
                counts.append(len(occupied_boxes))
            
            # 線形回帰でフラクタル次元を計算
            if len(counts) > 1:
                log_sizes = np.log(box_sizes)
                log_counts = np.log(counts)
                
                # 線形回帰
                slope = np.polyfit(log_sizes, log_counts, 1)[0]
                fractal_dimension = -slope
                
                return max(0.0, min(2.0, fractal_dimension))
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"フラクタル次元計算エラー: {e}")
            return 0.0
    
    def _calculate_fiedler_value(self, graph: nx.Graph) -> float:
        """Fiedler値（代数的連結度）を計算"""
        try:
            # 隣接行列を取得
            adj_matrix = nx.adjacency_matrix(graph).toarray()
            
            # ラプラシアン行列を計算
            degree_matrix = np.diag(np.sum(adj_matrix, axis=1))
            laplacian = degree_matrix - adj_matrix
            
            # 固有値を計算
            eigenvalues = np.linalg.eigvals(laplacian)
            eigenvalues = np.real(eigenvalues)  # 実部のみ取得
            eigenvalues = np.sort(eigenvalues)
            
            # Fiedler値（2番目に小さい固有値）
            if len(eigenvalues) >= 2:
                fiedler_value = eigenvalues[1]
                return max(0.0, fiedler_value)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Fiedler値計算エラー: {e}")
            return 0.0
    
    def _calculate_percolation_probability(self, grid_density: np.ndarray, threshold: float) -> float:
        """パーコレーション確率を計算"""
        try:
            # バイナリグリッドを作成
            binary_grid = (grid_density > threshold).astype(int)
            
            # 連結成分を計算
            from scipy import ndimage
            labeled_array, num_features = ndimage.label(binary_grid)
            
            # 最大連結成分のサイズを計算
            if num_features > 0:
                component_sizes = [np.sum(labeled_array == i) for i in range(1, num_features + 1)]
                max_component_size = max(component_sizes)
                total_cells = binary_grid.size
                
                # パーコレーション確率
                percolation_prob = max_component_size / total_cells if total_cells > 0 else 0.0
                return min(1.0, percolation_prob)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"パーコレーション確率計算エラー: {e}")
            return 0.0
    
    def _get_default_metrics(self) -> Dict[str, float]:
        """デフォルトの指標値を返す"""
        return {
            'sparsity': 0.5,
            'resilience': 0.5,
            'multi_nodality': 0.5,
            'permeability': 0.5,
            'emergence': 0.5,
            'overlap': 0.0
        }

# グローバルインスタンス
real_metrics_calculator = RealMetricsCalculator()

def calculate_real_metrics(lat: float, lon: float) -> Dict[str, float]:
    """
    実際の地理データから指標を計算する関数
    
    Args:
        lat: 緯度
        lon: 経度
        
    Returns:
        Dict[str, float]: 計算された指標値
    """
    return real_metrics_calculator.calculate_all_metrics(lat, lon)
