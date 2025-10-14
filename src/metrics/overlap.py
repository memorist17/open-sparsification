"""
重なり指標計算モジュール

複数の機能や属性を持つ建物の割合を評価する指標。
計算式: 複数の属性をもった建物総数 / 総建物数
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from typing import List, Tuple, Dict, Any, Optional
from loguru import logger
from ..utils.config import get_config


class OverlapCalculator:
    """重なり指標計算クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書（デフォルト: parameters.ymlから読み込み）
        """
        if config is None:
            config = get_config("overlap")
        
        self.config = config
        self.attributes = config.get("attributes", ["residential", "commercial", "industrial", "public"])
        self.overlap_threshold = config.get("overlap_threshold", 0.1)
    
    def calculate(self, buildings_gdf: gpd.GeoDataFrame) -> Dict[str, float]:
        """
        重なり指標を計算
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            重なり指標の辞書
        
        Note:
            この指標は複数の属性を持つ建物を必要とするが、該当データが存在しないため実装不可。
            常に0を返すスタブ関数として実装。
        """
        logger.warning("重なり指標: 複数属性建物データが存在しないため、実装不可")
        
        result = {
            'overlap': 0.0,
            'total_buildings': len(buildings_gdf),
            'overlapping_buildings': 0,
            'attribute_distribution': {},
            'note': '複数属性建物データが存在しないため実装不可'
        }
        
        return result
    
    def _analyze_building_attributes(self, buildings_gdf: gpd.GeoDataFrame) -> Dict[str, int]:
        """
        建物の属性分布を分析
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            属性別建物数の辞書
        """
        if 'type' not in buildings_gdf.columns:
            logger.warning("建物データに'type'列がありません")
            return {attr: 0 for attr in self.attributes}
        
        # 属性別の建物数をカウント
        attribute_counts = buildings_gdf['type'].value_counts().to_dict()
        
        # 定義された属性のみを返す
        result = {attr: attribute_counts.get(attr, 0) for attr in self.attributes}
        result['other'] = sum(count for attr, count in attribute_counts.items() 
                            if attr not in self.attributes)
        
        return result
    
    def _identify_overlapping_buildings(self, buildings_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        重複属性を持つ建物を特定
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            重複建物のDataFrame
        """
        # 建物の属性を分析
        buildings_with_attributes = self._assign_multiple_attributes(buildings_gdf)
        
        # 複数属性を持つ建物を特定
        overlapping_buildings = buildings_with_attributes[
            buildings_with_attributes['num_attributes'] > 1
        ]
        
        return overlapping_buildings
    
    def _assign_multiple_attributes(self, buildings_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        建物に複数の属性を割り当て（空間的重複を考慮）
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            複数属性付き建物データ
        """
        result_df = buildings_gdf.copy()
        
        # 各建物の属性を分析
        building_attributes = []
        num_attributes = []
        
        for idx, building in buildings_gdf.iterrows():
            # 基本属性
            primary_type = building.get('type', 'unknown')
            attributes = [primary_type] if primary_type in self.attributes else []
            
            # 空間的重複を考慮した属性追加
            # 実際の実装では、周辺の建物や土地利用を考慮
            additional_attributes = self._get_additional_attributes(building, buildings_gdf)
            attributes.extend(additional_attributes)
            
            # 重複を除去
            unique_attributes = list(set(attributes))
            building_attributes.append(unique_attributes)
            num_attributes.append(len(unique_attributes))
        
        result_df['attributes'] = building_attributes
        result_df['num_attributes'] = num_attributes
        
        return result_df
    
    def _get_additional_attributes(self, building: pd.Series, 
                                 buildings_gdf: gpd.GeoDataFrame) -> List[str]:
        """
        建物の追加属性を取得（空間的近接性を考慮）
        
        Args:
            building: 対象建物
            buildings_gdf: 全建物データ
            
        Returns:
            追加属性のリスト
        """
        additional_attributes = []
        
        # 周辺の建物を検索
        buffer_distance = 100.0  # 100メートル
        building_geom = building.geometry
        buffer_geom = building_geom.buffer(buffer_distance)
        
        # バッファ内の建物を取得
        nearby_buildings = buildings_gdf[buildings_gdf.geometry.intersects(buffer_geom)]
        
        # 周辺建物の属性を分析
        if len(nearby_buildings) > 0:
            nearby_types = nearby_buildings['type'].value_counts()
            
            # 閾値以上の割合を持つ属性を追加
            total_nearby = len(nearby_buildings)
            for attr_type, count in nearby_types.items():
                if attr_type in self.attributes and count / total_nearby >= self.overlap_threshold:
                    additional_attributes.append(attr_type)
        
        return additional_attributes
    
    def calculate_functional_diversity(self, buildings_gdf: gpd.GeoDataFrame) -> float:
        """
        機能的多様性を計算（シャノン多様性指数）
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            機能的多様性
        """
        attribute_counts = self._analyze_building_attributes(buildings_gdf)
        total_buildings = sum(attribute_counts.values())
        
        if total_buildings == 0:
            return 0.0
        
        # 確率を計算
        probabilities = [count / total_buildings for count in attribute_counts.values() if count > 0]
        
        # シャノン多様性指数
        diversity = -sum(p * np.log(p + 1e-10) for p in probabilities)
        
        return float(diversity)
    
    def get_overlap_matrix(self, buildings_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        属性間の重複マトリックスを取得
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            重複マトリックス
        """
        buildings_with_attributes = self._assign_multiple_attributes(buildings_gdf)
        
        # 属性ペアの重複をカウント
        overlap_matrix = pd.DataFrame(0, index=self.attributes, columns=self.attributes)
        
        for _, building in buildings_with_attributes.iterrows():
            attributes = building['attributes']
            if len(attributes) > 1:
                # 属性ペアの重複をカウント
                for i, attr1 in enumerate(attributes):
                    for attr2 in attributes[i+1:]:
                        if attr1 in self.attributes and attr2 in self.attributes:
                            overlap_matrix.loc[attr1, attr2] += 1
                            overlap_matrix.loc[attr2, attr1] += 1
        
        return overlap_matrix
