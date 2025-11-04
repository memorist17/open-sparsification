# 🏗️ Architecture Diagram

**OpenSparsity Metrics — System Architecture**

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   OpenSparsity Framework                        │
│                                                                 │
│  ┌───────────────┐          ┌──────────────────┐              │
│  │  CLI (main.py)│          │  Python API      │              │
│  │  - analyze    │          │  - Analyzer      │              │
│  │  - batch      │◄────────►│  - Functions     │              │
│  │  - demo       │          │  - Classes       │              │
│  └───────┬───────┘          └────────┬─────────┘              │
│          │                           │                         │
│          └───────────┬───────────────┘                         │
│                      ▼                                         │
│          ┌────────────────────────┐                           │
│          │   Pipeline Layer       │                           │
│          │  (src/pipeline.py)     │                           │
│          │  - OpenSparsityAnalyzer│                           │
│          │  - batch_analysis()    │                           │
│          └──────────┬─────────────┘                           │
│                     │                                          │
│         ┌───────────┴───────────┐                             │
│         ▼                       ▼                             │
│  ┌──────────────┐        ┌──────────────┐                    │
│  │  Metrics     │        │  Utils       │                    │
│  │  Layer       │        │  Layer       │                    │
│  └──────┬───────┘        └──────┬───────┘                    │
│         │                       │                             │
│  ┌──────┴───────────────────────┴──────┐                     │
│  │                                      │                     │
│  ▼                                      ▼                     │
│ ┌──────────────┐              ┌──────────────┐               │
│ │ Visualization│              │  Output      │               │
│ │    Layer     │              │  Layer       │               │
│ └──────────────┘              └──────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer Architecture

### 1️⃣ Interface Layer

```
┌─────────────────────────────────────────┐
│           User Interfaces               │
├─────────────────────────────────────────┤
│                                         │
│  CLI Interface (main.py)                │
│  ├─ analyze <file> --output <dir>     │
│  ├─ batch <dir> --output <dir>        │
│  └─ demo                               │
│                                         │
│  Python API                            │
│  ├─ from src.pipeline import ...      │
│  ├─ analyzer = OpenSparsityAnalyzer() │
│  └─ results = analyzer.run_all()      │
│                                         │
└─────────────────────────────────────────┘
```

### 2️⃣ Pipeline Layer

```
┌─────────────────────────────────────────┐
│          Analysis Pipeline              │
├─────────────────────────────────────────┤
│                                         │
│  OpenSparsityAnalyzer                  │
│  ├─ __init__(points, config)          │
│  ├─ run_lacunarity() ──► Lacunarity   │
│  ├─ run_percolation() ──► Percolation │
│  ├─ run_multifractal() ──► Multifractal│
│  ├─ run_all() ──► All metrics          │
│  ├─ save() ──► Disk I/O                │
│  └─ visualize() ──► Figures            │
│                                         │
│  batch_analysis()                      │
│  └─ Process multiple patterns          │
│                                         │
└─────────────────────────────────────────┘
```

### 3️⃣ Metrics Layer

```
┌──────────────────────────────────────────────────────┐
│                 Core Metrics                         │
├──────────────────┬───────────────┬───────────────────┤
│                  │               │                   │
│  Lacunarity      │  Percolation  │  Multifractal     │
│  ============    │  ===========  │  =============    │
│                  │               │                   │
│  ┌────────────┐  │ ┌──────────┐ │ ┌──────────────┐  │
│  │ Rasterize  │  │ │ Build    │ │ │ Box-counting │  │
│  │ Points     │  │ │ Network  │ │ │ Probability  │  │
│  └─────┬──────┘  │ └────┬─────┘ │ └──────┬───────┘  │
│        ▼         │      ▼       │        ▼          │
│  ┌────────────┐  │ ┌──────────┐ │ ┌──────────────┐  │
│  │ Gliding    │  │ │ Largest  │ │ │ Moment Sum   │  │
│  │ Box        │  │ │ Component│ │ │ χ(q,ε)       │  │
│  └─────┬──────┘  │ └────┬─────┘ │ └──────┬───────┘  │
│        ▼         │      ▼       │        ▼          │
│  ┌────────────┐  │ ┌──────────┐ │ ┌──────────────┐  │
│  │ Calculate  │  │ │ Find r_p │ │ │ Calculate    │  │
│  │ Λ(k)       │  │ │          │ │ │ τ(q), D(q)   │  │
│  └─────┬──────┘  │ └────┬─────┘ │ └──────┬───────┘  │
│        ▼         │      ▼       │        ▼          │
│  ┌────────────┐  │ ┌──────────┐ │ ┌──────────────┐  │
│  │ Summary    │  │ │ Network  │ │ │ Legendre     │  │
│  │ by Scale   │  │ │ Metrics  │ │ │ Transform    │  │
│  └────────────┘  │ └──────────┘ │ └──────────────┘  │
│                  │               │                   │
└──────────────────┴───────────────┴───────────────────┘
```

