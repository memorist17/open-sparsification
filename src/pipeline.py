"""
Main analysis pipeline for OpenSparsity three-indicator framework.

Coordinates Lacunarity, Percolation, and Multifractal analyses.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from tqdm import tqdm

from .metrics import (
    calculate_lacunarity,
    lacunarity_summary,
    lacunarity_scale_aggregation,
    calculate_percolation,
    calculate_percolation_network,
    percolation_summary,
    calculate_multifractal
)
from .utils import create_output_structure, save_results, HybridNetwork
from .visualization import (
    plot_lacunarity,
    plot_percolation,
    plot_multifractal,
    plot_combined_metrics
)


class OpenSparsityAnalyzer:
    """
    Main analyzer class for three-indicator framework.
    
    Attributes
    ----------
    points : gpd.GeoDataFrame
        Point data (buildings, facilities, etc.)
    config : dict
        Configuration parameters
    results : dict
        Analysis results
    """
    
    def __init__(
        self,
        points: gpd.GeoDataFrame,
        config: Optional[Dict] = None,
        network: Optional[HybridNetwork] = None,
    ):
        """
        Initialize analyzer.
        
        Parameters
        ----------
        points : gpd.GeoDataFrame
            Point geometries
        config : dict, optional
            Configuration with keys:
            - 'pixel_size': Raster resolution (default: 5.0 m)
            - 'lacunarity_scales': Window sizes for lacunarity
            - 'percolation_thresholds': Distance thresholds
            - 'multifractal_q': Moment orders
            - 'box_sizes': Box sizes for multifractal
        """
        self.points = points
        self.config = config or self._default_config()
        self.results = {}
        self.network = network
    
    @staticmethod
    def _default_config() -> Dict:
        """Default configuration parameters."""
        return {
            # Lacunarity
            'pixel_size': 5.0,
            'lacunarity_scales': [3, 5, 7, 11, 15, 21, 31, 41, 51, 71, 101],
            
            # Percolation
            'percolation_thresholds': [10, 25, 50, 100, 200, 400, 800],
            'percolation_method': 'radius',
            
            # Multifractal
            'multifractal_q': list(np.linspace(-5, 5, 21)),
            'box_sizes': [10, 25, 50, 100, 200, 400, 800, 1000],
        }
    
    def run_lacunarity(self, verbose: bool = True) -> pd.DataFrame:
        """
        Run lacunarity analysis.
        
        Parameters
        ----------
        verbose : bool
            Print progress messages
        
        Returns
        -------
        summary : pd.DataFrame
            Lacunarity summary by scale
        """
        if verbose:
            print("Running Lacunarity Analysis...")
        
        # Calculate lacunarity
        lac = calculate_lacunarity(
            self.points,
            pixel_size=self.config['pixel_size'],
            window_sizes=self.config['lacunarity_scales']
        )

        if not lac:
            summary = pd.DataFrame(
                columns=['scale_pixels', 'scale_meters', 'lacunarity', 'scale_category']
            )
            aggregation = {}
        else:
            summary = lacunarity_summary(lac, self.config['pixel_size'])
            aggregation = lacunarity_scale_aggregation(summary)
        
        # Store results
        self.results['lacunarity'] = summary
        self.results['lacunarity_aggregation'] = aggregation
        
        if verbose:
            print(f"  Completed. Scales analyzed: {len(summary)}")
            print(f"  Scale aggregation: {aggregation}")
        
        return summary
    
    def run_percolation(self, verbose: bool = True) -> pd.DataFrame:
        """
        Run percolation analysis.
        
        Parameters
        ----------
        verbose : bool
            Print progress messages
        
        Returns
        -------
        results : pd.DataFrame
            Percolation results by threshold
        """
        if verbose:
            print("Running Percolation Analysis...")
        
        # Calculate percolation
        method = self.config.get('percolation_method', 'radius')

        if method == 'network':
            if self.network is None:
                raise ValueError("Percolation method 'network' requires a HybridNetwork instance.")

            edges_iter = (
                (int(row.source), int(row.target), float(row.length))
                for row in self.network.edges.itertuples()
                if float(row.length) > 0.0
            )
            perc = calculate_percolation_network(
                num_nodes=len(self.network.nodes),
                weighted_edges=edges_iter,
                thresholds=self.config.get('percolation_thresholds'),
            )
        else:
            perc = calculate_percolation(
                self.points,
                thresholds=self.config['percolation_thresholds'],
                method=method
            )
        
        # Summarize
        summary = percolation_summary(perc)
        
        # Store results
        self.results['percolation'] = perc
        self.results['percolation_summary'] = summary
        
        if verbose:
            print(f"  Completed. Percolation threshold r_p = {summary['r_p']:.2f} m")
            print(f"  Max connectivity: {summary['max_S1_ratio']:.3f}")
        
        return perc
    
    def run_multifractal(self, verbose: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        Run multifractal analysis.
        
        Parameters
        ----------
        verbose : bool
            Print progress messages
        
        Returns
        -------
        spectrum : pd.DataFrame
            Multifractal spectrum
        summary : dict
            Summary statistics
        """
        if verbose:
            print("Running Multifractal Analysis...")
        
        # Calculate multifractal
        spectrum, summary = calculate_multifractal(
            self.points,
            q_values=self.config['multifractal_q'],
            box_sizes=self.config['box_sizes']
        )
        
        # Store results
        self.results['multifractal'] = spectrum
        self.results['multifractal_summary'] = summary
        
        if verbose:
            print(f"  Completed. Spectrum width Δα = {summary['Delta_alpha']:.4f}")
            print(f"  D0 = {summary['D0']:.3f}, D2 = {summary['D2']:.3f}")
        
        return spectrum, summary
    
    def run_all(self, verbose: bool = True) -> Dict:
        """
        Run complete three-indicator analysis.
        
        Parameters
        ----------
        verbose : bool
            Print progress messages
        
        Returns
        -------
        results : dict
            All analysis results
        """
        if verbose:
            print("=" * 60)
            print("OpenSparsity Three-Indicator Analysis")
            print("=" * 60)
            print(f"Input points: {len(self.points)}")
            print(f"Bounds: {self.points.total_bounds}")
            print()
        
        # Run analyses
        self.run_lacunarity(verbose=verbose)
        self.run_percolation(verbose=verbose)
        self.run_multifractal(verbose=verbose)
        
        # Compile summary
        self.results['summary'] = self._compile_summary()
        
        if verbose:
            print()
            print("=" * 60)
            print("Analysis Complete")
            print("=" * 60)
        
        return self.results
    
    def _compile_summary(self) -> Dict:
        """Compile cross-metric summary."""
        summary = {
            'n_points': len(self.points),
            'bounds': self.points.total_bounds.tolist(),
        }
        
        # Lacunarity
        if 'lacunarity_aggregation' in self.results:
            for scale, value in self.results['lacunarity_aggregation'].items():
                summary[f'lacunarity_{scale}'] = value
        
        # Percolation
        if 'percolation_summary' in self.results:
            for key, value in self.results['percolation_summary'].items():
                summary[f'percolation_{key}'] = value
        
        # Multifractal
        if 'multifractal_summary' in self.results:
            for key, value in self.results['multifractal_summary'].items():
                summary[f'multifractal_{key}'] = value
        
        return summary
    
    def save(self, output_dir: str, prefix: str = "analysis") -> None:
        """
        Save results to disk.
        
        Parameters
        ----------
        output_dir : str
            Output directory
        prefix : str
            File prefix
        """
        save_results(self.results, output_dir, prefix)
    
    def visualize(
        self,
        output_dir: Optional[str] = None,
        show: bool = True
    ) -> Dict:
        """
        Create visualizations.
        
        Parameters
        ----------
        output_dir : str, optional
            Directory to save figures
        show : bool
            Display figures interactively
        
        Returns
        -------
        figs : dict
            Dictionary of matplotlib figures
        """
        import matplotlib.pyplot as plt
        
        figs = {}
        
        # Individual plots
        lac_df = self.results.get('lacunarity')
        if isinstance(lac_df, pd.DataFrame) and len(lac_df) >= 3:
            output_file = Path(output_dir) / 'lacunarity.png' if output_dir else None
            figs['lacunarity'] = plot_lacunarity(
                lac_df,
                output_file=str(output_file) if output_file else None
            )
        
        perc_df = self.results.get('percolation')
        if isinstance(perc_df, pd.DataFrame) and len(perc_df) >= 3:
            output_file = Path(output_dir) / 'percolation.png' if output_dir else None
            r_p = self.results.get('percolation_summary', {}).get('r_p')
            figs['percolation'] = plot_percolation(
                perc_df,
                r_p=r_p,
                output_file=str(output_file) if output_file else None
            )
        
        mf_df = self.results.get('multifractal')
        if isinstance(mf_df, pd.DataFrame) and len(mf_df) >= 3:
            output_file = Path(output_dir) / 'multifractal.png' if output_dir else None
            figs['multifractal'] = plot_multifractal(
                mf_df,
                output_file=str(output_file) if output_file else None
            )
        
        # Combined plot
        if (
            isinstance(lac_df, pd.DataFrame) and len(lac_df) >= 3 and
            isinstance(perc_df, pd.DataFrame) and len(perc_df) >= 3 and
            isinstance(mf_df, pd.DataFrame) and len(mf_df) >= 3
        ):
            output_file = Path(output_dir) / 'combined.png' if output_dir else None
            figs['combined'] = plot_combined_metrics(
                lac_df,
                perc_df,
                mf_df,
                output_file=str(output_file) if output_file else None
            )
        
        if show:
            plt.show()
        
        return figs


