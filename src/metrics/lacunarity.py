"""
Lacunarity Analysis Module

Quantifies local vacancy structure in point patterns.
Based on Plotnick et al. (1996) and Batty (2008).

Lacunarity measures spatial heterogeneity:
- Λ ≈ 1: Homogeneous (closed)
- Λ ≫ 1: Heterogeneous (open)
"""

import numpy as np
from scipy import ndimage
from typing import Dict, List, Tuple, Optional
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd


def points_to_raster(
    points: gpd.GeoDataFrame,
    bounds: Tuple[float, float, float, float],
    pixel_size: float = 5.0
) -> np.ndarray:
    """
    Convert point cloud to binary raster (高速化版).
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Point geometries (building centroids, etc.)
    bounds : tuple
        (minx, miny, maxx, maxy) in projected coordinates
    pixel_size : float
        Pixel size in meters (default: 5m)
    
    Returns
    -------
    raster : np.ndarray
        Binary raster (1 = point present, 0 = empty)
    """
    minx, miny, maxx, maxy = bounds
    
    # Calculate raster dimensions
    width = int(np.ceil((maxx - minx) / pixel_size))
    height = int(np.ceil((maxy - miny) / pixel_size))
    
    # Initialize empty raster
    raster = np.zeros((height, width), dtype=np.uint8)
    
    # ベクトル化された座標変換（高速化）
    coords = np.array([[geom.x, geom.y] for geom in points.geometry if geom.geom_type == 'Point'])
    
    if len(coords) == 0:
        return raster
    
    # ピクセル座標に変換
    cols = ((coords[:, 0] - minx) / pixel_size).astype(int)
    rows = ((maxy - coords[:, 1]) / pixel_size).astype(int)  # Flip Y axis
    
    # 範囲内のポイントのみ処理
    valid_mask = (0 <= rows) & (rows < height) & (0 <= cols) & (cols < width)
    valid_rows = rows[valid_mask]
    valid_cols = cols[valid_mask]
    
    # ラスターに設定（ベクトル化）
    raster[valid_rows, valid_cols] = 1
    
    return raster


def sliding_window_lacunarity(
    raster: np.ndarray,
    window_sizes: List[int],
    n_jobs: Optional[int] = None
) -> Dict[int, float]:
    """
    Calculate lacunarity using gliding box method (並列化対応).
    
    Parameters
    ----------
    raster : np.ndarray
        Binary raster of point distribution
    window_sizes : list of int
        Box sizes k in pixels (e.g., [3, 5, 7, 11, 15, 21, ...])
    n_jobs : int, optional
        並列ワーカー数（Noneの場合は自動決定）
    
    Returns
    -------
    lacunarity : dict
        {window_size: Λ(k)} mapping
    
    Algorithm
    ---------
    1. For each window size k:
       - Slide k×k window across raster
       - Count points S(i,j,k) in each window
       - Calculate mean μ(k) and variance σ²(k)
    2. Lacunarity: Λ(k) = σ²(k) / μ(k)² + 1
    """
    from typing import Optional
    
    def compute_lacunarity_for_window(k: int) -> Tuple[int, float]:
        """単一ウィンドウサイズのラクナリティを計算"""
        if k > min(raster.shape):
            return k, np.nan
            
        # Apply sliding window using uniform_filter (mean)
        sums = ndimage.uniform_filter(raster.astype(float), size=k, mode='constant')
        sums = sums * (k * k)  # Convert back to sums
        
        # Extract valid window region (avoid edge effects)
        margin = k // 2
        if margin >= raster.shape[0] or margin >= raster.shape[1]:
            return k, np.nan
        
        valid_sums = sums[margin:-margin, margin:-margin]
        
        if valid_sums.size == 0:
            return k, np.nan
        
        # Calculate statistics
        mean_val = np.mean(valid_sums)
        var_val = np.var(valid_sums)
        
        # Lacunarity formula
        if mean_val > 0:
            lac = (var_val / (mean_val ** 2)) + 1
        else:
            lac = np.nan
        
        return k, lac
    
    # 並列処理（joblib使用）
    if n_jobs is None or n_jobs > 1:
        from joblib import Parallel, delayed
        try:
            from ..utils.parallel_utils import get_optimal_n_jobs
        except ImportError:
            import multiprocessing as mp
            def get_optimal_n_jobs(n_tasks):
                return min(n_tasks, mp.cpu_count())
        
        if n_jobs is None:
            n_jobs = get_optimal_n_jobs(len(window_sizes))
        
        if n_jobs > 1 and len(window_sizes) > 1:
            results = Parallel(n_jobs=n_jobs, backend='threading', verbose=0)(
                delayed(compute_lacunarity_for_window)(k) for k in window_sizes
            )
            lacunarity = {k: lac for k, lac in results}
        else:
            # 並列化しない
            lacunarity = {k: lac for k, lac in [compute_lacunarity_for_window(k) for k in window_sizes]}
    else:
        # 並列化しない
        lacunarity = {k: lac for k, lac in [compute_lacunarity_for_window(k) for k in window_sizes]}
    
    return lacunarity


