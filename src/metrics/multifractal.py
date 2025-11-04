"""
Multifractal Analysis Module

Quantifies hierarchical scale structure in spatial distributions.
Based on Halsey et al. (1986) and Murcio et al. (2015).

Multifractal analysis reveals:
- D(q): Generalized fractal dimensions
- f(α): Singularity spectrum
- Δα: Hierarchical diversity (spectrum width)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import geopandas as gpd
import pandas as pd
from scipy import stats, interpolate
from tqdm import tqdm


def box_counting_probabilities(
    points: gpd.GeoDataFrame,
    box_size: float,
    bounds: Optional[Tuple[float, float, float, float]] = None
) -> np.ndarray:
    """
    Calculate point density probabilities in grid boxes.
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Point locations
    box_size : float
        Grid cell size (epsilon) in meters
    bounds : tuple, optional
        (minx, miny, maxx, maxy)
    
    Returns
    -------
    probabilities : np.ndarray
        Normalized density p_i where sum(p_i) = 1
    """
    if bounds is None:
        bounds = points.total_bounds
    
    minx, miny, maxx, maxy = bounds
    
    # Create grid
    x_edges = np.arange(minx, maxx + box_size, box_size)
    y_edges = np.arange(miny, maxy + box_size, box_size)
    
    # Extract coordinates
    coords = np.array([[geom.x, geom.y] for geom in points.geometry])
    
    # Count points in each box
    counts, _, _ = np.histogram2d(
        coords[:, 0], coords[:, 1],
        bins=[x_edges, y_edges]
    )
    
    # Flatten and normalize to probabilities
    counts_flat = counts.flatten()
    counts_flat = counts_flat[counts_flat > 0]  # Remove empty boxes
    
    if len(counts_flat) == 0:
        return np.array([])
    
    probabilities = counts_flat / counts_flat.sum()
    
    return probabilities


def calculate_moment_sum(probabilities: np.ndarray, q: float) -> float:
    """
    Calculate moment sum: χ(q, ε) = Σ p_i^q
    
    Parameters
    ----------
    probabilities : np.ndarray
        Box probabilities
    q : float
        Moment order
    
    Returns
    -------
    moment_sum : float
        Σ p_i^q
    """
    if len(probabilities) == 0:
        return np.nan
    
    # Handle q = 1 separately (information dimension)
    if np.abs(q - 1.0) < 1e-10:
        # χ(1, ε) = Σ p_i * log(p_i)
        moment_sum = -np.sum(probabilities * np.log(probabilities))
    else:
        moment_sum = np.sum(probabilities ** q)
    
    return moment_sum


def calculate_tau_q(
    points: gpd.GeoDataFrame,
    q_values: List[float],
    box_sizes: Optional[List[float]] = None,
    bounds: Optional[Tuple[float, float, float, float]] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate mass exponent τ(q) from scaling of moment sums.
    
    τ(q) = lim[ε→0] log(χ(q,ε)) / log(ε)
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Point distribution
    q_values : list of float
        Moment orders (e.g., [-5, -3, -1, 0, 1, 2, 3, 5])
    box_sizes : list of float, optional
        Grid sizes in meters
        Default: [10, 25, 50, 100, 200, 400, 800, 1000]
    bounds : tuple, optional
        Analysis bounds
    
    Returns
    -------
    tau : np.ndarray
        Mass exponents τ(q)
    q : np.ndarray
        Corresponding q values
    """
    if box_sizes is None:
        box_sizes = [10, 25, 50, 100, 200, 400, 800, 1000]
    
    tau_values = []
    
    for q in tqdm(q_values, desc="Multifractal τ(q)"):
        moment_sums = []
        valid_sizes = []
        
        for epsilon in box_sizes:
            probs = box_counting_probabilities(points, epsilon, bounds)
            if len(probs) > 0:
                chi = calculate_moment_sum(probs, q)
                if not np.isnan(chi) and chi > 0:
                    moment_sums.append(chi)
                    valid_sizes.append(epsilon)
        
        if len(moment_sums) >= 3:
            # Linear regression: log(χ) vs log(ε)
            log_epsilon = np.log(valid_sizes)
            log_chi = np.log(moment_sums)
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(log_epsilon, log_chi)
            tau_values.append(slope)
        else:
            tau_values.append(np.nan)
    
    return np.array(tau_values), np.array(q_values)


