#!/usr/bin/env python3
"""全指標を含む改良版ペアプロットを作成（複数パネル構成）"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

project_root = Path(__file__).resolve().parent.parent
results_path = project_root / "data" / "processed" / "real_analysis_results.csv"
if not results_path.exists():
    raise FileNotFoundError(f"分析結果が見つかりません: {results_path}")

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

# データクリーニング
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna(subset=available_metrics, how='any').reset_index(drop=True)

print(f"処理後のデータ数: {len(df)}")

# 指標をグループ化（主要指標と補助指標）
core_metrics = ["sparsity", "resilience", "multi_nodality", "permeability"]
secondary_metrics = ["emergence", "overlap"]

# 利用可能な指標のみを選択
available_core = [m for m in core_metrics if m in available_metrics]
available_secondary = [m for m in secondary_metrics if m in available_metrics]

# シンプルな散布図用の設定
point_size = 60
point_color = "#1f77b4"

# スタイル設定
sns.set_theme(style="whitegrid", context="talk", font_scale=0.9)

# 複数パネル構成
fig = plt.figure(figsize=(20, 16))

# パネル1: 主要指標のペアプロット
if len(available_core) >= 2:
    ax1 = plt.subplot(2, 2, 1)
    pair_grid1 = sns.PairGrid(df, vars=available_core, corner=True, height=3.5)
    pair_grid1.map_diag(sns.histplot, color="#6c757d", edgecolor="white", linewidth=0.5)
    
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
    
    pair_grid1.map_lower(simple_scatter)
    
    pair_grid1.fig.suptitle("Core Urban Metrics", fontsize=14, y=0.95)

# パネル2: 補助指標のペアプロット
if len(available_secondary) >= 2:
    ax2 = plt.subplot(2, 2, 2)
    pair_grid2 = sns.PairGrid(df, vars=available_secondary, corner=True, height=3.5)
    pair_grid2.map_diag(sns.histplot, color="#4ECDC4", edgecolor="white", linewidth=0.5)
    pair_grid2.map_lower(simple_scatter)
    pair_grid2.fig.suptitle("Secondary Urban Metrics", fontsize=14, y=0.95)

# パネル3: 全指標の相関ヒートマップ
ax3 = plt.subplot(2, 2, 3)
correlation_matrix = df[available_metrics].corr()
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap="RdBu_r", center=0,
            square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax3)
ax3.set_title("Correlation Matrix", fontsize=14, pad=20)

# パネル4: 指標の分布比較
ax4 = plt.subplot(2, 2, 4)
# データを正規化して比較
normalized_data = df[available_metrics].copy()
for col in available_metrics:
    if col in normalized_data.columns:
        normalized_data[col] = (normalized_data[col] - normalized_data[col].min()) / (normalized_data[col].max() - normalized_data[col].min())

# 箱ひげ図
normalized_data.boxplot(ax=ax4, patch_artist=True)
ax4.set_title("Normalized Metrics Distribution", fontsize=14, pad=20)
ax4.set_ylabel("Normalized Value", fontsize=12)
ax4.tick_params(axis='x', rotation=45)

# 全体のタイトル
fig.suptitle(
    "Comprehensive Urban Morphology Analysis",
    fontsize=18,
    y=0.95
)

# 統計情報を追加
stats_text = f"Total locations: {len(df)}\n"
for metric in available_metrics:
    if metric in df.columns:
        values = df[metric]
        stats_text += f"{metric}: {values.mean():.3f}±{values.std():.3f}\n"

fig.text(0.02, 0.02, stats_text, fontsize=8, 
         bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))

plt.tight_layout()

# 保存
output_dir = project_root / "figures"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "enhanced_urban_metrics_analysis.png"
fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor='white')
plt.close(fig)

print(f"✅ 改良版ペアプロットを {output_path} に保存しました。")
print(f"📊 含まれる指標: {', '.join(available_metrics)}")
print(f"📈 データポイント数: {len(df)}")
