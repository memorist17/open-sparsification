"""
Overture Mapsデータローダー

Overture MapsのParquetファイルから建物重心と道路中心線を高速に読み出す。
キャッシュ機能により、一度読み込んだデータを再利用可能。
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from shapely.geometry import Point, LineString
import pyarrow.parquet as pq
import pyarrow as pa
from tqdm import tqdm
import warnings


@dataclass
class PlaceExtent:
    """場所の範囲を定義するデータクラス"""
    minx: float
    miny: float
    maxx: float
    maxy: float
    crs: str = "EPSG:4326"
    
    def to_3857(self) -> 'PlaceExtent':
        """Web Mercator (EPSG:3857)に変換"""
        import pyproj
        transformer = pyproj.Transformer.from_crs(
            self.crs, "EPSG:3857", always_xy=True
        )
        x1, y1 = transformer.transform(self.minx, self.miny)
        x2, y2 = transformer.transform(self.maxx, self.maxy)
        return PlaceExtent(
            minx=min(x1, x2),
            miny=min(y1, y2),
            maxx=max(x1, x2),
            maxy=max(y1, y2),
            crs="EPSG:3857"
        )


def ensure_columns(gdf: gpd.GeoDataFrame, required_cols: List[str]) -> gpd.GeoDataFrame:
    """
    必要なカラムが存在することを確認し、存在しない場合は追加。
    
    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        入力GeoDataFrame
    required_cols : list of str
        必要なカラム名のリスト
    
    Returns
    -------
    gdf : gpd.GeoDataFrame
        カラムが確保されたGeoDataFrame
    """
    for col in required_cols:
        if col not in gdf.columns:
            gdf[col] = None
    return gdf


def load_building_centroids(
    parquet_path: str,
    extent: Optional[PlaceExtent] = None,
    cache_dir: Optional[str] = None,
    max_points: Optional[int] = None,
    verbose: bool = True
) -> gpd.GeoDataFrame:
    """
    Overture Mapsの建物Parquetファイルから重心点を読み込む。
    
    Parameters
    ----------
    parquet_path : str
        Overture建物Parquetファイルのパス
    extent : PlaceExtent, optional
        読み込む範囲（WGS84座標）
    cache_dir : str, optional
        キャッシュディレクトリ（存在する場合は再利用）
    max_points : int, optional
        最大読み込み点数（サンプリング用）
    verbose : bool
        進捗表示
    
    Returns
    -------
    centroids : gpd.GeoDataFrame
        建物重心点（EPSG:3857）
    """
    parquet_file = Path(parquet_path)
    if not parquet_file.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    # キャッシュチェック
    if cache_dir:
        cache_path = Path(cache_dir) / f"buildings_{parquet_file.stem}.gpkg"
        if cache_path.exists():
            if verbose:
                print(f"Loading from cache: {cache_path}")
            gdf = gpd.read_file(cache_path)
            if extent:
                extent_3857 = extent.to_3857()
                gdf = gdf.cx[
                    extent_3857.minx:extent_3857.maxx,
                    extent_3857.miny:extent_3857.maxy
                ]
            if max_points and len(gdf) > max_points:
                gdf = gdf.sample(n=max_points, random_state=42)
            return gdf
    
    # Parquetファイルを読み込み
    if verbose:
        print(f"Reading Parquet file: {parquet_path}")
    
    # PyArrowで読み込み（メモリ効率的）
    table = pq.read_table(parquet_path)
    df = table.to_pandas()
    
    # ジオメトリカラムを確認
    geom_cols = [col for col in df.columns if col in ['geometry', 'geom']]
    if not geom_cols:
        # GeoJSON文字列からジオメトリを復元
        if 'geometry' in df.columns and df['geometry'].dtype == 'object':
            df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'])
        else:
            raise ValueError("No geometry column found in Parquet file")
    
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    
    # CRS設定
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    
    # 範囲フィルタ
    if extent:
        gdf = gdf.cx[extent.minx:extent.maxx, extent.miny:extent.maxy]
    
    # ポリゴンから重心を計算
    if gdf.geom_type.iloc[0] != 'Point':
        if verbose:
            print("Converting polygons to centroids...")
        gdf['geometry'] = gdf.geometry.centroid
    
    # EPSG:3857に変換
    if gdf.crs.to_string() != "EPSG:3857":
        gdf = gdf.to_crs("EPSG:3857")
    
    # サンプリング
    if max_points and len(gdf) > max_points:
        if verbose:
            print(f"Sampling {max_points} points from {len(gdf)}...")
        gdf = gdf.sample(n=max_points, random_state=42)
    
    # 必要なカラムを確保
    gdf = ensure_columns(gdf, ['id', 'name', 'class'])
    
    # キャッシュ保存
    if cache_dir:
        cache_path = Path(cache_dir) / f"buildings_{parquet_file.stem}.gpkg"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(cache_path, driver='GPKG')
        if verbose:
            print(f"Cached to: {cache_path}")
    
    return gdf


def load_resolved_places(
    parquet_path: str,
    extent: Optional[PlaceExtent] = None,
    cache_dir: Optional[str] = None,
    verbose: bool = True
) -> gpd.GeoDataFrame:
    """
    Overture Mapsのplaces Parquetファイルから場所情報を読み込む。
    
    Parameters
    ----------
    parquet_path : str
        Overture places Parquetファイルのパス
    extent : PlaceExtent, optional
        読み込む範囲
    cache_dir : str, optional
        キャッシュディレクトリ
    verbose : bool
        進捗表示
    
    Returns
    -------
    places : gpd.GeoDataFrame
        場所情報（EPSG:3857）
    """
    parquet_file = Path(parquet_path)
    if not parquet_file.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    # キャッシュチェック
    if cache_dir:
        cache_path = Path(cache_dir) / f"places_{parquet_file.stem}.gpkg"
        if cache_path.exists():
            if verbose:
                print(f"Loading from cache: {cache_path}")
            gdf = gpd.read_file(cache_path)
            if extent:
                extent_3857 = extent.to_3857()
                gdf = gdf.cx[
                    extent_3857.minx:extent_3857.maxx,
                    extent_3857.miny:extent_3857.maxy
                ]
            return gdf
    
    # Parquetファイルを読み込み
    if verbose:
        print(f"Reading Parquet file: {parquet_path}")
    
    table = pq.read_table(parquet_path)
    df = table.to_pandas()
    
    # ジオメトリ処理
    if 'geometry' in df.columns and df['geometry'].dtype == 'object':
        df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'])
    
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    
    # 範囲フィルタ
    if extent:
        gdf = gdf.cx[extent.minx:extent.maxx, extent.miny:extent.maxy]
    
    # EPSG:3857に変換
    if gdf.crs.to_string() != "EPSG:3857":
        gdf = gdf.to_crs("EPSG:3857")
    
    # 必要なカラムを確保
    gdf = ensure_columns(gdf, ['id', 'name', 'class'])
    
    # キャッシュ保存
    if cache_dir:
        cache_path = Path(cache_dir) / f"places_{parquet_file.stem}.gpkg"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(cache_path, driver='GPKG')
        if verbose:
            print(f"Cached to: {cache_path}")
    
    return gdf


def load_road_segments(
    parquet_path: str,
    extent: Optional[PlaceExtent] = None,
    cache_dir: Optional[str] = None,
    max_segments: Optional[int] = None,
    verbose: bool = True
) -> gpd.GeoDataFrame:
    """
    Overture Mapsの道路Parquetファイルから道路セグメントを読み込む。
    
    Parameters
    ----------
    parquet_path : str
        Overture道路Parquetファイルのパス
    extent : PlaceExtent, optional
        読み込む範囲
    cache_dir : str, optional
        キャッシュディレクトリ
    max_segments : int, optional
        最大読み込みセグメント数
    verbose : bool
        進捗表示
    
    Returns
    -------
    roads : gpd.GeoDataFrame
        道路セグメント（EPSG:3857）
    """
    parquet_file = Path(parquet_path)
    if not parquet_file.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    # キャッシュチェック
    if cache_dir:
        cache_path = Path(cache_dir) / f"roads_{parquet_file.stem}.gpkg"
        if cache_path.exists():
            if verbose:
                print(f"Loading from cache: {cache_path}")
            gdf = gpd.read_file(cache_path)
            if extent:
                extent_3857 = extent.to_3857()
                gdf = gdf.cx[
                    extent_3857.minx:extent_3857.maxx,
                    extent_3857.miny:extent_3857.maxy
                ]
            if max_segments and len(gdf) > max_segments:
                gdf = gdf.sample(n=max_segments, random_state=42)
            return gdf
    
    # Parquetファイルを読み込み
    if verbose:
        print(f"Reading Parquet file: {parquet_path}")
    
    table = pq.read_table(parquet_path)
    df = table.to_pandas()
    
    # ジオメトリ処理
    if 'geometry' in df.columns and df['geometry'].dtype == 'object':
        df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'])
    
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    
    # 範囲フィルタ
    if extent:
        gdf = gdf.cx[extent.minx:extent.maxx, extent.miny:extent.maxy]
    
    # LineStringに変換（必要に応じて）
    if gdf.geom_type.iloc[0] not in ['LineString', 'MultiLineString']:
        warnings.warn("Road geometries are not LineString, attempting conversion...")
        # ポリゴンの境界線を抽出
        gdf['geometry'] = gdf.geometry.boundary
    
    # EPSG:3857に変換
    if gdf.crs.to_string() != "EPSG:3857":
        gdf = gdf.to_crs("EPSG:3857")
    
    # サンプリング
    if max_segments and len(gdf) > max_segments:
        if verbose:
            print(f"Sampling {max_segments} segments from {len(gdf)}...")
        gdf = gdf.sample(n=max_segments, random_state=42)
    
    # 必要なカラムを確保
    gdf = ensure_columns(gdf, ['id', 'name', 'class', 'level'])
    
    # キャッシュ保存
    if cache_dir:
        cache_path = Path(cache_dir) / f"roads_{parquet_file.stem}.gpkg"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(cache_path, driver='GPKG')
        if verbose:
            print(f"Cached to: {cache_path}")
    
    return gdf


# Example usage
if __name__ == "__main__":
    # テスト用の例
    extent = PlaceExtent(
        minx=139.5, miny=35.5, maxx=140.0, maxy=36.0,
        crs="EPSG:4326"
    )
    
    print("Overture Loader Test")
    print(f"Extent: {extent}")
    print("Note: Requires actual Overture Parquet files to run")
