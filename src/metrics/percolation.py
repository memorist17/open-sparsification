"""
Percolation Analysis Module

Quantifies critical connectivity structure in spatial networks.
Based on Makse et al. (1998) and Arcaute et al. (2016).

Percolation measures connectivity as a function of distance threshold:
- Small r_p: High permeability (connects easily)
- Large r_p: Low permeability (fragmented)
"""

import numpy as np
import networkx as nx
from typing import Dict, Iterable, List, Tuple, Optional
import geopandas as gpd
from shapely.geometry import Point, LineString
import pandas as pd
from scipy.spatial import Delaunay
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Point-based percolation (existing implementation)
# ---------------------------------------------------------------------------


def build_distance_network(
    points: gpd.GeoDataFrame,
    threshold: float,
    method: str = 'radius'
) -> nx.Graph:
    """
    Build network based on distance threshold.
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Node locations
    threshold : float
        Distance threshold in meters
    method : str
        'radius': Connect all nodes within threshold
        'knn': Connect k nearest neighbors (not implemented)
    
    Returns
    -------
    G : nx.Graph
        Network with nodes within threshold distance connected
    """
    G = nx.Graph()
    
    # Extract coordinates
    coords = np.array([[geom.x, geom.y] for geom in points.geometry])
    n = len(coords)
    
    # Add nodes
    for i in range(n):
        G.add_node(i, pos=coords[i])
    
    # Add edges based on distance
    if method == 'radius':
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(coords[i] - coords[j])
                if dist <= threshold:
                    G.add_edge(i, j, weight=dist)
    
    return G


def calculate_percolation_metrics(G: nx.Graph) -> Dict[str, float]:
    """
    Calculate network connectivity metrics.
    
    Parameters
    ----------
    G : nx.Graph
        Input network
    
    Returns
    -------
    metrics : dict
        - 'S1_ratio': Largest connected component ratio
        - 'n_components': Number of connected components
        - 'avg_degree': Average node degree
        - 'clustering': Average clustering coefficient
        - 'avg_path_length': Average shortest path length (if connected)
    """
    n = G.number_of_nodes()
    
    if n == 0:
        return {
            'S1_ratio': 0.0,
            'n_components': 0,
            'avg_degree': 0.0,
            'clustering': 0.0,
            'avg_path_length': np.nan
        }
    
    # Largest connected component
    components = list(nx.connected_components(G))
    if components:
        largest_cc = max(components, key=len)
        S1_ratio = len(largest_cc) / n
    else:
        S1_ratio = 0.0
    
    # Number of components
    n_components = len(components)
    
    # Average degree
    degrees = [deg for node, deg in G.degree()]
    avg_degree = np.mean(degrees) if degrees else 0.0
    
    # Clustering coefficient
    clustering = nx.average_clustering(G) if G.number_of_edges() > 0 else 0.0
    
    # Average path length (only for largest component if graph is disconnected)
    if nx.is_connected(G):
        avg_path_length = nx.average_shortest_path_length(G)
    elif len(largest_cc) > 1:
        G_sub = G.subgraph(largest_cc)
        avg_path_length = nx.average_shortest_path_length(G_sub)
    else:
        avg_path_length = np.nan
    
    return {
        'S1_ratio': S1_ratio,
        'n_components': n_components,
        'avg_degree': avg_degree,
        'clustering': clustering,
        'avg_path_length': avg_path_length
    }


def calculate_percolation(
    points: gpd.GeoDataFrame,
    thresholds: Optional[List[float]] = None,
    method: str = 'radius'
) -> pd.DataFrame:
    """
    Calculate percolation transition across distance thresholds.
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Node locations
    thresholds : list of float, optional
        Distance thresholds in meters
        Default: [10, 25, 50, 100, 200, 400, 800]
    method : str
        Network construction method ('radius' or 'knn')
    
    Returns
    -------
    results : pd.DataFrame
        Columns: threshold, S1_ratio, n_components, avg_degree, 
                 clustering, avg_path_length
    """
    if thresholds is None:
        thresholds = [10, 25, 50, 100, 200, 400, 800]
    
    results = []
    
    for r in tqdm(thresholds, desc="Percolation analysis"):
        G = build_distance_network(points, r, method=method)
        metrics = calculate_percolation_metrics(G)
        
        results.append({
            'threshold': r,
            **metrics
        })
    
    return pd.DataFrame(results)


