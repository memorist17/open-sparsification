"""
多中心性指標計算モジュール

DBSCANクラスタリングを用いて都市の多中心性を定量化します。
計算式: 核の数 × 核の分散度 × 核の多様性
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances
from typing import List, Tuple, Dict, Any, Optional
from loguru import logger
from ..utils.config import get_config


class MultiNodalityCalculator:
    """多中心性指標計算クラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書（デフォルト: parameters.ymlから読み込み）
        """
        if config is None:
            config = get_config("multi_nodality")
        
        self.config = config
        self.dbscan_config = config.get("dbscan", {})
        self.dispersion_config = config.get("dispersion", {})
        self.diversity_config = config.get("diversity", {})
    
    def calculate(self, buildings_gdf: gpd.GeoDataFrame) -> Dict[str, float]:
        """
        多中心性指標を計算
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            多中心性指標の辞書
        """
        logger.info("多中心性指標計算開始")
        
        # 建物の重心を取得
        centroids = self._extract_centroids(buildings_gdf)
        
        if len(centroids) < 2:
            logger.warning("建物数が少なすぎます")
            return {
                'multi_nodality': 0.0,
                'num_cores': 0,
                'core_dispersion': 0.0,
                'core_diversity': 0.0
            }
        
        # DBSCANクラスタリング
        clusters = self._perform_dbscan(centroids)
        
        # 各指標を計算
        num_cores = self._calculate_num_cores(clusters)
        core_dispersion = self._calculate_core_dispersion(centroids, clusters)
        core_diversity = self._calculate_core_diversity(clusters)
        
        # 多中心性指標
        multi_nodality = num_cores * core_dispersion * core_diversity
        
        result = {
            'multi_nodality': multi_nodality,
            'num_cores': num_cores,
            'core_dispersion': core_dispersion,
            'core_diversity': core_diversity
        }
        
        logger.info(f"多中心性指標計算完了: {multi_nodality:.4f}")
        return result
    
    def _extract_centroids(self, buildings_gdf: gpd.GeoDataFrame) -> np.ndarray:
        """
        建物の重心を抽出
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            重心座標の配列
        """
        centroids = []
        for _, building in buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            centroids.append([centroid.x, centroid.y])
        
        return np.array(centroids)
    
    def _perform_dbscan(self, centroids: np.ndarray) -> np.ndarray:
        """
        DBSCANクラスタリングを実行
        
        Args:
            centroids: 重心座標（メートル単位）
            
        Returns:
            クラスターラベル
        """
        eps = self.dbscan_config.get("eps", 50.0)  # メートル単位
        min_samples = self.dbscan_config.get("min_samples", 5)
        metric = self.dbscan_config.get("metric", "euclidean")
        
        # DBSCAN実行（座標は既にメートル単位）
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric=metric)
        cluster_labels = clustering.fit_predict(centroids)
        
        logger.info(f"DBSCAN完了: {len(set(cluster_labels))}クラスター")
        return cluster_labels
    
    def _calculate_num_cores(self, clusters: np.ndarray) -> int:
        """
        核の数を計算
        
        Args:
            clusters: クラスターラベル
            
        Returns:
            核の数
        """
        # ノイズ（-1）を除いたクラスター数
        num_cores = len(set(clusters)) - (1 if -1 in clusters else 0)
        return max(0, num_cores)
    
    def _calculate_core_dispersion(self, centroids: np.ndarray, 
                                 clusters: np.ndarray) -> float:
        """
        核の分散度を計算
        
        Args:
            centroids: 重心座標
            clusters: クラスターラベル
            
        Returns:
            核の分散度
        """
        method = self.dispersion_config.get("method", "variance")
        
        # 各クラスターの中心を計算
        cluster_centers = []
        for cluster_id in set(clusters):
            if cluster_id == -1:  # ノイズをスキップ
                continue
            
            cluster_points = centroids[clusters == cluster_id]
            center = np.mean(cluster_points, axis=0)
            cluster_centers.append(center)
        
        if len(cluster_centers) < 2:
            return 0.0
        
        cluster_centers = np.array(cluster_centers)
        
        # 分散度計算
        if method == "variance":
            distances = pairwise_distances(cluster_centers)
            # 対角要素を除いた距離の分散
            mask = ~np.eye(distances.shape[0], dtype=bool)
            dispersion = np.var(distances[mask])
        elif method == "std":
            distances = pairwise_distances(cluster_centers)
            mask = ~np.eye(distances.shape[0], dtype=bool)
            dispersion = np.std(distances[mask])
        elif method == "iqr":
            distances = pairwise_distances(cluster_centers)
            mask = ~np.eye(distances.shape[0], dtype=bool)
            q75, q25 = np.percentile(distances[mask], [75, 25])
            dispersion = q75 - q25
        else:
            dispersion = 0.0
        
        return float(dispersion)
    
    def _calculate_core_diversity(self, clusters: np.ndarray) -> float:
        """
        核の多様性を計算
        
        Args:
            clusters: クラスターラベル
            
        Returns:
            核の多様性
        
        Note:
            現在は建物の属性データが存在しないため、多様性を1として計算する。
            将来的に建物の属性データが利用可能になった際の拡張ポイント。
        """
        # TODO: 建物の属性データが利用可能になった際に実装
        # 現在は多様性を1として返す（将来拡張用）
        logger.info("核の多様性計算: 属性データが存在しないため、多様性=1として計算")
        return 1.0
    
    def get_cluster_info(self, buildings_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        クラスター情報を取得
        
        Args:
            buildings_gdf: 建物データ
            
        Returns:
            クラスター情報のDataFrame
        """
        centroids = self._extract_centroids(buildings_gdf)
        clusters = self._perform_dbscan(centroids)
        
        # 建物データにクラスター情報を追加
        result_df = buildings_gdf.copy()
        result_df['cluster_id'] = clusters
        result_df['centroid_x'] = [c[0] for c in centroids]
        result_df['centroid_y'] = [c[1] for c in centroids]
        
        return result_df