### 4️⃣ Utility Layer

```
┌─────────────────────────────────────────┐
│            Utilities                    │
├──────────────────┬──────────────────────┤
│                  │                      │
│  Data Loader     │     I/O Utils        │
│  ============    │     =========        │
│                  │                      │
│  load_points()   │  save_results()      │
│  load_network()  │  load_results()      │
│  create_tiles()  │  export_summary()    │
│  sample_data()   │  create_dirs()       │
│                  │  save_network()      │
│                  │                      │
└──────────────────┴──────────────────────┘
```

### 5️⃣ Visualization Layer

```
┌─────────────────────────────────────────┐
│          Visualization                  │
├─────────────────────────────────────────┤
│                                         │
│  plot_lacunarity()                     │
│  ├─ Λ vs. scale (log-log)              │
│  └─ Scale categories highlighted       │
│                                         │
│  plot_percolation()                    │
│  ├─ S₁/N transition curve               │
│  └─ Network topology metrics           │
│                                         │
│  plot_multifractal()                   │
│  ├─ D(q) spectrum                      │
│  └─ f(α) singularity spectrum          │
│                                         │
│  plot_combined_metrics()               │
│  └─ All three metrics integrated       │
│                                         │
│  plot_comparison_matrix()              │
│  └─ Multi-pattern comparison           │
│                                         │
└─────────────────────────────────────────┘
```

---

## Data Flow Diagram

### Single Analysis Flow

```
Input File (*.gpkg)
        │
        ▼
 ┌──────────────┐
 │ load_points()│
 └──────┬───────┘
        │
        ▼
┌────────────────────┐
│ GeoDataFrame       │
│ (points in EPSG:   │
│  3857)             │
└────────┬───────────┘
         │
         ▼
┌────────────────────────┐
│ OpenSparsityAnalyzer   │
│ (points, config)       │
└────────┬───────────────┘
         │
         ├──────────────────────────┐
         │                          │
         ▼                          ▼
┌────────────────┐      ┌────────────────────┐
│ run_lacunarity │      │ run_percolation    │
└────────┬───────┘      └─────────┬──────────┘
         │                        │
         │              ┌─────────┴──────────┐
         │              │                     │
         ▼              ▼                     ▼
   ┌─────────┐   ┌──────────┐      ┌──────────────┐
   │ Λ(k)    │   │ S₁/N, r_p│      │ D(q), f(α)   │
   └────┬────┘   └────┬─────┘      └──────┬───────┘
        │             │                    │
        └─────────────┴────────────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │ Compile Summary  │
            └─────────┬────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
   ┌─────────┐               ┌──────────┐
   │ CSV     │               │ Figures  │
   │ JSON    │               │ (PNG)    │
   └─────────┘               └──────────┘
```

### Batch Analysis Flow

```
Input Directory
    │
    ├─ pattern1.gpkg
    ├─ pattern2.gpkg
    └─ pattern3.gpkg
        │
        ▼
   ┌──────────────┐
   │ Load all     │
   │ patterns     │
   └──────┬───────┘
          │
          ▼
    For each pattern:
          │
          ├─► Analyzer 1 ──► Results 1 ──► Save 1
          │
          ├─► Analyzer 2 ──► Results 2 ──► Save 2
          │
          └─► Analyzer 3 ──► Results 3 ──► Save 3
                                  │
                                  ▼
                        ┌──────────────────┐
                        │ Aggregate Summary│
                        └────────┬─────────┘
                                 │
                                 ▼
                     combined_summary.csv
```

---

## Configuration Flow

```
config_example.json
        │
        ├─ lacunarity: {pixel_size, window_sizes}
        ├─ percolation: {thresholds, method}
        └─ multifractal: {q_values, box_sizes}
        │
        ▼
   ┌──────────────┐
   │ Load config  │
   │ (optional)   │
   └──────┬───────┘
          │
          ▼
   ┌──────────────────────┐
   │ Merge with defaults  │
   │ from _default_config │
   └──────┬───────────────┘
          │
          ▼
   ┌──────────────────────┐
   │ Pass to each metric  │
   │ function             │
   └──────────────────────┘
          │
          ├─► Lacunarity gets pixel_size, window_sizes
          ├─► Percolation gets thresholds, method
          └─► Multifractal gets q_values, box_sizes
```

---

## Module Dependencies

```
main.py
  │
  └─► src.pipeline
        │
        ├─► src.metrics.lacunarity
        │     │
        │     ├─► numpy
        │     ├─► scipy.ndimage
        │     ├─► geopandas
        │     └─► pandas
        │
        ├─► src.metrics.percolation
        │     │
        │     ├─► numpy
        │     ├─► networkx
        │     ├─► scipy.spatial
        │     ├─► geopandas
        │     └─► pandas
        │
        ├─► src.metrics.multifractal
        │     │
        │     ├─► numpy
        │     ├─► scipy.stats
        │     ├─► geopandas
        │     └─► pandas
        │
        ├─► src.utils.data_loader
        │     │
        │     ├─► geopandas
        │     ├─► shapely
        │     └─► numpy
        │
        ├─► src.utils.io_utils
        │     │
        │     ├─► pandas
        │     ├─► json
        │     └─► pathlib
        │
        └─► src.visualization.plots
              │
              ├─► matplotlib
              ├─► seaborn
              └─► numpy
```

