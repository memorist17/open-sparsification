"""
流動性指標計算のテスト
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, LineString
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.metrics.permeability import PermeabilityCalculator


class TestPermeabilityCalculator:
    """流動性指標計算クラスのテスト"""
    
    @pytest.fixture
    def sample_buildings(self):
        """サンプル建物データを作成"""
        buildings_data = []
        
        # 建物を配置（一部密集、一部疎）
        # 密集エリア
        for i in range(5):
            for j in range(5):
                geom = Polygon([
                    (139.767 + i*0.001, 35.681 + j*0.001),
                    (139.767 + i*0.001 + 0.0005, 35.681 + j*0.001),
                    (139.767 + i*0.001 + 0.0005, 35.681 + j*0.001 + 0.0005),
                    (139.767 + i*0.001, 35.681 + j*0.001 + 0.0005)
                ])
                buildings_data.append({
                    'geometry': geom,
                    'type': 'residential',
                    'area_m2': 100.0
                })
        
        # 疎なエリア（間隔を空ける）
        for i in range(3):
            geom = Polygon([
                (139.780 + i*0.01, 35.690 + i*0.01),
                (139.780 + i*0.01 + 0.0005, 35.690 + i*0.01),
                (139.780 + i*0.01 + 0.0005, 35.690 + i*0.01 + 0.0005),
                (139.780 + i*0.01, 35.690 + i*0.01 + 0.0005)
            ])
            buildings_data.append({
                'geometry': geom,
                'type': 'commercial',
                'area_m2': 200.0
            })
        
        return gpd.GeoDataFrame(buildings_data, crs="EPSG:4326")
    
    @pytest.fixture
    def sample_roads(self):
        """サンプル道路データを作成"""
        roads_data = []
        
        # 道路を追加
        road1 = LineString([
            (139.765, 35.680),
            (139.785, 35.680)
        ])
        roads_data.append({
            'geometry': road1,
            'type': 'highway',
            'width': 10.0
        })
        
        road2 = LineString([
            (139.770, 35.675),
            (139.770, 35.695)
        ])
        roads_data.append({
            'geometry': road2,
            'type': 'primary',
            'width': 8.0
        })
        
        return gpd.GeoDataFrame(roads_data, crs="EPSG:4326")
    
    @pytest.fixture
    def calculator(self):
        """計算機インスタンスを作成"""
        config = {
            "grid_size": 50.0,
            "open_space": {
                "building_density_threshold": 0.3,
                "min_road_width": 3.0,
                "min_green_area": 100.0
            },
            "percolation_threshold": 0.5927
        }
        return PermeabilityCalculator(config)
    
    def test_calculate(self, calculator, sample_buildings, sample_roads):
        """流動性指標の計算テスト"""
        result = calculator.calculate(sample_buildings, sample_roads)
        
        # 結果の構造をチェック
        assert 'permeability' in result
        assert 'largest_cluster_area' in result
        assert 'total_open_area' in result
        assert 'num_clusters' in result
        assert 'percolation_threshold' in result
        
        # 値の妥当性をチェック
        assert 0 <= result['permeability'] <= 1
        assert result['largest_cluster_area'] >= 0
        assert result['total_open_area'] >= 0
        assert result['num_clusters'] >= 0
    
    def test_create_analysis_grid(self, calculator, sample_buildings):
        """分析グリッド作成のテスト"""
        bounds = sample_buildings.total_bounds
        grid_gdf = calculator._create_analysis_grid(bounds, 50.0)
        
        assert len(grid_gdf) > 0
        assert 'grid_id' in grid_gdf.columns
        assert 'x_index' in grid_gdf.columns
        assert 'y_index' in grid_gdf.columns
    
    def test_identify_open_spaces(self, calculator, sample_buildings, sample_roads):
        """オープンスペース特定のテスト"""
        bounds = sample_buildings.total_bounds
        grid_gdf = calculator._create_analysis_grid(bounds, 50.0)
        open_space_grid = calculator._identify_open_spaces(grid_gdf, sample_buildings, sample_roads)
        
        assert 'is_open_space' in open_space_grid.columns
        assert 'building_density' in open_space_grid.columns
        assert len(open_space_grid) == len(grid_gdf)
    
    def test_consider_roads(self, calculator, sample_roads):
        """道路考慮のテスト"""
        # 簡単なグリッドを作成
        grid_data = []
        for i in range(3):
            for j in range(3):
                geom = Polygon([
                    (139.767 + i*0.01, 35.681 + j*0.01),
                    (139.767 + i*0.01 + 0.005, 35.681 + j*0.01),
                    (139.767 + i*0.01 + 0.005, 35.681 + j*0.01 + 0.005),
                    (139.767 + i*0.01, 35.681 + j*0.01 + 0.005)
                ])
                grid_data.append({
                    'geometry': geom,
                    'grid_id': f"{i}_{j}",
                    'is_open_space': False
                })
        
        grid_gdf = gpd.GeoDataFrame(grid_data, crs="EPSG:4326")
        result = calculator._consider_roads(grid_gdf, sample_roads)
        
        assert 'is_open_space' in result.columns
        assert len(result) == len(grid_gdf)
    
    def test_analyze_percolation(self, calculator):
        """パーコレーション解析のテスト"""
        # 簡単なグリッドデータを作成
        grid_data = []
        for i in range(5):
            for j in range(5):
                geom = Polygon([
                    (i*10, j*10),
                    (i*10 + 10, j*10),
                    (i*10 + 10, j*10 + 10),
                    (i*10, j*10 + 10)
                ])
                # 一部をオープンスペースにする
                is_open = (i + j) % 2 == 0
                grid_data.append({
                    'geometry': geom,
                    'grid_id': f"{i}_{j}",
                    'x_index': i,
                    'y_index': j,
                    'is_open_space': is_open
                })
        
        grid_gdf = gpd.GeoDataFrame(grid_data, crs="EPSG:3857")
        result = calculator._analyze_percolation(grid_gdf)
        
        assert 'largest_cluster_area' in result
        assert 'total_open_area' in result
        assert 'num_clusters' in result
        assert 'cluster_areas' in result
    
    def test_grid_to_array(self, calculator):
        """グリッド配列変換のテスト"""
        grid_data = []
        for i in range(3):
            for j in range(3):
                geom = Polygon([
                    (i*10, j*10),
                    (i*10 + 10, j*10),
                    (i*10 + 10, j*10 + 10),
                    (i*10, j*10 + 10)
                ])
                grid_data.append({
                    'geometry': geom,
                    'grid_id': f"{i}_{j}",
                    'x_index': i,
                    'y_index': j,
                    'is_open_space': (i + j) % 2 == 0
                })
        
        grid_gdf = gpd.GeoDataFrame(grid_data, crs="EPSG:3857")
        grid_array = calculator._grid_to_array(grid_gdf)
        
        assert grid_array.shape == (3, 3)
        assert isinstance(grid_array, np.ndarray)
        assert grid_array.dtype == bool
