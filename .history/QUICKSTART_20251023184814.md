# 🚀 Quick Start Guide

**OpenSparsity Metrics — Get started in 5 minutes**

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

---

## Run Demo (No Data Required)

```bash
python main.py demo
```

This will:
1. Generate 3 synthetic point patterns (clustered, random, grid)
2. Run complete three-indicator analysis on each
3. Generate visualizations
4. Save results to `./demo_output/`

**Check the results:**
```bash
# View summary
cat demo_output/summary/combined_summary.csv

# View figures
open demo_output/*/figures/combined.png
```

---

## Analyze Your Own Data

### 1. Prepare Point Data

Your data should be:
- Point geometries (e.g., building centroids)
- In a projected coordinate system (meters)
- Saved as GeoPackage (`.gpkg`), Shapefile (`.shp`), or GeoJSON

**Example data preparation:**

```python
import geopandas as gpd

# Load your data
buildings = gpd.read_file('your_data.gpkg')

# Convert to centroids if needed
buildings['geometry'] = buildings.geometry.centroid

# Ensure projected CRS (e.g., EPSG:3857)
buildings = buildings.to_crs('EPSG:3857')

# Save
buildings.to_file('points.gpkg', driver='GPKG')
```

### 2. Run Analysis

```bash
python main.py analyze points.gpkg --output results/my_analysis --verbose
```

### 3. View Results

```bash
# Summary statistics
cat results/my_analysis/summary.json

# Visualizations
open results/my_analysis/figures/combined.png
```

---

## Python API

```python
from src.pipeline import OpenSparsityAnalyzer
from src.utils.data_loader import load_points

# Load data
points = load_points('points.gpkg')

# Run analysis
analyzer = OpenSparsityAnalyzer(points)
results = analyzer.run_all()

# Access results
print("Lacunarity (small scale):", results['lacunarity_aggregation']['small'])
print("Percolation threshold:", results['percolation_summary']['r_p'], "meters")
print("Multifractal width Δα:", results['multifractal_summary']['Delta_alpha'])

# Save and visualize
analyzer.save('./output', prefix='my_pattern')
analyzer.visualize(output_dir='./output/figures')
```

---

## Understanding Results

### Lacunarity (Λ)
- **Low (≈1)**: Uniform, homogeneous distribution
- **High (≫1)**: Clustered, many gaps

### Percolation Threshold (r_p)
- **Low**: Points connect easily (high permeability)
- **High**: Fragmented structure (low permeability)

### Multifractal Width (Δα)
- **Large**: Multi-scale, hierarchical structure
- **Small**: Uniform, monofractal structure

---

## Next Steps

1. **Compare patterns**: Use `batch` command to analyze multiple datasets
2. **Customize parameters**: Edit `config_example.json` and use `--config` flag
3. **Explore visualizations**: Check `figures/` directory for publication-quality plots

---

## Common Issues

### "No CRS found" warning
→ Specify CRS: `--crs EPSG:3857`

### Import errors
→ Install all dependencies: `pip install -r requirements.txt`

### GDAL issues
→ On macOS: `brew install gdal`  
→ On Ubuntu: `apt-get install gdal-bin libgdal-dev`

---

## Help

```bash
# General help
python main.py --help

# Command-specific help
python main.py analyze --help
python main.py batch --help
```

---

**Ready to analyze!** 🎯

For detailed documentation, see [README.md](README.md)

