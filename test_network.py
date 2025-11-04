#!/usr/bin/env python3
"""Test network figure creation for specific patterns."""

import sys
from pathlib import Path
from dashboard import load_all_patterns, create_network_figure
import numpy as np

# Load data
print("Loading data...")
data_dir = Path("demo_output_new")
all_results = load_all_patterns(data_dir)

# Test problematic patterns
test_patterns = ['singleclustered', 'radial', 'random', 'multiclustered']

for pattern in test_patterns:
    print(f"\n{'='*60}")
    print(f"Testing pattern: {pattern}")
    print(f"{'='*60}")
    
    if pattern not in all_results:
        print(f"  Pattern not found in results")
        continue
    
    # Check summary
    if 'summary' in all_results[pattern]:
        summary = all_results[pattern]['summary']
        print(f"  Summary keys: {list(summary.keys())[:5]}...")
        if 'percolation_r_p' in summary:
            print(f"  Percolation r_p: {summary['percolation_r_p']}")
    
    # Check percolation data
    if 'percolation' in all_results[pattern]:
        percolation_df = all_results[pattern]['percolation']
        print(f"  Percolation data: {len(percolation_df)} rows")
        if len(percolation_df) > 0:
            print(f"  Threshold range: {percolation_df['threshold'].min():.2f} - {percolation_df['threshold'].max():.2f}")
    
    # Test network figure creation
    try:
        fig = create_network_figure(all_results, [pattern])
        print(f"  Figure created: {len(fig.data)} traces")
        
        # Count edges and nodes
        edge_count = sum(1 for trace in fig.data if trace.mode == 'lines')
        node_count = sum(1 for trace in fig.data if trace.mode == 'markers')
        print(f"  Edges: {edge_count}, Nodes: {node_count}")
        
        # Check if edges have data
        for i, trace in enumerate(fig.data):
            if trace.mode == 'lines':
                if hasattr(trace, 'x') and trace.x is not None:
                    x_data = trace.x if isinstance(trace.x, (list, np.ndarray)) else []
                    non_none_count = sum(1 for x in x_data if x is not None)
                    print(f"    Trace {i} (edges): {non_none_count} non-None x values")
                else:
                    print(f"    Trace {i} (edges): No x data")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

