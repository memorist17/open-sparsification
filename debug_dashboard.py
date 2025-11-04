#!/usr/bin/env python3
"""Debug script to check dashboard data loading."""

import sys
from pathlib import Path
from dashboard import load_all_patterns, load_pattern_results, create_lacunarity_figure

# Test data loading
print("="*60)
print("Testing Data Loading")
print("="*60)

data_dir = Path("demo_output_new")
print(f"Data directory: {data_dir}")
print(f"Exists: {data_dir.exists()}")
print()

# Test loading all patterns
print("Loading all patterns...")
try:
    all_results = load_all_patterns(data_dir)
    print(f"Loaded {len(all_results)} patterns: {list(all_results.keys())}")
    print()
    
    # Check each pattern
    for pattern_name, results in all_results.items():
        print(f"Pattern: {pattern_name}")
        print(f"  Keys: {list(results.keys())}")
        
        if 'lacunarity' in results:
            df = results['lacunarity']
            print(f"  Lacunarity: {len(df)} rows, columns: {list(df.columns)}")
            if len(df) > 0:
                print(f"    First row: {df.iloc[0].to_dict()}")
        else:
            print(f"  Lacunarity: NOT FOUND")
        
        if 'percolation' in results:
            df = results['percolation']
            print(f"  Percolation: {len(df)} rows, columns: {list(df.columns)}")
        else:
            print(f"  Percolation: NOT FOUND")
        
        if 'multifractal' in results:
            df = results['multifractal']
            print(f"  Multifractal: {len(df)} rows, columns: {list(df.columns)}")
        else:
            print(f"  Multifractal: NOT FOUND")
        
        if 'summary' in results:
            summary = results['summary']
            print(f"  Summary: {list(summary.keys())[:5]}...")
        else:
            print(f"  Summary: NOT FOUND")
        
        print()
    
    # Test creating a figure
    print("="*60)
    print("Testing Graph Creation")
    print("="*60)
    
    test_patterns = list(all_results.keys())[:2]
    print(f"Testing with patterns: {test_patterns}")
    
    try:
        fig = create_lacunarity_figure(all_results, test_patterns)
        print(f"Figure created successfully!")
        print(f"  Data traces: {len(fig.data)}")
        for i, trace in enumerate(fig.data):
            print(f"    Trace {i}: {trace.name}, points: {len(trace.x) if hasattr(trace, 'x') else 'N/A'}")
    except Exception as e:
        print(f"ERROR creating figure: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("="*60)
print("Debug complete")
print("="*60)

