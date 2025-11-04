"""
Data loading and preprocessing utilities.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
import networkx as nx
from shapely.geometry import box, Point
import pickle


def load_points(
    filepath: str,
    crs: str = 'EPSG:3857'
) -> gpd.GeoDataFrame:
    """
    Load point data from GeoPackage or other geospatial formats.
    
    Parameters
    ----------
    filepath : str
        Path to point data file (*.gpkg, *.shp, *.geojson)
    crs : str
        Target CRS (default: EPSG:3857 - Web Mercator)
    
    Returns
    -------
    points : gpd.GeoDataFrame
        Point geometries in target CRS
    """
    gdf = gpd.read_file(filepath)
    
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


def prepare_sample_data(
    n_points: int = 500,
    pattern: str = 'clustered',
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
        'random': Poisson random
        'clustered': Hierarchical clusters
        'grid': Regular grid
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
    
    if pattern == 'random':
        x = np.random.uniform(minx, maxx, n_points)
        y = np.random.uniform(miny, maxy, n_points)
        coords = np.column_stack([x, y])
    
    elif pattern == 'clustered':
        n_clusters = int(np.sqrt(n_points) / 2)
        points_per_cluster = n_points // n_clusters
        
        # Cluster centers
        cx = np.random.uniform(minx, maxx, n_clusters)
        cy = np.random.uniform(miny, maxy, n_clusters)
        centers = np.column_stack([cx, cy])
        
        # Points around centers
        coords_list = []
        for center in centers:
            cluster_points = np.random.normal(
                center,
                scale=(maxx - minx) / 20,
                size=(points_per_cluster, 2)
            )
            coords_list.append(cluster_points)
        
        coords = np.vstack(coords_list)
    
    elif pattern == 'grid':
        n_side = int(np.sqrt(n_points))
        x = np.linspace(minx, maxx, n_side)
        y = np.linspace(miny, maxy, n_side)
        xx, yy = np.meshgrid(x, y)
        coords = np.column_stack([xx.flatten(), yy.flatten()])
    
    else:
        raise ValueError(f"Unknown pattern: {pattern}")
    
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

