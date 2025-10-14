#!/usr/bin/env python3
"""GSIベクトルタイルから建物・道路データを取得する高水準インターフェース"""

from __future__ import annotations

from typing import Optional, Tuple

import geopandas as gpd
import numpy as np
from loguru import logger

from src.data.fetcher import VectorTileFetcher
from src.utils.config import get_config


class GSIRealDataFetcher:
    """VectorTileFetcher を利用して実データを取得するラッパークラス"""

    def __init__(self, fetcher: Optional[VectorTileFetcher] = None):
        if fetcher is None:
            data_config = get_config("data")
            fetcher = VectorTileFetcher(data_config)
        self.fetcher = fetcher

    def fetch_buildings_and_roads(
        self, lat: float, lon: float, radius_meters: int = 2000
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """指定地点の建物・道路データを取得"""

        bounds = self._calculate_bounds(lat, lon, radius_meters)
        logger.info(
            "GSIデータ取得: lat={:.5f}, lon={:.5f}, radius={}m".format(
                lat, lon, radius_meters
            )
        )

        buildings_gdf = self.fetcher.fetch_building_data(bounds)
        roads_gdf = self.fetcher.fetch_road_data(bounds)

        if buildings_gdf.empty and roads_gdf.empty:
            logger.warning("指定地点で建物・道路データを取得できませんでした")

        return buildings_gdf, roads_gdf

    @staticmethod
    def _calculate_bounds(
        lat: float, lon: float, radius_meters: int
    ) -> Tuple[float, float, float, float]:
        """緯度経度と半径からバウンディングボックスを計算"""

        lat_offset = radius_meters / 111000.0
        cos_lat = np.cos(np.radians(lat))
        cos_lat = np.clip(cos_lat, 1e-6, None)
        lon_offset = radius_meters / (111000.0 * cos_lat)

        west = max(-180.0, lon - lon_offset)
        east = min(180.0, lon + lon_offset)
        south = max(-90.0, lat - lat_offset)
        north = min(90.0, lat + lat_offset)

        return (west, south, east, north)


_REAL_DATA_FETCHER: Optional[GSIRealDataFetcher] = None


def _get_fetcher() -> GSIRealDataFetcher:
    global _REAL_DATA_FETCHER
    if _REAL_DATA_FETCHER is None:
        _REAL_DATA_FETCHER = GSIRealDataFetcher()
    return _REAL_DATA_FETCHER


def fetch_real_geographic_data(
    lat: float, lon: float, radius_meters: int = 2000
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """実際の地理データを取得するエントリポイント"""

    fetcher = _get_fetcher()
    return fetcher.fetch_buildings_and_roads(lat, lon, radius_meters)

