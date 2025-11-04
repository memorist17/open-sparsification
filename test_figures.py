#!/usr/bin/env python3
"""Test figure creation functions."""

import sys
from pathlib import Path
from dashboard import load_all_patterns, create_point_distribution_figure, create_network_figure

# Load data
print("Loading data...")
data_dir = Path("demo_output_new")
all_results = load_all_patterns(data_dir)
print(f"Loaded {len(all_results)} patterns: {list(all_results.keys())}")

# Test with selected patterns
selected_patterns = list(all_results.keys())[:3]
print(f"\nTesting with patterns: {selected_patterns}")

# Test point distribution
print("\n1. Testing point distribution figure...")
try:
    fig1 = create_point_distribution_figure(all_results, selected_patterns)
    print(f"   ✓ Created successfully")
    print(f"   Data traces: {len(fig1.data)}")
    print(f"   Layout: {fig1.layout}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test network figure
print("\n2. Testing network figure...")
try:
    fig2 = create_network_figure(all_results, selected_patterns)
    print(f"   ✓ Created successfully")
    print(f"   Data traces: {len(fig2.data)}")
    print(f"   Layout: {fig2.layout}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All tests passed!")

