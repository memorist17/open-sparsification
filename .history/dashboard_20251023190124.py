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
    
    # Load point data if available (for spatial visualization)
    try:
        import geopandas as gpd
        point_file = pattern_dir.parent.parent / 'data' / 'points' / f'{pattern_dir.name}.gpkg'
        if point_file.exists():
            results['points'] = gpd.read_file(point_file)
    except:
        pass
    
    return results


def load_all_patterns(data_dir):
    """Load results from all patterns in directory."""
    data_dir = Path(data_dir)
    patterns = {}
    
    # Find all pattern directories
    for pattern_dir in data_dir.iterdir():
        if pattern_dir.is_dir() and pattern_dir.name != 'summary':
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
        
        # f(α) spectrum
        fig.add_trace(
            go.Scatter(
                x=df['alpha'],
                y=df['f_alpha'],
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
    """Create spatial point distribution visualization."""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set2
    
    for i, pattern in enumerate(selected_patterns):
        if pattern not in results:
            continue
        
        # Generate mock point data for visualization
        np.random.seed(hash(pattern) % 2**32)
        n_points = 500
        
        if pattern == 'clustered':
            # Clustered pattern
            n_clusters = 5
            points_per_cluster = n_points // n_clusters
            x_coords, y_coords = [], []
            for _ in range(n_clusters):
                cx, cy = np.random.uniform(100, 900, 2)
                x = np.random.normal(cx, 80, points_per_cluster)
                y = np.random.normal(cy, 80, points_per_cluster)
                x_coords.extend(x)
                y_coords.extend(y)
        elif pattern == 'random':
            # Random pattern
            x_coords = np.random.uniform(0, 1000, n_points)
            y_coords = np.random.uniform(0, 1000, n_points)
        else:  # grid
            # Grid pattern
            n_side = int(np.sqrt(n_points))
            x = np.linspace(50, 950, n_side)
            y = np.linspace(50, 950, n_side)
            xx, yy = np.meshgrid(x, y)
            x_coords = xx.flatten()[:n_points]
            y_coords = yy.flatten()[:n_points]
        
        fig.add_trace(go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='markers',
            name=pattern,
            marker=dict(
                size=4,
                color=colors[i % len(colors)],
                opacity=0.6
            ),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'X: %{x:.1f}<br>' +
                         'Y: %{y:.1f}<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title='Spatial Point Distribution',
        xaxis_title='X (meters)',
        yaxis_title='Y (meters)',
        template='plotly_white',
        hovermode='closest',
        height=600,
        yaxis=dict(scaleanchor="x", scaleratio=1)
    )
    
    return fig


def create_network_figure(results, selected_patterns):
    """Create network structure visualization."""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set2
    
    for idx, pattern in enumerate(selected_patterns):
        if pattern not in results:
            continue
        
        # Generate mock network data
        np.random.seed(hash(pattern) % 2**32)
        n_points = 100
        
        if pattern == 'clustered':
            n_clusters = 5
            points_per_cluster = n_points // n_clusters
            coords = []
            for _ in range(n_clusters):
                cx, cy = np.random.uniform(100, 900, 2)
                x = np.random.normal(cx, 60, points_per_cluster)
                y = np.random.normal(cy, 60, points_per_cluster)
                coords.extend(zip(x, y))
            threshold = 150
        elif pattern == 'random':
            x_coords = np.random.uniform(0, 1000, n_points)
            y_coords = np.random.uniform(0, 1000, n_points)
            coords = list(zip(x_coords, y_coords))
            threshold = 100
        else:  # grid
            n_side = int(np.sqrt(n_points))
            x = np.linspace(100, 900, n_side)
            y = np.linspace(100, 900, n_side)
            xx, yy = np.meshgrid(x, y)
            coords = list(zip(xx.flatten(), yy.flatten()))
            threshold = 120
        
        coords = np.array(coords)
        
        # Create edges
        edge_x, edge_y = [], []
        for i in range(len(coords)):
            for j in range(i+1, len(coords)):
                dist = np.linalg.norm(coords[i] - coords[j])
                if dist < threshold:
                    edge_x.extend([coords[i][0], coords[j][0], None])
                    edge_y.extend([coords[i][1], coords[j][1], None])
        
        # Add edges
        if edge_x:
            fig.add_trace(go.Scatter(
                x=edge_x,
                y=edge_y,
                mode='lines',
                line=dict(width=0.5, color=colors[idx % len(colors)]),
                opacity=0.3,
                hoverinfo='skip',
                showlegend=False
            ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=coords[:, 0],
            y=coords[:, 1],
            mode='markers',
            name=pattern,
            marker=dict(
                size=6,
                color=colors[idx % len(colors)],
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'X: %{x:.1f}<br>' +
                         'Y: %{y:.1f}<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title=f'Network Structure (threshold-based connectivity)',
        xaxis_title='X (meters)',
        yaxis_title='Y (meters)',
        template='plotly_white',
        hovermode='closest',
        height=600,
        yaxis=dict(scaleanchor="x", scaleratio=1)
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
        return html.Div("No summary data available")
    
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
        if not selected_patterns:
            selected_patterns = pattern_names[:1]
        
        summary_fig = create_summary_table(all_results, selected_patterns)
        point_fig = create_point_distribution_figure(all_results, selected_patterns)
        network_fig = create_network_figure(all_results, selected_patterns)
        lac_fig = create_lacunarity_figure(all_results, selected_patterns)
        perc_fig = create_percolation_figure(all_results, selected_patterns)
        mf_fig = create_multifractal_figure(all_results, selected_patterns)
        
        return summary_fig, point_fig, network_fig, lac_fig, perc_fig, mf_fig
    
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