def calculate_percolation_network(
    num_nodes: int,
    weighted_edges: Iterable[Tuple[int, int, float]],
    thresholds: Optional[List[float]] = None,
) -> pd.DataFrame:
    """Calculate percolation transition on a weighted network using union-find.

    Parameters
    ----------
    num_nodes : int
        Number of nodes in the network.
    weighted_edges : iterable of tuple
        Iterable of edges as ``(u, v, length)`` with ``length`` in meters.
    thresholds : list of float, optional
        Distance thresholds in meters. When omitted, unique edge lengths are used.

    Returns
    -------
    pd.DataFrame
        Per-threshold metrics (S1 ratio, component count, average degree, etc.).
    """

    if num_nodes <= 0:
        raise ValueError("num_nodes must be positive for network percolation analysis.")

    edges = [(int(u), int(v), float(w)) for u, v, w in weighted_edges]
    if not edges:
        thresholds = sorted(set(thresholds or []))
        if not thresholds:
            raise ValueError("At least one threshold or edge is required for analysis.")
        empty_metrics = {
            "threshold": thresholds,
            "S1_ratio": [0.0] * len(thresholds),
            "n_components": [num_nodes] * len(thresholds),
            "avg_degree": [0.0] * len(thresholds),
            "clustering": [np.nan] * len(thresholds),
            "avg_path_length": [np.nan] * len(thresholds),
        }
        return pd.DataFrame(empty_metrics)

    if thresholds is None:
        thresholds = sorted({edge[2] for edge in edges})
    else:
        thresholds = sorted(thresholds)

    edges_sorted = sorted(edges, key=lambda e: e[2])

    parent = list(range(num_nodes))
    size = [1] * num_nodes
    components = num_nodes
    largest_size = 1
    active_edges = 0

    results = {
        "threshold": [],
        "S1_ratio": [],
        "n_components": [],
        "avg_degree": [],
        "clustering": [],
        "avg_path_length": [],
    }

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> bool:
        nonlocal largest_size, components
        root_x = find(x)
        root_y = find(y)
        if root_x == root_y:
            return False
        if size[root_x] < size[root_y]:
            root_x, root_y = root_y, root_x
        parent[root_y] = root_x
        size[root_x] += size[root_y]
        largest_size = max(largest_size, size[root_x])
        components -= 1
        return True

    edge_index = 0
    num_edges = len(edges_sorted)

    for threshold in thresholds:
        while edge_index < num_edges and edges_sorted[edge_index][2] <= threshold:
            u, v, _ = edges_sorted[edge_index]
            union(u, v)
            active_edges += 1
            edge_index += 1

        s1_ratio = largest_size / num_nodes
        avg_degree = (2.0 * active_edges) / num_nodes if num_nodes > 0 else 0.0

        results["threshold"].append(float(threshold))
        results["S1_ratio"].append(s1_ratio)
        results["n_components"].append(components)
        results["avg_degree"].append(avg_degree)
        results["clustering"].append(np.nan)
        results["avg_path_length"].append(np.nan)

    return pd.DataFrame(results)


def find_percolation_threshold(results: pd.DataFrame, target_ratio: float = 0.5) -> float:
    """
    Find distance threshold where S1_ratio reaches target (percolation threshold).
    
    Parameters
    ----------
    results : pd.DataFrame
        Output from calculate_percolation()
    target_ratio : float
        Target S1_ratio (default: 0.5)
    
    Returns
    -------
    r_p : float
        Percolation threshold distance
    """
    # Interpolate to find threshold
    df = results.sort_values('threshold')
    
    # Find crossing point
    below = df[df['S1_ratio'] < target_ratio]
    above = df[df['S1_ratio'] >= target_ratio]
    
    if len(below) == 0:
        return df['threshold'].min()
    if len(above) == 0:
        return df['threshold'].max()
    
    # Linear interpolation
    r1 = below.iloc[-1]['threshold']
    r2 = above.iloc[0]['threshold']
    s1 = below.iloc[-1]['S1_ratio']
    s2 = above.iloc[0]['S1_ratio']
    
    if s2 - s1 > 0:
        r_p = r1 + (target_ratio - s1) * (r2 - r1) / (s2 - s1)
    else:
        r_p = r1
    
    return r_p


def percolation_summary(results: pd.DataFrame) -> Dict[str, float]:
    """
    Summarize percolation analysis results.
    
    Parameters
    ----------
    results : pd.DataFrame
        Output from calculate_percolation()
    
    Returns
    -------
    summary : dict
        - 'r_p': Percolation threshold (r where S1_ratio = 0.5)
        - 'max_S1_ratio': Maximum connectivity achieved
        - 'critical_degree': Average degree at r_p
    """
    r_p = find_percolation_threshold(results, target_ratio=0.5)
    max_S1 = results['S1_ratio'].max()
    
    # Find metrics at r_p (interpolate)
    df = results.sort_values('threshold')
    idx = np.searchsorted(df['threshold'].values, r_p)
    
    if idx > 0 and idx < len(df):
        # Interpolate degree at r_p
        r1, r2 = df.iloc[idx-1]['threshold'], df.iloc[idx]['threshold']
        d1, d2 = df.iloc[idx-1]['avg_degree'], df.iloc[idx]['avg_degree']
        critical_degree = d1 + (r_p - r1) * (d2 - d1) / (r2 - r1)
    else:
        critical_degree = np.nan
    
    return {
        'r_p': r_p,
        'max_S1_ratio': max_S1,
        'critical_degree': critical_degree
    }


def build_delaunay_network(points: gpd.GeoDataFrame) -> nx.Graph:
    """
    Build Delaunay triangulation network.
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Point locations
    
    Returns
    -------
    G : nx.Graph
        Delaunay network with edge weights as Euclidean distances
    """
    coords = np.array([[geom.x, geom.y] for geom in points.geometry])
    
    G = nx.Graph()
    for i, coord in enumerate(coords):
        G.add_node(i, pos=coord)
    
    # Compute Delaunay triangulation
    tri = Delaunay(coords)
    
    # Add edges
    for simplex in tri.simplices:
        for i in range(3):
            j = (i + 1) % 3
            node1, node2 = simplex[i], simplex[j]
            dist = np.linalg.norm(coords[node1] - coords[node2])
            G.add_edge(node1, node2, weight=dist)
    
    return G


# Example usage and testing
if __name__ == "__main__":
    # Create synthetic point pattern
    np.random.seed(42)
    
    # Random points
    n_points = 100
    coords = np.random.uniform(0, 1000, (n_points, 2))
    geometry = [Point(x, y) for x, y in coords]
    gdf = gpd.GeoDataFrame(geometry=geometry, crs='EPSG:3857')
    
    # Calculate percolation
    results = calculate_percolation(gdf)
    
    print("Percolation Analysis Results:")
    print(results)
    print("\nSummary:")
    print(percolation_summary(results))

