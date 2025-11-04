"""
Plotting functions for OpenSparsity metrics visualization.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10


def plot_lacunarity(
    results: pd.DataFrame,
    output_file: Optional[str] = None,
    title: str = "Lacunarity Analysis",
    figsize: Tuple[float, float] = (10, 6)
) -> plt.Figure:
    """
    Plot lacunarity vs scale.
    
    Parameters
    ----------
    results : pd.DataFrame
        Lacunarity results with columns: scale_meters, lacunarity
    output_file : str, optional
        Save figure to file
    title : str
        Plot title
    figsize : tuple
        Figure size
    
    Returns
    -------
    fig : matplotlib.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot lacunarity curve
    ax.plot(
        results['scale_meters'],
        results['lacunarity'],
        marker='o',
        linewidth=2,
        markersize=6,
        color='#2E86AB',
        label='Lacunarity Λ(ε)'
    )
    
    # Add scale categories if present
    if 'scale_category' in results.columns:
        for category, color in [('small', '#A23B72'), ('medium', '#F18F01'), ('large', '#C73E1D')]:
            cat_data = results[results['scale_category'] == category]
            if len(cat_data) > 0:
                ax.axvspan(
                    cat_data['scale_meters'].min(),
                    cat_data['scale_meters'].max(),
                    alpha=0.1,
                    color=color,
                    label=f'{category.capitalize()} scale'
                )
    
    ax.set_xlabel('Scale (meters)', fontsize=12)
    ax.set_ylabel('Lacunarity Λ', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xscale('log')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_file}")
    
    return fig


