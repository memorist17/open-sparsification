#!/usr/bin/env python3
"""
OpenSparsity Metrics — Interactive Dashboard

Web-based dashboard for exploring three-indicator analysis results.
Uses Dash/Plotly for interactive visualization.

Usage:
    python dashboard.py [--port 8050] [--data demo_output]
"""

import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Dash imports
import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


def load_pattern_results(pattern_dir):
    """Load results for a single pattern."""
    pattern_dir = Path(pattern_dir)
    
    results = {
        'pattern_name': pattern_dir.name
    }
    
    # Load CSV files
    for metric in ['lacunarity', 'percolation', 'multifractal']:
        csv_file = pattern_dir / f'{pattern_dir.name}_{metric}.csv'
        if not csv_file.exists():
            csv_file = pattern_dir / f'{metric}.csv'
        
        if csv_file.exists():
            results[metric] = pd.read_csv(csv_file)
    
    # Load JSON summaries
    for metric in ['lacunarity_aggregation', 'percolation_summary', 
                   'multifractal_summary', 'summary']:
        json_file = pattern_dir / f'{pattern_dir.name}_{metric}.json'
        if not json_file.exists():
            json_file = pattern_dir / f'{metric}.json'
        
        if json_file.exists():
            with open(json_file, 'r') as f:
                results[metric] = json.load(f)
    
    # If summary.json exists but 'summary' key is not set, use the summary file content directly
    summary_file = pattern_dir / f'{pattern_dir.name}_summary.json'
    if not summary_file.exists():
        summary_file = pattern_dir / 'summary.json'
    
    if summary_file.exists() and 'summary' not in results:
        with open(summary_file, 'r') as f:
            results['summary'] = json.load(f)
    
    # Load point data if available (for spatial visualization)
    try:
        import geopandas as gpd
        point_file = pattern_dir / f'{pattern_dir.name}_points.gpkg'
        if point_file.exists():
            results['points'] = gpd.read_file(point_file)
            print(f"DEBUG [LOAD] {pattern_dir.name}: Loaded point data from {point_file} - {len(results['points'])} points")
        else:
            print(f"DEBUG [LOAD] {pattern_dir.name}: Point file not found: {point_file}")
    except Exception as e:
        print(f"Warning: Could not load point data for {pattern_dir.name}: {e}")
        import traceback
        traceback.print_exc()
        pass
    
    return results


def load_all_patterns(data_dir):
    """Load results from all patterns in directory."""
    data_dir = Path(data_dir)
    patterns = {}
    
    # Exclude directories that are not actual patterns
    exclude_dirs = {'summary', 'figures', 'lacunarity', 'percolation', 'multifractal'}
    
    # Find all pattern directories
    for pattern_dir in data_dir.iterdir():
        if not pattern_dir.is_dir():
            continue
        
        # Skip excluded directories
        if pattern_dir.name in exclude_dirs:
            continue
        
        # Only load if it has a summary.json file (indicating it's a valid pattern)
        summary_file = pattern_dir / f'{pattern_dir.name}_summary.json'
        if not summary_file.exists():
            # Try alternative naming
            summary_file = pattern_dir / 'summary.json'
            if not summary_file.exists():
                continue
        
        try:
            results = load_pattern_results(pattern_dir)
            patterns[results['pattern_name']] = results
        except Exception as e:
            print(f"Could not load {pattern_dir.name}: {e}")
    
    return patterns


