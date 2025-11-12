"""
Data loading and preprocessing utilities.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
import networkx as nx
from shapely.geometry import box, Point
import pickle
from scipy.spatial import cKDTree
import warnings


def load_points(
    filepath: str,
    crs: str = 'EPSG:3857',
    layer: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Load point data from GeoPackage or other geospatial formats.
    
    Parameters
    ----------
    filepath : str
        Path to point data file (*.gpkg, *.shp, *.geojson)
    crs : str
        Target CRS (default: EPSG:3857 - Web Mercator)
    layer : str, optional
        Layer name for multi-layer sources (e.g., GeoPackage)
    
    Returns
    -------
    points : gpd.GeoDataFrame
        Point geometries in target CRS
    """
    read_kwargs = {"layer": layer} if layer else {}
    gdf = gpd.read_file(filepath, **read_kwargs)
    
    # Reproject if necessary
    if gdf.crs is None:
        print(f"Warning: No CRS found. Assuming {crs}")
        gdf.set_crs(crs, inplace=True)
    elif gdf.crs.to_string() != crs:
        gdf = gdf.to_crs(crs)
    
    # Filter to Point geometries only
    if 'Point' not in gdf.geom_type.unique():
        # Try to convert to centroids
        print("Converting geometries to centroids...")
        gdf['geometry'] = gdf.geometry.centroid
    
    return gdf


def load_network(
    filepath: str,
    format: str = 'pickle'
) -> nx.Graph:
    """
    Load network from file.
    
    Parameters
    ----------
    filepath : str
        Path to network file
    format : str
        'pickle': NetworkX pickle format (*.gpickle)
        'edges': Edge list CSV
    
    Returns
    -------
    G : nx.Graph
        Network graph
    """
    if format == 'pickle':
        with open(filepath, 'rb') as f:
            G = pickle.load(f)
    elif format == 'edges':
        # Load edge list
        edges = pd.read_csv(filepath)
        G = nx.from_pandas_edgelist(
            edges,
            source='source',
            target='target',
            edge_attr='weight'
        )
    else:
        raise ValueError(f"Unknown format: {format}")
    
    return G


def create_analysis_tiles(
    bounds: Tuple[float, float, float, float],
    tile_size: float = 1000.0,
    crs: str = 'EPSG:3857'
) -> gpd.GeoDataFrame:
    """
    Create regular grid tiles for spatial analysis.
    
    Parameters
    ----------
    bounds : tuple
        (minx, miny, maxx, maxy) in target CRS
    tile_size : float
        Tile size in meters (default: 1 km)
    crs : str
        Coordinate reference system
    
    Returns
    -------
    tiles : gpd.GeoDataFrame
        Grid tiles with columns: tile_id, geometry
    """
    minx, miny, maxx, maxy = bounds
    
    # Generate grid
    x_coords = np.arange(minx, maxx, tile_size)
    y_coords = np.arange(miny, maxy, tile_size)
    
    tiles = []
    tile_id = 0
    
    for x in x_coords:
        for y in y_coords:
            tile_geom = box(x, y, x + tile_size, y + tile_size)
            tiles.append({
                'tile_id': tile_id,
                'x_min': x,
                'y_min': y,
                'geometry': tile_geom
            })
            tile_id += 1
    
    tiles_gdf = gpd.GeoDataFrame(tiles, crs=crs)
    
    return tiles_gdf


