# 🧩 OpenSparsity Metrics - Three Indicators Framework

**Version:** 2.0.0  
**Date:** 2025-10-23  
**Author:** Kotaro Iwata / OpenSparsity Project

---

## Overview

A comprehensive framework for multi-scale urban spatial analysis using three complementary fractal/network metrics:

| Layer | Metric | Urban Meaning | Research Heritage |
|-------|--------|---------------|-------------------|
| **Local Structure** | **Lacunarity** | Spatial vacancy structure | Plotnick 1996 / Batty 2008 |
| **Connectivity** | **Percolation** | Critical connectivity | Makse 1998 / Arcaute 2016 |
| **Hierarchy** | **Multifractal** | Scale-dependent hierarchy | Halsey 1986 / Murcio 2015 |

This framework quantifies the **openness, sparsity, and hierarchical complexity** of spatial patterns — core concepts in the OpenSparsity research program.

---

## Features

✅ **Three integrated metrics** with unified data pipeline  
✅ **Scientifically rigorous** implementations based on peer-reviewed methods  
✅ **Batch processing** for comparative pattern analysis  
✅ **Beautiful visualizations** with publication-quality plots  
✅ **Flexible configuration** via JSON or Python API  
✅ **CLI and Python API** for diverse workflows  

---

## Installation

### Requirements

- Python 3.8+
- GDAL (for geospatial data handling)

### Setup

```bash
# Clone repository
git clone <repository_url>
cd three_indicator

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

Core scientific computing:
- `numpy`, `scipy`, `pandas`

Geospatial processing:
- `geopandas`, `shapely`, `rasterio`, `fiona`

Network analysis:
- `networkx`

Visualization:
- `matplotlib`, `seaborn`, `plotly`

---

## Quick Start

### Demo Mode

Run built-in demo with synthetic patterns:

```bash
python main.py demo
```

This generates three synthetic patterns (clustered, random, grid) and runs complete analysis.

### Analyze Single Pattern

```bash
python main.py analyze data/buildings.gpkg --output results/buildings
```

### Batch Analysis

```bash
python main.py batch data/patterns/ --output results/batch
```

---

## Usage

### Command-Line Interface

#### 1. Single Pattern Analysis

```bash
python main.py analyze <input_file> --output <output_dir> [OPTIONS]

Options:
  --prefix PREFIX       Output file prefix (default: 'analysis')
  --config CONFIG.json  Configuration file
  --crs EPSG:XXXX      Target coordinate system (default: EPSG:3857)
  --no-plot            Skip visualization
  --show               Display plots interactively
  --verbose, -v        Verbose output
```

**Example:**
```bash
python main.py analyze data/tokyo_buildings.gpkg \
  --output results/tokyo \
  --config config_example.json \
  --verbose
```

#### 2. Batch Analysis

```bash
python main.py batch <input_dir> --output <output_dir> [OPTIONS]

Options:
  --pattern PATTERN    File glob pattern (default: '*.gpkg')
  --config CONFIG.json Configuration file
  --crs EPSG:XXXX     Target CRS
  --verbose, -v       Verbose output
```

**Example:**
```bash
python main.py batch data/cities/ \
  --output results/comparative \
  --pattern "*.gpkg" \
  --verbose
```

### Python API

#### Basic Usage

```python
from src.pipeline import OpenSparsityAnalyzer
from src.utils.data_loader import load_points

# Load data
points = load_points('data/buildings.gpkg')

# Create analyzer
analyzer = OpenSparsityAnalyzer(points)

# Run analysis
results = analyzer.run_all(verbose=True)

# Save results
analyzer.save('./output', prefix='my_analysis')

# Visualize
figs = analyzer.visualize(output_dir='./output/figures')
```

#### Custom Configuration

```python
config = {
    'pixel_size': 5.0,
    'lacunarity_scales': [3, 5, 7, 11, 15, 21, 31, 41, 51, 71, 101],
    'percolation_thresholds': [10, 25, 50, 100, 200, 400, 800],
    'multifractal_q': [-5, -3, -2, -1, 0, 1, 2, 3, 5],
    'box_sizes': [10, 25, 50, 100, 200, 400, 800, 1000],
}

analyzer = OpenSparsityAnalyzer(points, config)
results = analyzer.run_all()
```

#### Run Individual Metrics

```python
# Lacunarity only
lac_summary = analyzer.run_lacunarity()

# Percolation only
perc_results = analyzer.run_percolation()

