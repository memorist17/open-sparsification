#!/usr/bin/env python3
"""
Installation Test Script

Verifies that all dependencies are installed correctly
and core functionality works.

Run: python test_installation.py
"""

import sys
from pathlib import Path

print("="*60)
print("OpenSparsity Metrics — Installation Test")
print("="*60)
print()

# Test 1: Import core dependencies
print("1. Testing core dependencies...")
try:
    import numpy as np
    print("   ✓ NumPy", np.__version__)
except ImportError as e:
    print(f"   ✗ NumPy failed: {e}")
    sys.exit(1)

try:
    import scipy
    print("   ✓ SciPy", scipy.__version__)
except ImportError as e:
    print(f"   ✗ SciPy failed: {e}")
    sys.exit(1)

try:
    import pandas as pd
    print("   ✓ Pandas", pd.__version__)
except ImportError as e:
    print(f"   ✗ Pandas failed: {e}")
    sys.exit(1)

# Test 2: Import geospatial dependencies
print("\n2. Testing geospatial dependencies...")
try:
    import geopandas as gpd
    print("   ✓ GeoPandas", gpd.__version__)
except ImportError as e:
    print(f"   ✗ GeoPandas failed: {e}")
    print("   Install with: pip install geopandas")
    sys.exit(1)

try:
    import shapely
    print("   ✓ Shapely", shapely.__version__)
except ImportError as e:
    print(f"   ✗ Shapely failed: {e}")
    sys.exit(1)

try:
    import rasterio
    print("   ✓ Rasterio", rasterio.__version__)
except ImportError as e:
    print(f"   ✗ Rasterio failed: {e}")
    print("   Install with: pip install rasterio")
    sys.exit(1)

# Test 3: Import network dependencies
print("\n3. Testing network analysis dependencies...")
try:
    import networkx as nx
    print("   ✓ NetworkX", nx.__version__)
except ImportError as e:
    print(f"   ✗ NetworkX failed: {e}")
    sys.exit(1)

# Test 4: Import visualization dependencies
print("\n4. Testing visualization dependencies...")
try:
    import matplotlib
    print("   ✓ Matplotlib", matplotlib.__version__)
except ImportError as e:
    print(f"   ✗ Matplotlib failed: {e}")
    sys.exit(1)

try:
    import seaborn as sns
    print("   ✓ Seaborn", sns.__version__)
except ImportError as e:
    print(f"   ✗ Seaborn failed: {e}")
    sys.exit(1)

try:
    import plotly
    print("   ✓ Plotly", plotly.__version__)
except ImportError as e:
    print(f"   ✗ Plotly failed: {e}")
    sys.exit(1)

# Test 5: Import project modules
print("\n5. Testing project modules...")
try:
    from src.metrics import calculate_lacunarity
    print("   ✓ Lacunarity module")
except ImportError as e:
    print(f"   ✗ Lacunarity module failed: {e}")
    sys.exit(1)

try:
    from src.metrics import calculate_percolation
    print("   ✓ Percolation module")
except ImportError as e:
    print(f"   ✗ Percolation module failed: {e}")
    sys.exit(1)

try:
    from src.metrics import calculate_multifractal
    print("   ✓ Multifractal module")
except ImportError as e:
    print(f"   ✗ Multifractal module failed: {e}")
    sys.exit(1)

try:
    from src.pipeline import OpenSparsityAnalyzer
    print("   ✓ Pipeline module")
except ImportError as e:
    print(f"   ✗ Pipeline module failed: {e}")
    sys.exit(1)

try:
    from src.utils import load_points, prepare_sample_data
    print("   ✓ Utils module")
except ImportError as e:
    print(f"   ✗ Utils module failed: {e}")
    sys.exit(1)

try:
    from src.visualization import plot_lacunarity
    print("   ✓ Visualization module")
except ImportError as e:
    print(f"   ✗ Visualization module failed: {e}")
    sys.exit(1)

# Test 6: Quick functionality test
print("\n6. Testing core functionality...")
try:
    from shapely.geometry import Point
    
    # Generate small test dataset
    print("   → Generating test data (10 points)...")
    np.random.seed(42)
    coords = np.random.uniform(0, 100, (10, 2))
    geometry = [Point(x, y) for x, y in coords]
    gdf = gpd.GeoDataFrame(geometry=geometry, crs='EPSG:3857')
    
    # Test lacunarity
    print("   → Testing lacunarity calculation...")
    lac = calculate_lacunarity(
        gdf,
        pixel_size=5.0,
        window_sizes=[3, 5, 7]
    )
    assert len(lac) > 0, "Lacunarity returned no results"
    print("   ✓ Lacunarity calculation works")
    
    # Test percolation
    print("   → Testing percolation calculation...")
    perc = calculate_percolation(
        gdf,
        thresholds=[10, 50, 100]
    )
    assert len(perc) > 0, "Percolation returned no results"
    print("   ✓ Percolation calculation works")
    
    # Test multifractal
    print("   → Testing multifractal calculation...")
    mf_spectrum, mf_summary = calculate_multifractal(
        gdf,
        q_values=[-2, 0, 2],
        box_sizes=[10, 25, 50]
    )
    assert len(mf_spectrum) > 0, "Multifractal returned no results"
    print("   ✓ Multifractal calculation works")
    
    # Test pipeline
    print("   → Testing analysis pipeline...")
    analyzer = OpenSparsityAnalyzer(gdf)
    results = analyzer.run_all(verbose=False)
    assert 'summary' in results, "Pipeline did not generate summary"
    print("   ✓ Analysis pipeline works")
    
except Exception as e:
    print(f"\n   ✗ Functionality test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# All tests passed
print("\n" + "="*60)
print("✅ All tests passed!")
print("="*60)
print("\nInstallation is complete and working correctly.")
print("\nNext steps:")
print("  1. Run demo: python main.py demo")
print("  2. Check QUICKSTART.md for usage examples")
print("  3. Read README.md for full documentation")
print()