def calculate_D_q(tau: np.ndarray, q: np.ndarray) -> np.ndarray:
    """
    Calculate generalized dimensions D(q) from τ(q).
    
    D(q) = τ(q) / (q - 1)
    
    Parameters
    ----------
    tau : np.ndarray
        Mass exponents
    q : np.ndarray
        Moment orders
    
    Returns
    -------
    D_q : np.ndarray
        Generalized fractal dimensions
    """
    D_q = np.zeros_like(tau)
    
    for i, (t, qi) in enumerate(zip(tau, q)):
        if np.abs(qi - 1.0) < 1e-10:
            # D(1) requires special treatment (information dimension)
            # Typically computed separately; here we use limiting value
            D_q[i] = np.nan  # Placeholder
        else:
            D_q[i] = t / (qi - 1.0)
    
    return D_q


def calculate_multifractal_spectrum(
    points: gpd.GeoDataFrame,
    q_values: Optional[List[float]] = None,
    box_sizes: Optional[List[float]] = None,
    bounds: Optional[Tuple[float, float, float, float]] = None
) -> pd.DataFrame:
    """
    Complete multifractal analysis: D(q) and f(α) spectrum.
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Point distribution
    q_values : list of float, optional
        Moment orders (default: -5 to +5)
    box_sizes : list of float, optional
        Box sizes in meters
    bounds : tuple, optional
        Analysis bounds
    
    Returns
    -------
    results : pd.DataFrame
        Columns: q, tau_q, D_q, alpha, f_alpha
    """
    if q_values is None:
        q_values = [-5, -3, -2, -1, -0.5, 0, 0.5, 1, 1.5, 2, 3, 5]
    
    # Calculate τ(q)
    tau, q = calculate_tau_q(points, q_values, box_sizes, bounds)
    
    # Calculate D(q)
    D_q = calculate_D_q(tau, q)
    
    # Legendre transform to get f(α) spectrum
    # α(q) = dτ/dq
    # f(α) = q·α - τ(q)
    
    # Filter out NaN values for interpolation
    valid_mask = ~(np.isnan(tau) | np.isnan(q))
    if np.sum(valid_mask) < 3:
        # Not enough valid points, use simple gradient
        alpha = np.gradient(tau, q)
    else:
        # Use spline interpolation for smoother derivative
        q_valid = q[valid_mask]
        tau_valid = tau[valid_mask]
        
        # Sort by q for interpolation
        sort_idx = np.argsort(q_valid)
        q_sorted = q_valid[sort_idx]
        tau_sorted = tau_valid[sort_idx]
        
        # Create spline interpolation (cubic for smoothness)
        try:
            # Use cubic spline if enough points
            if len(q_sorted) >= 4:
                spline = interpolate.CubicSpline(q_sorted, tau_sorted, bc_type='natural')
                # Calculate derivative analytically
                alpha_sorted = spline(q_sorted, nu=1)
            else:
                # Fallback to linear interpolation
                spline = interpolate.interp1d(q_sorted, tau_sorted, kind='linear', 
                                             fill_value='extrapolate')
                alpha_sorted = np.gradient(tau_sorted, q_sorted)
            
            # Map back to original q order
            alpha_interp = interpolate.interp1d(q_sorted, alpha_sorted, 
                                               kind='linear', fill_value='extrapolate')
            alpha = alpha_interp(q)
            
            # Ensure alpha values are reasonable (typically 0 < α < 2 for 2D)
            alpha = np.clip(alpha, 0.1, 3.0)
            
        except Exception as e:
            # Fallback to gradient if spline fails
            print(f"Warning: Spline interpolation failed, using gradient: {e}")
            alpha = np.gradient(tau, q)
    
    f_alpha = q * alpha - tau
    
    # Ensure f(α) is reasonable (should be ≤ 2 for 2D space)
    f_alpha = np.clip(f_alpha, 0, 2.5)
    
    # Create results DataFrame
    results = pd.DataFrame({
        'q': q,
        'tau_q': tau,
        'D_q': D_q,
        'alpha': alpha,
        'f_alpha': f_alpha
    })
    
    return results


