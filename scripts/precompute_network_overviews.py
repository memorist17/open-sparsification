#!/usr/bin/env python3
"""ネットワーク概要画像を事前生成するスクリプト"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

project_root = Path(__file__).resolve().parent.parent

import sys
sys.path.append(str(project_root))

from src.visualization.location_overview import summarize_metrics
from src.visualization.network_overview_cache import ensure_overview_image


def main() -> None:
    data_path = project_root / "data" / "processed" / "real_analysis_results.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"分析結果が見つかりません: {data_path}")

    df = pd.read_csv(data_path)
    metric_summary = summarize_metrics(
        df,
        ["sparsity", "resilience", "multi_nodality", "permeability"],
    )

    output_dir = project_root / "data" / "network_overviews"
    output_dir.mkdir(parents=True, exist_ok=True)

    for _, row in df.iterrows():
        path = ensure_overview_image(row, metric_summary, output_dir)
        if path is None:
            print(f"⚠️ {row['name']} で建物・道路データを取得できませんでした")
        else:
            print(f"✅ {path.name} を生成済み")


if __name__ == "__main__":
    main()

