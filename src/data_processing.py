"""
データ処理モジュール

指定された緯度経度周辺の地理空間データを取得・処理する機能を提供します。
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, LineString
from typing import Tuple, Dict, Any, Optional
import requests
import json
from loguru import logger
from .utils.config import get_config


def load_spatial_data(lat: float, lon: float) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    指定された緯度経度を中心として地理空間データを取得する
    
    Args:
        lat: 緯度
        lon: 経度
        
    Returns:
        (building_gdf, road_gdf): 建物データと道路データのGeoDataFrame
    """
    logger.info(f"地理空間データ取得開始: ({lat}, {lon})")
    
    # 設定を読み込み
    config = get_config()
    radius_meters = config.get("analysis_radius_meters", 2000)
    
    # 分析範囲を計算
    bounds = _calculate_bounds(lat, lon, radius_meters)
    
    # 建物データを取得
    building_gdf = _fetch_building_data(bounds)
    
    # 道路データを取得
    road_gdf = _fetch_road_data(bounds)
    
    logger.info(f"データ取得完了: 建物{len(building_gdf)}件, 道路{len(road_gdf)}件")
    
    return building_gdf, road_gdf


def _calculate_bounds(lat: float, lon: float, radius_meters: float) -> Dict[str, float]:
    """
    緯度経度と半径から分析範囲を計算する
    
    Args:
        lat: 緯度
        lon: 経度
        radius_meters: 半径（メートル）
        
    Returns:
        分析範囲の辞書 (west, south, east, north)
    """
    # 大まかな緯度経度からメートルへの変換
    # 1度の緯度 ≈ 111,000メートル
    # 1度の経度 ≈ 111,000 * cos(緯度) メートル
    
    lat_offset = radius_meters / 111000.0
    lon_offset = radius_meters / (111000.0 * np.cos(np.radians(lat)))
    
    bounds = {
        'west': lon - lon_offset,
        'south': lat - lat_offset,
        'east': lon + lon_offset,
        'north': lat + lat_offset
    }
    
    return bounds


def _fetch_building_data(bounds: Dict[str, float]) -> gpd.GeoDataFrame:
    """
    建物データを取得する（サンプル実装）
    
    Args:
        bounds: 分析範囲
        
    Returns:
        建物データのGeoDataFrame
    """
    logger.info("建物データ取得中...")
    
    # 実際の実装では国土地理院ベクトルタイルから取得
    # ここではサンプルデータを生成
    buildings_data = []
    
    # 分析範囲内にランダムに建物を配置
    np.random.seed(42)  # 再現性のため
    num_buildings = np.random.randint(50, 200)
    
    for i in range(num_buildings):
        # ランダムな位置
        lon = np.random.uniform(bounds['west'], bounds['east'])
        lat = np.random.uniform(bounds['south'], bounds['north'])
        
        # 建物サイズ（10-100m²）
        width = np.random.uniform(0.0001, 0.001)  # 約10-100m
        height = np.random.uniform(0.0001, 0.001)
        
        # 建物ポリゴン
        geom = Polygon([
            (lon, lat),
            (lon + width, lat),
            (lon + width, lat + height),
            (lon, lat + height)
        ])
        
        building = {
            'geometry': geom,
            'building_id': i,
            'type': np.random.choice(['residential', 'commercial', 'industrial', 'public']),
            'area_m2': width * height * 111000 * 111000  # 大まかな面積
        }
        buildings_data.append(building)
    
    return gpd.GeoDataFrame(buildings_data, crs="EPSG:4326")


