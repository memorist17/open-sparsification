#!/usr/bin/env python3
"""Detailed debug of network edge generation."""

import numpy as np
from pathlib import Path
from dashboard import load_all_patterns
import json

# Load data
data_dir = Path("demo_output_new")
all_results = load_all_patterns(data_dir)

# Test singleclustered pattern
pattern = 'singleclustered'
print(f"Testing: {pattern}")
print("="*60)

# Get threshold
threshold = None
if 'percolation' in all_results[pattern] and 'summary' in all_results[pattern]:
    summary = all_results[pattern]['summary']
    if 'percolation_r_p' in summary:
        threshold = summary['percolation_r_p']
        print(f"Threshold from data: {threshold}")

# Generate coordinates
np.random.seed(hash(pattern) % 2**32)
n_points = 150
center_x, center_y = 500, 500

x_coords = np.random.normal(center_x, 100, n_points)
y_coords = np.random.normal(center_y, 100, n_points)
coords = np.column_stack([x_coords, y_coords])

print(f"\nGenerated {len(coords)} points")
print(f"Coordinate range: X=[{coords[:, 0].min():.1f}, {coords[:, 0].max():.1f}], Y=[{coords[:, 1].min():.1f}, {coords[:, 1].max():.1f}]")

if threshold is None:
    threshold = 60
print(f"Using threshold: {threshold}")

# Create edges
edge_x, edge_y = [], []
edge_count = 0
max_edges = 500

print(f"\nChecking distances...")
distances = []
for i in range(min(10, len(coords))):  # Check first 10 points
    for j in range(i+1, min(10, len(coords))):
        dist = np.linalg.norm(coords[i] - coords[j])
        distances.append(dist)
        if dist < threshold:
            print(f"  Point {i} to {j}: {dist:.2f} < {threshold} (CONNECTED)")
        else:
            print(f"  Point {i} to {j}: {dist:.2f} >= {threshold} (not connected)")

print(f"\nDistance statistics:")
print(f"  Min: {min(distances):.2f}")
print(f"  Max: {max(distances):.2f}")
print(f"  Mean: {np.mean(distances):.2f}")
print(f"  Points within threshold: {sum(1 for d in distances if d < threshold)}")

# Full edge generation
print(f"\nGenerating all edges...")
for i in range(len(coords)):
    if edge_count >= max_edges:
        break
    for j in range(i+1, len(coords)):
        if edge_count >= max_edges:
            break
        dist = np.linalg.norm(coords[i] - coords[j])
        if dist < threshold:
            edge_x.extend([coords[i][0], coords[j][0], None])
            edge_y.extend([coords[i][1], coords[j][1], None])
            edge_count += 1

print(f"Generated {edge_count} edges")
print(f"edge_x length: {len(edge_x)}")
print(f"edge_y length: {len(edge_y)}")
if len(edge_x) > 0:
    print(f"First few edge_x values: {edge_x[:10]}")
    print(f"Non-None count: {sum(1 for x in edge_x if x is not None)}")

