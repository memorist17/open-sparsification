#!/usr/bin/env python3
"""生成済み指標データからペアプロットを出力するスクリプト (バブル散布)"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

project_root = Path(__file__).resolve().parent.parent
results_path = project_root / "data" / "processed" / "real_analysis_results.csv"
if not results_path.exists():
    raise FileNotFoundError(f"分析結果が見つかりません: {results_path}")

metrics_df = pd.read_csv(results_path)
metrics = ["sparsity", "resilience", "multi_nodality", "permeability"]

# 欠損がある行は除外
metrics_df = metrics_df.dropna(subset=["sparsity", "resilience", "multi_nodality", "permeability"])

per_values = metrics_df["permeability"].to_numpy()
if per_values.max() > per_values.min():
    bubble_sizes = np.interp(per_values, (per_values.min(), per_values.max()), (40, 220))
else:
    bubble_sizes = np.full_like(per_values, 100.0)

color_values = metrics_df["multi_nodality"].to_numpy()

sns.set_theme(style="whitegrid", context="talk")

pair_grid = sns.PairGrid(metrics_df, vars=metrics, corner=True, diag_sharey=False)

pair_grid.map_diag(sns.histplot, color="#6c757d", edgecolor="white", linewidth=0.5)


def lower_scatter(x, y, **kwargs):
    ax = plt.gca()
    mask = ~np.isnan(x) & ~np.isnan(y)
    ax.scatter(
        x[mask],
        y[mask],
        s=bubble_sizes[mask],
        c=color_values[mask],
        cmap="viridis",
        alpha=0.75,
        edgecolor='none'
    )


pair_grid.map_lower(lower_scatter)

# カラーバーを追加
norm = plt.Normalize(color_values.min(), color_values.max())
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
sm.set_array([])
pair_grid.fig.colorbar(sm, ax=pair_grid.axes[1:, 0], fraction=0.02, pad=0.04, label="Polycentricity")

pair_grid.fig.subplots_adjust(top=0.92)
pair_grid.fig.suptitle(
    "Pair Plot of Urban Morphological Metrics\n"
    "Color: Polycentricity · Bubble size: Permeability",
    fontsize=18,
)

output_dir = project_root / "figures"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "urban_metrics_pairplot.png"
pair_grid.fig.savefig(output_path, dpi=200, bbox_inches="tight")
plt.close(pair_grid.fig)

print(f"✅ ペアプロットを {output_path} に保存しました。")
