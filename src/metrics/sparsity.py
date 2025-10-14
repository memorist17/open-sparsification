"""
疎性指標計算モジュール

空間充填率（フラクタル次元）と建物数の関係から都市の疎性を定量化します。
計算式: 空間充填率（フラクタル次元数） / 建物数
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from typing import List, Tuple, Dict, Any, Optional
from loguru import logger
from ..utils.config import get_config


class SparsityCalculator:
    """疎性指標計算クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書（デフォルト: parameters.ymlから読み込み）
        """
        if config is None:
            config = get_config("sparsity")
        
        self.config = config
        self.fractal_config = config.get("fractal", {})
        self.building_count_config = config.get("building_count", {})
    
    def calculate(self, buildings_gdf: gpd.GeoDataFrame) -> Dict[str, float]:
        """
        疎性指標を計算
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            疎性指標の辞書
        """
        logger.info("疎性指標計算開始")
        
        # フラクタル次元を計算
        fractal_dimension = self._calculate_fractal_dimension(buildings_gdf)
        
        # 建物数を計算
        building_count = self._calculate_building_count(buildings_gdf)
        
        # 疎性指標
        if building_count > 0:
            sparsity = fractal_dimension / building_count
        else:
            sparsity = 0.0
        
        result = {
            'sparsity': sparsity,
            'fractal_dimension': fractal_dimension,
            'building_count': building_count
        }
        
        logger.info(f"疎性指標計算完了: {sparsity:.4f}")
        return result
    
    def _calculate_fractal_dimension(self, buildings_gdf: gpd.GeoDataFrame) -> float:
        """
        フラクタル次元を計算（ボックスカウンティング法）
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            フラクタル次元
        """
        method = self.fractal_config.get("method", "box_counting")
        box_sizes = self.fractal_config.get("box_sizes", [1, 2, 4, 8, 16, 32, 64])
        
        if method == "box_counting":
            return self._box_counting_dimension(buildings_gdf, box_sizes)
        else:
            logger.warning(f"未対応のフラクタル次元計算方法: {method}")
            return 0.0
    
    def _box_counting_dimension(self, buildings_gdf: gpd.GeoDataFrame, 
                               box_sizes: List[float]) -> float:
        """
        ボックスカウンティング法によるフラクタル次元計算
        
        Args:
            buildings_gdf: 建物データ
            box_sizes: ボックスサイズのリスト（メートル）
            
        Returns:
            フラクタル次元
        """
        # 建物の境界を取得
        bounds = buildings_gdf.total_bounds  # [minx, miny, maxx, maxy]
        
        counts = []
        sizes = []
        
        for box_size in box_sizes:
            # グリッドを作成
            x_min, y_min, x_max, y_max = bounds
            
            # グリッドのセル数を計算
            nx = int(np.ceil((x_max - x_min) / box_size))
            ny = int(np.ceil((y_max - y_min) / box_size))
            
            # 建物を含むセルをカウント
            occupied_cells = set()
            
            for _, building in buildings_gdf.iterrows():
                # 建物の重心を取得
                centroid = building.geometry.centroid
                
                # セルインデックスを計算
                cell_x = int((centroid.x - x_min) / box_size)
                cell_y = int((centroid.y - y_min) / box_size)
                
                # 境界チェック
                if 0 <= cell_x < nx and 0 <= cell_y < ny:
                    occupied_cells.add((cell_x, cell_y))
            
            counts.append(len(occupied_cells))
            sizes.append(box_size)
        
        # 対数回帰でフラクタル次元を計算
        if len(counts) > 1 and all(c > 0 for c in counts):
            log_sizes = np.log(sizes)
            log_counts = np.log(counts)
            
            # 線形回帰
            slope, _ = np.polyfit(log_sizes, log_counts, 1)
            fractal_dimension = -slope
        else:
            fractal_dimension = 0.0
        
        return float(fractal_dimension)
    
    def _calculate_building_count(self, buildings_gdf: gpd.GeoDataFrame) -> int:
        """
        建物数を計算
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            建物数
        """
        min_area = self.building_count_config.get("min_area", 10.0)
        
        # 最小面積以上の建物をカウント
        if 'area_m2' in buildings_gdf.columns:
            valid_buildings = buildings_gdf[buildings_gdf['area_m2'] >= min_area]
        else:
            # 面積が計算されていない場合はジオメトリから計算
            buildings_gdf = buildings_gdf.copy()
            buildings_gdf['area_m2'] = buildings_gdf.geometry.area
            valid_buildings = buildings_gdf[buildings_gdf['area_m2'] >= min_area]
        
        return len(valid_buildings)
    
    def calculate_spatial_filling_ratio(self, buildings_gdf: gpd.GeoDataFrame) -> float:
        """
        空間充填率を計算
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            空間充填率
        """
        # 建物の総面積
        total_building_area = buildings_gdf.geometry.area.sum()
        
        # 建物の境界ボックスの面積
        bounds = buildings_gdf.total_bounds
        bounding_box_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
        
        if bounding_box_area > 0:
            filling_ratio = total_building_area / bounding_box_area
        else:
            filling_ratio = 0.0
        
        return float(filling_ratio)
