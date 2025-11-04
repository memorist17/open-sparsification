#!/usr/bin/env python3
"""
OpenSparsity Metrics - Main CLI Interface

Command-line interface for three-indicator analysis:
- Lacunarity (local vacancy structure)
- Percolation (critical connectivity)
- Multifractal (hierarchical structure)

Usage:
    python main.py analyze <input_file> --output <output_dir>
    python main.py batch <input_dir> --output <output_dir>
    python main.py demo
"""

import argparse
import sys
from pathlib import Path
import geopandas as gpd

from src.pipeline import OpenSparsityAnalyzer, batch_analysis
from src.utils.data_loader import load_points, prepare_sample_data
from src.utils.io_utils import create_output_structure


def cmd_analyze(args):
    """Run analysis on single point dataset."""
    print("="*60)
    print("OpenSparsity Single Pattern Analysis")
    print("="*60)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print()
    
    # Load data
    print("Loading data...")
    points = load_points(args.input, crs=args.crs)
    print(f"Loaded {len(points)} points")
    
    # Configure
    config = {}
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Run analysis
    analyzer = OpenSparsityAnalyzer(points, config)
    results = analyzer.run_all(verbose=args.verbose)
    
    # Save results
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    analyzer.save(str(output_path), prefix=args.prefix)
    
    # Visualize
    if not args.no_plot:
        fig_dir = output_path / 'figures'
        fig_dir.mkdir(exist_ok=True)
        analyzer.visualize(output_dir=str(fig_dir), show=args.show)
    
    print()
    print("="*60)
    print("Analysis Complete")
    print(f"Results saved to: {output_path}")
    print("="*60)


def cmd_batch(args):
    """Run batch analysis on multiple datasets."""
    print("="*60)
    print("OpenSparsity Batch Analysis")
    print("="*60)
    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output}")
    print()
    
    # Find all point files
    input_path = Path(args.input_dir)
    pattern = args.pattern or "*.gpkg"
    files = list(input_path.glob(pattern))
    
    if len(files) == 0:
        print(f"No files found matching pattern: {pattern}")
        sys.exit(1)
    
    print(f"Found {len(files)} files")
    
    # Load all datasets
    points_dict = {}
    for file in files:
        name = file.stem
        print(f"Loading: {name}...")
        points = load_points(str(file), crs=args.crs)
        points_dict[name] = points
    
    # Configure
    config = {}
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Run batch analysis
    results = batch_analysis(
        points_dict,
        output_dir=args.output,
        config=config,
        verbose=args.verbose
    )
    
    print()
    print("="*60)
    print(f"Batch analysis complete: {len(results)} patterns analyzed")
    print(f"Results saved to: {args.output}")
    print("="*60)


def cmd_demo(args):
    """Run demo with synthetic data."""
    print("="*60)
    print("OpenSparsity Demo")
    print("="*60)
    print("Generating synthetic point patterns...")
    print()
    
    # Generate synthetic patterns
    patterns = {
        'singlelinear': prepare_sample_data(500, 'singlelinear', seed=42),
        'uniform': prepare_sample_data(500, 'uniform', seed=42),
        'random': prepare_sample_data(500, 'random', seed=42),
        'radial': prepare_sample_data(500, 'radial', seed=42),
        'singleclustered': prepare_sample_data(500, 'singleclustered', seed=42),
        'multiclustered': prepare_sample_data(500, 'multiclustered', seed=42),
    }
    
    for name, points in patterns.items():
        print(f"  {name}: {len(points)} points")
    
    # Run batch analysis
    output_dir = args.output or './demo_output'
    print(f"\nRunning analysis...")
    print(f"Output directory: {output_dir}")
    print()
    
    results = batch_analysis(
        patterns,
        output_dir=output_dir,
        verbose=True
    )
    
    print()
    print("="*60)
    print("Demo Complete")
    print(f"Results saved to: {output_dir}")
    print()
    print("Explore the results:")
    print(f"  - Summary: {output_dir}/summary/combined_summary.csv")
    print(f"  - Visualizations: {output_dir}/*/figures/")
    print("="*60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenSparsity Metrics - Three-Indicator Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single pattern
  python main.py analyze data/buildings.gpkg --output results/buildings
  
  # Batch analysis
  python main.py batch data/patterns/ --output results/batch
  
  # Run demo
  python main.py demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Analyze command
    parser_analyze = subparsers.add_parser('analyze', help='Analyze single pattern')
    parser_analyze.add_argument('input', help='Input point file (*.gpkg, *.shp, *.geojson)')
    parser_analyze.add_argument('--output', '-o', required=True, help='Output directory')
    parser_analyze.add_argument('--prefix', default='analysis', help='Output file prefix')
    parser_analyze.add_argument('--config', '-c', help='Configuration JSON file')
    parser_analyze.add_argument('--crs', default='EPSG:3857', help='Target CRS (default: EPSG:3857)')
    parser_analyze.add_argument('--no-plot', action='store_true', help='Skip visualization')
    parser_analyze.add_argument('--show', action='store_true', help='Display plots interactively')
    parser_analyze.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Batch command
    parser_batch = subparsers.add_parser('batch', help='Batch analysis on multiple patterns')
    parser_batch.add_argument('input_dir', help='Input directory with point files')
    parser_batch.add_argument('--output', '-o', required=True, help='Output directory')
    parser_batch.add_argument('--pattern', '-p', help='File pattern (default: *.gpkg)')
    parser_batch.add_argument('--config', '-c', help='Configuration JSON file')
    parser_batch.add_argument('--crs', default='EPSG:3857', help='Target CRS')
    parser_batch.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Demo command
    parser_demo = subparsers.add_parser('demo', help='Run demo with synthetic data')
    parser_demo.add_argument('--output', '-o', help='Output directory (default: ./demo_output)')
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Set verbose default
    if not hasattr(args, 'verbose'):
        args.verbose = True
    
    # Execute command
    if args.command == 'analyze':
        cmd_analyze(args)
    elif args.command == 'batch':
        cmd_batch(args)
    elif args.command == 'demo':
        cmd_demo(args)


if __name__ == "__main__":
    main()

