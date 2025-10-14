"""
適応性（レジリエンス）指標計算モジュール

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
    """適応性（レジリエンス）指標計算クラス"""
    
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
                 roads_gdf: Optional[gpd.GeoDataFrame] = None) -> Dict[str, float]:
        """
        適応性指標を計算
        
        Args:
            buildings_gdf: 建物データ
            roads_gdf: 道路データ（オプション）
            
        Returns:
            適応性指標の辞書
        """
        logger.info("適応性指標計算開始")
        
        results = {}
        
        # 各ネットワークタイプについて計算
        for network_type in self.network_types:
            try:
                # ネットワークグラフを作成
                if network_type == "building":
                    graph = self._create_building_network(buildings_gdf)
                elif network_type == "road" and roads_gdf is not None:
                    graph = self._create_road_network(roads_gdf)
                elif network_type == "mixed" and roads_gdf is not None:
                    graph = self._create_mixed_network(buildings_gdf, roads_gdf)
                else:
                    logger.warning(f"ネットワークタイプ '{network_type}' のデータが不足しています")
                    continue
                
                if graph.number_of_nodes() < 2:
                    logger.warning(f"ネットワーク '{network_type}' のノード数が少なすぎます")
                    results[f"{network_type}_resilience"] = 0.0
                    results[f"{network_type}_fiedler_value"] = 0.0
                    continue
                
                # Fiedler値を計算
                fiedler_value = self._calculate_fiedler_value(graph)
                
                # その他のネットワーク指標も計算
                network_metrics = self._calculate_network_metrics(graph)
                
                results[f"{network_type}_resilience"] = fiedler_value
                results[f"{network_type}_fiedler_value"] = fiedler_value
                results.update({f"{network_type}_{k}": v for k, v in network_metrics.items()})
                
            except Exception as e:
                logger.error(f"ネットワーク '{network_type}' の計算エラー: {e}")
                results[f"{network_type}_resilience"] = 0.0
                results[f"{network_type}_fiedler_value"] = 0.0
        
        # 全体の適応性指標（主要なネットワークの平均）
        main_resilience = results.get("mixed_resilience", 
                                    results.get("building_resilience", 
                                              results.get("road_resilience", 0.0)))
        
        results['resilience'] = main_resilience
        
        logger.info(f"適応性指標計算完了: {main_resilience:.4f}")
        return results
    
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
    
    def _create_mixed_network(self, buildings_gdf: gpd.GeoDataFrame, 
                            roads_gdf: gpd.GeoDataFrame) -> nx.Graph:
        """
        混合ネットワークを作成（建物と道路の結合）
        
        Args:
            buildings_gdf: 建物データ
            roads_gdf: 道路データ
            
        Returns:
            混合ネットワークグラフ
        """
        # 建物ネットワークを作成
        building_graph = self._create_building_network(buildings_gdf)
        
        # 道路ネットワークを作成
        road_graph = self._create_road_network(roads_gdf)
        
        # ネットワークを結合
        mixed_graph = nx.compose(building_graph, road_graph)
        
        # 建物と道路の接続を追加
        connection_threshold = 50.0  # 50メートル
        
        for building_node, building_data in building_graph.nodes(data=True):
            building_pos = building_data['pos']
            
            for road_node, road_data in road_graph.nodes(data=True):
                road_pos = road_data['pos']
                
                distance = np.sqrt((building_pos[0] - road_pos[0])**2 + 
                                 (building_pos[1] - road_pos[1])**2)
                
                if distance <= connection_threshold:
                    mixed_graph.add_edge(building_node, road_node, 
                                       weight=distance, connection_type='building_road')
        
        logger.info(f"混合ネットワーク作成完了: {mixed_graph.number_of_nodes()}ノード, {mixed_graph.number_of_edges()}エッジ")
        return mixed_graph
    
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
    
    def _calculate_network_metrics(self, graph: nx.Graph) -> Dict[str, float]:
        """
        その他のネットワーク指標を計算
        
        Args:
            graph: ネットワークグラフ
            
        Returns:
            ネットワーク指標の辞書
        """
        metrics = {}
        
        try:
            # 基本統計
            metrics['num_nodes'] = graph.number_of_nodes()
            metrics['num_edges'] = graph.number_of_edges()
            
            if graph.number_of_nodes() > 0:
                metrics['density'] = nx.density(graph)
                metrics['avg_clustering'] = nx.average_clustering(graph)
                
                # 連結性
                if nx.is_connected(graph):
                    metrics['diameter'] = nx.diameter(graph)
                    metrics['avg_path_length'] = nx.average_shortest_path_length(graph)
                else:
                    # 最大連結成分の指標
                    largest_cc = max(nx.connected_components(graph), key=len)
                    subgraph = graph.subgraph(largest_cc)
                    metrics['largest_cc_size'] = len(largest_cc)
                    metrics['diameter'] = nx.diameter(subgraph) if len(largest_cc) > 1 else 0
                    metrics['avg_path_length'] = nx.average_shortest_path_length(subgraph) if len(largest_cc) > 1 else 0
                
                # 中心性の平均
                betweenness = nx.betweenness_centrality(graph, weight='weight')
                metrics['avg_betweenness'] = np.mean(list(betweenness.values()))
                
                closeness = nx.closeness_centrality(graph, distance='weight')
                metrics['avg_closeness'] = np.mean(list(closeness.values()))
            
        except Exception as e:
            logger.warning(f"ネットワーク指標計算エラー: {e}")
            # デフォルト値を設定
            for key in ['density', 'avg_clustering', 'diameter', 'avg_path_length', 
                       'avg_betweenness', 'avg_closeness']:
                metrics[key] = 0.0
        
        return metrics
    
    def calculate_robustness(self, graph: nx.Graph, 
                           attack_strategy: str = "random") -> Dict[str, float]:
        """
        ネットワークの堅牢性を計算
        
        Args:
            graph: ネットワークグラフ
            attack_strategy: 攻撃戦略 ("random", "degree", "betweenness")
            
        Returns:
            堅牢性指標の辞書
        """
        if graph.number_of_nodes() < 3:
            return {'robustness': 0.0, 'critical_fraction': 0.0}
        
        # 元の連結性を記録
        original_connectivity = nx.is_connected(graph)
        if not original_connectivity:
            return {'robustness': 0.0, 'critical_fraction': 0.0}
        
        # ノードの重要度を計算
        if attack_strategy == "degree":
            importance = dict(graph.degree())
        elif attack_strategy == "betweenness":
            importance = nx.betweenness_centrality(graph, weight='weight')
        else:  # random
            importance = {node: np.random.random() for node in graph.nodes()}
        
        # ノードを重要度順にソート
        sorted_nodes = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        # 段階的にノードを削除して連結性を測定
        test_graph = graph.copy()
        critical_fraction = 0.0
        
        for i, (node, _) in enumerate(sorted_nodes):
            if node in test_graph:
                test_graph.remove_node(node)
                
                if not nx.is_connected(test_graph):
                    critical_fraction = (i + 1) / len(sorted_nodes)
                    break
        
        # 堅牢性指標（1に近いほど堅牢）
        robustness = 1.0 - critical_fraction
        
        return {
            'robustness': robustness,
            'critical_fraction': critical_fraction,
            'attack_strategy': attack_strategy
        }