# Multifractal only
mf_spectrum, mf_summary = analyzer.run_multifractal()
```

---

## Metrics Description

### 1. Lacunarity — Local Vacancy Structure

**Concept:** Measures spatial heterogeneity of point distributions at multiple scales.

**Formula:**
```
Λ(k) = σ²(k) / μ(k)² + 1
```

**Interpretation:**
- `Λ ≈ 1`: Homogeneous (uniform distribution)
- `Λ ≫ 1`: Heterogeneous (clustered with large gaps)

**Output:**
- `lacunarity.csv`: Scale vs. Λ(ε)
- `lacunarity_aggregation`: Summary by scale category (small/medium/large)

**References:**
- Plotnick, R. E. et al. (1996) *Lacunarity analysis: A general technique for the analysis of spatial patterns.*
- Batty, M. (2008) *The size, scale, and shape of cities.*

---

### 2. Percolation — Critical Connectivity

**Concept:** Analyzes connectivity transition as distance threshold increases.

**Key Metrics:**
- `S₁/N`: Ratio of largest connected component to total nodes
- `r_p`: Percolation threshold (distance where S₁/N ≈ 0.5)
- `⟨k⟩`: Average node degree
- `C`: Clustering coefficient

**Interpretation:**
- Small `r_p`: High permeability (easily connected)
- Large `r_p`: Fragmented structure

**Output:**
- `percolation.csv`: Threshold vs. connectivity metrics
- `percolation_summary`: r_p and critical statistics

**References:**
- Makse, H. A. et al. (1998) *Modeling urban growth patterns with correlated percolation.*
- Arcaute, E. et al. (2016) *Cities and regions in Britain through hierarchical percolation.*

---

### 3. Multifractal — Hierarchical Structure

**Concept:** Reveals scale-dependent complexity through generalized fractal dimensions.

**Key Measures:**
- `D(q)`: Generalized fractal dimensions
- `f(α)`: Singularity spectrum
- `Δα = α_max - α_min`: Spectrum width (hierarchical diversity)

**Interpretation:**
- Large `Δα`: Multi-scale, self-similar structure
- Small `Δα`: Uniform, monofractal structure
- `D₀`: Capacity dimension (box-counting)
- `D₁`: Information dimension
- `D₂`: Correlation dimension

**Output:**
- `multifractal.csv`: q, D(q), α, f(α)
- `multifractal_summary`: Key dimensions and Δα

**References:**
- Halsey, T. C. et al. (1986) *Fractal measures and their singularities.*
- Murcio, R. et al. (2015) *Multifractal analysis of the London urban form.*

---

## Output Structure

```
output_dir/
├── summary/
│   └── combined_summary.csv       # Cross-pattern comparison
├── pattern_name/
│   ├── lacunarity.csv
│   ├── lacunarity_aggregation.json
│   ├── percolation.csv
│   ├── percolation_summary.json
│   ├── multifractal.csv
│   ├── multifractal_summary.json
│   ├── summary.json               # Integrated summary
│   └── figures/
│       ├── lacunarity.png
│       ├── percolation.png
│       ├── multifractal.png
│       └── combined.png
```

---

## Configuration

Configuration can be provided via JSON file (see `config_example.json`):

```json
{
  "lacunarity": {
    "pixel_size": 5.0,
    "window_sizes": [3, 5, 7, 11, 15, 21, 31, 41, 51, 71, 101]
  },
  "percolation": {
    "thresholds": [10, 25, 50, 100, 200, 400, 800],
    "method": "radius"
  },
  "multifractal": {
    "q_values": [-5, -3, -2, -1, -0.5, 0, 0.5, 1, 1.5, 2, 3, 5],
    "box_sizes": [10, 25, 50, 100, 200, 400, 800, 1000]
  }
}
```

**Parameters:**

| Parameter | Unit | Description |
|-----------|------|-------------|
| `pixel_size` | meters | Raster resolution for lacunarity |
| `window_sizes` | pixels | Gliding box sizes |
| `thresholds` | meters | Distance thresholds for percolation |
| `method` | - | Network construction method ('radius' or 'knn') |
| `q_values` | - | Moment orders for multifractal |
| `box_sizes` | meters | Box sizes for multifractal |

---

## Data Format

### Input Data

**Required:** Point geometries (building centroids, facilities, nodes, etc.)

**Supported formats:**
- GeoPackage (`.gpkg`) — recommended
- Shapefile (`.shp`)
- GeoJSON (`.geojson`)

**Coordinate system:**
- Must be in projected CRS (meters)
- Default: EPSG:3857 (Web Mercator)
- Specify with `--crs` flag or in config

**Example data preparation:**

```python
import geopandas as gpd

# Load building polygons
buildings = gpd.read_file('buildings.gpkg')

# Convert to centroids
buildings['geometry'] = buildings.geometry.centroid

# Ensure projected CRS
buildings = buildings.to_crs('EPSG:3857')

# Save as points
buildings.to_file('building_points.gpkg', driver='GPKG')
```

---

## Visualization

The framework generates four types of plots:

### 1. Lacunarity Plot
- X-axis: Scale (meters, log scale)
- Y-axis: Lacunarity Λ
- Shows scale-dependent heterogeneity

### 2. Percolation Plot
- Left panel: S₁/N vs. threshold (percolation curve)
- Right panel: Network topology metrics
- Highlights percolation threshold r_p

### 3. Multifractal Plot
- Left panel: D(q) spectrum
- Right panel: f(α) singularity spectrum
- Shows hierarchical complexity

### 4. Combined Plot
- Integrated view of all three metrics
- Cross-scale comparison

All plots are saved as high-resolution PNG (300 dpi).

---

## Advanced Usage

### Batch Processing with Custom Patterns

```python
from src.pipeline import batch_analysis
from src.utils.data_loader import load_points