def multifractal_summary(results: pd.DataFrame) -> Dict[str, float]:
    """
    Summarize multifractal analysis.
    
    Parameters
    ----------
    results : pd.DataFrame
        Output from calculate_multifractal_spectrum()
    
    Returns
    -------
    summary : dict
        - 'D0': Box-counting dimension (capacity)
        - 'D1': Information dimension
        - 'D2': Correlation dimension
        - 'alpha_min': Minimum singularity
        - 'alpha_max': Maximum singularity
        - 'Delta_alpha': Spectrum width (hierarchical diversity)
        - 'f_alpha_max': Maximum f(α)
    """
    # Filter valid results
    df = results.dropna()
    
    # Extract key dimensions
    D0 = df[df['q'] == 0]['D_q'].values[0] if 0 in df['q'].values else np.nan
    D1 = df[df['q'] == 1]['D_q'].values[0] if 1 in df['q'].values else np.nan
    D2 = df[df['q'] == 2]['D_q'].values[0] if 2 in df['q'].values else np.nan
    
    # Spectrum characteristics
    alpha_min = df['alpha'].min()
    alpha_max = df['alpha'].max()
    Delta_alpha = alpha_max - alpha_min
    f_alpha_max = df['f_alpha'].max()
    
    return {
        'D0': D0,
        'D1': D1,
        'D2': D2,
        'alpha_min': alpha_min,
        'alpha_max': alpha_max,
        'Delta_alpha': Delta_alpha,
        'f_alpha_max': f_alpha_max
    }


def calculate_multifractal(
    points: gpd.GeoDataFrame,
    q_values: Optional[List[float]] = None,
    box_sizes: Optional[List[float]] = None
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Convenience function for complete multifractal analysis.
    
    Parameters
    ----------
    points : gpd.GeoDataFrame
        Point distribution
    q_values : list of float, optional
        Moment orders
    box_sizes : list of float, optional
        Box sizes in meters
    
    Returns
    -------
    spectrum : pd.DataFrame
        Full multifractal spectrum
    summary : dict
        Key summary statistics
    """
    spectrum = calculate_multifractal_spectrum(points, q_values, box_sizes)
    summary = multifractal_summary(spectrum)
    
    return spectrum, summary


# Example usage and testing
if __name__ == "__main__":
    # Create synthetic multifractal point pattern
    np.random.seed(42)
    
    # Hierarchical clustered pattern
    n_clusters = 10
    points_per_cluster = 50
    cluster_centers = np.random.uniform(0, 1000, (n_clusters, 2))
    
    points_list = []
    for center in cluster_centers:
        # Multi-scale structure
        for scale in [20, 50, 100]:
            n = points_per_cluster // 3
            cluster_points = np.random.normal(center, scale, (n, 2))
            points_list.extend(cluster_points)
    
    from shapely.geometry import Point
    points_array = np.array(points_list)
    geometry = [Point(x, y) for x, y in points_array]
    gdf = gpd.GeoDataFrame(geometry=geometry, crs='EPSG:3857')
    
    # Calculate multifractal spectrum
    spectrum, summary = calculate_multifractal(gdf)
    
    print("Multifractal Spectrum:")
    print(spectrum)
    print("\nSummary Statistics:")
    for key, value in summary.items():
        print(f"{key}: {value:.4f}")

