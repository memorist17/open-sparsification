"""
Metrics module for OpenSparsity analysis.

Contains three core metrics:
- lacunarity: Local vacancy structure analysis
- percolation: Critical connectivity analysis
- multifractal: Hierarchical structure analysis
"""

from .lacunarity import calculate_lacunarity, lacunarity_summary
from .percolation import calculate_percolation, percolation_summary
from .multifractal import calculate_multifractal, multifractal_summary

__all__ = [
    'calculate_lacunarity',
    'lacunarity_summary',
    'calculate_percolation',
    'percolation_summary',
    'calculate_multifractal',
    'multifractal_summary',
]