def batch_analysis(
    points_dict: Dict[str, gpd.GeoDataFrame],
    output_dir: str,
    config: Optional[Dict] = None,
    networks: Optional[Dict[str, HybridNetwork]] = None,
    verbose: bool = True
) -> Dict[str, Dict]:
    """
    Run batch analysis on multiple point datasets.
    
    Parameters
    ----------
    points_dict : dict
        {pattern_name: points_gdf}
    output_dir : str
        Base output directory
    config : dict, optional
        Shared configuration
    verbose : bool
        Print progress
    
    Returns
    -------
    all_results : dict
        {pattern_name: results}
    """
    all_results = {}
    
    # Create output structure
    paths = create_output_structure(output_dir)

    save_figures_flag = True
    analyzer_config = None
    if config is not None:
        save_figures_flag = config.get('save_figures', True)
        analyzer_config = {k: v for k, v in config.items() if k != 'save_figures'}
    else:
        analyzer_config = None
    
    for pattern_name, points in tqdm(points_dict.items(), desc="Batch analysis"):
        if verbose:
            print(f"\n{'='*60}")
            print(f"Processing: {pattern_name}")
            print(f"{'='*60}")
        
        # Run analysis
        analyzer_network = networks.get(pattern_name) if networks else None
        analyzer = OpenSparsityAnalyzer(points, analyzer_config, network=analyzer_network)
        results = analyzer.run_all(verbose=verbose)
        
        # Save results
        pattern_dir = paths['base'] / pattern_name
        pattern_dir.mkdir(exist_ok=True)
        analyzer.save(str(pattern_dir), prefix=pattern_name)
        
        # Save point data for visualization
        points_file = pattern_dir / f"{pattern_name}_points.gpkg"
        points.to_file(str(points_file), driver='GPKG')
        if verbose:
            print(f"Saved point data: {points_file}")

        if analyzer_network is not None:
            network_dir = pattern_dir / "network"
            network_dir.mkdir(exist_ok=True)
            nodes_path = network_dir / f"{pattern_name}_nodes.gpkg"
            edges_path = network_dir / f"{pattern_name}_edges.parquet"
            analyzer_network.nodes.to_file(str(nodes_path), driver="GPKG")
            analyzer_network.edges.to_parquet(edges_path, index=False)
            if verbose:
                print(f"Saved network nodes: {nodes_path}")
                print(f"Saved network edges: {edges_path}")
        
        # Save visualizations if requested and data sufficient
        if save_figures_flag:
            fig_dir = pattern_dir / 'figures'
            fig_dir.mkdir(exist_ok=True)
            analyzer.visualize(output_dir=str(fig_dir), show=False)
        
        all_results[pattern_name] = results
    
    # Export combined summary
    summaries = pd.DataFrame([
        {'pattern': name, **res['summary']}
        for name, res in all_results.items()
    ])
    summaries.to_csv(paths['summary'] / 'combined_summary.csv', index=False)
    
    if verbose:
        print(f"\n{'='*60}")
        print("Batch analysis complete")
        print(f"Results saved to: {output_dir}")
        print(f"{'='*60}")
    
    return all_results


# Example usage
if __name__ == "__main__":
    from .utils.data_loader import prepare_sample_data
    
    # Generate test data
    print("Generating test data...")
    points_clustered = prepare_sample_data(500, 'clustered')
    points_random = prepare_sample_data(500, 'random')
    
    # Single analysis
    print("\n" + "="*60)
    print("Single Pattern Analysis")
    print("="*60)
    analyzer = OpenSparsityAnalyzer(points_clustered)
    results = analyzer.run_all(verbose=True)
    
    # Save and visualize
    analyzer.save('./output_test/single', prefix='clustered')
    figs = analyzer.visualize(output_dir='./output_test/single/figures', show=False)
    
    print("\nResults keys:", list(results.keys()))
    print("\nSummary:")
    for key, value in results['summary'].items():
        print(f"  {key}: {value}")
    
    # Batch analysis
    print("\n" + "="*60)
    print("Batch Analysis")
    print("="*60)
    batch_results = batch_analysis(
        {
            'clustered': points_clustered,
            'random': points_random
        },
        output_dir='./output_test/batch',
        verbose=True
    )
    
    print("\nBatch complete!")

