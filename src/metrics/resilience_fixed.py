"""
適応性（レジリエンス）指標計算モジュール（修正版）

ネットワークのFiedler値（代数的連結度）を用いて都市の適応性・レジリエンスを評価。
計算式: Fiedler値（グラフの代数的連結度）
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from scipy.sparse import csgraph
from typing import List, Tuple, Dict, Any, Optional
from loguru import logger
from ..utils.config import get_config


class ResilienceCalculator:
    """適応性（レジリエンス）指標計算クラス（修正版）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書（デフォルト: parameters.ymlから読み込み）
        """
        if config is None:
            config = get_config("resilience")
        
        self.config = config
        self.fiedler_config = config.get("fiedler", {})
        self.network_types = config.get("network_type", ["road", "building", "mixed"])
    
    def calculate(self, buildings_gdf: gpd.GeoDataFrame, 
                 roads_gdf: Optional[gpd.GeoDataFrame] = None,
                 network_graph: Optional[nx.Graph] = None) -> float:
        """
        適応性指標を計算（修正版：単一のfloat値を返す）
        
        Args:
            buildings_gdf: 建物データ
            roads_gdf: 道路データ（オプション）
            network_graph: ネットワークグラフ（オプション）
            
        Returns:
            適応性指標値（float）
        """
        logger.info("適応性指標計算開始")
        
        try:
            # ネットワークグラフが提供されている場合はそれを使用
            if network_graph is not None and network_graph.number_of_nodes() > 1:
                fiedler_value = self._calculate_fiedler_value(network_graph)
                logger.info(f"適応性指標計算完了: {fiedler_value:.4f}")
                return float(fiedler_value)
            
            # 建物データからネットワークを作成
            if not buildings_gdf.empty:
                graph = self._create_building_network(buildings_gdf)
                if graph.number_of_nodes() > 1:
                    fiedler_value = self._calculate_fiedler_value(graph)
                    logger.info(f"適応性指標計算完了: {fiedler_value:.4f}")
                    return float(fiedler_value)
            
            # 道路データからネットワークを作成
            if roads_gdf is not None and not roads_gdf.empty:
                graph = self._create_road_network(roads_gdf)
                if graph.number_of_nodes() > 1:
                    fiedler_value = self._calculate_fiedler_value(graph)
                    logger.info(f"適応性指標計算完了: {fiedler_value:.4f}")
                    return float(fiedler_value)
            
            # データが不足している場合はデフォルト値を返す
            logger.warning("適応性指標計算: データが不足しているためデフォルト値を返します")
            return 0.0
            
        except Exception as e:
            logger.error(f"適応性指標計算エラー: {e}")
            return 0.0
    
    def _create_building_network(self, buildings_gdf: gpd.GeoDataFrame) -> nx.Graph:
        """
        建物ネットワークを作成
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            建物ネットワークグラフ
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
        distance_threshold = self.fiedler_config.get("distance_threshold", 100.0)
        weight_method = self.fiedler_config.get("weight_method", "distance")
        
        for i, building1 in buildings_gdf.iterrows():
            for j, building2 in buildings_gdf.iterrows():
                if i < j:  # 重複を避ける
                    distance = building1.geometry.distance(building2.geometry)
                    if distance <= distance_threshold:
                        if weight_method == "distance":
                            weight = distance
                        else:  # uniform
                            weight = 1.0
                        G.add_edge(i, j, weight=weight)
        
        logger.info(f"建物ネットワーク作成完了: {G.number_of_nodes()}ノード, {G.number_of_edges()}エッジ")
        return G
    
    def _create_road_network(self, roads_gdf: gpd.GeoDataFrame) -> nx.Graph:
        """
        道路ネットワークを作成
        
        Args:
            roads_gdf: 道路データ
            
        Returns:
            道路ネットワークグラフ
        """
        G = nx.Graph()
        
        # 道路の端点をノードとして追加
        node_counter = 0
        point_to_node = {}
        
        for idx, road in roads_gdf.iterrows():
            coords = list(road.geometry.coords)
            
            for coord in coords:
                coord_key = (round(coord[0], 6), round(coord[1], 6))
                if coord_key not in point_to_node:
                    point_to_node[coord_key] = node_counter
                    G.add_node(node_counter, pos=coord)
                    node_counter += 1
        
        # 道路をエッジとして追加
        for idx, road in roads_gdf.iterrows():
            coords = list(road.geometry.coords)
            length = road.geometry.length
            
            for i in range(len(coords) - 1):
                coord1 = (round(coords[i][0], 6), round(coords[i][1], 6))
                coord2 = (round(coords[i+1][0], 6), round(coords[i+1][1], 6))
                
                if coord1 in point_to_node and coord2 in point_to_node:
                    node1 = point_to_node[coord1]
                    node2 = point_to_node[coord2]
                    
                    if not G.has_edge(node1, node2):
                        G.add_edge(node1, node2, weight=length, road_type=road.get('type', 'unknown'))
        
        logger.info(f"道路ネットワーク作成完了: {G.number_of_nodes()}ノード, {G.number_of_edges()}エッジ")
        return G
    
    def _calculate_fiedler_value(self, graph: nx.Graph) -> float:
        """
        Fiedler値（代数的連結度）を計算
        
        Args:
            graph: ネットワークグラフ
            
        Returns:
            Fiedler値
        """
        try:
            # ラプラシアン行列を計算
            laplacian = nx.laplacian_matrix(graph, weight='weight')
            
            # 固有値を計算
            eigenvalues = np.linalg.eigvals(laplacian.toarray())
            eigenvalues = np.real(eigenvalues)  # 実部のみ取得
            eigenvalues = np.sort(eigenvalues)
            
            # Fiedler値は2番目に小さい固有値
            if len(eigenvalues) >= 2:
                fiedler_value = eigenvalues[1]
            else:
                fiedler_value = 0.0
            
            return float(fiedler_value)
            
        except Exception as e:
            logger.error(f"Fiedler値計算エラー: {e}")
            return 0.0

