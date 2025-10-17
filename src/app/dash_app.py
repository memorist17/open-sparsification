#!/usr/bin/env python3
"""
Dashアプリケーション - ペアプロットとハイブリッドネットワークの連携可視化

設計思想:
- 🔄 再現性 (Reproducibility): コンテナ化と設定管理による再現可能性
- 🧩 モジュール性 (Modularity): 機能を独立したモジュールに分離
- ⚙️ 設定駆動 (Configuration-Driven): パラメータを外部YAMLで管理
- 📚 ドキュメント先行 (Documentation-First): コード内に設計意図を明記
"""

from pathlib import Path
import sys

import dash
from dash import Input, Output, State, dcc, html
import numpy as np
import pandas as pd

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# モジュール化されたコンポーネントのインポート
from src.app.dashboard_config import get_dashboard_config
from src.app.dashboard_components import (
    normalize_metrics_frame,
    create_pairplot_figure,
    extract_location_id,
    create_default_overlay_children,
    build_overlay_children,
)
from src.visualization.location_overview import summarize_metrics


def create_dash_app():
    """
    Dashアプリケーションを作成
    
    設定ファイル (config/dashboard.yml) に基づいて
    インタラクティブなダッシュボードを構築します。
    
    Returns:
        Dashアプリケーションインスタンス
    """
    # 設定の読み込み
    config = get_dashboard_config()
    
    # データの読み込み
    data_path = config.analysis_results_path
    if not data_path.exists():
        # サンプルデータを生成（本番環境では実際のデータを使用）
        df_raw = pd.DataFrame(
            {
                "location_id": range(100),
                "latitude": np.random.uniform(30.0, 46.0, 100),
                "longitude": np.random.uniform(129.0, 146.0, 100),
                "sparsity": np.random.uniform(0.1, 1.5, 100),
                "resilience": np.random.uniform(0.2, 0.9, 100),
                "multi_nodality": np.random.uniform(0.0, 1.0, 100),
                "permeability": np.random.uniform(0.3, 1.0, 100),
                "emergence": np.random.uniform(0.0, 0.8, 100),
                "overlap": np.zeros(100),
            }
        )
    else:
        df_raw = pd.read_csv(data_path)

    # 正規化処理
    normalization_targets = list(dict.fromkeys(config.metric_columns + ["overlap"]))
    df_normalized, metric_scale = normalize_metrics_frame(df_raw, normalization_targets)

    # 正規化された指標列のリストを作成
    normalized_metric_columns = [
        f"{metric}_normalized"
        for metric in config.metric_columns
        if f"{metric}_normalized" in df_normalized.columns
    ]
    if not normalized_metric_columns:
        normalized_metric_columns = [
            metric for metric in config.metric_columns if metric in df_normalized.columns
        ]

    # 指標サマリーの計算
    metric_summary = summarize_metrics(
        df_raw,
        ["sparsity", "resilience", "multi_nodality", "permeability"],
    )

    # ベースとなるペアプロット図を生成
    base_figure = create_pairplot_figure(df_normalized, normalized_metric_columns, config=config)

    # Dashアプリケーションの初期化
    app = dash.Dash(__name__)
    app.css.config.serve_locally = True
    app.scripts.config.serve_locally = True

    # レイアウトの定義
    app.layout = html.Div(
        [
            # 状態管理用のストレージ
            dcc.Store(id="last-hovered-location", data=None),
            
            # タイトル
            html.H1(
                config.app_title,
                style={"textAlign": "center", "marginBottom": "24px"},
            ),
            
            # メインコンテンツ
            html.Div(
                [
                    html.H3(
                        config.app_subtitle,
                        style={"marginBottom": "12px"},
                    ),
                    html.Div(
                        [
                            # ペアプロット
                            dcc.Graph(
                                id="pairplot-graph",
                                figure=base_figure,
                                clear_on_unhover=True,
                                config={
                                    "displayModeBar": False,
                                    "responsive": True,
                                },
                                style={
                                    "backgroundColor": "#ffffff",
                                    "borderRadius": "12px",
                                    "border": "1px solid #e2e8f0",
                                    "padding": "8px",
                                    "width": "100%",
                                    "margin": 0,
                                    "height": "720px",
                                },
                            ),
                            
                            # オーバーレイ（ネットワーク画像表示エリア）
                            html.Div(
                                create_default_overlay_children(config),
                                id="hybrid-image-container",
                                style=config.overlay_style,
                            ),
                        ],
                        style={
                            "position": "relative",
                            "width": "100%",
                            "maxWidth": "960px",
                            "margin": "0 auto",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "gap": "8px"
                },
            ),
        ],
        style={"padding": "12px"},
    )

    @app.callback(
        Output("pairplot-graph", "figure"),
        Output("hybrid-image-container", "children"),
        Output("last-hovered-location", "data"),
        Input("pairplot-graph", "hoverData"),
        State("last-hovered-location", "data"),
    )
    def update_dashboard(hover_data, stored_location):
        """
        ホバーイベントに応じてダッシュボードを更新
        
        Args:
            hover_data: ホバーイベントデータ
            stored_location: 前回選択された地点ID
        
        Returns:
            更新されたフィギュア、オーバーレイコンテンツ、地点IDのタプル
        """
        # 地点IDの抽出
        location_id = extract_location_id(hover_data)
        if location_id is None and stored_location is not None:
            try:
                location_id = int(stored_location)
            except (TypeError, ValueError):
                location_id = None

        # ペアプロット図の更新（ハイライト付き）
        updated_figure = create_pairplot_figure(
            df_normalized,
            normalized_metric_columns,
            highlight_id=location_id,
            config=config,
        )

        # 地点が選択されていない場合
        if location_id is None:
            return (
                updated_figure,
                create_default_overlay_children(config),
                stored_location,
            )

        # 該当地点のデータを取得
        location_match = df_raw[df_raw["location_id"] == location_id]
        if location_match.empty:
            return (
                updated_figure,
                create_default_overlay_children(config),
                stored_location,
            )

        # オーバーレイコンテンツの生成
        location_row = location_match.iloc[0]
        overlay_children = build_overlay_children(
            location_row,
            metric_summary,
            metric_scale,
            config.network_overviews_dir,
            config.metric_columns,
            config=config,
        )

        return (
            updated_figure,
            overlay_children,
            int(location_row["location_id"]),
        )

    return app


if __name__ == "__main__":
    # 設定を取得
    config = get_dashboard_config()
    
    # アプリケーションを作成して実行
    dash_app = create_dash_app()
    dash_app.run(
        debug=config.server_debug,
        host=config.server_host,
        port=config.server_port,
    )