def create_lacunarity_figure(results, selected_patterns):
    """Create interactive lacunarity plot."""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set2
    
    for i, pattern in enumerate(selected_patterns):
        if pattern not in results:
            continue
        
        data = results[pattern]
        if 'lacunarity' not in data:
            continue
        
        df = data['lacunarity']
        
        fig.add_trace(go.Scatter(
            x=df['scale_meters'],
            y=df['lacunarity'],
            mode='lines+markers',
            name=pattern,
            line=dict(width=3, color=colors[i % len(colors)]),
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Scale: %{x:.1f} m<br>' +
                         'Λ: %{y:.3f}<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title='Lacunarity Analysis — Local Vacancy Structure',
        xaxis_title='Scale ε (meters)',
        yaxis_title='Lacunarity Λ',
        xaxis_type='log',
        template='plotly_white',
        hovermode='closest',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        height=500
    )
    
    return fig


def create_percolation_figure(results, selected_patterns):
    """Create interactive percolation plot."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Percolation Transition', 'Network Topology'),
        horizontal_spacing=0.12
    )
    
    colors = px.colors.qualitative.Set2
    
    for i, pattern in enumerate(selected_patterns):
        if pattern not in results:
            continue
        
        data = results[pattern]
        if 'percolation' not in data:
            continue
        
        df = data['percolation']
        color = colors[i % len(colors)]
        
        # S1/N ratio
        fig.add_trace(
            go.Scatter(
                x=df['threshold'],
                y=df['S1_ratio'],
                mode='lines+markers',
                name=pattern,
                line=dict(width=3, color=color),
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Threshold: %{x:.1f} m<br>' +
                             'S₁/N: %{y:.3f}<br>' +
                             '<extra></extra>',
                showlegend=True
            ),
            row=1, col=1
        )
        
        # Average degree
        fig.add_trace(
            go.Scatter(
                x=df['threshold'],
                y=df['avg_degree'],
                mode='lines+markers',
                name=pattern,
                line=dict(width=3, color=color),
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Threshold: %{x:.1f} m<br>' +
                             'Degree: %{y:.2f}<br>' +
                             '<extra></extra>',
                showlegend=False
            ),
            row=1, col=2
        )
    
    # Add percolation threshold line
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray", 
                  opacity=0.5, row=1, col=1)
    
    fig.update_xaxes(title_text="Distance threshold r (m)", type='log', row=1, col=1)
    fig.update_xaxes(title_text="Distance threshold r (m)", type='log', row=1, col=2)
    fig.update_yaxes(title_text="S₁/N", row=1, col=1)
    fig.update_yaxes(title_text="Average degree ⟨k⟩", row=1, col=2)
    
    fig.update_layout(
        title='Percolation Analysis — Critical Connectivity',
        template='plotly_white',
        hovermode='closest',
        height=500
    )
    
    return fig


def create_multifractal_figure(results, selected_patterns):
    """Create interactive multifractal plot."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Generalized Dimensions D(q)', 'Singularity Spectrum f(α)'),
        horizontal_spacing=0.12
    )
    
    colors = px.colors.qualitative.Set2
    
    for i, pattern in enumerate(selected_patterns):
        if pattern not in results:
            continue
        
        data = results[pattern]
        if 'multifractal' not in data:
            continue
        
        df = data['multifractal'].dropna()
        color = colors[i % len(colors)]
        
        # D(q) spectrum
        fig.add_trace(
            go.Scatter(
                x=df['q'],
                y=df['D_q'],
                mode='lines+markers',
                name=pattern,
                line=dict(width=3, color=color),
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'q: %{x:.2f}<br>' +
                             'D(q): %{y:.3f}<br>' +
                             '<extra></extra>',
                showlegend=True
            ),
            row=1, col=1
        )
        
        # f(α) spectrum with loop removal
        # Sort by alpha for loop detection
        df_sorted = df.sort_values('alpha').reset_index(drop=True)
        
        # Remove backward loops: if f(alpha) decreases when alpha increases, it's a loop
        valid_mask = np.ones(len(df_sorted), dtype=bool)
        alpha_arr = df_sorted['alpha'].values
        f_alpha_arr = df_sorted['f_alpha'].values
        
        for i in range(1, len(df_sorted)):
            # If alpha increases but f_alpha decreases significantly, check for loop
            if alpha_arr[i] > alpha_arr[i-1] and f_alpha_arr[i] < f_alpha_arr[i-1] - 0.05:
                # Check if this creates a backward loop with earlier points
                for j in range(max(0, i-5), i-1):
                    if alpha_arr[j] < alpha_arr[i] and f_alpha_arr[j] > f_alpha_arr[i]:
                        # Loop detected, mark this point for removal
                        valid_mask[i] = False
                        break
        
        df_filtered = df_sorted[valid_mask].sort_values('alpha')
        
        fig.add_trace(
            go.Scatter(
                x=df_filtered['alpha'],
                y=df_filtered['f_alpha'],
                mode='lines+markers',
                name=pattern,
                line=dict(width=3, color=color),
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'α: %{x:.3f}<br>' +
                             'f(α): %{y:.3f}<br>' +
                             '<extra></extra>',
                showlegend=False
            ),
            row=1, col=2
        )
    
    fig.update_xaxes(title_text="Moment order q", row=1, col=1)
    fig.update_xaxes(title_text="Singularity strength α", row=1, col=2)
    fig.update_yaxes(title_text="D(q)", row=1, col=1)
    fig.update_yaxes(title_text="f(α)", row=1, col=2)
    
    fig.update_layout(
        title='Multifractal Analysis — Hierarchical Structure',
        template='plotly_white',
        hovermode='closest',
        height=500
    )
    
    return fig


