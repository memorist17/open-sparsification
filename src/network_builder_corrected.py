#!/usr/bin/env python3
"""
修正された都市ネットワーク構築モジュール
道路データと建物データを正しく統合してネットワークを構築
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
from scipy.spatial.distance import cdist
import logging
from typing import Tuple, Dict, Any, List
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logger = logging.getLogger(__name__)

def create_urban_network(buildings_gdf: gpd.GeoDataFrame, roads_gdf: gpd.GeoDataFrame) -> nx.Graph:
    """
    建物と道路データから都市ネットワークを構築（修正版）
    
    Args:
        buildings_gdf: 建物のGeoDataFrame
        roads_gdf: 道路のGeoDataFrame
        
    Returns:
        NetworkXグラフ
    """
    logger.info("都市ネットワーク構築開始")
    
    try:
        # CRSを統一（EPSG:4326）
        if buildings_gdf.crs is None:
            buildings_gdf = buildings_gdf.set_crs('EPSG:4326')
        if roads_gdf.crs is None:
            roads_gdf = roads_gdf.set_crs('EPSG:4326')
        
        # 同じCRSに統一
        if buildings_gdf.crs != roads_gdf.crs:
            roads_gdf = roads_gdf.to_crs(buildings_gdf.crs)
        
        # ネットワークグラフを初期化
        G = nx.Graph()
        
        # 建物をノードとして追加
        building_nodes = _add_building_nodes(G, buildings_gdf)
        
        # 道路をエッジとして追加
        road_edges = _add_road_edges(G, roads_gdf)
        
        # 建物と道路の接続を追加
        _connect_buildings_to_roads(G, buildings_gdf, roads_gdf)
        
        logger.info(f"都市ネットワーク構築完了: {G.number_of_nodes()}ノード, {G.number_of_edges()}エッジ")
        
        return G
        
    except Exception as e:
        logger.error(f"ネットワーク構築エラー: {e}")
        # エラー時は空のグラフを返す
        return nx.Graph()

def _add_building_nodes(G: nx.Graph, buildings_gdf: gpd.GeoDataFrame) -> List[int]:
    """建物をノードとして追加"""
    building_nodes = []
    
    for idx, building in buildings_gdf.iterrows():
        # 建物の重心を計算
        centroid = building.geometry.centroid
        
        # ノードを追加
        G.add_node(
            f"building_{idx}",
            pos=(centroid.x, centroid.y),
            type='building',
            area=building.get('area', 0),
            building_id=building.get('building_id', f"building_{idx}")
        )
        building_nodes.append(f"building_{idx}")
    
    logger.info(f"建物ノード追加完了: {len(building_nodes)}個")
    return building_nodes

def _add_road_edges(G: nx.Graph, roads_gdf: gpd.GeoDataFrame) -> List[Tuple[str, str]]:
    """道路をエッジとして追加"""
    road_edges = []
    
    for idx, road in roads_gdf.iterrows():
        # 道路の座標を取得
        coords = list(road.geometry.coords)
        
        if len(coords) < 2:
            continue
        
        # 道路の各セグメントをエッジとして追加
        for i in range(len(coords) - 1):
            start_coord = coords[i]
            end_coord = coords[i + 1]
            
            # ノードIDを生成
            start_node = f"road_{idx}_{i}"
            end_node = f"road_{idx}_{i+1}"
            
            # ノードを追加
            G.add_node(
                start_node,
                pos=start_coord,
                type='road',
                road_id=road.get('road_id', f"road_{idx}")
            )
            G.add_node(
                end_node,
                pos=end_coord,
                type='road',
                road_id=road.get('road_id', f"road_{idx}")
            )
            
            # エッジを追加
            distance = Point(start_coord).distance(Point(end_coord))
            G.add_edge(
                start_node,
                end_node,
                weight=distance,
                type='road',
                road_id=road.get('road_id', f"road_{idx}")
            )
            
            road_edges.append((start_node, end_node))
    
    logger.info(f"道路エッジ追加完了: {len(road_edges)}個")
    return road_edges

def _connect_buildings_to_roads(G: nx.Graph, buildings_gdf: gpd.GeoDataFrame, roads_gdf: gpd.GeoDataFrame):
    """建物と道路の接続を追加"""
    connection_threshold = 0.001  # 度単位（約100メートル）
    connections = 0
    
    for building_idx, building in buildings_gdf.iterrows():
        building_node = f"building_{building_idx}"
        building_centroid = building.geometry.centroid
        
        # 最も近い道路を見つける
        min_distance = float('inf')
        closest_road_node = None
        
        for road_idx, road in roads_gdf.iterrows():
            # 道路の各セグメントをチェック
            coords = list(road.geometry.coords)
            for i in range(len(coords) - 1):
                road_node = f"road_{road_idx}_{i}"
                if road_node in G:
                    road_pos = G.nodes[road_node]['pos']
                    distance = building_centroid.distance(Point(road_pos))
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_road_node = road_node
        
        # 閾値内の道路に接続
        if closest_road_node and min_distance <= connection_threshold:
            G.add_edge(
                building_node,
                closest_road_node,
                weight=min_distance,
                type='building_road_connection'
            )
            connections += 1
    
    logger.info(f"建物-道路接続完了: {connections}個")

def create_network_from_coordinates(buildings_gdf: gpd.GeoDataFrame, roads_gdf: gpd.GeoDataFrame) -> nx.Graph:
    """
    座標データから直接ネットワークを構築（修正版）
    
    Args:
        buildings_gdf: 建物のGeoDataFrame
        roads_gdf: 道路のGeoDataFrame
        
    Returns:
        NetworkXグラフ
    """
    logger.info("座標データからネットワーク構築開始")
    
    try:
        # ネットワークグラフを初期化
        G = nx.Graph()
        
        # 建物の座標を取得
        building_coords = []
        for idx, building in buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            building_coords.append((centroid.x, centroid.y))
            
            # ノードを追加
            G.add_node(
                f"building_{idx}",
                pos=(centroid.x, centroid.y),
                type='building',
                area=building.get('area', 0)
            )
        
        # 道路の座標を取得
        road_coords = []
        for idx, road in roads_gdf.iterrows():
            coords = list(road.geometry.coords)
            for i, coord in enumerate(coords):
                road_coords.append(coord)
                
                # ノードを追加
                G.add_node(
                    f"road_{idx}_{i}",
                    pos=coord,
                    type='road'
                )
        
        # 建物間の接続（近接建物）
        _connect_nearby_buildings(G, building_coords)
        
        # 道路間の接続
        _connect_road_segments(G, roads_gdf)
        
        # 建物と道路の接続
        _connect_buildings_to_roads_simple(G, building_coords, road_coords)
        
        logger.info(f"座標データからネットワーク構築完了: {G.number_of_nodes()}ノード, {G.number_of_edges()}エッジ")
        
        return G
        
    except Exception as e:
        logger.error(f"座標データからネットワーク構築エラー: {e}")
        return nx.Graph()

def _connect_nearby_buildings(G: nx.Graph, building_coords: List[Tuple[float, float]]):
    """近接建物を接続"""
    threshold = 0.002  # 度単位（約200メートル）
    
    for i, coord1 in enumerate(building_coords):
        for j, coord2 in enumerate(building_coords[i+1:], i+1):
            distance = Point(coord1).distance(Point(coord2))
            if distance <= threshold:
                G.add_edge(
                    f"building_{i}",
                    f"building_{j}",
                    weight=distance,
                    type='building_connection'
                )

def _connect_road_segments(G: nx.Graph, roads_gdf: gpd.GeoDataFrame):
    """道路セグメントを接続"""
    for idx, road in roads_gdf.iterrows():
        coords = list(road.geometry.coords)
        for i in range(len(coords) - 1):
            G.add_edge(
                f"road_{idx}_{i}",
                f"road_{idx}_{i+1}",
                weight=Point(coords[i]).distance(Point(coords[i+1])),
                type='road_segment'
            )

def _connect_buildings_to_roads_simple(G: nx.Graph, building_coords: List[Tuple[float, float]], road_coords: List[Tuple[float, float]]):
    """建物と道路を簡単に接続"""
    threshold = 0.001  # 度単位（約100メートル）
    
    for i, building_coord in enumerate(building_coords):
        for j, road_coord in enumerate(road_coords):
            distance = Point(building_coord).distance(Point(road_coord))
            if distance <= threshold:
                G.add_edge(
                    f"building_{i}",
                    f"road_{j//10}_{j%10}",  # 道路ノードIDを生成
                    weight=distance,
                    type='building_road_connection'
                )

