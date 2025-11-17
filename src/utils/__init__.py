"""
Utility functions for OpenSparsity analysis.
"""

from dataclasses import dataclass
from typing import Any, Dict

from .data_loader import (
    load_points,
    load_network,
    create_analysis_tiles,
    filter_points_by_tile,
    sample_points_random,
    sample_points_spatial_grid,
    sample_points_uniform_spacing,
    sample_points_density_based,
    prepare_sample_data,
)
from .io_utils import (
    save_results,
    load_results,
    export_summary,
    create_output_structure,
    save_network,
)

try:
    from .hybrid_network import HybridNetwork, build_hybrid_network  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    @dataclass
    class HybridNetwork:
        """
        Minimal placeholder hybrid network container.

        Provides the attributes expected by the pipeline when the optional
        hybrid network utilities are not available.
        """

        nodes: Any
        edges: Any

    def build_hybrid_network(*_args: Any, **_kwargs: Dict[str, Any]) -> HybridNetwork:
        raise ImportError(
            "Hybrid network utilities are not available. "
            "Add `src/utils/hybrid_network.py` or install the optional dependencies."
        )


__all__ = [
    'load_points',
    'load_network',
    'create_analysis_tiles',
    'filter_points_by_tile',
    'sample_points_random',
    'sample_points_spatial_grid',
    'sample_points_uniform_spacing',
    'sample_points_density_based',
    'prepare_sample_data',
    'save_results',
    'load_results',
    'export_summary',
    'create_output_structure',
    'save_network',
    'HybridNetwork',
    'build_hybrid_network',
]
