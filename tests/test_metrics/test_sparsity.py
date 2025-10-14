"""
疎性指標計算のテスト
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.metrics.sparsity import SparsityCalculator


class TestSparsityCalculator:
    """疎性指標計算クラスのテスト"""
    
    @pytest.fixture
    def sample_buildings(self):
        """サンプル建物データを作成"""
        buildings_data = []
        
        # 密集した建物群
        for i in range(10):
            for j in range(10):
                geom = Polygon([
                    (139.767 + i*0.0001, 35.681 + j*0.0001),
                    (139.767 + i*0.0001 + 0.00005, 35.681 + j*0.0001),
                    (139.767 + i*0.0001 + 0.00005, 35.681 + j*0.0001 + 0.00005),
                    (139.767 + i*0.0001, 35.681 + j*0.0001 + 0.00005)
                ])
                buildings_data.append({
                    'geometry': geom,
                    'type': 'residential',
                    'area_m2': 50.0
                })
        
        return gpd.GeoDataFrame(buildings_data, crs="EPSG:4326")
    
    @pytest.fixture
    def calculator(self):
        """計算機インスタンスを作成"""
        config = {
            "fractal": {
                "method": "box_counting",
                "box_sizes": [1, 2, 4, 8, 16, 32, 64]
            },
            "building_count": {
                "min_area": 10.0
            }
        }
        return SparsityCalculator(config)
    
    def test_calculate(self, calculator, sample_buildings):
        """疎性指標の計算テスト"""
        result = calculator.calculate(sample_buildings)
        
        # 結果の構造をチェック
        assert 'sparsity' in result
        assert 'fractal_dimension' in result
        assert 'building_count' in result
        
        # 値の妥当性をチェック
        assert result['fractal_dimension'] >= 0
        assert result['building_count'] > 0
        assert result['sparsity'] >= 0
    
    def test_calculate_fractal_dimension(self, calculator, sample_buildings):
        """フラクタル次元計算のテスト"""
        fractal_dim = calculator._calculate_fractal_dimension(sample_buildings)
        assert fractal_dim >= 0
    
    def test_box_counting_dimension(self, calculator, sample_buildings):
        """ボックスカウンティング法のテスト"""
        box_sizes = [1, 2, 4, 8, 16, 32, 64]
        dimension = calculator._box_counting_dimension(sample_buildings, box_sizes)
        assert dimension >= 0
    
    def test_calculate_building_count(self, calculator, sample_buildings):
        """建物数計算のテスト"""
        count = calculator._calculate_building_count(sample_buildings)
        assert count > 0
        assert count == len(sample_buildings)  # 全ての建物が最小面積以上
    
    def test_calculate_spatial_filling_ratio(self, calculator, sample_buildings):
        """空間充填率計算のテスト"""
        ratio = calculator.calculate_spatial_filling_ratio(sample_buildings)
        assert 0 <= ratio <= 1
    
    def test_empty_buildings(self, calculator):
        """空の建物データのテスト"""
        empty_gdf = gpd.GeoDataFrame(columns=['geometry', 'type', 'area_m2'], crs="EPSG:4326")
        result = calculator.calculate(empty_gdf)
        
        assert result['sparsity'] == 0.0
        assert result['fractal_dimension'] == 0.0
        assert result['building_count'] == 0
    
    def test_single_building(self, calculator):
        """単一建物のテスト"""
        single_building = gpd.GeoDataFrame([{
            'geometry': Polygon([
                (139.767, 35.681),
                (139.767 + 0.001, 35.681),
                (139.767 + 0.001, 35.681 + 0.001),
                (139.767, 35.681 + 0.001)
            ]),
            'type': 'residential',
            'area_m2': 100.0
        }], crs="EPSG:4326")
        
        result = calculator.calculate(single_building)
        assert result['building_count'] == 1
        assert result['sparsity'] >= 0