def _fetch_road_data(bounds: Dict[str, float]) -> gpd.GeoDataFrame:
    """
    道路データを取得する（サンプル実装）
    
    Args:
        bounds: 分析範囲
        
    Returns:
        道路データのGeoDataFrame
    """
    logger.info("道路データ取得中...")
    
    # 実際の実装では国土地理院ベクトルタイルから取得
    # ここではサンプルデータを生成
    roads_data = []
    
    # 分析範囲内にランダムに道路を配置
    np.random.seed(42)  # 再現性のため
    num_roads = np.random.randint(20, 50)
    
    for i in range(num_roads):
        # ランダムな道路
        start_lon = np.random.uniform(bounds['west'], bounds['east'])
        start_lat = np.random.uniform(bounds['south'], bounds['north'])
        end_lon = np.random.uniform(bounds['west'], bounds['east'])
        end_lat = np.random.uniform(bounds['south'], bounds['north'])
        
        geom = LineString([(start_lon, start_lat), (end_lon, end_lat)])
        
        road = {
            'geometry': geom,
            'road_id': i,
            'type': np.random.choice(['highway', 'primary', 'secondary', 'residential']),
            'width': np.random.uniform(3.0, 20.0)
        }
        roads_data.append(road)
    
    return gpd.GeoDataFrame(roads_data, crs="EPSG:4326")


def preprocess_building_data(building_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    建物データを前処理する
    
    Args:
        building_gdf: 建物データ
        
    Returns:
        前処理済み建物データ
    """
    logger.info("建物データ前処理開始")
    
    # 座標系を投影座標系に変換（メートル単位）
    building_gdf = building_gdf.to_crs("EPSG:3857")
    
    # 面積を再計算
    building_gdf['area_m2'] = building_gdf.geometry.area
    
    # 最小面積フィルタリング
    min_area = 10.0  # 10m²
    building_gdf = building_gdf[building_gdf['area_m2'] >= min_area]
    
    # 重心を計算
    building_gdf['centroid'] = building_gdf.geometry.centroid
    
    logger.info(f"建物データ前処理完了: {len(building_gdf)}件")
    return building_gdf


def preprocess_road_data(road_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    道路データを前処理する
    
    Args:
        road_gdf: 道路データ
        
    Returns:
        前処理済み道路データ
    """
    logger.info("道路データ前処理開始")
    
    # 座標系を投影座標系に変換
    road_gdf = road_gdf.to_crs("EPSG:3857")
    
    # 長さを計算
    road_gdf['length_m'] = road_gdf.geometry.length
    
    # 最小長さフィルタリング
    min_length = 10.0  # 10m
    road_gdf = road_gdf[road_gdf['length_m'] >= min_length]
    
    logger.info(f"道路データ前処理完了: {len(road_gdf)}件")
    return road_gdf


def create_analysis_area(lat: float, lon: float, radius_meters: float) -> gpd.GeoDataFrame:
    """
    分析エリアのポリゴンを作成する
    
    Args:
        lat: 緯度
        lon: 経度
        radius_meters: 半径（メートル）
        
    Returns:
        分析エリアのGeoDataFrame
    """
    bounds = _calculate_bounds(lat, lon, radius_meters)
    
    # 分析エリアのポリゴンを作成
    area_polygon = Polygon([
        (bounds['west'], bounds['south']),
        (bounds['east'], bounds['south']),
        (bounds['east'], bounds['north']),
        (bounds['west'], bounds['north'])
    ])
    
    area_gdf = gpd.GeoDataFrame([{
        'geometry': area_polygon,
        'center_lat': lat,
        'center_lon': lon,
        'radius_m': radius_meters
    }], crs="EPSG:4326")
    
    return area_gdf


def filter_data_by_bounds(gdf: gpd.GeoDataFrame, bounds: Dict[str, float]) -> gpd.GeoDataFrame:
    """
    指定された範囲内のデータをフィルタリングする
    
    Args:
        gdf: フィルタリング対象のGeoDataFrame
        bounds: フィルタリング範囲
        
    Returns:
        フィルタリング済みGeoDataFrame
    """
    # 範囲ポリゴンを作成
    filter_polygon = Polygon([
        (bounds['west'], bounds['south']),
        (bounds['east'], bounds['south']),
        (bounds['east'], bounds['north']),
        (bounds['west'], bounds['north'])
    ])
    
    # 空間フィルタリング
    filtered_gdf = gdf[gdf.geometry.intersects(filter_polygon)]
    
    return filtered_gdf
