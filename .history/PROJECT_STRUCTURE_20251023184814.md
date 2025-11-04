# 📁 Project Structure

**OpenSparsity Metrics — Three Indicators Framework**

---

## Directory Tree

```
three_indicator/
│
├── 📄 main.py                      # CLI entry point
├── 📄 requirements.txt             # Python dependencies
├── 📄 config_example.json          # Configuration template
│
├── 📚 Documentation
│   ├── README.md                   # Complete documentation
│   ├── QUICKSTART.md              # Quick start guide
│   ├── CHANGELOG.md               # Version history
│   └── PROJECT_STRUCTURE.md       # This file
│
├── 🔧 Configuration
│   ├── .gitignore                 # Git ignore patterns
│   └── config_example.json        # Example configuration
│
└── 📦 src/                        # Source code
    │
    ├── __init__.py                # Package initialization
    ├── pipeline.py                # Main analysis pipeline
    │
    ├── 📊 metrics/                # Core metric implementations
    │   ├── __init__.py
    │   ├── lacunarity.py         # Lacunarity analysis
    │   ├── percolation.py        # Percolation analysis
    │   └── multifractal.py       # Multifractal analysis
    │
    ├── 🛠️ utils/                  # Utility functions
    │   ├── __init__.py
    │   ├── data_loader.py        # Data I/O
    │   └── io_utils.py           # Results I/O
    │
    └── 📈 visualization/          # Plotting functions
        ├── __init__.py
        └── plots.py              # All visualization functions
```

---

## Module Overview

### 🎯 Core Modules

#### `src/metrics/lacunarity.py`
**Purpose:** Local vacancy structure analysis

**Key Functions:**
- `calculate_lacunarity()` — Main lacunarity calculation
- `lacunarity_summary()` — Scale-wise summary
- `lacunarity_scale_aggregation()` — Aggregate by scale category
- `points_to_raster()` — Convert points to binary raster
- `sliding_window_lacunarity()` — Gliding box algorithm

**Algorithm:** Gliding box method with variance-to-mean ratio

---

#### `src/metrics/percolation.py`
**Purpose:** Critical connectivity analysis

**Key Functions:**
- `calculate_percolation()` — Main percolation analysis
- `percolation_summary()` — Extract key statistics
- `find_percolation_threshold()` — Detect r_p
- `build_distance_network()` — Construct threshold network
- `calculate_percolation_metrics()` — Network topology

**Algorithm:** Distance-threshold network with largest component tracking

---

#### `src/metrics/multifractal.py`
**Purpose:** Hierarchical structure analysis

**Key Functions:**
- `calculate_multifractal()` — Complete multifractal spectrum
- `multifractal_summary()` — Key dimensions and Δα
- `calculate_tau_q()` — Mass exponent τ(q)
- `calculate_D_q()` — Generalized dimensions
- `calculate_multifractal_spectrum()` — Full D(q) and f(α)

**Algorithm:** Box-counting with moment analysis and Legendre transform

---

### 🔄 Pipeline Module

#### `src/pipeline.py`
**Purpose:** Orchestrate analysis workflow

**Main Class:** `OpenSparsityAnalyzer`
- `run_lacunarity()` — Run lacunarity analysis
- `run_percolation()` — Run percolation analysis
- `run_multifractal()` — Run multifractal analysis
- `run_all()` — Complete three-indicator analysis
- `save()` — Save all results
- `visualize()` — Generate all plots

**Batch Function:** `batch_analysis()`
- Process multiple patterns in one call
- Comparative summary generation

---

### 🛠️ Utility Modules

#### `src/utils/data_loader.py`
**Purpose:** Data loading and preparation

**Key Functions:**
- `load_points()` — Load geospatial point data
- `load_network()` — Load network graphs
- `create_analysis_tiles()` — Generate spatial grid
- `filter_points_by_tile()` — Spatial filtering
- `prepare_sample_data()` — Synthetic data generation

---

#### `src/utils/io_utils.py`
**Purpose:** Results I/O management

**Key Functions:**
- `save_results()` — Save analysis outputs
- `load_results()` — Load saved results
- `export_summary()` — Export combined summaries
- `create_output_structure()` — Create directory tree
- `save_network()` — Save network graphs

---

### 📊 Visualization Module

#### `src/visualization/plots.py`
**Purpose:** Generate publication-quality visualizations

**Plot Functions:**
- `plot_lacunarity()` — Λ vs. scale
- `plot_percolation()` — S₁/N transition + network metrics
- `plot_multifractal()` — D(q) and f(α) spectra
- `plot_combined_metrics()` — Integrated view
- `plot_comparison_matrix()` — Multi-pattern comparison

