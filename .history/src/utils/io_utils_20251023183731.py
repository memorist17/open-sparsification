"""
Input/Output utilities for saving and loading analysis results.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from typing import Dict, Any, Optional
import pickle


def save_results(
    results: Dict[str, Any],
    output_dir: str,
    prefix: str = "analysis"
) -> None:
    """
    Save analysis results to disk.
    
    Parameters
    ----------
    results : dict
        Analysis results with keys like:
        - 'lacunarity': DataFrame
        - 'percolation': DataFrame
        - 'multifractal': DataFrame
        - 'summary': dict
    output_dir : str
        Output directory path
    prefix : str
        File prefix (e.g., pattern name)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save DataFrames as CSV
    for key, value in results.items():
        if isinstance(value, pd.DataFrame):
            filepath = output_path / f"{prefix}_{key}.csv"
            value.to_csv(filepath, index=False)
            print(f"Saved: {filepath}")
        
        elif isinstance(value, dict):
            # Save dict as JSON
            filepath = output_path / f"{prefix}_{key}.json"
            with open(filepath, 'w') as f:
                # Convert numpy types to native Python types
                serializable = {
                    k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                    for k, v in value.items()
                }
                json.dump(serializable, f, indent=2)
            print(f"Saved: {filepath}")


def load_results(
    input_dir: str,
    prefix: str = "analysis"
) -> Dict[str, Any]:
    """
    Load analysis results from disk.
    
    Parameters
    ----------
    input_dir : str
        Input directory path
    prefix : str
        File prefix
    
    Returns
    -------
    results : dict
        Loaded results
    """
    input_path = Path(input_dir)
    results = {}
    
    # Load CSVs
    for csv_file in input_path.glob(f"{prefix}_*.csv"):
        key = csv_file.stem.replace(f"{prefix}_", "")
        results[key] = pd.read_csv(csv_file)
        print(f"Loaded: {csv_file}")
    
    # Load JSONs
    for json_file in input_path.glob(f"{prefix}_*.json"):
        key = json_file.stem.replace(f"{prefix}_", "")
        with open(json_file, 'r') as f:
            results[key] = json.load(f)
        print(f"Loaded: {json_file}")
    
    return results


def export_summary(
    results_list: list,
    output_file: str,
    format: str = 'csv'
) -> None:
    """
    Export combined summary from multiple analyses.
    
    Parameters
    ----------
    results_list : list of dict
        List of result dictionaries with 'summary' key
    output_file : str
        Output file path
    format : str
        'csv' or 'json'
    """
    summaries = []
    
    for i, res in enumerate(results_list):
        if 'summary' in res:
            summary = res['summary'].copy()
            summary['analysis_id'] = i
            
            # Add pattern info if available
            if 'pattern' in res:
                summary['pattern'] = res['pattern']
            
            summaries.append(summary)
    
    if format == 'csv':
        df = pd.DataFrame(summaries)
        df.to_csv(output_file, index=False)
    elif format == 'json':
        with open(output_file, 'w') as f:
            json.dump(summaries, f, indent=2)
    
    print(f"Exported summary: {output_file}")


def save_network(G, filepath: str, format: str = 'pickle') -> None:
    """
    Save network to file.
    
    Parameters
    ----------
    G : nx.Graph
        Network graph
    filepath : str
        Output file path
    format : str
        'pickle' or 'edgelist'
    """
    if format == 'pickle':
        with open(filepath, 'wb') as f:
            pickle.dump(G, f)
    elif format == 'edgelist':
        import networkx as nx
        nx.write_edgelist(G, filepath)
    
    print(f"Saved network: {filepath}")


def create_output_structure(base_dir: str) -> Dict[str, Path]:
    """
    Create standard output directory structure.
    
    Parameters
    ----------
    base_dir : str
        Base output directory
    
    Returns
    -------
    paths : dict
        Dictionary of output paths
    """
    base_path = Path(base_dir)
    
    paths = {
        'base': base_path,
        'lacunarity': base_path / 'lacunarity',
        'percolation': base_path / 'percolation',
        'multifractal': base_path / 'multifractal',
        'summary': base_path / 'summary',
        'figures': base_path / 'figures',
    }
    
    # Create directories
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return paths


# Example usage
if __name__ == "__main__":
    # Test directory creation
    paths = create_output_structure('./output_test')
    print("Created output structure:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    
    # Test save/load
    test_results = {
        'lacunarity': pd.DataFrame({
            'scale': [10, 50, 100],
            'value': [1.2, 1.5, 1.8]
        }),
        'summary': {
            'metric': 'test',
            'value': 1.5
        }
    }
    
    save_results(test_results, './output_test', prefix='test')
    loaded = load_results('./output_test', prefix='test')
    print("\nLoaded results:")
    print(loaded)

