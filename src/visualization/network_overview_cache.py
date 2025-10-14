#!/usr/bin/env python3
"""ネットワーク可視化キャッシュユーティリティ"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import geopandas as gpd
import numpy as np
import osmnx as ox

from src.data_fetcher import fetch_real_geographic_data
from src.visualization.location_overview import create_location_overview_figure


def _is_in_japan(lat: float, lon: float) -> bool:
    return 24.0 <= lat <= 46.5 and 122.0 <= lon <= 146.5


def fetch_buildings_and_roads(lat: float, lon: float, radius: int) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """GSIまたはOSMから建物・道路データを取得"""

    if _is_in_japan(lat, lon):
        buildings, roads = fetch_real_geographic_data(lat, lon, radius)
        if not buildings.empty or not roads.empty:
            return buildings, roads

    try:
        buildings = ox.features_from_point((lat, lon), tags={"building": True}, dist=radius)
        buildings = buildings[buildings.geometry.notnull()].copy()
        buildings = buildings.explode(ignore_index=True) if not buildings.empty else buildings
        if not buildings.empty:
            buildings = buildings.to_crs("EPSG:4326").reset_index(drop=True)
            buildings = buildings[["geometry"]]
            buildings['building_id'] = buildings.index.astype(str)
            buildings['area'] = buildings.geometry.to_crs(3857).area
        else:
            buildings = gpd.GeoDataFrame(columns=["geometry", "building_id", "area"], crs="EPSG:4326")

        graph = ox.graph_from_point((lat, lon), dist=radius, network_type="drive")
        _, roads = ox.graph_to_gdfs(graph)
        roads = roads[['geometry', 'highway']].copy()
        roads = roads[roads.geometry.notnull()].explode(ignore_index=True)
        roads = roads.to_crs("EPSG:4326").reset_index(drop=True)
        roads.rename(columns={'highway': 'type'}, inplace=True)
        roads['road_id'] = roads.index.astype(str)
        roads['width'] = np.nan
        roads = roads[['geometry', 'road_id', 'type', 'width']]

    except Exception:
        buildings = gpd.GeoDataFrame(columns=["geometry", "building_id", "area"], crs="EPSG:4326")
        roads = gpd.GeoDataFrame(columns=["geometry", "road_id", "type", "width"], crs="EPSG:4326")

    return buildings, roads


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_overview_image(location_row, metric_summary, output_dir: Path) -> Optional[Path]:
    output_dir = ensure_directory(output_dir)
    location_id = int(location_row['location_id'])
    file_path = output_dir / f"overview_{location_id:03d}.png"

    if file_path.exists():
        return file_path

    lat = float(location_row['latitude'])
    lon = float(location_row['longitude'])
    radius = int(location_row.get('radius', 1000))

    buildings, roads = fetch_buildings_and_roads(lat, lon, radius)

    if buildings.empty and roads.empty:
        return None

    fig, _ = create_location_overview_figure(
        location_row,
        metric_summary,
        radius_meters=radius,
        buildings_gdf=buildings,
        roads_gdf=roads,
        layout="hybrid",
    )

    file_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(file_path, dpi=150, bbox_inches='tight')
    import matplotlib.pyplot as plt

    plt.close(fig)
    return file_path