def calculate_lacunarity(
    points: gpd.GeoDataFrame,
    bounds: Optional[Tuple[float, float, float, float]] = None,
    pixel_size: float = 5.0,
    window_sizes: Optional[List[int]] = None,
    n_jobs: Optional[int] = None
) -> Dict[int, float]:
    """
    Calculate lacunarity from point cloud.
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Point geometries
    bounds : tuple, optional
        Analysis bounds (minx, miny, maxx, maxy)
        If None, uses points.total_bounds
    pixel_size : float
        Raster resolution in meters (default: 5m)
    window_sizes : list of int, optional
        Window sizes in pixels
        Default: [3, 5, 7, 11, 15, 21, 31, 41, 51, 71, 101]
    
    Returns
    -------
    lacunarity : dict
        {window_size_pixels: Λ(k)}
    """
    if bounds is None:
        bounds = points.total_bounds
    
    if window_sizes is None:
        # Default window sizes (corresponding to ~15m to 500m at 5m resolution)
        window_sizes = [3, 5, 7, 11, 15, 21, 31, 41, 51, 71, 101]
    
    # Convert to raster
    raster = points_to_raster(points, bounds, pixel_size)
    
    # Calculate lacunarity (並列化対応)
    lacunarity = sliding_window_lacunarity(raster, window_sizes, n_jobs=n_jobs)
    
    return lacunarity


def lacunarity_summary(
    lacunarity: Dict[int, float],
    pixel_size: float = 5.0
) -> pd.DataFrame:
    """
    Summarize lacunarity results by scale.
    
    Parameters
    ----------
    lacunarity : dict
        {window_size_pixels: Λ(k)}
    pixel_size : float
        Pixel size in meters
    
    Returns
    -------
    summary : pd.DataFrame
        Columns: scale_pixels, scale_meters, lacunarity
        
        Additional aggregations:
        - Small scale (10-50m): mean Λ
        - Medium scale (50-200m): mean Λ
        - Large scale (200-600m): mean Λ
    """
    # Convert to DataFrame
    data = []
    for k, lac in lacunarity.items():
        scale_meters = k * pixel_size
        data.append({
            'scale_pixels': k,
            'scale_meters': scale_meters,
            'lacunarity': lac
        })
    
    df = pd.DataFrame(data).sort_values('scale_pixels')
    
    # Add scale categories
    def categorize_scale(meters):
        if meters < 50:
            return 'small'
        elif meters < 200:
            return 'medium'
        else:
            return 'large'
    
    df['scale_category'] = df['scale_meters'].apply(categorize_scale)
    
    return df


def lacunarity_scale_aggregation(summary_df: pd.DataFrame) -> Dict[str, float]:
    """
    Aggregate lacunarity by scale category.
    
    Parameters
    ----------
    summary_df : pd.DataFrame
        Output from lacunarity_summary()
    
    Returns
    -------
    agg : dict
        {'small': Λ_mean, 'medium': Λ_mean, 'large': Λ_mean}
    """
    agg = summary_df.groupby('scale_category')['lacunarity'].mean().to_dict()
    return agg


# Example usage and testing
if __name__ == "__main__":
    # Create synthetic point pattern
    np.random.seed(42)
    
    # Clustered pattern (high lacunarity)
    n_clusters = 5
    points_per_cluster = 20
    cluster_centers = np.random.uniform(0, 1000, (n_clusters, 2))
    
    points_list = []
    for center in cluster_centers:
        cluster_points = np.random.normal(center, 50, (points_per_cluster, 2))
        points_list.extend(cluster_points)
    
    points_array = np.array(points_list)
    geometry = [Point(x, y) for x, y in points_array]
    gdf = gpd.GeoDataFrame(geometry=geometry, crs='EPSG:3857')
    
    # Calculate lacunarity
    lac = calculate_lacunarity(gdf)
    summary = lacunarity_summary(lac)
    
    print("Lacunarity Analysis Results:")
    print(summary)
    print("\nScale Aggregation:")
    print(lacunarity_scale_aggregation(summary))

