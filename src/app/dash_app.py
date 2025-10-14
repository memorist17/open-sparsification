#!/usr/bin/env python3
"""
Dashアプリケーション - ペアプロットとハイブリッドネットワークの連携可視化
"""

from typing import List, Optional

import base64
import io
from pathlib import Path
import sys

import dash
from dash import Input, Output, State, dcc, html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.visualization.location_overview import summarize_metrics
from src.visualization.network_overview_cache import ensure_overview_image

NETWORK_OVERVIEW_DIR = project_root / "data" / "network_overviews"

METRIC_COLUMNS = [
    "sparsity",
    "resilience",
    "multi_nodality",
    "permeability",
    "emergence",
]

METRIC_LABELS = {
    "sparsity": "疎性",
    "resilience": "レジリエンス",
    "multi_nodality": "多中心性",
    "permeability": "流動性",
    "emergence": "創発性",
    "overlap": "重なり",
}

OVERLAY_BASE_STYLE = {
    "position": "absolute",
    "top": "16px",
    "right": "16px",
    "width": "240px",
    "backgroundColor": "rgba(255, 255, 255, 0.98)",
    "border": "1px solid #e2e8f0",
    "borderRadius": "12px",
    "boxShadow": "0 18px 36px rgba(15, 23, 42, 0.12)",
    "padding": "14px",
    "display": "flex",
    "flexDirection": "column",
    "gap": "10px",
    "boxSizing": "border-box",
}

DEFAULT_OVERLAY_CHILDREN = [
    html.Span(
        "Hybrid network preview",
        style={"fontWeight": 600, "color": "#0f172a"},
    ),
    html.Span(
        "ペアプロットで地点をホバーすると、ここにネットワーク図が表示されます。",
        style={"color": "#475569", "fontSize": "0.85rem"},
    ),
    html.Div(
        "Awaiting selection...",
        style={
            "height": "260px",
            "border": "1px dashed #cbd5f5",
            "borderRadius": "10px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "color": "#94a3b8",
            "fontSize": "0.85rem",
            "backgroundColor": "#ffffff",
        },
    ),
]


def _axis_id(axis: str, row: int, col: int, ncols: int) -> str:
    """サブプロットの軸IDを取得"""
    index = (row - 1) * ncols + col
    if index == 1:
        return axis
    return f"{axis}{index}"