def create_point_distribution_figure(results, selected_patterns):
    """Create spatial point distribution visualization with subplots."""
    if not selected_patterns:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No patterns selected", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        empty_fig.update_layout(template='plotly_white', height=400)
        return empty_fig
    
    n_patterns = len(selected_patterns)
    cols = min(3, n_patterns)  # Max 3 columns
    rows = (n_patterns + cols - 1) // cols
    
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=selected_patterns,
        horizontal_spacing=0.1,
        vertical_spacing=0.15
    )
    
    colors = px.colors.qualitative.Set2
    
    for idx, pattern in enumerate(selected_patterns):
        if pattern not in results:
            continue
        
        row = idx // cols + 1
        col = idx % cols + 1
        
        # Use actual point data if available, otherwise generate mock data
        if 'points' in results[pattern] and results[pattern]['points'] is not None:
            import geopandas as gpd
            points_gdf = results[pattern]['points']
            x_coords = points_gdf.geometry.x.values
            y_coords = points_gdf.geometry.y.values
            print(f"DEBUG [POINT] {pattern}: Using ACTUAL data - {len(x_coords)} points")
            print(f"DEBUG [POINT] {pattern}: X range: [{min(x_coords):.2f}, {max(x_coords):.2f}]")
            print(f"DEBUG [POINT] {pattern}: Y range: [{min(y_coords):.2f}, {max(y_coords):.2f}]")
        else:
            print(f"DEBUG [POINT] {pattern}: Using MOCK data (fallback)")
            # Generate mock point data for visualization (fallback)
            np.random.seed(hash(pattern) % 2**32)
            n_points = 500
            center_x, center_y = 500, 500
            
            if pattern == 'singlelinear':
                t = np.linspace(0, 1, n_points)
                x_coords = 100 + t * 800
                y_coords = 100 + t * 800
                noise = np.random.normal(0, 20, n_points)
                x_coords += -noise * (y_coords - center_y) / 1000
                y_coords += noise * (x_coords - center_x) / 1000
            elif pattern == 'uniform':
                n_side = int(np.sqrt(n_points))
                x = np.linspace(100, 900, n_side)
                y = np.linspace(100, 900, n_side)
                xx, yy = np.meshgrid(x, y)
                x_flat = xx.flatten()
                y_flat = yy.flatten()
                if len(x_flat) > n_points:
                    indices = np.random.choice(len(x_flat), n_points, replace=False)
                    x_flat = x_flat[indices]
                    y_flat = y_flat[indices]
                elif len(x_flat) < n_points:
                    n_missing = n_points - len(x_flat)
                    x_flat = np.concatenate([x_flat, np.random.uniform(100, 900, n_missing)])
                    y_flat = np.concatenate([y_flat, np.random.uniform(100, 900, n_missing)])
                noise_scale = 30
                x_coords = x_flat + np.random.normal(0, noise_scale, len(x_flat))
                y_coords = y_flat + np.random.normal(0, noise_scale, len(y_flat))
            elif pattern == 'random':
                x_coords = np.random.uniform(0, 1000, n_points)
                y_coords = np.random.uniform(0, 1000, n_points)
            elif pattern == 'radial':
                angles = np.random.uniform(0, 2 * np.pi, n_points)
                radii = np.random.exponential(scale=200, size=n_points)
                radii = np.clip(radii, 0, 400)
                x_coords = center_x + radii * np.cos(angles)
                y_coords = center_y + radii * np.sin(angles)
            elif pattern == 'singleclustered':
                x_coords = np.random.normal(center_x, 100, n_points)
                y_coords = np.random.normal(center_y, 100, n_points)
            else:  # multiclustered
                n_clusters = 5
                points_per_cluster = n_points // n_clusters
                remainder = n_points % n_clusters  # Handle remainder points
                x_coords, y_coords = [], []
                for i in range(n_clusters):
                    cx, cy = np.random.uniform(100, 900, 2)
                    # Distribute remainder points across first few clusters
                    cluster_size = points_per_cluster + (1 if i < remainder else 0)
                    x = np.random.normal(cx, 80, cluster_size)
                    y = np.random.normal(cy, 80, cluster_size)
                    x_coords.extend(x)
                    y_coords.extend(y)
        
        # Convert to Python floats for Plotly
        x_coords = [float(x) for x in x_coords]
        y_coords = [float(y) for y in y_coords]
        
        # Calculate actual bounds for consistent axis ranges
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        x_padding = (x_max - x_min) * 0.05 if x_max > x_min else 50
        y_padding = (y_max - y_min) * 0.05 if y_max > y_min else 50
        x_range = [max(0, x_min - x_padding), min(1000, x_max + x_padding)]
        y_range = [max(0, y_min - y_padding), min(1000, y_max + y_padding)]
        
        fig.add_trace(
            go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers',
                name=pattern,
                marker=dict(
                    size=3,
                    color=colors[idx % len(colors)],
                    opacity=0.7
                ),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'X: %{x:.1f}<br>' +
                             'Y: %{y:.1f}<br>' +
                             '<extra></extra>',
                showlegend=False
            ),
            row=row, col=col
        )
        
        # Update axes for each subplot with consistent ranges
        fig.update_xaxes(title_text="X (meters)", row=row, col=col, range=x_range)
        fig.update_yaxes(title_text="Y (meters)", row=row, col=col, range=y_range, scaleanchor="x", scaleratio=1)
    
    fig.update_layout(
        title='Spatial Point Distribution',
        template='plotly_white',
        hovermode='closest',
        height=300 * rows
    )
    
    return fig