def plot_percolation(
    results: pd.DataFrame,
    r_p: Optional[float] = None,
    output_file: Optional[str] = None,
    title: str = "Percolation Analysis",
    figsize: Tuple[float, float] = (12, 5)
) -> plt.Figure:
    """
    Plot percolation transition and network metrics.
    
    Parameters
    ----------
    results : pd.DataFrame
        Percolation results with columns: threshold, S1_ratio, avg_degree, etc.
    r_p : float, optional
        Percolation threshold to highlight
    output_file : str, optional
        Save figure to file
    title : str
        Plot title
    figsize : tuple
        Figure size
    
    Returns
    -------
    fig : matplotlib.Figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # Left panel: S1 ratio (percolation order parameter)
    ax1 = axes[0]
    ax1.plot(
        results['threshold'],
        results['S1_ratio'],
        marker='o',
        linewidth=2.5,
        markersize=7,
        color='#E63946',
        label='Largest component S₁/N'
    )
    
    # Mark percolation threshold
    if r_p is not None:
        ax1.axvline(r_p, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
        ax1.axhline(0.5, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
        ax1.plot(r_p, 0.5, 'ko', markersize=10, label=f'r_p = {r_p:.1f} m')
    
    ax1.set_xlabel('Distance threshold r (m)', fontsize=12)
    ax1.set_ylabel('S₁/N (connectivity ratio)', fontsize=12)
    ax1.set_title('Percolation Transition', fontsize=13, fontweight='bold')
    ax1.set_xscale('log')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best')
    
    # Right panel: Network metrics
    ax2 = axes[1]
    ax2_twin = ax2.twinx()
    
    # Average degree
    line1 = ax2.plot(
        results['threshold'],
        results['avg_degree'],
        marker='s',
        linewidth=2,
        markersize=5,
        color='#457B9D',
        label='Average degree ⟨k⟩'
    )
    
    # Clustering coefficient
    line2 = ax2_twin.plot(
        results['threshold'],
        results['clustering'],
        marker='^',
        linewidth=2,
        markersize=5,
        color='#F4A261',
        label='Clustering C'
    )
    
    ax2.set_xlabel('Distance threshold r (m)', fontsize=12)
    ax2.set_ylabel('Average degree ⟨k⟩', fontsize=12, color='#457B9D')
    ax2_twin.set_ylabel('Clustering C', fontsize=12, color='#F4A261')
    ax2.set_title('Network Topology', fontsize=13, fontweight='bold')
    ax2.set_xscale('log')
    ax2.grid(True, alpha=0.3)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc='best')
    
    fig.suptitle(title, fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_file}")
    
    return fig


def plot_multifractal(
    results: pd.DataFrame,
    output_file: Optional[str] = None,
    title: str = "Multifractal Analysis",
    figsize: Tuple[float, float] = (12, 5)
) -> plt.Figure:
    """
    Plot multifractal spectrum: D(q) and f(α).
    
    Parameters
    ----------
    results : pd.DataFrame
        Multifractal results with columns: q, D_q, alpha, f_alpha
    output_file : str, optional
        Save figure to file
    title : str
        Plot title
    figsize : tuple
        Figure size
    
    Returns
    -------
    fig : matplotlib.Figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # Filter valid data
    df = results.dropna()
    
    # Left panel: D(q) spectrum
    ax1 = axes[0]
    ax1.plot(
        df['q'],
        df['D_q'],
        marker='o',
        linewidth=2.5,
        markersize=7,
        color='#6A4C93',
        label='D(q)'
    )
    
    # Mark key dimensions
    for q_val, label, color in [(0, 'D₀', '#E63946'), (2, 'D₂', '#F4A261')]:
        if q_val in df['q'].values:
            D_val = df[df['q'] == q_val]['D_q'].values[0]
            ax1.plot(q_val, D_val, 'o', markersize=10, color=color, label=f'{label} = {D_val:.3f}')
    
    ax1.set_xlabel('Moment order q', fontsize=12)
    ax1.set_ylabel('Generalized dimension D(q)', fontsize=12)
    ax1.set_title('Dimension Spectrum', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best')
    
    # Right panel: f(α) spectrum
    ax2 = axes[1]
    ax2.plot(
        df['alpha'],
        df['f_alpha'],
        marker='o',
        linewidth=2.5,
        markersize=7,
        color='#1D3557',
        label='f(α)'
    )
    
    # Mark spectrum width
    alpha_min, alpha_max = df['alpha'].min(), df['alpha'].max()
    Delta_alpha = alpha_max - alpha_min
    ax2.axvline(alpha_min, color='gray', linestyle='--', alpha=0.5)
    ax2.axvline(alpha_max, color='gray', linestyle='--', alpha=0.5)
    ax2.text(
        (alpha_min + alpha_max) / 2,
        ax2.get_ylim()[1] * 0.9,
        f'Δα = {Delta_alpha:.3f}',
        ha='center',
        fontsize=11,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    ax2.set_xlabel('Singularity strength α', fontsize=12)
    ax2.set_ylabel('f(α)', fontsize=12)
    ax2.set_title('Singularity Spectrum', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='best')
    
    fig.suptitle(title, fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_file}")
    
    return fig


def plot_combined_metrics(
    lacunarity_df: pd.DataFrame,
    percolation_df: pd.DataFrame,
    multifractal_df: pd.DataFrame,
    output_file: Optional[str] = None,
    title: str = "OpenSparsity Three-Layer Analysis",
    figsize: Tuple[float, float] = (15, 10)
) -> plt.Figure:
    """
    Combined visualization of all three metrics.
    
    Parameters
    ----------
    lacunarity_df : pd.DataFrame
        Lacunarity results
    percolation_df : pd.DataFrame
        Percolation results
    multifractal_df : pd.DataFrame
        Multifractal results
    output_file : str, optional
        Save figure to file
    title : str
        Overall title
    figsize : tuple
        Figure size
    
    Returns
    -------
    fig : matplotlib.Figure
    """
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # Row 1: Individual metrics
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    
    # Row 2: Combined view
    ax4 = fig.add_subplot(gs[1, :])
    
    # Plot 1: Lacunarity
    ax1.plot(lacunarity_df['scale_meters'], lacunarity_df['lacunarity'],
             marker='o', linewidth=2, color='#2E86AB', label='Λ(ε)')
    ax1.set_xlabel('Scale ε (m)', fontsize=10)
    ax1.set_ylabel('Lacunarity Λ', fontsize=10)
    ax1.set_title('Local Vacancy Structure', fontsize=11, fontweight='bold')
    ax1.set_xscale('log')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot 2: Percolation
    ax2.plot(percolation_df['threshold'], percolation_df['S1_ratio'],
             marker='o', linewidth=2, color='#E63946', label='S₁/N')
    ax2.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Threshold r (m)', fontsize=10)
    ax2.set_ylabel('Connectivity S₁/N', fontsize=10)
    ax2.set_title('Critical Connectivity', fontsize=11, fontweight='bold')
    ax2.set_xscale('log')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Plot 3: Multifractal
    mf_df = multifractal_df.dropna()
    ax3.plot(mf_df['alpha'], mf_df['f_alpha'],
             marker='o', linewidth=2, color='#6A4C93', label='f(α)')
    ax3.set_xlabel('Singularity α', fontsize=10)
    ax3.set_ylabel('f(α)', fontsize=10)
    ax3.set_title('Hierarchical Structure', fontsize=11, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Plot 4: Cross-scale comparison (parallel coordinates style)
    # Normalize all metrics to [0, 1] for comparison
    scales = lacunarity_df['scale_meters'].values
    lac_norm = (lacunarity_df['lacunarity'] - lacunarity_df['lacunarity'].min()) / \
               (lacunarity_df['lacunarity'].max() - lacunarity_df['lacunarity'].min())
    
    ax4.plot(scales, lac_norm, marker='o', linewidth=2, color='#2E86AB', 
             label='Lacunarity (normalized)', alpha=0.7)
    
    # Align percolation on same scale axis
    perc_scales = percolation_df['threshold'].values
    perc_norm = percolation_df['S1_ratio'].values
    ax4.plot(perc_scales, perc_norm, marker='s', linewidth=2, color='#E63946',
             label='Connectivity S₁/N', alpha=0.7)
    
    ax4.set_xlabel('Scale / Threshold (m)', fontsize=11)
    ax4.set_ylabel('Normalized metric value', fontsize=11)
    ax4.set_title('Cross-Scale Integration', fontsize=12, fontweight='bold')
    ax4.set_xscale('log')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='best')
    
    # Overall title
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    
    if output_file:
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_file}")
    
    return fig


def plot_comparison_matrix(
    results_dict: Dict[str, Dict],
    metric: str = 'lacunarity',
    output_file: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 8)
) -> plt.Figure:
    """
    Compare multiple patterns side-by-side.
    
    Parameters
    ----------
    results_dict : dict
        {pattern_name: {metric: DataFrame}}
    metric : str
        Metric to compare ('lacunarity', 'percolation', 'multifractal')
    output_file : str, optional
        Save figure to file
    figsize : tuple
        Figure size
    
    Returns
    -------
    fig : matplotlib.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    colors = sns.color_palette("husl", len(results_dict))
    
    for i, (pattern, results) in enumerate(results_dict.items()):
        df = results.get(metric)
        if df is None:
            continue
        
        if metric == 'lacunarity':
            ax.plot(df['scale_meters'], df['lacunarity'],
                   marker='o', linewidth=2, label=pattern, color=colors[i])
            ax.set_xlabel('Scale (m)')
            ax.set_ylabel('Lacunarity Λ')
        
        elif metric == 'percolation':
            ax.plot(df['threshold'], df['S1_ratio'],
                   marker='o', linewidth=2, label=pattern, color=colors[i])
            ax.set_xlabel('Threshold r (m)')
            ax.set_ylabel('S₁/N')
        
        elif metric == 'multifractal':
            df_valid = df.dropna()
            ax.plot(df_valid['alpha'], df_valid['f_alpha'],
                   marker='o', linewidth=2, label=pattern, color=colors[i])
            ax.set_xlabel('α')
            ax.set_ylabel('f(α)')
    
    ax.set_title(f'{metric.capitalize()} Comparison', fontsize=14, fontweight='bold')
    ax.set_xscale('log')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    
    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_file}")
    
    return fig


# Example usage
if __name__ == "__main__":
    # Test with synthetic data
    lac_df = pd.DataFrame({
        'scale_meters': [10, 25, 50, 100, 200, 400],
        'lacunarity': [1.1, 1.3, 1.6, 1.9, 2.1, 2.3],
        'scale_category': ['small', 'small', 'medium', 'medium', 'large', 'large']
    })
    
    perc_df = pd.DataFrame({
        'threshold': [10, 25, 50, 100, 200, 400, 800],
        'S1_ratio': [0.05, 0.12, 0.35, 0.68, 0.92, 0.98, 1.0],
        'avg_degree': [0.5, 1.2, 2.5, 4.8, 8.2, 12.5, 18.3],
        'clustering': [0, 0.1, 0.25, 0.42, 0.55, 0.62, 0.68]
    })
    
    mf_df = pd.DataFrame({
        'q': [-3, -2, -1, 0, 1, 2, 3],
        'D_q': [1.95, 1.85, 1.72, 1.58, 1.45, 1.32, 1.18],
        'alpha': [1.2, 1.35, 1.5, 1.65, 1.8, 1.95, 2.1],
        'f_alpha': [0.8, 1.3, 1.6, 1.65, 1.6, 1.3, 0.8]
    })
    
    # Test plots
    fig1 = plot_lacunarity(lac_df, title="Test Lacunarity")
    fig2 = plot_percolation(perc_df, r_p=95, title="Test Percolation")
    fig3 = plot_multifractal(mf_df, title="Test Multifractal")
    fig4 = plot_combined_metrics(lac_df, perc_df, mf_df)
    
    plt.show()

