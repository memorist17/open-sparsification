#!/usr/bin/env python3
"""
実際の地理データから指標を計算するスクリプト（修正版）
GSI最適化ベクトルタイルの正しい仕様に基づく
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import asyncio
from tqdm.asyncio import tqdm_asyncio
import osmnx as ox
import geopandas as gpd


# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.utils.config import load_config, get_config
from src.utils.logger import get_logger
from src.data_fetcher_fixed import fetch_real_geographic_data
from src.real_metrics_calculator import RealMetricsCalculator
from src.network_builder import create_urban_network
logger = get_logger(__name__)
config = get_config()

CURATED_LOCATIONS = [
    {"name": "Tokyo Station", "lat": 35.681236, "lon": 139.767125, "radius": 800},
    {"name": "Shinjuku", "lat": 35.690921, "lon": 139.700258, "radius": 800},
    {"name": "Shibuya", "lat": 35.659516, "lon": 139.700450, "radius": 800},
    {"name": "Ueno", "lat": 35.712056, "lon": 139.776431, "radius": 800},
    {"name": "Osaka Umeda", "lat": 34.702485, "lon": 135.495951, "radius": 800},
    {"name": "Nagoya Sakae", "lat": 35.169918, "lon": 136.908155, "radius": 800},
    {"name": "Hakata", "lat": 33.590204, "lon": 130.420997, "radius": 800},
    {"name": "Sapporo", "lat": 43.062096, "lon": 141.354376, "radius": 800},
    {"name": "Sendai", "lat": 38.260686, "lon": 140.882549, "radius": 800},
    {"name": "Hiroshima", "lat": 34.391606, "lon": 132.451597, "radius": 800},
]

USER_SPECIFIED_LOCATIONS = [
    {"name": "Yokohama", "lat": 35.4438, "lon": 139.6380, "radius": 1000},
    {"name": "Yamanashi City", "lat": 35.6635, "lon": 138.5684, "radius": 1000},
    {"name": "Greenwich CT", "lat": 41.049179869296566, "lon": -73.63494225610658, "radius": 1000},
    {"name": "Bell Labs Holmdel", "lat": 40.391006, "lon": -74.184581, "radius": 1000},
    {"name": "Kamiyama A", "lat": 33.959822829540045, "lon": 134.30761543643712, "radius": 1000},
    {"name": "Kamiyama Week", "lat": 33.9687294040191, "lon": 134.3383325623779, "radius": 1000},
    {"name": "Kamiyama Miyamoto Residence", "lat": 33.963637118765526, "lon": 134.35049344583854, "radius": 1000},
    {"name": "Kamiyama Marugoto Technical College", "lat": 33.972864196733795, "lon": 134.36278905827217, "radius": 1000},
    {"name": "Observation Deck", "lat": 33.953743569235925, "lon": 134.4063620051131, "radius": 1000},
    {"name": "Kawaba Village", "lat": 36.699016518887866, "lon": 139.10910525819972, "radius": 1000},
    {"name": "Tonami Plain", "lat": 36.602711035167594, "lon": 136.9867048847905, "radius": 1000},
    {"name": "Taketomi Island", "lat": 24.330804124388035, "lon": 124.08550639616077, "radius": 1000},
]

def build_target_locations():
    """構造物が多い都市部とユーザー指定地点を合わせた地点リストを作成"""

    locations = []
    for idx, info in enumerate(CURATED_LOCATIONS + USER_SPECIFIED_LOCATIONS):
        locations.append({
            "location_id": idx,
            "latitude": info["lat"],
            "longitude": info["lon"],
            "name": info["name"],
            "radius": info.get("radius", config['analysis_radius_meters'])
        })

    return pd.DataFrame(locations)


def fetch_buildings_and_roads(lat: float, lon: float, radius: int) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """GSIまたはOSMから建物・道路データを取得"""

    def is_japan(lat_val: float, lon_val: float) -> bool:
        return 24.0 <= lat_val <= 46.5 and 122.0 <= lon_val <= 146.5

    if is_japan(lat, lon):
        buildings_gdf, roads_gdf = fetch_real_geographic_data(lat, lon, radius)
        if not buildings_gdf.empty or not roads_gdf.empty:
            return buildings_gdf, roads_gdf

    # Fallback to OpenStreetMap
    try:
        tags = {"building": True}
        buildings = ox.features_from_point((lat, lon), tags=tags, dist=radius)
        buildings = buildings[buildings.geometry.notnull()].copy()
        if not buildings.empty:
            buildings = buildings.explode(ignore_index=True)
            buildings = buildings.to_crs("EPSG:4326")
            buildings = buildings.reset_index(drop=True)
            buildings = buildings[["geometry"]]
            buildings["building_id"] = buildings.index.astype(str)
            buildings["area"] = buildings.geometry.to_crs(3857).area
        else:
            buildings = gpd.GeoDataFrame(columns=["geometry", "building_id", "area"], crs="EPSG:4326")

        road_graph = ox.graph_from_point((lat, lon), dist=radius, network_type="drive")
    except Exception:
        buildings = gpd.GeoDataFrame(columns=["geometry", "building_id", "area"], crs="EPSG:4326")
        roads = gpd.GeoDataFrame(columns=["geometry", "road_id", "type", "width"], crs="EPSG:4326")
    else:
        try:
            _, roads = ox.graph_to_gdfs(road_graph)
        except Exception:
            roads = gpd.GeoDataFrame(columns=["geometry", "road_id", "type", "width"], crs="EPSG:4326")
        else:
            roads = roads[['geometry', 'highway', 'length']].copy()
            roads = roads[roads.geometry.notnull()].explode(ignore_index=True)
            roads = roads.to_crs("EPSG:4326").reset_index(drop=True)
            roads.rename(columns={'highway': 'type'}, inplace=True)
            roads['road_id'] = roads.index.astype(str)
            roads['width'] = roads.get('width', np.nan)
            if 'type' not in roads.columns:
                roads['type'] = 'road'
            roads = roads[['geometry', 'road_id', 'type', 'width']]

    return buildings, roads

def generate_real_sample_data():
    """
    構造物が多い都市部10地点とユーザー指定地点を対象に指標を計算し、CSVとして保存する（修正版）
    """
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "real_analysis_results.csv"

    locations_df = build_target_locations()
    num_locations = len(locations_df)

    results = []
    metrics_calculator = RealMetricsCalculator()

    logger.info(f"実際の地理データから指標計算開始: {num_locations}地点")

    for idx, row in locations_df.iterrows():
        lat, lon = row['latitude'], row['longitude']
        location_id = row['location_id']
        radius = row.get('radius', config['analysis_radius_meters'])
        name = row.get('name', f"Location {location_id}")
        logger.info(f"指標計算中: {idx+1}/{num_locations} - {name} (緯度: {lat:.3f}, 経度: {lon:.3f}, 半径: {radius}m)")

        try:
            # 建物・道路データを取得（修正版）
            buildings_gdf, roads_gdf = fetch_buildings_and_roads(lat, lon, radius)

            if buildings_gdf.empty and roads_gdf.empty:
                logger.warning(f"地点 {location_id} ({lat:.3f}, {lon:.3f}) で建物・道路データが見つかりませんでした。スキップします。")
                continue

            # ジオメトリを分解して単純化
            if not buildings_gdf.empty:
                buildings_gdf = buildings_gdf.explode(ignore_index=True)
                buildings_gdf = buildings_gdf[buildings_gdf.geometry.notnull()].reset_index(drop=True)
            if not roads_gdf.empty:
                roads_gdf = roads_gdf.explode(ignore_index=True)
                roads_gdf = roads_gdf[roads_gdf.geometry.notnull()].reset_index(drop=True)

            buildings_metric_gdf = buildings_gdf.to_crs(3857) if not buildings_gdf.empty else buildings_gdf
            roads_metric_gdf = roads_gdf.to_crs(3857) if not roads_gdf.empty else roads_gdf

            network_graph = create_urban_network(buildings_gdf, roads_gdf)

            # 指標を計算
            metrics = {
                'sparsity': metrics_calculator.calculate_sparsity(buildings_metric_gdf),
                'resilience': metrics_calculator.calculate_resilience(network_graph),
                'multi_nodality': metrics_calculator.calculate_multi_nodality(buildings_metric_gdf),
                'permeability': metrics_calculator.calculate_permeability(buildings_metric_gdf, roads_metric_gdf),
                'emergence': metrics_calculator.calculate_emergence(buildings_metric_gdf, network_graph),
                'overlap': metrics_calculator.calculate_overlap(buildings_metric_gdf, roads_metric_gdf),
            }
            
            result = {
                'location_id': location_id,
                'latitude': lat,
                'longitude': lon,
                'name': name,
                'radius': radius,
                **metrics
            }
            results.append(result)
            
        except Exception as e:
            logger.error(f"地点 {location_id} ({lat:.3f}, {lon:.3f}) の指標計算エラー: {e}")
            continue

    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_path, index=False)
        logger.info(f"実際の分析結果を {output_path} に保存しました。")
        logger.info(f"生成されたデータフレームの統計情報:\n{df_results.describe()}")
        logger.info(f"相関行列:\n{df_results.corr(numeric_only=True)}")
    else:
        logger.warning("計算された指標データがありませんでした。")

if __name__ == "__main__":
    generate_real_sample_data()