patterns = {
    'tokyo': load_points('data/tokyo.gpkg'),
    'osaka': load_points('data/osaka.gpkg'),
    'kyoto': load_points('data/kyoto.gpkg'),
}

results = batch_analysis(
    patterns,
    output_dir='./results/comparison',
    verbose=True
)
```

### Custom Metrics Integration

```python
from src.metrics import calculate_lacunarity, calculate_percolation, calculate_multifractal

# Manual workflow
lac = calculate_lacunarity(points, pixel_size=5.0)
perc = calculate_percolation(points, thresholds=[50, 100, 200])
mf_spectrum, mf_summary = calculate_multifractal(points)
```

### Generating Synthetic Test Data

```python
from src.utils.data_loader import prepare_sample_data

# Clustered pattern (high lacunarity)
clustered = prepare_sample_data(500, pattern='clustered', seed=42)

# Random pattern (low lacunarity)
random = prepare_sample_data(500, pattern='random', seed=42)

# Grid pattern (minimal lacunarity)
grid = prepare_sample_data(500, pattern='grid', seed=42)
```

---

## Project Structure

```
three_indicator/
├── main.py                    # CLI entry point
├── config_example.json        # Configuration template
├── requirements.txt           # Dependencies
├── README.md                  # This file
│
├── src/
│   ├── __init__.py
│   ├── pipeline.py            # Main analysis pipeline
│   │
│   ├── metrics/               # Core metric implementations
│   │   ├── __init__.py
│   │   ├── lacunarity.py
│   │   ├── percolation.py
│   │   └── multifractal.py
│   │
│   ├── utils/                 # Data I/O utilities
│   │   ├── __init__.py
│   │   ├── data_loader.py
│   │   └── io_utils.py
│   │
│   └── visualization/         # Plotting functions
│       ├── __init__.py
│       └── plots.py
│
└── data/                      # (Optional) Sample data directory
```

---

## Testing

Each module includes self-contained tests. Run individual modules:

```bash
# Test lacunarity
python -m src.metrics.lacunarity

# Test percolation
python -m src.metrics.percolation

# Test multifractal
python -m src.metrics.multifractal

# Test pipeline
python -m src.pipeline

# Test visualization
python -m src.visualization.plots
```

---

## Theoretical Background

### OpenSparsity Conceptual Framework

| OpenSparsity Concept | Metric | Urban Function | Mathematical Foundation |
|----------------------|--------|----------------|-------------------------|
| **Openness** | Lacunarity | Spatial "gaps" | 2D raster statistics (μ, σ²) |
| **Sparsity** | Percolation | Connectivity at critical threshold | Connected component analysis |
| **Hierarchy** | Multifractal | Self-similar complexity | Generalized dimensions D(q) |

### Scale Integration

All three metrics operate on compatible spatial scales (10m — 1000m), enabling:
- **Cross-scale correlation analysis**
- **Unified spatial interpretation**
- **Multi-layer urban structure characterization**

---

## Citation

If you use this framework in academic research, please cite:

```bibtex
@software{opensparsity2025,
  title = {OpenSparsity Metrics: Three-Indicator Framework},
  author = {Iwata, Kotaro},
  year = {2025},
  version = {2.0.0},
  organization = {OpenSparsity Project}
}
```

---

## References

### Lacunarity
- Plotnick, R. E., Gardner, R. H., & O'Neill, R. V. (1996). *Lacunarity analysis: A general technique for the analysis of spatial patterns.* Physical Review E, 53(5), 5461.
- Batty, M. (2008). *The size, scale, and shape of cities.* Science, 319(5864), 769-771.

### Percolation
- Makse, H. A., Havlin, S., & Stanley, H. E. (1995). *Modelling urban growth patterns.* Nature, 377(6550), 608-612.
- Arcaute, E., et al. (2016). *Cities and regions in Britain through hierarchical percolation.* Royal Society Open Science, 3(4), 150691.

### Multifractal
- Halsey, T. C., et al. (1986). *Fractal measures and their singularities: The characterization of strange sets.* Physical Review A, 33(2), 1141.
- Murcio, R., et al. (2015). *Multifractal to monofractal evolution of the London street network.* Physical Review E, 92(6), 062130.

---

## License

MIT License (modify as appropriate)

---

## Contact

**Author:** Kotaro Iwata  
**Project:** OpenSparsity  
**Email:** [your-email]  
**GitHub:** [repository-url]

---

## Acknowledgments

This framework builds upon decades of fractal geometry, network science, and urban morphology research. Special thanks to the researchers whose methods are implemented here.

---

**OpenSparsity Project**  
*Quantifying the structure of open, sparse, hierarchical space*

