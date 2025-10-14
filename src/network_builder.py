"""
ネットワーク構築モジュール

建物と道路データから都市ネットワークを構築する機能を提供します。
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import networkx as nx
from shapely.geometry import Point, LineString
from typing import Tuple, Dict, Any, Optional, List
from loguru import logger
from .utils.config import get_config


def create_urban_network(building_gdf: gpd.GeoDataFrame, 
                        road_gdf: gpd.GeoDataFrame) -> nx.Graph:
    """
    建物と道路データから都市ネットワークを構築する
    
    Args:
        building_gdf: 建物データ
        road_gdf: 道路データ
        
    Returns:
        都市ネットワークのNetworkX Graph
    """
    logger.info("都市ネットワーク構築開始")
    
    # 座標系を統一（投影座標系）
    building_gdf = building_gdf.to_crs("EPSG:3857")
    road_gdf = road_gdf.to_crs("EPSG:3857")
    
    # グラフを初期化
    G = nx.Graph()
    
    # 1. 建物をノードとして追加
    _add_building_nodes(G, building_gdf)
    
    # 2. 道路ネットワークを構築
    _add_road_network(G, road_gdf)
    
    # 3. 建物と道路を接続
    _connect_buildings_to_roads(G, building_gdf, road_gdf)
    
    # 4. 建物間の接続を追加（近接建物）
    # 建物間の接続は解析対象外にするためスキップ
    
    logger.info(f"都市ネットワーク構築完了: {G.number_of_nodes()}ノード, {G.number_of_edges()}エッジ")
    
    return G


def _add_building_nodes(G: nx.Graph, building_gdf: gpd.GeoDataFrame) -> None:
    """
    建物をノードとして追加する
    
    Args:
        G: ネットワークグラフ
        building_gdf: 建物データ
    """
    for idx, building in building_gdf.iterrows():
        centroid = building.geometry.centroid
        
        G.add_node(
            f"building_{idx}",
            node_type="building",
            pos=(centroid.x, centroid.y),
            building_id=idx,
            building_type=building.get('type', 'unknown'),
            area=building.get('area_m2', 0),
            geometry=building.geometry
        )


def _add_road_network(G: nx.Graph, road_gdf: gpd.GeoDataFrame) -> None:
    """
    道路ネットワークを構築する
    
    Args:
        G: ネットワークグラフ
        road_gdf: 道路データ
    """
    # 道路の端点をノードとして追加
    point_to_node = {}
    node_counter = 0
    
    for idx, road in road_gdf.iterrows():
        coords = list(road.geometry.coords)
        
        for coord in coords:
            # 座標をキーとして使用（精度を下げて重複を避ける）
            coord_key = (round(coord[0], 2), round(coord[1], 2))
            
            if coord_key not in point_to_node:
                point_to_node[coord_key] = f"road_node_{node_counter}"
                G.add_node(
                    f"road_node_{node_counter}",
                    node_type="road",
                    pos=coord,
                    road_type=road.get('type', 'unknown')
                )
                node_counter += 1
    
    # 道路をエッジとして追加
    for idx, road in road_gdf.iterrows():
        coords = list(road.geometry.coords)
        length = road.geometry.length
        
        for i in range(len(coords) - 1):
            coord1 = (round(coords[i][0], 2), round(coords[i][1], 2))
            coord2 = (round(coords[i+1][0], 2), round(coords[i+1][1], 2))
            
            if coord1 in point_to_node and coord2 in point_to_node:
                node1 = point_to_node[coord1]
                node2 = point_to_node[coord2]
                
                if not G.has_edge(node1, node2):
                    G.add_edge(
                        node1, 
                        node2, 
                        weight=length,
                        edge_type="road",
                        road_type=road.get('type', 'unknown')
                    )


def _connect_buildings_to_roads(G: nx.Graph, 
                               building_gdf: gpd.GeoDataFrame, 
                               road_gdf: gpd.GeoDataFrame) -> None:
    """
    建物と道路を接続する
    
    Args:
        G: ネットワークグラフ
        building_gdf: 建物データ
        road_gdf: 道路データ
    """
    connection_threshold = 100.0  # 100メートル
    
    for idx, building in building_gdf.iterrows():
        building_node = f"building_{idx}"
        building_pos = building.geometry.centroid
        
        # 最も近い道路ノードを見つける
        nearest_road_node = _find_nearest_road_node(G, building_pos, connection_threshold)
        
        if nearest_road_node:
            distance = Point(building_pos).distance(Point(G.nodes[nearest_road_node]['pos']))
            G.add_edge(
                building_node,
                nearest_road_node,
                weight=distance,
                edge_type="building_road_connection"
            )


def _connect_nearby_buildings(G: nx.Graph, building_gdf: gpd.GeoDataFrame) -> None:
    """
    近接する建物間を接続する
    
    Args:
        G: ネットワークグラフ
        building_gdf: 建物データ
    """
    distance_threshold = 200.0  # 200メートル
    
    for i, building1 in building_gdf.iterrows():
        for j, building2 in building_gdf.iterrows():
            if i < j:  # 重複を避ける
                distance = building1.geometry.distance(building2.geometry)
                
                if distance <= distance_threshold:
                    building_node1 = f"building_{i}"
                    building_node2 = f"building_{j}"
                    
                    G.add_edge(
                        building_node1,
                        building_node2,
                        weight=distance,
                        edge_type="building_building"
                    )


def _find_nearest_road_node(G: nx.Graph, point: Point, max_distance: float) -> Optional[str]:
    """
    指定点に最も近い道路ノードを見つける
    
    Args:
        G: ネットワークグラフ
        point: 検索点
        max_distance: 最大検索距離
        
    Returns:
        最も近い道路ノードID（見つからない場合はNone）
    """
    min_distance = float('inf')
    nearest_node = None
    
    for node_id, data in G.nodes(data=True):
        if data.get('node_type') == 'road':
            node_pos = data['pos']
            distance = point.distance(Point(node_pos))
            
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_node = node_id
    
    return nearest_node


def get_network_statistics(G: nx.Graph) -> Dict[str, Any]:
    """
    ネットワークの統計情報を取得する
    
    Args:
        G: ネットワークグラフ
        
    Returns:
        統計情報の辞書
    """
    stats = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'density': nx.density(G),
        'is_connected': nx.is_connected(G)
    }
    
    # ノードタイプ別の統計
    node_types = {}
    for node_id, data in G.nodes(data=True):
        node_type = data.get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    stats['node_types'] = node_types
    
    # エッジタイプ別の統計
    edge_types = {}
    for edge_id, data in G.edges(data=True):
        edge_type = data.get('edge_type', 'unknown')
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    stats['edge_types'] = edge_types
    
    # 連結成分の統計
    if not nx.is_connected(G):
        connected_components = list(nx.connected_components(G))
        stats['num_components'] = len(connected_components)
        stats['largest_component_size'] = len(max(connected_components, key=len))
    else:
        stats['num_components'] = 1
        stats['largest_component_size'] = G.number_of_nodes()
    
    return stats


def visualize_network(G: nx.Graph, 
                     building_gdf: Optional[gpd.GeoDataFrame] = None,
                     road_gdf: Optional[gpd.GeoDataFrame] = None) -> Dict[str, Any]:
    """
    ネットワークの可視化用データを準備する
    
    Args:
        G: ネットワークグラフ
        building_gdf: 建物データ（オプション）
        road_gdf: 道路データ（オプション）
        
    Returns:
        可視化用データの辞書
    """
    # ノードの位置情報を取得
    node_positions = {}
    node_types = {}
    
    for node_id, data in G.nodes(data=True):
        node_positions[node_id] = data['pos']
        node_types[node_id] = data.get('node_type', 'unknown')
    
    # エッジの情報を取得
    edges = []
    for edge in G.edges(data=True):
        edges.append({
            'source': edge[0],
            'target': edge[1],
            'weight': edge[2].get('weight', 1.0),
            'edge_type': edge[2].get('edge_type', 'unknown')
        })
    
    return {
        'nodes': {
            'positions': node_positions,
            'types': node_types
        },
        'edges': edges,
        'statistics': get_network_statistics(G)
    }


def extract_building_network(G: nx.Graph) -> nx.Graph:
    """
    建物のみのネットワークを抽出する
    
    Args:
        G: 元のネットワークグラフ
        
    Returns:
        建物のみのネットワークグラフ
    """
    building_nodes = [node for node, data in G.nodes(data=True) 
                     if data.get('node_type') == 'building']
    
    building_subgraph = G.subgraph(building_nodes)
    
    return building_subgraph


def extract_road_network(G: nx.Graph) -> nx.Graph:
    """
    道路のみのネットワークを抽出する
    
    Args:
        G: 元のネットワークグラフ
        
    Returns:
        道路のみのネットワークグラフ
    """
    road_nodes = [node for node, data in G.nodes(data=True) 
                 if data.get('node_type') == 'road']
    
    road_subgraph = G.subgraph(road_nodes)
    
    return road_subgraph
