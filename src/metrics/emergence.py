"""
創発性指標計算モジュール

ネットワーク中心性と建物密度の関係から都市空間における創発的現象の可能性を評価。
計算式: (各余白地点のネットワーク中心性 / (1 + 建物密度))の平均
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from typing import List, Tuple, Dict, Any, Optional
from loguru import logger
from ..utils.config import get_config


class EmergenceCalculator:
    """創発性指標計算クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書（デフォルト: parameters.ymlから読み込み）
        """
        if config is None:
            config = get_config("emergence")
        
        self.config = config
        self.centrality_types = config.get("centrality", ["betweenness", "closeness", "eigenvector"])
        self.density_config = config.get("density", {})
    
    def calculate(self, buildings_gdf: gpd.GeoDataFrame, 
                 network_graph: Optional[nx.Graph] = None) -> Dict[str, float]:
        """
        創発性指標を計算
        
        Args:
            buildings_gdf: 建物データ
            network_graph: ネットワークグラフ（オプション）
            
        Returns:
            創発性指標の辞書
        """
        logger.info("創発性指標計算開始")
        
        # ネットワークグラフを作成（提供されていない場合）
        if network_graph is None:
            network_graph = self._create_network_graph(buildings_gdf)
        
        # 余白地点を特定
        open_spaces = self._identify_open_spaces(buildings_gdf)
        
        # 各余白地点の創発性を計算
        emergence_scores = []
        centrality_scores = {}
        
        for centrality_type in self.centrality_types:
            centrality_scores[centrality_type] = []
        
        for _, open_space in open_spaces.iterrows():
            # ネットワーク中心性を計算
            centrality = self._calculate_centrality_at_point(
                open_space.geometry.centroid, network_graph
            )
            
            # 建物密度を計算
            density = self._calculate_building_density(
                open_space.geometry.centroid, buildings_gdf
            )
            
            # 創発性スコアを計算
            for centrality_type in self.centrality_types:
                if centrality_type in centrality:
                    emergence_score = centrality[centrality_type] / (1 + density)
                    emergence_scores.append(emergence_score)
                    centrality_scores[centrality_type].append(centrality[centrality_type])
        
        # 平均創発性を計算
        if emergence_scores:
            mean_emergence = np.mean(emergence_scores)
        else:
            mean_emergence = 0.0
        
        # 各中心性の平均も計算
        mean_centralities = {}
        for centrality_type in self.centrality_types:
            if centrality_scores[centrality_type]:
                mean_centralities[f"mean_{centrality_type}"] = np.mean(centrality_scores[centrality_type])
            else:
                mean_centralities[f"mean_{centrality_type}"] = 0.0
        
        result = {
            'emergence': mean_emergence,
            'num_open_spaces': len(open_spaces),
            'num_emergence_scores': len(emergence_scores)
        }
        result.update(mean_centralities)
        
        logger.info(f"創発性指標計算完了: {mean_emergence:.4f}")
        return result
    
    def _create_network_graph(self, buildings_gdf: gpd.GeoDataFrame) -> nx.Graph:
        """
        建物からネットワークグラフを作成
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            ネットワークグラフ
        """
        G = nx.Graph()
        
        # 建物をノードとして追加
        for idx, building in buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            G.add_node(idx, 
                      pos=(centroid.x, centroid.y),
                      type=building.get('type', 'unknown'),
                      area=building.get('area_m2', 0))
        
        # 近接建物間をエッジで接続
        distance_threshold = 200.0  # 200メートル
        
        for i, building1 in buildings_gdf.iterrows():
            for j, building2 in buildings_gdf.iterrows():
                if i < j:  # 重複を避ける
                    distance = building1.geometry.distance(building2.geometry)
                    if distance <= distance_threshold:
                        G.add_edge(i, j, weight=distance)
        
        logger.info(f"ネットワークグラフ作成完了: {G.number_of_nodes()}ノード, {G.number_of_edges()}エッジ")
        return G
    
    def _identify_open_spaces(self, buildings_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        余白地点（オープンスペース）を特定
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            余白地点のGeoDataFrame
        """
        # 建物の境界を取得
        bounds = buildings_gdf.total_bounds
        
        # グリッドを作成して余白地点を特定
        grid_size = 100.0  # 100メートル
        x_min, y_min, x_max, y_max = bounds
        
        x_coords = np.arange(x_min, x_max, grid_size)
        y_coords = np.arange(y_min, y_max, grid_size)
        
        open_spaces = []
        
        for x in x_coords:
            for y in y_coords:
                from shapely.geometry import Point
                point = Point(x, y)
                
                # 建物との距離を計算
                min_distance = min(buildings_gdf.geometry.distance(point))
                
                # 十分な距離がある地点を余白地点とする
                if min_distance >= 50.0:  # 50メートル以上
                    open_spaces.append({
                        'geometry': point,
                        'min_distance_to_building': min_distance
                    })
        
        return gpd.GeoDataFrame(open_spaces, crs=buildings_gdf.crs)
    
    def _calculate_centrality_at_point(self, point, network_graph: nx.Graph) -> Dict[str, float]:
        """
        指定点でのネットワーク中心性を計算
        
        Args:
            point: 計算点
            network_graph: ネットワークグラフ
            
        Returns:
            中心性の辞書
        """
        # 最も近いノードを見つける
        nearest_node = self._find_nearest_node(point, network_graph)
        
        if nearest_node is None:
            return {centrality_type: 0.0 for centrality_type in self.centrality_types}
        
        # 各中心性を計算
        centrality_scores = {}
        
        try:
            # 設定ファイルで指定された中心性手法のみを計算
            centrality_method = self.config.get("centrality_method", "betweenness")
            
            if centrality_method == "betweenness":
                betweenness = nx.betweenness_centrality(network_graph, weight='weight')
                centrality_scores["betweenness"] = betweenness.get(nearest_node, 0.0)
            elif centrality_method == "closeness":
                closeness = nx.closeness_centrality(network_graph, distance='weight')
                centrality_scores["closeness"] = closeness.get(nearest_node, 0.0)
            elif centrality_method == "eigenvector":
                try:
                    eigenvector = nx.eigenvector_centrality(network_graph, weight='weight')
                    centrality_scores["eigenvector"] = eigenvector.get(nearest_node, 0.0)
                except nx.PowerIterationFailedConvergence:
                    centrality_scores["eigenvector"] = 0.0
            
            # 他の中心性は0として設定
            for centrality_type in self.centrality_types:
                if centrality_type not in centrality_scores:
                    centrality_scores[centrality_type] = 0.0
            
        except Exception as e:
            logger.warning(f"中心性計算エラー: {e}")
            for centrality_type in self.centrality_types:
                centrality_scores[centrality_type] = 0.0
        
        return centrality_scores
    
    def _find_nearest_node(self, point, network_graph: nx.Graph, 
                          max_distance: float = 200.0) -> Optional[int]:
        """
        指定点に最も近いノードを見つける
        
        Args:
            point: 検索点
            network_graph: ネットワークグラフ
            max_distance: 最大検索距離
            
        Returns:
            最も近いノードID（見つからない場合はNone）
        """
        min_distance = float('inf')
        nearest_node = None
        
        for node_id, data in network_graph.nodes(data=True):
            if 'pos' in data:
                node_pos = data['pos']
                from shapely.geometry import Point
                distance = point.distance(Point(node_pos))
                
                if distance < min_distance and distance <= max_distance:
                    min_distance = distance
                    nearest_node = node_id
        
        return nearest_node
    
    def _calculate_building_density(self, point, buildings_gdf: gpd.GeoDataFrame) -> float:
        """
        指定点周辺の建物密度を計算
        
        Args:
            point: 計算点
            buildings_gdf: 建物データ
            
        Returns:
            建物密度
        """
        radius = self.density_config.get("radius", 200.0)
        method = self.density_config.get("method", "gaussian")
        
        # 半径内の建物を取得
        buffer_geom = point.buffer(radius)
        nearby_buildings = buildings_gdf[buildings_gdf.geometry.intersects(buffer_geom)]
        
        if len(nearby_buildings) == 0:
            return 0.0
        
        # 密度計算
        if method == "gaussian":
            # ガウシアン重み付け
            total_weight = 0.0
            weighted_area = 0.0
            
            for _, building in nearby_buildings.iterrows():
                distance = point.distance(building.geometry.centroid)
                weight = np.exp(-(distance ** 2) / (2 * (radius / 3) ** 2))
                total_weight += weight
                weighted_area += building.get('area_m2', 0) * weight
            
            if total_weight > 0:
                density = weighted_area / (np.pi * radius ** 2)
            else:
                density = 0.0
        
        else:  # uniform
            # 一様重み付け
            total_area = nearby_buildings.get('area_m2', 0).sum()
            density = total_area / (np.pi * radius ** 2)
        
        return float(density)