def filter_points_by_tile(
    points: gpd.GeoDataFrame,
    tile: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Filter points within a single tile.
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Point data
    tile : gpd.GeoDataFrame
        Single tile (one row)
    
    Returns
    -------
    filtered : gpd.GeoDataFrame
        Points within tile bounds
    """
    tile_geom = tile.geometry.iloc[0] if hasattr(tile.geometry, 'iloc') else tile.geometry
    
    # Spatial filter
    filtered = points[points.within(tile_geom)]
    
    return filtered


def _reset_and_preserve_crs(points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return a copy with reset index while keeping CRS information."""

    sampled = points.copy()
    sampled.reset_index(drop=True, inplace=True)
    if points.crs is not None:
        sampled.set_crs(points.crs, inplace=True)
    return sampled


def sample_points_random(
    points: gpd.GeoDataFrame,
    n_samples: int,
    random_state: Optional[int] = None
) -> gpd.GeoDataFrame:
    """Randomly sample point geometries without spatial bias."""

    if n_samples <= 0:
        raise ValueError("n_samples must be a positive integer")

    if len(points) <= n_samples:
        return _reset_and_preserve_crs(points)

    sampled = points.sample(n=n_samples, random_state=random_state).copy()
    sampled.reset_index(drop=True, inplace=True)
    if points.crs is not None:
        sampled.set_crs(points.crs, inplace=True)
    return sampled


def sample_points_spatial_grid(
    points: gpd.GeoDataFrame,
    cell_size: float,
    max_per_cell: int = 1,
    target_count: Optional[int] = None,
    random_state: Optional[int] = None
) -> gpd.GeoDataFrame:
    """Sample representative points from each spatial grid cell."""

    if cell_size <= 0:
        raise ValueError("cell_size must be positive")
    if max_per_cell <= 0:
        raise ValueError("max_per_cell must be positive")

    if len(points) == 0:
        return _reset_and_preserve_crs(points)

    coords = np.column_stack([
        points.geometry.x.values,
        points.geometry.y.values
    ])

    minx, miny, _, _ = points.total_bounds
    cell_x = np.floor((coords[:, 0] - minx) / cell_size).astype(int)
    cell_y = np.floor((coords[:, 1] - miny) / cell_size).astype(int)

    df = points.copy()
    df["__cell_x"] = cell_x
    df["__cell_y"] = cell_y

    rng = np.random.default_rng(random_state)
    selected_indices: List[int] = []

    for (_, group) in df.groupby(["__cell_x", "__cell_y"], sort=False):
        indices = group.index.to_numpy()
        if len(indices) <= max_per_cell:
            selected_indices.extend(indices.tolist())
        else:
            choice = rng.choice(indices, size=max_per_cell, replace=False)
            selected_indices.extend(choice.tolist())

    if target_count is not None and len(selected_indices) > target_count:
        selected_indices = rng.choice(
            selected_indices, size=target_count, replace=False
        ).tolist()

    sampled = points.loc[selected_indices].copy()
    df.drop(columns=["__cell_x", "__cell_y"], inplace=True, errors="ignore")
    sampled.reset_index(drop=True, inplace=True)
    if points.crs is not None:
        sampled.set_crs(points.crs, inplace=True)
    return sampled


def sample_points_uniform_spacing(
    points: gpd.GeoDataFrame,
    target_count: int,
    random_state: Optional[int] = None
) -> gpd.GeoDataFrame:
    """Sample points that are approximately evenly spaced over the extent."""

    if target_count <= 0:
        raise ValueError("target_count must be positive")

    n_points = len(points)
    if n_points <= target_count:
        return _reset_and_preserve_crs(points)

    bounds = points.total_bounds
    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    height = maxy - miny
    if width <= 0 or height <= 0:
        warnings.warn("Zero-area bounds detected; falling back to random sampling")
        return sample_points_random(points, target_count, random_state=random_state)

    area = width * height
    spacing = np.sqrt(area / target_count)
    spacing = max(spacing, 1e-9)

    grid_x = np.arange(minx, maxx + spacing, spacing)
    grid_y = np.arange(miny, maxy + spacing, spacing)
    gx, gy = np.meshgrid(grid_x, grid_y)
    grid_points = np.column_stack([gx.ravel(), gy.ravel()])

    coords = np.column_stack([
        points.geometry.x.values,
        points.geometry.y.values
    ])

    tree = cKDTree(coords)
    _, indices = tree.query(grid_points, k=1)
    unique_indices = np.unique(indices)

    if len(unique_indices) > target_count:
        rng = np.random.default_rng(random_state)
        unique_indices = rng.choice(unique_indices, size=target_count, replace=False)

    sampled = points.iloc[unique_indices].copy()
    sampled.reset_index(drop=True, inplace=True)
    if points.crs is not None:
        sampled.set_crs(points.crs, inplace=True)
    return sampled


def sample_points_density_based(
    points: gpd.GeoDataFrame,
    n_samples: int,
    k_neighbors: int = 8,
    random_state: Optional[int] = None
) -> gpd.GeoDataFrame:
    """Sample points favouring dense areas using k-nearest neighbour density."""

    if n_samples <= 0:
        raise ValueError("n_samples must be positive")

    if len(points) <= n_samples:
        return _reset_and_preserve_crs(points)

    if k_neighbors < 1:
        raise ValueError("k_neighbors must be at least 1")

    coords = np.column_stack([
        points.geometry.x.values,
        points.geometry.y.values
    ])

    tree = cKDTree(coords)
    k = min(k_neighbors + 1, len(points))
    distances, _ = tree.query(coords, k=k)

    if distances.ndim == 1:
        # Only one neighbour available (self)
        weights = np.ones(len(points), dtype=float)
    else:
        kth_distance = distances[:, -1]
        weights = 1.0 / (kth_distance + 1e-9)

    if np.all(weights == 0):
        warnings.warn("All density weights are zero; falling back to random sampling")
        return sample_points_random(points, n_samples, random_state=random_state)

    weights = np.nan_to_num(weights, nan=0.0)
    if weights.sum() == 0:
        warnings.warn("Density weights sum to zero; falling back to random sampling")
        return sample_points_random(points, n_samples, random_state=random_state)

    probabilities = weights / weights.sum()
    rng = np.random.default_rng(random_state)
    chosen_indices = rng.choice(
        np.arange(len(points)), size=n_samples, replace=False, p=probabilities
    )

    sampled = points.iloc[chosen_indices].copy()
    sampled.reset_index(drop=True, inplace=True)
    if points.crs is not None:
        sampled.set_crs(points.crs, inplace=True)
    return sampled


def prepare_sample_data(
    n_points: int = 500,
    pattern: str = 'random',
    bounds: Tuple[float, float, float, float] = (0, 0, 1000, 1000),
    seed: int = 42
) -> gpd.GeoDataFrame:
    """
    Generate synthetic point patterns for testing.
    
    Parameters
    ----------
    n_points : int
        Number of points
    pattern : str
        'singlelinear': Single linear pattern (points along a line)
        'uniform': Uniform distribution (grid-like with slight randomness)
        'random': Poisson random distribution
        'radial': Radial pattern (points radiating from center)
        'singleclustered': Single cluster (one large cluster)
        'multiclustered': Multiple clusters
    bounds : tuple
        (minx, miny, maxx, maxy)
    seed : int
        Random seed
    
    Returns
    -------
    points : gpd.GeoDataFrame
        Synthetic point pattern
    """
    np.random.seed(seed)
    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    height = maxy - miny
    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2
    
    if pattern == 'singlelinear':
        # Single linear pattern: points along a diagonal line
        # Line from bottom-left to top-right with some perpendicular noise
        t = np.linspace(0, 1, n_points)
        # Diagonal line
        x = minx + t * width
        y = miny + t * height
        # Add perpendicular noise
        noise_scale = min(width, height) / 50
        perp_x = -(y - center_y) / np.sqrt(width**2 + height**2)
        perp_y = (x - center_x) / np.sqrt(width**2 + height**2)
        noise = np.random.normal(0, noise_scale, n_points)
        x += perp_x * noise
        y += perp_y * noise
        coords = np.column_stack([x, y])
    
    elif pattern == 'uniform':
        # Uniform distribution: grid-like with slight randomness
        n_side = int(np.sqrt(n_points))
        x_spacing = width / n_side
        y_spacing = height / n_side
        x_base = np.linspace(minx + x_spacing/2, maxx - x_spacing/2, n_side)
        y_base = np.linspace(miny + y_spacing/2, maxy - y_spacing/2, n_side)
        xx, yy = np.meshgrid(x_base, y_base)
        # Flatten and take exactly n_points
        x_flat = xx.flatten()
        y_flat = yy.flatten()
        # If we have more points than needed, randomly sample
        if len(x_flat) > n_points:
            indices = np.random.choice(len(x_flat), n_points, replace=False)
            x_flat = x_flat[indices]
            y_flat = y_flat[indices]
        # If we have fewer points, pad with random points
        elif len(x_flat) < n_points:
            n_missing = n_points - len(x_flat)
            x_flat = np.concatenate([x_flat, np.random.uniform(minx, maxx, n_missing)])
            y_flat = np.concatenate([y_flat, np.random.uniform(miny, maxy, n_missing)])
        # Add small random perturbation
        noise_scale = min(x_spacing, y_spacing) / 4
        x = x_flat + np.random.normal(0, noise_scale, len(x_flat))
        y = y_flat + np.random.normal(0, noise_scale, len(y_flat))
        coords = np.column_stack([x, y])
    
    elif pattern == 'random':
        # Poisson random distribution
        x = np.random.uniform(minx, maxx, n_points)
        y = np.random.uniform(miny, maxy, n_points)
        coords = np.column_stack([x, y])
    
    elif pattern == 'radial':
        # Radial pattern: points radiating from center
        # Angular distribution
        angles = np.random.uniform(0, 2 * np.pi, n_points)
        # Radial distribution (exponential for more points near center)
        radii = np.random.exponential(scale=min(width, height) / 4, size=n_points)
        radii = np.clip(radii, 0, min(width, height) / 2)
        # Convert to Cartesian
        x = center_x + radii * np.cos(angles)
        y = center_y + radii * np.sin(angles)
        # Clip to bounds
        x = np.clip(x, minx, maxx)
        y = np.clip(y, miny, maxy)
        coords = np.column_stack([x, y])
    
    elif pattern == 'singleclustered':
        # Single large cluster
        cluster_center = np.array([center_x, center_y])
        cluster_std = min(width, height) / 8
        coords = np.random.normal(
            cluster_center,
            scale=cluster_std,
            size=(n_points, 2)
        )
        # Clip to bounds
        coords[:, 0] = np.clip(coords[:, 0], minx, maxx)
        coords[:, 1] = np.clip(coords[:, 1], miny, maxy)
    
    elif pattern == 'multiclustered':
        # Multiple clusters (similar to old 'clustered')
        n_clusters = int(np.sqrt(n_points) / 2)
        points_per_cluster = n_points // n_clusters
        remainder = n_points % n_clusters  # Handle remainder points
        
        # Cluster centers
        cx = np.random.uniform(minx, maxx, n_clusters)
        cy = np.random.uniform(miny, maxy, n_clusters)
        centers = np.column_stack([cx, cy])
        
        # Points around centers
        coords_list = []
        for i, center in enumerate(centers):
            # Distribute remainder points across first few clusters
            cluster_size = points_per_cluster + (1 if i < remainder else 0)
            cluster_points = np.random.normal(
                center,
                scale=(maxx - minx) / 20,
                size=(cluster_size, 2)
            )
            coords_list.append(cluster_points)
        
        coords = np.vstack(coords_list)
        # Clip to bounds
        coords[:, 0] = np.clip(coords[:, 0], minx, maxx)
        coords[:, 1] = np.clip(coords[:, 1], miny, maxy)
    
    else:
        raise ValueError(f"Unknown pattern: {pattern}. Supported patterns: "
                        f"singlelinear, uniform, random, radial, singleclustered, multiclustered")
    
    # Create GeoDataFrame
    geometry = [Point(x, y) for x, y in coords]
    gdf = gpd.GeoDataFrame(
        {'pattern': [pattern] * len(geometry)},
        geometry=geometry,
        crs='EPSG:3857'
    )
    
    return gdf


# Example usage
if __name__ == "__main__":
    # Test data generation
    points_clustered = prepare_sample_data(500, 'clustered')
    points_random = prepare_sample_data(500, 'random')
    
    print("Clustered pattern:")
    print(points_clustered.head())
    
    # Test tile creation
    tiles = create_analysis_tiles((0, 0, 2000, 2000), tile_size=500)
    print(f"\nCreated {len(tiles)} tiles")
    
    # Test filtering
    filtered = filter_points_by_tile(points_clustered, tiles.iloc[[0]])
    print(f"Points in first tile: {len(filtered)}")

