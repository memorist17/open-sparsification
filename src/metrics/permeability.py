"""
流動性指標計算モジュール

パーコレーション分析を用いて都市の流動性を定量化します。
計算式: 最大オープンスペース面積 / 全オープンスペースの総面積
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import ndimage
from typing import List, Tuple, Dict, Any, Optional
from loguru import logger
from ..utils.config import get_config


class PermeabilityCalculator:
    """流動性指標計算クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書（デフォルト: parameters.ymlから読み込み）
        """
        if config is None:
            config = get_config("permeability")
        
        self.config = config
        self.grid_size = config.get("grid_size", 50.0)
        self.open_space_config = config.get("open_space", {})
        self.percolation_threshold = config.get("percolation_threshold", 0.5927)
    
    def calculate(self, buildings_gdf: gpd.GeoDataFrame, 
                 roads_gdf: Optional[gpd.GeoDataFrame] = None) -> Dict[str, float]:
        """
        流動性指標を計算
        
        Args:
            buildings_gdf: 建物データ
            roads_gdf: 道路データ（オプション）
            
        Returns:
            流動性指標の辞書
        """
        logger.info("流動性指標計算開始")
        
        # グリッドを作成
        grid_gdf = self._create_analysis_grid(buildings_gdf)
        
        # オープンスペースを判定
        open_space_grid = self._identify_open_spaces(grid_gdf, buildings_gdf, roads_gdf)
        
        # パーコレーション解析
        percolation_results = self._analyze_percolation(open_space_grid)
        
        # 流動性指標
        if percolation_results['total_open_area'] > 0:
            permeability = percolation_results['largest_cluster_area'] / percolation_results['total_open_area']
        else:
            permeability = 0.0
        
        result = {
            'permeability': permeability,
            'largest_cluster_area': percolation_results['largest_cluster_area'],
            'total_open_area': percolation_results['total_open_area'],
            'num_clusters': percolation_results['num_clusters'],
            'percolation_threshold': self.percolation_threshold
        }
        
        logger.info(f"流動性指標計算完了: {permeability:.4f}")
        return result
    
    def _create_analysis_grid(self, buildings_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        分析用グリッドを作成
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            グリッドのGeoDataFrame
        """
        # 空のGeoDataFrameの場合はデフォルト範囲を使用
        if buildings_gdf.empty:
            # デフォルトの分析範囲（2000m x 2000m）
            x_min, y_min = -1000, -1000
            x_max, y_max = 1000, 1000
        else:
            bounds = buildings_gdf.total_bounds
            x_min, y_min, x_max, y_max = bounds
        
        # グリッド作成（設定ファイルから解像度を取得）
        grid_size = self.config.get("grid_resolution_meters", 10.0)
        x_coords = np.arange(x_min, x_max, grid_size)
        y_coords = np.arange(y_min, y_max, grid_size)
        
        grid_cells = []
        for i, x in enumerate(x_coords[:-1]):
            for j, y in enumerate(y_coords[:-1]):
                from shapely.geometry import Polygon
                cell = Polygon([
                    (x, y),
                    (x + grid_size, y),
                    (x + grid_size, y + grid_size),
                    (x, y + grid_size)
                ])
                grid_cells.append({
                    'geometry': cell,
                    'grid_id': f"{i}_{j}",
                    'x_index': i,
                    'y_index': j
                })
        
        # 空のGeoDataFrameの場合はデフォルトCRSを使用
        if buildings_gdf.empty:
            crs = 'EPSG:4326'
        else:
            crs = buildings_gdf.crs
        
        return gpd.GeoDataFrame(grid_cells, crs=crs)
    
    def _identify_open_spaces(self, grid_gdf: gpd.GeoDataFrame, 
                            buildings_gdf: gpd.GeoDataFrame,
                            roads_gdf: Optional[gpd.GeoDataFrame] = None) -> gpd.GeoDataFrame:
        """
        オープンスペースを特定
        
        Args:
            grid_gdf: グリッドデータ
            buildings_gdf: 建物データ
            roads_gdf: 道路データ
            
        Returns:
            オープンスペース判定付きグリッドデータ
        """
        # 建物密度を計算
        grid_with_buildings = gpd.sjoin(grid_gdf, buildings_gdf, how='left', predicate='intersects')
        
        # グリッドごとに建物面積を集計
        building_area_stats = grid_with_buildings.groupby('grid_id').agg({
            'area_m2': 'sum'
        }).reset_index()
        
        # 元のグリッドと結合
        result = grid_gdf.merge(building_area_stats, on='grid_id', how='left')
        result['building_area'] = result['area_m2'].fillna(0)
        
        # 建物密度を計算
        grid_area = self.grid_size ** 2
        result['building_density'] = result['building_area'] / grid_area
        
        # オープンスペース判定
        threshold = self.open_space_config.get("building_density_threshold", 0.3)
        result['is_open_space'] = result['building_density'] <= threshold
        
        # 道路を考慮（オプション）
        if roads_gdf is not None:
            result = self._consider_roads(result, roads_gdf)
        
        return result
    
    def _consider_roads(self, grid_gdf: gpd.GeoDataFrame, 
                       roads_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        道路を考慮してオープンスペースを調整
        
        Args:
            grid_gdf: グリッドデータ
            roads_gdf: 道路データ
            
        Returns:
            道路考慮後のグリッドデータ
        """
        # 道路とグリッドの空間結合
        grid_with_roads = gpd.sjoin(grid_gdf, roads_gdf, how='left', predicate='intersects')
        
        # 道路を含むグリッドをオープンスペースとして扱う
        has_road = grid_with_roads.groupby('grid_id').size() > 0
        road_grids = has_road[has_road].index.tolist()
        
        grid_gdf.loc[grid_gdf['grid_id'].isin(road_grids), 'is_open_space'] = True
        
        return grid_gdf
    
    def _analyze_percolation(self, grid_gdf: gpd.GeoDataFrame) -> Dict[str, float]:
        """
        パーコレーション解析を実行
        
        Args:
            grid_gdf: オープンスペース判定付きグリッドデータ
            
        Returns:
            パーコレーション解析結果
        """
        # グリッドを2次元配列に変換
        grid_array = self._grid_to_array(grid_gdf)
        
        # 連結成分を検出
        labeled_array, num_clusters = ndimage.label(grid_array)
        
        # 各クラスターの面積を計算
        cluster_areas = []
        for i in range(1, num_clusters + 1):
            area = np.sum(labeled_array == i) * (self.grid_size ** 2)
            cluster_areas.append(area)
        
        if cluster_areas:
            largest_cluster_area = max(cluster_areas)
            total_open_area = sum(cluster_areas)
        else:
            largest_cluster_area = 0.0
            total_open_area = 0.0
        
        return {
            'largest_cluster_area': largest_cluster_area,
            'total_open_area': total_open_area,
            'num_clusters': num_clusters,
            'cluster_areas': cluster_areas
        }
    
    def _grid_to_array(self, grid_gdf: gpd.GeoDataFrame) -> np.ndarray:
        """
        グリッドを2次元配列に変換
        
        Args:
            grid_gdf: グリッドデータ
            
        Returns:
            2次元配列（True: オープンスペース, False: 建物）
        """
        # グリッドのサイズを取得
        max_x = grid_gdf['x_index'].max()
        max_y = grid_gdf['y_index'].max()
        
        # 配列を初期化
        grid_array = np.zeros((max_y + 1, max_x + 1), dtype=bool)
        
        # オープンスペースを設定
        for _, row in grid_gdf.iterrows():
            x_idx = int(row['x_index'])
            y_idx = int(row['y_index'])
            if row['is_open_space']:
                grid_array[y_idx, x_idx] = True
        
        return grid_array