def create_network_figure(results, selected_patterns):
    """Create network structure visualization with subplots using actual analysis network."""
    if not selected_patterns:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No patterns selected", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        empty_fig.update_layout(template='plotly_white', height=400)
        return empty_fig
    
    n_patterns = len(selected_patterns)
    cols = min(3, n_patterns)  # Max 3 columns
    rows = (n_patterns + cols - 1) // cols
    
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=selected_patterns,
        horizontal_spacing=0.1,
        vertical_spacing=0.15
    )
    
    colors = px.colors.qualitative.Set2
    
    # Import the actual network building function used in percolation analysis
    from src.metrics.percolation import build_distance_network
    
    for idx, pattern in enumerate(selected_patterns):
        if pattern not in results:
            continue
        
        row = idx // cols + 1
        col = idx % cols + 1
        
        # Get threshold from percolation data (r_p)
        threshold = None
        if 'percolation' in results[pattern] and 'summary' in results[pattern]:
            summary = results[pattern]['summary']
            # Use percolation threshold (r_p) if available
            if 'percolation_r_p' in summary:
                threshold = summary['percolation_r_p']
            elif 'percolation' in results[pattern]:
                percolation_df = results[pattern]['percolation']
                if len(percolation_df) > 0:
                    threshold = percolation_df['threshold'].median()
        
        print(f"DEBUG [NETWORK] {pattern}: threshold = {threshold}")
        
        # Use actual point data - skip if not available
        if 'points' not in results[pattern] or results[pattern]['points'] is None:
            print(f"DEBUG [NETWORK] {pattern}: No point data available - SKIPPING")
            continue
        
        points_gdf = results[pattern]['points']
        
        # Get coordinates from the same point data as left side
        x_coords = points_gdf.geometry.x.values
        y_coords = points_gdf.geometry.y.values
        coords = np.column_stack([x_coords, y_coords])
        
        print(f"DEBUG [NETWORK] {pattern}: Using ACTUAL data - {len(x_coords)} points")
        print(f"DEBUG [NETWORK] {pattern}: X range: [{min(x_coords):.2f}, {max(x_coords):.2f}]")
        print(f"DEBUG [NETWORK] {pattern}: Y range: [{min(y_coords):.2f}, {max(y_coords):.2f}]")
        
        # Build network using the same function as in percolation analysis
        if threshold is not None and threshold > 0:
            G = build_distance_network(points_gdf, threshold, method='radius')
            print(f"DEBUG [NETWORK] {pattern}: Network built - {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        else:
            print(f"DEBUG [NETWORK] {pattern}: No threshold available - SKIPPING")
            continue
        
        # Extract edges from graph (use node indices to match coordinates)
        edge_x, edge_y = [], []
        for edge in G.edges():
            # G.nodes[node]['pos'] contains the coordinates, but we use the same coords array
            # to ensure exact correspondence with left side
            node_i, node_j = edge[0], edge[1]
            x0, y0 = coords[node_i]
            x1, y1 = coords[node_j]
            edge_x.extend([float(x0), float(x1), None])
            edge_y.extend([float(y0), float(y1), None])
        
        print(f"DEBUG [NETWORK] {pattern}: Extracted {len(edge_x)} edge coordinates (including None separators)")
        
        # Add edges first (so they appear behind nodes)
        if edge_x and len(edge_x) > 0:
            edge_x_clean = [float(x) if x is not None else None for x in edge_x]
            edge_y_clean = [float(y) if y is not None else None for y in edge_y]
            
            fig.add_trace(
                go.Scatter(
                    x=edge_x_clean,
                    y=edge_y_clean,
                    mode='lines',
                    line=dict(width=0.8, color=colors[idx % len(colors)]),
                    opacity=0.4,
                    hoverinfo='skip',
                    showlegend=False
                ),
                row=row, col=col
            )
            print(f"DEBUG [NETWORK] {pattern}: Added edge trace with {len(edge_x_clean)} points")
        else:
            print(f"DEBUG [NETWORK] {pattern}: WARNING - No edges to display!")
        
        # Add nodes - use the same coordinates as left side
        node_x = [float(coord[0]) for coord in coords]
        node_y = [float(coord[1]) for coord in coords]
        
        print(f"DEBUG [NETWORK] {pattern}: Adding {len(node_x)} nodes")
        
        # Calculate same axis ranges as left side (from same data)
        x_min, x_max = min(node_x), max(node_x)
        y_min, y_max = min(node_y), max(node_y)
        x_padding = (x_max - x_min) * 0.05 if x_max > x_min else 50
        y_padding = (y_max - y_min) * 0.05 if y_max > y_min else 50
        x_range = [max(0, x_min - x_padding), min(1000, x_max + x_padding)]
        y_range = [max(0, y_min - y_padding), min(1000, y_max + y_padding)]
        
        fig.add_trace(
            go.Scatter(
                x=node_x,
                y=node_y,
                mode='markers',
                name=pattern,
                marker=dict(
                    size=3,  # Same size as left side
                    color=colors[idx % len(colors)],
                    opacity=0.7,  # Same opacity as left side
                    line=dict(width=0.3, color='white')
                ),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'X: %{x:.1f}<br>' +
                             'Y: %{y:.1f}<br>' +
                             '<extra></extra>',
                showlegend=False
            ),
            row=row, col=col
        )
        
        # Update axes for each subplot with same ranges as left side
        fig.update_xaxes(title_text="X (meters)", row=row, col=col, range=x_range)
        fig.update_yaxes(title_text="Y (meters)", row=row, col=col, range=y_range, scaleanchor="x", scaleratio=1)
    
    fig.update_layout(
        title='Network Structure (threshold-based connectivity)',
        template='plotly_white',
        hovermode='closest',
        height=300 * rows
    )
    
    return fig


def create_summary_table(results, selected_patterns):
    """Create summary statistics table."""
    summary_data = []
    
    for pattern in selected_patterns:
        if pattern not in results or 'summary' not in results[pattern]:
            continue
        
        summary = results[pattern]['summary']
        
        row = {
            'Pattern': pattern,
            'N points': f"{summary.get('n_points', 500)}",
            'Λ (small)': f"{summary.get('lacunarity_small', np.nan):.3f}",
            'Λ (large)': f"{summary.get('lacunarity_large', np.nan):.3f}",
            'r_p (m)': f"{summary.get('percolation_r_p', np.nan):.1f}",
            'Max S₁/N': f"{summary.get('percolation_max_S1_ratio', np.nan):.3f}",
            'Δα': f"{summary.get('multifractal_Delta_alpha', np.nan):.4f}",
            'D₀': f"{summary.get('multifractal_D0', np.nan):.3f}",
        }
        summary_data.append(row)
    
    if not summary_data:
        # Return empty figure instead of html.Div
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="No summary data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        empty_fig.update_layout(
            title='Summary Statistics',
            template='plotly_white',
            height=200
        )
        return empty_fig
    
    df = pd.DataFrame(summary_data)
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df.columns),
            fill_color='paleturquoise',
            align='left',
            font=dict(size=12, color='black')
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color='lavender',
            align='left',
            font=dict(size=11)
        )
    )])
    
    fig.update_layout(
        title='Summary Statistics',
        template='plotly_white',
        height=200 + len(summary_data) * 30
    )
    
    return fig


