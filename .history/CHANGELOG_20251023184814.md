# Changelog

All notable changes to the OpenSparsity Three-Indicator Framework will be documented in this file.

## [2.0.0] - 2025-10-23

### Added
- Initial release of unified three-indicator framework
- Lacunarity analysis module with gliding box method
- Percolation analysis with network connectivity metrics
- Multifractal analysis with D(q) and f(α) spectra
- Integrated pipeline with `OpenSparsityAnalyzer` class
- Batch processing capabilities
- CLI interface with `analyze`, `batch`, and `demo` commands
- Comprehensive visualization suite
- Publication-quality plot generation
- JSON configuration support
- Data I/O utilities for geospatial formats
- Synthetic data generation for testing
- Complete documentation and examples

### Features
- **Lacunarity**: Multi-scale vacancy structure analysis
  - Gliding box algorithm
  - Scale categorization (small/medium/large)
  - Raster-based implementation
  
- **Percolation**: Critical connectivity analysis
  - Distance-threshold network construction
  - Largest component tracking
  - Percolation threshold detection
  - Network topology metrics (degree, clustering, path length)
  
- **Multifractal**: Hierarchical structure analysis
  - Generalized dimension D(q) spectrum
  - Singularity spectrum f(α) via Legendre transform
  - Hierarchical diversity measure (Δα)
  - Box-counting probability method

### Documentation
- Comprehensive README with usage examples
- Configuration template with parameter descriptions
- Inline code documentation
- Example workflows for CLI and Python API
- Theoretical background and references

### Dependencies
- NumPy, SciPy, Pandas for scientific computing
- GeoPandas, Shapely, Rasterio for geospatial processing
- NetworkX for graph analysis
- Matplotlib, Seaborn, Plotly for visualization

---

## Future Roadmap

### [2.1.0] - Planned
- [ ] Interactive dashboard with Dash/Plotly
- [ ] Additional network construction methods (k-NN, Delaunay)
- [ ] Spatial partitioning for large datasets
- [ ] Parallel processing support
- [ ] Export to additional formats (HDF5, Parquet)

### [2.2.0] - Planned
- [ ] Cross-scale correlation analysis
- [ ] Statistical significance testing
- [ ] Comparison with null models
- [ ] Time-series analysis support
- [ ] 3D point cloud support

### [3.0.0] - Planned
- [ ] Integration with OpenSparsity ecosystem
- [ ] Real-time analysis capabilities
- [ ] Cloud processing support
- [ ] Machine learning integration
- [ ] Web API service

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 2.0.0 | 2025-10-23 | Initial unified framework release |

---

For detailed changes, see commit history.