---

## Class Hierarchy

```
OpenSparsityAnalyzer
├── Attributes:
│   ├── points: GeoDataFrame
│   ├── config: dict
│   └── results: dict
│
├── Methods:
│   ├── __init__(points, config)
│   ├── run_lacunarity() → DataFrame
│   ├── run_percolation() → DataFrame
│   ├── run_multifractal() → (DataFrame, dict)
│   ├── run_all() → dict
│   ├── save(output_dir, prefix)
│   ├── visualize(output_dir, show) → dict[Figure]
│   └── _compile_summary() → dict
│
└── Static Methods:
    └── _default_config() → dict
```

---

## File System Organization

```
three_indicator/
│
├─ 📂 Root Files
│  ├─ main.py               (Entry point)
│  ├─ requirements.txt      (Dependencies)
│  ├─ config_example.json   (Template)
│  ├─ test_installation.py  (Verification)
│  └─ LICENSE              (MIT)
│
├─ 📂 Documentation
│  ├─ README.md            (Main guide)
│  ├─ QUICKSTART.md        (Tutorial)
│  ├─ METRICS_REFERENCE.md (Technical)
│  ├─ PROJECT_STRUCTURE.md (Organization)
│  ├─ ARCHITECTURE.md      (This file)
│  ├─ IMPLEMENTATION_SUMMARY.md
│  └─ CHANGELOG.md         (History)
│
├─ 📂 src/                 (Source code)
│  ├─ __init__.py
│  ├─ pipeline.py          (Orchestration)
│  │
│  ├─ 📂 metrics/
│  │  ├─ __init__.py
│  │  ├─ lacunarity.py     (250+ lines)
│  │  ├─ percolation.py    (300+ lines)
│  │  └─ multifractal.py   (350+ lines)
│  │
│  ├─ 📂 utils/
│  │  ├─ __init__.py
│  │  ├─ data_loader.py    (200+ lines)
│  │  └─ io_utils.py       (150+ lines)
│  │
│  └─ 📂 visualization/
│     ├─ __init__.py
│     └─ plots.py          (450+ lines)
│
└─ 📂 output/              (Generated)
   ├─ summary/
   └─ pattern_name/
      ├─ *.csv
      ├─ *.json
      └─ figures/*.png
```

---

## Execution Flow

### Demo Command

```
$ python main.py demo

1. Parse arguments
2. Generate synthetic patterns
   ├─ clustered
   ├─ random
   └─ grid
3. Call batch_analysis()
4. For each pattern:
   ├─ Create analyzer
   ├─ Run all metrics
   ├─ Save results
   └─ Generate figures
5. Create combined summary
6. Print completion message
```

### Analyze Command

```
$ python main.py analyze data.gpkg --output results/

1. Parse arguments
2. Load points from file
3. Load config (if specified)
4. Create OpenSparsityAnalyzer
5. Run all three metrics
6. Save results to output/
7. Generate visualizations
8. Print summary statistics
```

---

## Performance Characteristics

### Computational Complexity

| Component | Time | Space | Bottleneck |
|-----------|------|-------|------------|
| Lacunarity | O(n·k²) | O(w·h) | Sliding window |
| Percolation | O(n²) | O(n²) | Distance matrix |
| Multifractal | O(n·q·s) | O(boxes) | Box counting |

*n=points, k=window, w/h=raster, q=moments, s=scales*

### Scaling Behavior

```
Points (n)     Lacunarity    Percolation    Multifractal
---------------------------------------------------------
100            <1s           <1s            ~2s
500            ~2s           ~5s            ~10s
1,000          ~5s           ~15s           ~20s
5,000          ~20s          ~3min          ~2min
10,000         ~1min         ~12min         ~5min
```

*Approximate times on modern CPU (single core)*

---

## Extension Points

### Adding New Metrics

```
1. Create: src/metrics/new_metric.py
2. Implement:
   ├─ calculate_new_metric(points, **kwargs)
   └─ new_metric_summary(results)
3. Import in: src/metrics/__init__.py
4. Add to pipeline:
   └─ OpenSparsityAnalyzer.run_new_metric()
5. Add visualization:
   └─ src/visualization/plots.py
      └─ plot_new_metric()
```

### Custom Visualizations

```
src/visualization/plots.py
├─ Follow naming: plot_<metric>()
├─ Use seaborn style
├─ Return Figure object
└─ Save to file if output_file provided
```

---

**OpenSparsity Project**  
*Architecture Documentation v2.0.0*

