#!/usr/bin/env python3
"""全指標を含む包括的なペアプロットを作成"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

project_root = Path(__file__).resolve().parent.parent
results_path = project_root / "data" / "processed" / "real_analysis_results.csv"
if not results_path.exists():
    raise FileNotFoundError(f"analysis results not found: {results_path}")

df = pd.read_csv(results_path)

# 全指標を定義
all_metrics = [
    "sparsity", 
    "resilience", 
    "multi_nodality", 
    "permeability", 
    "emergence", 
    "overlap"
]

# 利用可能な指標のみを選択
available_metrics = [metric for metric in all_metrics if metric in df.columns]
print(f"利用可能な指標: {available_metrics}")

df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna(subset=available_metrics, how='any').reset_index(drop=True)


def normalize_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """指定された列を最小値–最大値で正規化"""
    normalized = frame.copy()
    for column in columns:
        if column not in normalized.columns:
            continue
        series = normalized[column].astype(float)
        col_min = series.min()
        col_max = series.max()
        if np.isclose(col_max, col_min):
            normalized[column] = 0.0
        else:
            normalized[column] = (series - col_min) / (col_max - col_min)
    return normalized


normalized_df = normalize_columns(df, available_metrics)

# シンプルな散布図用の設定
point_size = 60
point_color = "#1f77b4"

sns.set_theme(style="whitegrid", context="talk", font_scale=0.8)

pair_grid = sns.PairGrid(normalized_df, vars=available_metrics, corner=True, height=2.8)

pair_grid.map_diag(sns.histplot, color="#adb5bd", edgecolor="white", linewidth=0.5)


def simple_scatter(x, y, **kwargs):
    ax = plt.gca()
    mask = (~np.isnan(x)) & (~np.isnan(y))
    ax.scatter(
        x[mask],
        y[mask],
        s=point_size,
        c=point_color,
        alpha=0.75,
        edgecolor='white',
        linewidth=0.5
    )
    ax.set_xlim(left=max(0, ax.get_xlim()[0]))
    ax.set_ylim(bottom=max(0, ax.get_ylim()[0]))
    ax.ticklabel_format(style='plain', axis='both', scilimits=(-3, 3))


pair_grid.map_lower(simple_scatter)

pair_grid.fig.subplots_adjust(top=0.92, wspace=0.05, hspace=0.05)
pair_grid.fig.suptitle(
    "Comprehensive Settlement Metrics Pair Plot (Normalized)",
    fontsize=16,
    y=0.98
)

# 軸ラベルを日本語化
metric_labels = {
    "sparsity": "Sparsity",
    "resilience": "Resilience", 
    "multi_nodality": "Multi-nodality",
    "permeability": "Permeability",
    "emergence": "Emergence",
    "overlap": "Overlap"
}

# 軸ラベルを設定
for i, metric in enumerate(available_metrics):
    # 対角線のラベル
    if i < len(pair_grid.axes):
        ax = pair_grid.axes[i, i]
        ax.set_ylabel(metric_labels.get(metric, metric), fontsize=10, fontweight='bold')
        ax.set_xlabel(metric_labels.get(metric, metric), fontsize=10, fontweight='bold')
    
    # 下三角のラベル
    for j in range(i):
        if j < len(pair_grid.axes) and i < len(pair_grid.axes[j]):
            ax = pair_grid.axes[i, j]
            ax.set_ylabel(metric_labels.get(metric, metric), fontsize=9)
            ax.set_xlabel(metric_labels.get(available_metrics[j], available_metrics[j]), fontsize=9)

# 統計情報を追加
stats_text = f"Total locations: {len(df)}\n"
for metric in available_metrics:
    if metric in normalized_df.columns:
        values = normalized_df[metric]
        stats_text += f"{metric_labels.get(metric, metric)}: {values.mean():.3f}±{values.std():.3f}\n"
stats_text += "All metrics scaled to [0, 1]"

# 統計情報を図に追加
pair_grid.fig.text(0.02, 0.02, stats_text, fontsize=8, 
                  bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))

output_dir = project_root / "figures"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "comprehensive_urban_metrics_pairplot.png"
pair_grid.fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor='white')
plt.close(pair_grid.fig)

print(f"✅ 包括的ペアプロットを {output_path} に保存しました。")
print(f"📊 含まれる指標: {', '.join(available_metrics)}")
print(f"📈 データポイント数: {len(df)}")