def create_app(data_dir):
    """Create Dash app."""
    
    # Load data
    print("Loading data...")
    all_results = load_all_patterns(data_dir)
    pattern_names = list(all_results.keys())
    
    if not pattern_names:
        print(f"No patterns found in {data_dir}")
        return None
    
    print(f"Loaded {len(pattern_names)} patterns: {', '.join(pattern_names)}")
    
    # Initialize app
    app = dash.Dash(__name__)
    
    app.layout = html.Div([
        html.Div([
            html.H1("🧩 OpenSparsity Metrics Dashboard",
                   style={'textAlign': 'center', 'color': '#2c3e50'}),
            html.P("Interactive Three-Indicator Framework",
                  style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': 18}),
            html.Hr()
        ]),
        
        # Pattern selector
        html.Div([
            html.Label("Select Patterns to Compare:", 
                      style={'fontSize': 16, 'fontWeight': 'bold'}),
            dcc.Checklist(
                id='pattern-selector',
                options=[{'label': f' {name}', 'value': name} 
                        for name in pattern_names],
                value=pattern_names[:3] if len(pattern_names) > 3 else pattern_names,
                inline=True,
                style={'marginTop': 10}
            )
        ], style={'padding': 20, 'backgroundColor': '#ecf0f1', 'marginBottom': 20}),
        
        # Summary table
        html.Div([
            dcc.Graph(id='summary-table')
        ], style={'marginBottom': 30}),
        
        # Spatial visualization section
        html.H2("🗺️ Spatial Structure", 
               style={'textAlign': 'center', 'color': '#2c3e50', 'marginTop': 30}),
        
        html.Div([
            html.Div([
                dcc.Graph(id='point-distribution')
            ], style={'width': '49%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id='network-structure')
            ], style={'width': '49%', 'display': 'inline-block', 'marginLeft': '2%'})
        ], style={'marginBottom': 30}),
        
        # Metrics section
        html.H2("📊 Three-Indicator Metrics", 
               style={'textAlign': 'center', 'color': '#2c3e50', 'marginTop': 30}),
        
        # Three metric plots
        html.Div([
            dcc.Graph(id='lacunarity-plot')
        ], style={'marginBottom': 30}),
        
        html.Div([
            dcc.Graph(id='percolation-plot')
        ], style={'marginBottom': 30}),
        
        html.Div([
            dcc.Graph(id='multifractal-plot')
        ], style={'marginBottom': 30}),
        
        # Footer
        html.Div([
            html.Hr(),
            html.P("OpenSparsity Project — Three-Indicator Framework v2.0.0",
                  style={'textAlign': 'center', 'color': '#95a5a6'}),
            html.P("Lacunarity × Percolation × Multifractal",
                  style={'textAlign': 'center', 'color': '#bdc3c7', 'fontSize': 12})
        ])
    ], style={'maxWidth': 1400, 'margin': 'auto', 'padding': 20})
    
    # Callbacks
    @app.callback(
        [Output('summary-table', 'figure'),
         Output('point-distribution', 'figure'),
         Output('network-structure', 'figure'),
         Output('lacunarity-plot', 'figure'),
         Output('percolation-plot', 'figure'),
         Output('multifractal-plot', 'figure')],
        Input('pattern-selector', 'value')
    )
    def update_plots(selected_patterns):
        try:
            if not selected_patterns:
                selected_patterns = pattern_names[:1]
            
            print(f"DEBUG: Updating plots for patterns: {selected_patterns}")
            print(f"DEBUG: Available results: {list(all_results.keys())}")
            
            # Create empty figure as fallback
            empty_fig = go.Figure()
            empty_fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            empty_fig.update_layout(template='plotly_white')
            
            try:
                summary_fig = create_summary_table(all_results, selected_patterns)
                # If summary_fig is html.Div, convert to empty figure
                if not isinstance(summary_fig, go.Figure):
                    summary_fig = empty_fig
            except Exception as e:
                print(f"ERROR in summary_table: {e}")
                import traceback
                traceback.print_exc()
                summary_fig = empty_fig
            
            try:
                point_fig = create_point_distribution_figure(all_results, selected_patterns)
            except Exception as e:
                print(f"ERROR in point_distribution: {e}")
                import traceback
                traceback.print_exc()
                point_fig = empty_fig
            
            try:
                network_fig = create_network_figure(all_results, selected_patterns)
            except Exception as e:
                print(f"ERROR in network_structure: {e}")
                import traceback
                traceback.print_exc()
                network_fig = empty_fig
            
            try:
                lac_fig = create_lacunarity_figure(all_results, selected_patterns)
                print(f"DEBUG: Lacunarity figure created, traces: {len(lac_fig.data)}")
            except Exception as e:
                print(f"ERROR in lacunarity: {e}")
                import traceback
                traceback.print_exc()
                lac_fig = empty_fig
            
            try:
                perc_fig = create_percolation_figure(all_results, selected_patterns)
            except Exception as e:
                print(f"ERROR in percolation: {e}")
                import traceback
                traceback.print_exc()
                perc_fig = empty_fig
            
            try:
                mf_fig = create_multifractal_figure(all_results, selected_patterns)
            except Exception as e:
                print(f"ERROR in multifractal: {e}")
                import traceback
                traceback.print_exc()
                mf_fig = empty_fig
            
            return summary_fig, point_fig, network_fig, lac_fig, perc_fig, mf_fig
        
        except Exception as e:
            print(f"FATAL ERROR in update_plots: {e}")
            import traceback
            traceback.print_exc()
            # Return empty figures
            empty_fig = go.Figure()
            empty_fig.add_annotation(text=f"Error: {str(e)}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            empty_fig.update_layout(template='plotly_white')
            return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig
    
    return app


def main():
    parser = argparse.ArgumentParser(
        description="OpenSparsity Metrics Interactive Dashboard"
    )
    parser.add_argument(
        '--data', '-d',
        default='demo_output',
        help='Data directory containing pattern results (default: demo_output)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8050,
        help='Port to run dashboard on (default: 8050)'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to run dashboard on (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    
    args = parser.parse_args()
    
    # Check if data directory exists
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: Data directory '{args.data}' not found!")
        print("\nPlease run analysis first:")
        print("  python main.py demo")
        print("  python main.py analyze <file> --output <dir>")
        return
    
    # Create app
    app = create_app(args.data)
    
    if app is None:
        print("Failed to create dashboard. Check data directory.")
        return
    
    # Run server
    print("\n" + "="*60)
    print("🚀 Starting OpenSparsity Dashboard")
    print("="*60)
    print(f"📂 Data directory: {data_path.absolute()}")
    print(f"🌐 Dashboard URL: http://{args.host}:{args.port}")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(
        debug=args.debug,
        host=args.host,
        port=args.port
    )


if __name__ == '__main__':
    main()

