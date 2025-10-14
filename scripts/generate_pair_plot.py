#!/usr/bin/env python3
"""主要指標のペアプロットを生成して保存"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def load_metric_dataframe(project_root: Path) -> pd.DataFrame:
    processed_dir = project_root / "data" / "processed"
    realistic_path = processed_dir / "real_analysis_results.csv"
    fallback_path = processed_dir / "sample_analysis_results.csv"

    if realistic_path.exists():
        return pd.read_csv(realistic_path)
    if fallback_path.exists():
        return pd.read_csv(fallback_path)
    raise FileNotFoundError("分析結果のCSVが見つかりません。先にデータ生成スクリプトを実行してください。")


def create_pair_plot(df: pd.DataFrame, output_path: Path) -> None:
    metrics = ['sparsity', 'resilience', 'multi_nodality', 'permeability']
    available_metrics = [metric for metric in metrics if metric in df.columns]
    if len(available_metrics) < 2:
        raise ValueError("ペアプロットを生成するための指標が不足しています。")

    plot_df = df[available_metrics].dropna()
    sns.set_theme(style="whitegrid", context="talk")

    grid = sns.PairGrid(plot_df, vars=available_metrics, corner=True)
    grid.map_lower(sns.scatterplot, s=30, alpha=0.6, edgecolor=None, color="#1f77b4")
    grid.map_diag(sns.histplot, kde=True, color="#4ECDC4", edgecolor="white")

    grid.fig.suptitle(
        "Urban Morphology Metrics Pair Plot",
        fontsize=18,
        y=1.02,
    )

    for ax in grid.axes.flatten():
        if ax is None:
            continue
        ax.set_facecolor("white")

    grid.fig.tight_layout()
    grid.fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(grid.fig)


def main() -> None:
    project_root = Path(__file__).parent.parent
    df = load_metric_dataframe(project_root)
    output_path = project_root / "data" / "processed" / "metrics_pair_plot.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    create_pair_plot(df, output_path)
    print(f"✅ Pair plot saved to {output_path}")


if __name__ == "__main__":  # pragma: no cover
    main()