**Output:** High-resolution PNG (300 dpi)

---

## Data Flow

```
Input Data (GeoPackage/Shapefile)
        ↓
   load_points()
        ↓
OpenSparsityAnalyzer
        ↓
    ┌───┴───┐
    │       │
Lacunarity  Percolation  Multifractal
    │       │       │
    └───┬───┘
        ↓
   Integrated
    Results
        ↓
    ┌───┴───┐
    │       │
   CSV    Figures
  (data)  (PNG)
```

---

## Configuration Flow

```
config_example.json
        ↓
    Load config
        ↓
OpenSparsityAnalyzer(points, config)
        ↓
Individual metrics receive parameters
        ↓
    Results with
  custom settings
```

---

## Output Structure

```
output_dir/
│
├── summary/
│   └── combined_summary.csv      # Cross-pattern comparison
│
└── pattern_name/
    ├── Data Files
    │   ├── lacunarity.csv
    │   ├── lacunarity_aggregation.json
    │   ├── percolation.csv
    │   ├── percolation_summary.json
    │   ├── multifractal.csv
    │   ├── multifractal_summary.json
    │   └── summary.json           # Integrated summary
    │
    └── figures/                   # Visualizations
        ├── lacunarity.png
        ├── percolation.png
        ├── multifractal.png
        └── combined.png           # All three metrics
```

---

## Key Design Principles

### ✅ Modularity
Each metric is self-contained and can be used independently

### ✅ Consistency
Unified data structures (GeoDataFrame, DataFrame, dict) across all modules

### ✅ Configurability
All parameters can be customized via config files or API

### ✅ Reproducibility
Fixed random seeds for synthetic data, deterministic algorithms

### ✅ Scalability
Designed for batch processing and large datasets

### ✅ Transparency
Clear mathematical formulas and algorithm descriptions in docstrings

---

## Testing Strategy

Each module includes `if __name__ == "__main__"` block for standalone testing:

```bash
# Test individual modules
python -m src.metrics.lacunarity
python -m src.metrics.percolation
python -m src.metrics.multifractal

# Test pipeline
python -m src.pipeline

# Test visualization
python -m src.visualization.plots

# Integration test
python main.py demo
```

---

## Extension Points

### Adding New Metrics

1. Create `src/metrics/new_metric.py`
2. Implement `calculate_new_metric()` function
3. Add to `src/metrics/__init__.py`
4. Integrate in `src/pipeline.py` as `run_new_metric()`
5. Add visualization in `src/visualization/plots.py`

### Adding New Data Formats

1. Extend `src/utils/data_loader.py`
2. Add format-specific loader function
3. Update `load_points()` with new format branch

### Adding New Visualizations

1. Add function to `src/visualization/plots.py`
2. Follow naming convention: `plot_<metric_name>()`
3. Use consistent styling (seaborn theme, color palette)

---

## Dependencies Graph

```
main.py
  └─→ src.pipeline
       ├─→ src.metrics.lacunarity
       │     └─→ numpy, scipy, geopandas
       │
       ├─→ src.metrics.percolation
       │     └─→ numpy, networkx, geopandas
       │
       ├─→ src.metrics.multifractal
       │     └─→ numpy, scipy, pandas
       │
       ├─→ src.utils
       │     └─→ geopandas, pandas
       │
       └─→ src.visualization
             └─→ matplotlib, seaborn
```

---

## Version Control

### Main Branch Structure
- `main.py` — Stable CLI
- `src/` — Core implementation
- Documentation files — README, guides

### Suggested Workflow
1. Feature development in `dev/` branches
2. Testing with demo data
3. Merge to `main` when stable
4. Tag releases: `v2.0.0`, `v2.1.0`, etc.

---

## Performance Considerations

### Computation Complexity

| Metric | Complexity | Bottleneck | Optimization |
|--------|-----------|------------|--------------|
| Lacunarity | O(n × k²) | Sliding window | Use `scipy.ndimage` |
| Percolation | O(n²) | Distance matrix | Spatial indexing |
| Multifractal | O(n × q) | Box counting | Vectorized operations |

### Memory Usage
- Lacunarity: Raster size = (area / pixel_size²)
- Percolation: Network storage ~ O(n²) worst case
- Multifractal: Probability arrays ~ O(boxes)

---

## Future Development

See [CHANGELOG.md](CHANGELOG.md) for roadmap.

Priority areas:
1. **Performance**: Parallel processing, spatial indexing
2. **Scalability**: Chunked processing for large datasets
3. **Interactivity**: Dash dashboard for live exploration
4. **Integration**: Connection to broader OpenSparsity ecosystem

---

**OpenSparsity Project**  
*Structure documentation v2.0.0*

