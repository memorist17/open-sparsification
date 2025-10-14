"""
多中心性指標計算のテスト
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

from src.metrics.multi_nodality import MultiNodalityCalculator


class TestMultiNodalityCalculator:
    """多中心性指標計算クラスのテスト"""
    
    @pytest.fixture
    def sample_buildings(self):
        """サンプル建物データを作成"""
        # 2つのクラスターを作成
        buildings_data = []
        
        # クラスター1: 東京駅周辺
        for i in range(5):
            geom = Polygon([
                (139.767 + i*0.001, 35.681 + i*0.001),
                (139.767 + i*0.001 + 0.0005, 35.681 + i*0.001),
                (139.767 + i*0.001 + 0.0005, 35.681 + i*0.001 + 0.0005),
                (139.767 + i*0.001, 35.681 + i*0.001 + 0.0005)
            ])
            buildings_data.append({
                'geometry': geom,
                'type': 'commercial',
                'area_m2': 100.0
            })
        
        # クラスター2: 新宿駅周辺
        for i in range(3):
            geom = Polygon([
                (139.700 + i*0.001, 35.690 + i*0.001),
                (139.700 + i*0.001 + 0.0005, 35.690 + i*0.001),
                (139.700 + i*0.001 + 0.0005, 35.690 + i*0.001 + 0.0005),
                (139.700 + i*0.001, 35.690 + i*0.001 + 0.0005)
            ])
            buildings_data.append({
                'geometry': geom,
                'type': 'commercial',
                'area_m2': 100.0
            })
        
        return gpd.GeoDataFrame(buildings_data, crs="EPSG:4326")
    
    @pytest.fixture
    def calculator(self):
        """計算機インスタンスを作成"""
        config = {
            "dbscan": {
                "eps": 0.5,
                "min_samples": 2,
                "metric": "euclidean"
            },
            "dispersion": {
                "method": "variance"
            },
            "diversity": {
                "method": "shannon"
            }
        }
        return MultiNodalityCalculator(config)
    
    def test_calculate(self, calculator, sample_buildings):
        """多中心性指標の計算テスト"""
        result = calculator.calculate(sample_buildings)
        
        # 結果の構造をチェック
        assert 'multi_nodality' in result
        assert 'num_cores' in result
        assert 'core_dispersion' in result
        assert 'core_diversity' in result
        
        # 値の妥当性をチェック
        assert result['num_cores'] >= 0
        assert result['core_dispersion'] >= 0
        assert result['core_diversity'] >= 0
        assert result['multi_nodality'] >= 0
    
    def test_extract_centroids(self, calculator, sample_buildings):
        """重心抽出のテスト"""
        centroids = calculator._extract_centroids(sample_buildings)
        
        assert len(centroids) == len(sample_buildings)
        assert centroids.shape[1] == 2  # x, y座標
    
    def test_perform_dbscan(self, calculator, sample_buildings):
        """DBSCANクラスタリングのテスト"""
        centroids = calculator._extract_centroids(sample_buildings)
        clusters = calculator._perform_dbscan(centroids)
        
        assert len(clusters) == len(centroids)
        assert isinstance(clusters, np.ndarray)
    
    def test_calculate_num_cores(self, calculator):
        """核の数計算のテスト"""
        # テストケース1: 2つのクラスター
        clusters1 = np.array([0, 0, 1, 1, -1])  # -1はノイズ
        num_cores1 = calculator._calculate_num_cores(clusters1)
        assert num_cores1 == 2
        
        # テストケース2: ノイズのみ
        clusters2 = np.array([-1, -1, -1])
        num_cores2 = calculator._calculate_num_cores(clusters2)
        assert num_cores2 == 0
    
    def test_calculate_core_dispersion(self, calculator):
        """核の分散度計算のテスト"""
        centroids = np.array([[0, 0], [1, 1], [2, 2], [3, 3]])
        clusters = np.array([0, 0, 1, 1])
        
        dispersion = calculator._calculate_core_dispersion(centroids, clusters)
        assert dispersion >= 0
    
    def test_calculate_core_diversity(self, calculator):
        """核の多様性計算のテスト"""
        # テストケース1: 2つのクラスター（サイズが異なる）
        clusters1 = np.array([0, 0, 0, 1, 1])
        diversity1 = calculator._calculate_core_diversity(clusters1)
        assert 0 <= diversity1 <= 1
        
        # テストケース2: 1つのクラスター
        clusters2 = np.array([0, 0, 0, 0])
        diversity2 = calculator._calculate_core_diversity(clusters2)
        assert diversity2 == 0
    
    def test_get_cluster_info(self, calculator, sample_buildings):
        """クラスター情報取得のテスト"""
        cluster_info = calculator.get_cluster_info(sample_buildings)
        
        assert len(cluster_info) == len(sample_buildings)
        assert 'cluster_id' in cluster_info.columns
        assert 'centroid_x' in cluster_info.columns
        assert 'centroid_y' in cluster_info.columns
