"""
ハイブリッドネットワーク構築モジュール

道路ノードと建物ノードを結合したネットワークを構築し、
パーコレーション解析の基盤を提供する。
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict
from shapely.geometry import Point, LineString
from scipy.spatial import cKDTree
import networkx as nx
from tqdm import tqdm
import warnings


class HybridNetwork:
    """
    道路と建物を統合したハイブリッドネットワーク。
    
    道路ノードと建物ノードを結合し、距離ベースのエッジで接続する。
    パーコレーション解析に最適化されたデータ構造。
    """
    
    def __init__(
        self,
        road_nodes: gpd.GeoDataFrame,
        building_nodes: gpd.GeoDataFrame,
        edges: Optional[pd.DataFrame] = None
    ):
        """
        ハイブリッドネットワークを初期化。
        
        Parameters
        ----------
        road_nodes : gpd.GeoDataFrame
            道路ノード（Pointジオメトリ）
        building_nodes : gpd.GeoDataFrame
            建物ノード（Pointジオメトリ）
        edges : pd.DataFrame, optional
            エッジデータ（source, target, lengthカラム）
        """
        self.road_nodes = road_nodes.copy()
        self.building_nodes = building_nodes.copy()
        
        # ノードIDを設定
        self.road_nodes['node_id'] = range(len(self.road_nodes))
        self.road_nodes['node_type'] = 'road'
        
        n_roads = len(self.road_nodes)
        self.building_nodes['node_id'] = range(n_roads, n_roads + len(self.building_nodes))
        self.building_nodes['node_type'] = 'building'
        
        # 全ノードを結合
        self.nodes = pd.concat([
            self.road_nodes[['node_id', 'node_type', 'geometry']],
            self.building_nodes[['node_id', 'node_type', 'geometry']]
        ], ignore_index=True)
        
        # エッジデータ
        if edges is None:
            self.edges = pd.DataFrame(columns=['source', 'target', 'length'])
        else:
            self.edges = edges.copy()
    
    def get_node_coords(self) -> np.ndarray:
        """全ノードの座標を取得"""
        coords = np.column_stack([
            self.nodes.geometry.x.values,
            self.nodes.geometry.y.values
        ])
        return coords
    
    def get_road_coords(self) -> np.ndarray:
        """道路ノードの座標を取得"""
        road_coords = np.column_stack([
            self.road_nodes.geometry.x.values,
            self.road_nodes.geometry.y.values
        ])
        return road_coords
    
    def get_building_coords(self) -> np.ndarray:
        """建物ノードの座標を取得"""
        building_coords = np.column_stack([
            self.building_nodes.geometry.x.values,
            self.building_nodes.geometry.y.values
        ])
        return building_coords
    
    def add_road_edges(self, max_distance: float = 50.0, verbose: bool = True):
        """
        道路ノード間のエッジを追加（道路セグメントに基づく）。
        
        Parameters
        ----------
        max_distance : float
            最大接続距離（メートル）
        verbose : bool
            進捗表示
        """
        if len(self.road_nodes) < 2:
            return
        
        road_coords = self.get_road_coords()
        tree = cKDTree(road_coords)
        
        # 近接ノードを検索
        pairs = tree.query_pairs(max_distance, output_type='ndarray')
        
        if len(pairs) == 0:
            return
        
        # 距離を計算
        distances = np.linalg.norm(
            road_coords[pairs[:, 0]] - road_coords[pairs[:, 1]],
            axis=1
        )
        
        # エッジデータフレームを作成
        road_edges = pd.DataFrame({
            'source': self.road_nodes.iloc[pairs[:, 0]]['node_id'].values,
            'target': self.road_nodes.iloc[pairs[:, 1]]['node_id'].values,
            'length': distances
        })
        
        # 既存のエッジと結合
        if len(self.edges) > 0:
            self.edges = pd.concat([self.edges, road_edges], ignore_index=True)
        else:
            self.edges = road_edges
        
        if verbose:
            print(f"Added {len(road_edges)} road edges")
    
    def add_building_to_road_edges(
        self,
        max_distance: float = 100.0,
        verbose: bool = True
    ):
        """
        建物ノードから最も近い道路ノードへのエッジを追加。
        
        Parameters
        ----------
        max_distance : float
            最大接続距離（メートル）
        verbose : bool
            進捗表示
        """
        if len(self.building_nodes) == 0 or len(self.road_nodes) == 0:
            return
        
        building_coords = self.get_building_coords()
        road_coords = self.get_road_coords()
        
        # 各建物から最も近い道路ノードを検索
        tree = cKDTree(road_coords)
        distances, indices = tree.query(building_coords, k=1)
        
        # 距離フィルタ
        valid_mask = distances <= max_distance
        
        if not np.any(valid_mask):
            return
        
        # エッジデータフレームを作成
        building_edges = pd.DataFrame({
            'source': self.building_nodes.iloc[valid_mask]['node_id'].values,
            'target': self.road_nodes.iloc[indices[valid_mask]]['node_id'].values,
            'length': distances[valid_mask]
        })
        
        # 既存のエッジと結合
        if len(self.edges) > 0:
            self.edges = pd.concat([self.edges, building_edges], ignore_index=True)
        else:
            self.edges = building_edges
        
        if verbose:
            print(f"Added {len(building_edges)} building-to-road edges")
    
    def add_building_edges(
        self,
        max_distance: float = 200.0,
        verbose: bool = True
    ):
        """
        建物ノード間のエッジを追加（距離ベース）。
        
        Parameters
        ----------
        max_distance : float
            最大接続距離（メートル）
        verbose : bool
            進捗表示
        """
        if len(self.building_nodes) < 2:
            return
        
        building_coords = self.get_building_coords()
        tree = cKDTree(building_coords)
        
        # 近接ノードを検索
        pairs = tree.query_pairs(max_distance, output_type='ndarray')
        
        if len(pairs) == 0:
            return
        
        # 距離を計算
        distances = np.linalg.norm(
            building_coords[pairs[:, 0]] - building_coords[pairs[:, 1]],
            axis=1
        )
        
        # エッジデータフレームを作成
        building_edges = pd.DataFrame({
            'source': self.building_nodes.iloc[pairs[:, 0]]['node_id'].values,
            'target': self.building_nodes.iloc[pairs[:, 1]]['node_id'].values,
            'length': distances
        })
        
        # 既存のエッジと結合
        if len(self.edges) > 0:
            self.edges = pd.concat([self.edges, building_edges], ignore_index=True)
        else:
            self.edges = building_edges
        
        if verbose:
            print(f"Added {len(building_edges)} building edges")
    
    def to_networkx(self) -> nx.Graph:
        """NetworkXグラフに変換"""
        G = nx.Graph()
        
        # ノードを追加
        for _, row in self.nodes.iterrows():
            G.add_node(
                int(row['node_id']),
                pos=(row.geometry.x, row.geometry.y),
                node_type=row['node_type']
            )
        
        # エッジを追加
        for _, row in self.edges.iterrows():
            G.add_edge(
                int(row['source']),
                int(row['target']),
                weight=float(row['length'])
            )
        
        return G


def build_hybrid_network(
    road_segments: gpd.GeoDataFrame,
    building_centroids: gpd.GeoDataFrame,
    road_node_distance: float = 50.0,
    building_to_road_distance: float = 100.0,
    building_to_building_distance: float = 200.0,
    verbose: bool = True
) -> HybridNetwork:
    """
    道路セグメントと建物重心からハイブリッドネットワークを構築。
    
    Parameters
    ----------
    road_segments : gpd.GeoDataFrame
        道路セグメント（LineString）
    building_centroids : gpd.GeoDataFrame
        建物重心（Point）
    road_node_distance : float
        道路ノード間の最大距離
    building_to_road_distance : float
        建物から道路への最大距離
    building_to_building_distance : float
        建物間の最大距離
    verbose : bool
        進捗表示
    
    Returns
    -------
    network : HybridNetwork
        構築されたハイブリッドネットワーク
    """
    if verbose:
        print("Building hybrid network...")
        print(f"  Road segments: {len(road_segments)}")
        print(f"  Building centroids: {len(building_centroids)}")
    
    # 道路セグメントからノードを抽出
    road_nodes_list = []
    for _, row in road_segments.iterrows():
        geom = row.geometry
        if geom.geom_type == 'LineString':
            # 始点と終点をノードとして追加
            road_nodes_list.append(Point(geom.coords[0]))
            road_nodes_list.append(Point(geom.coords[-1]))
        elif geom.geom_type == 'MultiLineString':
            for line in geom.geoms:
                road_nodes_list.append(Point(line.coords[0]))
                road_nodes_list.append(Point(line.coords[-1]))
    
    if len(road_nodes_list) == 0:
        warnings.warn("No road nodes extracted from segments")
        road_nodes = gpd.GeoDataFrame(
            geometry=[],
            crs=road_segments.crs
        )
    else:
        # 重複ノードを削除（近接ノードをマージ）
        road_points = gpd.GeoDataFrame(geometry=road_nodes_list, crs=road_segments.crs)
        road_coords = np.column_stack([
            road_points.geometry.x.values,
            road_points.geometry.y.values
        ])
        
        # 近接ノードをマージ（50m以内）
        tree = cKDTree(road_coords)
        pairs = tree.query_pairs(road_node_distance, output_type='ndarray')
        
        # クラスタリング（Union-Find）
        n = len(road_points)
        parent = list(range(n))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        for i, j in pairs:
            union(i, j)
        
        # 代表ノードを選択
        clusters = {}
        for i in range(n):
            root = find(i)
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(i)
        
        # 各クラスタの中心を代表ノードとして選択
        representative_nodes = []
        for cluster_indices in clusters.values():
            cluster_coords = road_coords[cluster_indices]
            center = cluster_coords.mean(axis=0)
            representative_nodes.append(Point(center[0], center[1]))
        
        road_nodes = gpd.GeoDataFrame(
            geometry=representative_nodes,
            crs=road_segments.crs
        )
    
    # 建物重心をノードとして使用
    building_nodes = building_centroids.copy()
    
    # ハイブリッドネットワークを作成
    network = HybridNetwork(road_nodes, building_nodes)
    
    # エッジを追加
    network.add_road_edges(max_distance=road_node_distance, verbose=verbose)
    network.add_building_to_road_edges(
        max_distance=building_to_road_distance,
        verbose=verbose
    )
    network.add_building_edges(
        max_distance=building_to_building_distance,
        verbose=verbose
    )
    
    if verbose:
        print(f"Network built: {len(network.nodes)} nodes, {len(network.edges)} edges")
    
    return network


# Example usage
if __name__ == "__main__":
    # テスト用の例
    print("Hybrid Network Builder Test")
    print("Note: Requires road segments and building centroids to run")
