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
    percolation_summary,
    calculate_multifractal
)
from .utils import create_output_structure, save_results
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
        config: Optional[Dict] = None
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
        
        # Summarize
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
        perc = calculate_percolation(
            self.points,
            thresholds=self.config['percolation_thresholds'],
            method=self.config['percolation_method']
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
        if 'lacunarity' in self.results:
            output_file = Path(output_dir) / 'lacunarity.png' if output_dir else None
            figs['lacunarity'] = plot_lacunarity(
                self.results['lacunarity'],
                output_file=str(output_file) if output_file else None
            )
        
        if 'percolation' in self.results:
            output_file = Path(output_dir) / 'percolation.png' if output_dir else None
            r_p = self.results.get('percolation_summary', {}).get('r_p')
            figs['percolation'] = plot_percolation(
                self.results['percolation'],
                r_p=r_p,
                output_file=str(output_file) if output_file else None
            )
        
        if 'multifractal' in self.results:
            output_file = Path(output_dir) / 'multifractal.png' if output_dir else None
            figs['multifractal'] = plot_multifractal(
                self.results['multifractal'],
                output_file=str(output_file) if output_file else None
            )
        
        # Combined plot
        if all(k in self.results for k in ['lacunarity', 'percolation', 'multifractal']):
            output_file = Path(output_dir) / 'combined.png' if output_dir else None
            figs['combined'] = plot_combined_metrics(
                self.results['lacunarity'],
                self.results['percolation'],
                self.results['multifractal'],
                output_file=str(output_file) if output_file else None
            )
        
        if show:
            plt.show()
        
        return figs


def batch_analysis(
    points_dict: Dict[str, gpd.GeoDataFrame],
    output_dir: str,
    config: Optional[Dict] = None,
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
    
    for pattern_name, points in tqdm(points_dict.items(), desc="Batch analysis"):
        if verbose:
            print(f"\n{'='*60}")
            print(f"Processing: {pattern_name}")
            print(f"{'='*60}")
        
        # Run analysis
        analyzer = OpenSparsityAnalyzer(points, config)
        results = analyzer.run_all(verbose=verbose)
        
        # Save results
        pattern_dir = paths['base'] / pattern_name
        pattern_dir.mkdir(exist_ok=True)
        analyzer.save(str(pattern_dir), prefix=pattern_name)
        
        # Save visualizations
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

