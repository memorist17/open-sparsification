#!/usr/bin/env python3
"""Test network trace data directly."""

import sys
from pathlib import Path
from dashboard import load_all_patterns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Load data
data_dir = Path("demo_output_new")
all_results = load_all_patterns(data_dir)

# Test singleclustered
pattern = 'singleclustered'
print(f"Testing: {pattern}")

# Get threshold
threshold = 21.4  # From percolation data

# Generate coordinates
np.random.seed(hash(pattern) % 2**32)
n_points = 150
center_x, center_y = 500, 500
x_coords = np.random.normal(center_x, 100, n_points)
y_coords = np.random.normal(center_y, 100, n_points)
coords = np.column_stack([x_coords, y_coords])

# Create edges
edge_x, edge_y = [], []
edge_count = 0
max_edges = 500

for i in range(len(coords)):
    if edge_count >= max_edges:
        break
    for j in range(i+1, len(coords)):
        if edge_count >= max_edges:
            break
        dist = np.linalg.norm(coords[i] - coords[j])
        if dist < threshold:
            edge_x.extend([float(coords[i][0]), float(coords[j][0]), None])
            edge_y.extend([float(coords[i][1]), float(coords[j][1]), None])
            edge_count += 1

print(f"Generated {edge_count} edges")
print(f"edge_x length: {len(edge_x)}")
print(f"First 10 edge_x: {edge_x[:10]}")

# Convert to clean list
edge_x_clean = [float(x) if x is not None else None for x in edge_x]
edge_y_clean = [float(y) if y is not None else None for y in edge_y]

print(f"edge_x_clean length: {len(edge_x_clean)}")
print(f"First 10 edge_x_clean: {edge_x_clean[:10]}")
print(f"Non-None count: {sum(1 for x in edge_x_clean if x is not None)}")

# Create figure with subplot
fig = make_subplots(rows=1, cols=1, subplot_titles=[pattern])

# Add edges
if edge_x_clean and len(edge_x_clean) > 0:
    print(f"\nAdding edge trace...")
    trace = go.Scatter(
        x=edge_x_clean,
        y=edge_y_clean,
        mode='lines',
        line=dict(width=0.8, color='blue'),
        opacity=0.4,
        hoverinfo='skip',
        showlegend=False
    )
    fig.add_trace(trace, row=1, col=1)
    print(f"  Trace added: x length={len(trace.x)}, y length={len(trace.y)}")
    print(f"  Trace x type: {type(trace.x)}")
    if hasattr(trace.x, '__len__'):
        print(f"  First 10 trace.x values: {list(trace.x)[:10]}")
else:
    print("No edges to add!")

# Add nodes
node_x = [float(x) for x in coords[:, 0]]
node_y = [float(y) for y in coords[:, 1]]
print(f"\nAdding node trace...")
trace2 = go.Scatter(
    x=node_x,
    y=node_y,
    mode='markers',
    marker=dict(size=5, color='red')
)
fig.add_trace(trace2, row=1, col=1)
print(f"  Node trace added: {len(trace2.x)} points")

print(f"\nFinal figure has {len(fig.data)} traces")