def create_pairplot_figure(
    df: pd.DataFrame,
    metrics: List[str],
    highlight_id: Optional[int] = None,
) -> go.Figure:
    """都市指標のペアプロットを生成"""
    n_metrics = len(metrics)
    fig = make_subplots(
        rows=n_metrics,
        cols=n_metrics,
        shared_xaxes=True,
        shared_yaxes=True,
        horizontal_spacing=0.02,
        vertical_spacing=0.02,
    )

    highlight_row = None
    if highlight_id is not None:
        match = df[df["location_id"] == highlight_id]
        if not match.empty:
            highlight_row = match.iloc[0]

    location_customdata = df[["location_id"]].to_numpy()

    for row_idx, y_metric in enumerate(metrics):
        for col_idx, x_metric in enumerate(metrics):
            row = row_idx + 1
            col = col_idx + 1
            if col_idx > row_idx:
                continue

            if row_idx == col_idx:
                fig.add_trace(
                    go.Histogram(
                        x=df[x_metric],
                        nbinsx=16,
                        marker=dict(color="#60a5fa", opacity=0.85),
                        hovertemplate=(
                            f"{METRIC_LABELS.get(x_metric, x_metric)}: "
                            "%{x:.3f}<extra></extra>"
                        ),
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )
            else:
                fig.add_trace(
                    go.Scattergl(
                        x=df[x_metric],
                        y=df[y_metric],
                        mode="markers",
                        marker=dict(
                            size=6,
                            color="rgba(37, 99, 235, 0.4)",
                            line=dict(width=0),
                        ),
                        customdata=location_customdata,
                        hovertemplate=(
                            "<b>地点 %{customdata[0]}</b><br>"
                            f"{METRIC_LABELS.get(x_metric, x_metric)}: "
                            "%{x:.3f}<br>"
                            f"{METRIC_LABELS.get(y_metric, y_metric)}: "
                            "%{y:.3f}<extra></extra>"
                        ),
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )

                if highlight_row is not None:
                    fig.add_trace(
                        go.Scattergl(
                            x=[highlight_row[x_metric]],
                            y=[highlight_row[y_metric]],
                            mode="markers",
                            marker=dict(
                                size=10,
                                color="#f97316",
                                line=dict(color="#1e1b4b", width=1),
                            ),
                            hoverinfo="skip",
                            showlegend=False,
                        ),
                        row=row,
                        col=col,
                    )

    if highlight_row is not None:
        shapes = []
        for idx, metric in enumerate(metrics):
            axis_x = _axis_id("x", idx + 1, idx + 1, n_metrics)
            axis_y = _axis_id("y", idx + 1, idx + 1, n_metrics)
            shapes.append(
                {
                    "type": "line",
                    "x0": highlight_row[metric],
                    "x1": highlight_row[metric],
                    "y0": 0,
                    "y1": 1,
                    "xref": axis_x,
                    "yref": f"{axis_y} domain",
                    "line": {"color": "#d62728", "width": 2},
                }
            )
        fig.update_layout(shapes=shapes)

    for idx, metric in enumerate(metrics):
        label = METRIC_LABELS.get(metric, metric)
        fig.update_xaxes(title_text=label, row=n_metrics, col=idx + 1)
        fig.update_yaxes(title_text=label, row=idx + 1, col=1)

    fig.update_layout(
        hovermode="closest",
        height=120 + 120 * n_metrics,
        bargap=0.05,
        margin=dict(l=24, r=200, t=40, b=24),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        autosize=True,
        font=dict(size=12),
    )
    return fig


def extract_location_id(hover_data) -> Optional[int]:
    """hoverDataから地点IDを抽出"""
    if not hover_data:
        return None
    points = hover_data.get("points")
    if not points:
        return None
    customdata = points[0].get("customdata")
    if customdata is None:
        point_number = points[0].get("pointIndex")
        if point_number is None:
            return None
        return int(point_number)
    if isinstance(customdata, (list, tuple, np.ndarray)):
        return int(customdata[0])
    return int(customdata)


def build_overlay_children(
    location_row: pd.Series,
    metric_summary: pd.DataFrame,
):
    """地点に対応するハイブリッドネットワーク画像のコンテンツを生成"""
    location_id = int(location_row["location_id"])
    metric_keys = [m for m in METRIC_COLUMNS if m in location_row.index]
    if "overlap" in location_row.index and "overlap" not in metric_keys:
        metric_keys.append("overlap")

    metric_rows = []
    for metric in metric_keys:
        metric_rows.append(
            html.Div(
                [
                    html.Span(
                        METRIC_LABELS.get(metric, metric),
                        style={"color": "#475569"},
                    ),
                    html.Span(
                        f"{location_row[metric]:.3f}",
                        style={"fontWeight": 600, "color": "#0f172a"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "padding": "4px 0",
                    "borderBottom": "1px solid #e2e8f0",
                    "fontSize": "0.85rem",
                },
            )
        )
    if metric_rows:
        metric_rows[-1] = html.Div(
            metric_rows[-1].children,
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "padding": "4px 0",
                "fontSize": "0.85rem",
            },
        )

    image_path = ensure_overview_image(
        location_row,
        metric_summary,
        NETWORK_OVERVIEW_DIR,
    )

    header = html.Div(
        [
            html.Span(
                f"地点 {location_id}",
                style={"fontWeight": 600, "color": "#0f172a"},
            ),
            html.Span(
                f"{location_row['latitude']:.4f}, {location_row['longitude']:.4f}",
                style={"color": "#475569", "fontSize": "0.85rem"},
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "2px"},
    )

    if image_path is None or not image_path.exists():
        return [
            header,
            html.Div(
                [
                    html.P(
                        "ネットワーク図が未生成です。",
                        style={"margin": 0, "color": "#475569", "fontSize": "0.85rem"},
                    ),
                    html.Code(
                        "venv/bin/python scripts/precompute_network_overviews.py",
                        style={
                            "display": "block",
                            "whiteSpace": "pre-wrap",
                            "marginTop": "6px",
                            "fontSize": "0.75rem",
                        },
                    ),
                ]
            ),
        ]

    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()

    return [
        header,
        html.Img(
            src=f"data:image/png;base64,{img_base64}",
            style={
                "width": "100%",
                "height": "auto",
                "borderRadius": "10px",
                "border": "1px solid #e2e8f0",
            },
        ),
    ]


def create_dash_app():
    """Dashアプリケーションを作成"""
    data_path = project_root / "data" / "processed" / "real_analysis_results.csv"
    if not data_path.exists():
        df = pd.DataFrame(
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
        df = pd.read_csv(data_path)

    metric_summary = summarize_metrics(
        df,
        ["sparsity", "resilience", "multi_nodality", "permeability"],
    )

    base_figure = create_pairplot_figure(df, METRIC_COLUMNS)

    app = dash.Dash(__name__)
    app.css.config.serve_locally = True
    app.scripts.config.serve_locally = True

    app.layout = html.Div(
        [
            dcc.Store(id="last-hovered-location", data=None),
            html.H1(
                "🏙️ OpenSparsity - 都市空間ハイブリッド可視化",
                style={"textAlign": "center", "marginBottom": "24px"},
            ),
            html.Div(
                [
                    html.H3(
                        "都市形態指標ペアプロット",
                        style={"marginBottom": "12px"},
                    ),
                    html.Div(
                        [
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
                            html.Div(
                                DEFAULT_OVERLAY_CHILDREN,
                                id="hybrid-image-container",
                                style=OVERLAY_BASE_STYLE,
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
                style={"display": "flex", "flexDirection": "column", "alignItems": "center", "gap": "8px"},
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
        location_id = extract_location_id(hover_data)
        if location_id is None and stored_location is not None:
            try:
                location_id = int(stored_location)
            except (TypeError, ValueError):
                location_id = None

        updated_figure = create_pairplot_figure(
            df,
            METRIC_COLUMNS,
            highlight_id=location_id,
        )

        if location_id is None:
            return (
                updated_figure,
                DEFAULT_OVERLAY_CHILDREN,
                stored_location,
            )

        location_match = df[df["location_id"] == location_id]
        if location_match.empty:
            return (
                updated_figure,
                DEFAULT_OVERLAY_CHILDREN,
                stored_location,
            )

        location_row = location_match.iloc[0]
        overlay_children = build_overlay_children(location_row, metric_summary)

        return (
            updated_figure,
            overlay_children,
            int(location_row["location_id"]),
        )

    return app


if __name__ == "__main__":
    dash_app = create_dash_app()
    dash_app.run(debug=True, host="0.0.0.0", port=8051)
