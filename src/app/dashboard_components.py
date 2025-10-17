#!/usr/bin/env python3
"""
ダッシュボードコンポーネント - グラフ生成とUI要素

設計思想: 🧩 モジュール性 (Modularity)
- グラフ生成ロジックを独立したモジュールとして分離
- 再利用可能なコンポーネントとして実装
- 責務を明確に分割
"""

from typing import Dict, List, Optional, Tuple
import base64

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html

from src.app.dashboard_config import get_dashboard_config


def normalize_metrics_frame(
    df: pd.DataFrame,
    metrics: List[str],
) -> Tuple[pd.DataFrame, Dict[str, Tuple[float, float]]]:
    """
    指定指標を0〜1スケールに正規化し、*_normalized列を追加
    
    Args:
        df: データフレーム
        metrics: 正規化する指標のリスト
    
    Returns:
        正規化済みデータフレームとスケール情報のタプル
    """
    normalized = df.copy()
    scale_info: Dict[str, Tuple[float, float]] = {}

    for metric in metrics:
        if metric not in normalized.columns:
            continue
        series = normalized[metric].astype(float)
        min_val = float(series.min())
        max_val = float(series.max())
        scale_info[metric] = (min_val, max_val)

        rng = max(max_val - min_val, 1e-9)
        normalized_values = (series - min_val) / rng
        normalized[f"{metric}_normalized"] = normalized_values.clip(0.0, 1.0)

    return normalized, scale_info


def _axis_id(axis: str, row: int, col: int, ncols: int) -> str:
    """
    サブプロットの軸IDを取得
    
    Args:
        axis: 軸の種類 ('x' または 'y')
        row: 行番号
        col: 列番号
        ncols: 列数
    
    Returns:
        軸ID文字列
    """
    index = (row - 1) * ncols + col
    if index == 1:
        return axis
    return f"{axis}{index}"


def _base_metric(metric_name: str) -> str:
    """
    正規化された指標名からベース指標名を取得
    
    Args:
        metric_name: 指標名（_normalizedサフィックス付きの可能性あり）
    
    Returns:
        ベース指標名
    """
    return metric_name[:-11] if metric_name.endswith("_normalized") else metric_name


def create_pairplot_figure(
    df: pd.DataFrame,
    metrics: List[str],
    highlight_id: Optional[int] = None,
    config: Optional[object] = None,
) -> go.Figure:
    """
    集落指標のペアプロットを生成（正規化済みデータを想定）
    
    Args:
        df: 正規化済みデータフレーム
        metrics: 表示する指標のリスト
        highlight_id: ハイライトする地点ID（オプション）
        config: 設定オブジェクト（省略時はデフォルト設定を使用）
    
    Returns:
        Plotlyのフィギュアオブジェクト
    """
    if config is None:
        config = get_dashboard_config()
    
    n_metrics = len(metrics)
    fig = make_subplots(
        rows=n_metrics,
        cols=n_metrics,
        shared_xaxes=True,
        shared_yaxes=True,
        horizontal_spacing=config.horizontal_spacing,
        vertical_spacing=config.vertical_spacing,
    )

    highlight_row = None
    if highlight_id is not None:
        match = df[df["location_id"] == highlight_id]
        if not match.empty:
            highlight_row = match.iloc[0]

    # 各サブプロットを生成
    for row_idx, y_metric in enumerate(metrics):
        base_y_metric = _base_metric(y_metric)
        if y_metric not in df.columns or base_y_metric not in df.columns:
            continue
        for col_idx, x_metric in enumerate(metrics):
            row = row_idx + 1
            col = col_idx + 1
            if col_idx > row_idx:
                continue
            if x_metric not in df.columns:
                continue
            base_x_metric = _base_metric(x_metric)
            if base_x_metric not in df.columns or base_y_metric not in df.columns:
                continue

            if row_idx == col_idx:
                # 対角線: ヒストグラム
                fig.add_trace(
                    go.Histogram(
                        x=df[x_metric],
                        nbinsx=config.histogram_bins,
                        marker=dict(
                            color=config.histogram_color,
                            opacity=config.histogram_opacity
                        ),
                        hovertemplate=(
                            f"{config.get_metric_label(base_x_metric)}: "
                            "%{x:.3f}<extra></extra>"
                        ),
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )
            else:
                # 下三角: 散布図
                customdata = df[["location_id", base_x_metric, base_y_metric]].to_numpy()
                fig.add_trace(
                    go.Scattergl(
                        x=df[x_metric],
                        y=df[y_metric],
                        mode="markers",
                        marker=dict(
                            size=config.scatter_size,
                            color=config.scatter_color,
                            line=dict(width=config.scatter_line_width),
                        ),
                        customdata=customdata,
                        hovertemplate=(
                            "<b>地点 %{customdata[0]:.0f}</b><br>"
                            f"{config.get_metric_label(base_x_metric)}（正規化）: "
                            "%{x:.3f}<br>"
                            f"{config.get_metric_label(base_x_metric)}（raw）: "
                            "%{customdata[1]:.3f}<br>"
                            f"{config.get_metric_label(base_y_metric)}（正規化）: "
                            "%{y:.3f}<br>"
                            f"{config.get_metric_label(base_y_metric)}（raw）: "
                            "%{customdata[2]:.3f}<extra></extra>"
                        ),
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )

                # ハイライト表示
                if highlight_row is not None:
                    fig.add_trace(
                        go.Scattergl(
                            x=[highlight_row[x_metric]],
                            y=[highlight_row[y_metric]],
                            mode="markers",
                            marker=dict(
                                size=config.highlight_size,
                                color=config.highlight_color,
                                line=dict(
                                    color=config.highlight_line_color,
                                    width=config.highlight_line_width
                                ),
                            ),
                            hoverinfo="skip",
                            showlegend=False,
                        ),
                        row=row,
                        col=col,
                    )

            fig.update_xaxes(range=[0, 1], row=row, col=col)
            fig.update_yaxes(range=[0, 1], row=row, col=col)

    # ハイライトラインの追加
    if highlight_row is not None:
        shapes = []
        for idx, metric in enumerate(metrics):
            if metric not in df.columns:
                continue
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
                    "line": {
                        "color": config.highlight_marker_color,
                        "width": config.highlight_line_width_accent
                    },
                }
            )
        fig.update_layout(shapes=shapes)

    # 軸ラベルの設定
    for idx, metric in enumerate(metrics):
        if metric not in df.columns:
            continue
        base_metric = _base_metric(metric)
        base_label = config.get_metric_label(base_metric)
        label = f"{base_label}（正規化）"
        fig.update_xaxes(title_text=label, row=n_metrics, col=idx + 1)
        fig.update_yaxes(title_text=label, row=idx + 1, col=1)
        fig.update_xaxes(range=[0, 1], row=idx + 1, col=idx + 1)
        fig.update_yaxes(range=[0, 1], row=idx + 1, col=idx + 1)

    # 区切り線の追加
    separator_shapes = []
    if config.separator_enabled:
        for row_idx in range(n_metrics):
            for col_idx in range(n_metrics):
                if col_idx > row_idx:
                    continue
                row = row_idx + 1
                col = col_idx + 1
                
                axis_x = _axis_id("x", row, col, n_metrics)
                axis_y = _axis_id("y", row, col, n_metrics)
                
                # 右側の区切り線（最後の列以外）
                if col_idx < row_idx:
                    separator_shapes.append({
                        "type": "line",
                        "x0": 1,
                        "x1": 1,
                        "y0": 0,
                        "y1": 1,
                        "xref": axis_x,
                        "yref": f"{axis_y} domain",
                        "line": {
                            "color": config.separator_color,
                            "width": config.separator_width
                        },
                        "layer": config.separator_layer,
                    })
                
                # 下側の区切り線（最後の行以外）
                if row_idx < n_metrics - 1:
                    separator_shapes.append({
                        "type": "line",
                        "x0": 0,
                        "x1": 1,
                        "y0": 0,
                        "y1": 0,
                        "xref": f"{axis_x} domain",
                        "yref": axis_y,
                        "line": {
                            "color": config.separator_color,
                            "width": config.separator_width
                        },
                        "layer": config.separator_layer,
                    })
    
    # 既存のshapesと結合
    existing_shapes = list(fig.layout.shapes) if fig.layout.shapes else []
    all_shapes = existing_shapes + separator_shapes
    
    # レイアウトの更新
    fig.update_layout(
        hovermode="closest",
        height=config.base_height + config.height_per_metric * n_metrics,
        bargap=0.05,
        margin=config.margin_dict,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        autosize=True,
        font=dict(size=12),
        shapes=all_shapes,
    )
    return fig


def extract_location_id(hover_data) -> Optional[int]:
    """
    hoverDataから地点IDを抽出
    
    Args:
        hover_data: Dashのホバーイベントデータ
    
    Returns:
        地点ID（取得できない場合はNone）
    """
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


def create_default_overlay_children(config: Optional[object] = None) -> List:
    """
    デフォルトのオーバーレイコンテンツを生成
    
    Args:
        config: 設定オブジェクト（省略時はデフォルト設定を使用）
    
    Returns:
        Dashコンポーネントのリスト
    """
    if config is None:
        config = get_dashboard_config()
    
    return [
        html.Span(
            config.overlay_title,
            style={"fontWeight": 600, "color": "#0f172a"},
        ),
        html.Span(
            config.overlay_instruction,
            style={"color": "#475569", "fontSize": "0.85rem"},
        ),
        html.Div(
            config.awaiting_selection,
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


def build_overlay_children(
    location_row: pd.Series,
    metric_summary: pd.DataFrame,
    metric_scale: Dict[str, Tuple[float, float]],
    network_overviews_dir,
    metric_columns: List[str],
    config: Optional[object] = None,
):
    """
    地点に対応するハイブリッドネットワーク画像のコンテンツを生成
    
    Args:
        location_row: 地点データの行
        metric_summary: 指標サマリー
        metric_scale: スケール情報
        network_overviews_dir: ネットワーク概要画像のディレクトリ
        metric_columns: 表示する指標のリスト
        config: 設定オブジェクト（省略時はデフォルト設定を使用）
    
    Returns:
        Dashコンポーネントのリスト
    """
    if config is None:
        config = get_dashboard_config()
    
    # ネットワーク概要画像の生成を試みる
    from src.visualization.network_overview_cache import ensure_overview_image
    
    location_id = int(location_row["location_id"])
    metric_keys = [m for m in metric_columns if m in location_row.index]
    if "overlap" in location_row.index and "overlap" not in metric_keys:
        metric_keys.append("overlap")

    # 指標情報の表示
    metric_rows = []
    for metric in metric_keys:
        min_val, max_val = metric_scale.get(metric, (np.nan, np.nan))
        if np.isnan(min_val) or np.isnan(max_val) or np.isclose(min_val, max_val):
            normalized_value = 0.0
        else:
            normalized_value = (float(location_row[metric]) - min_val) / (max_val - min_val)
        metric_rows.append(
            html.Div(
                [
                    html.Span(
                        config.get_metric_label(metric),
                        style={"color": "#475569"},
                    ),
                    html.Span(
                        f"{normalized_value:.3f}（raw {location_row[metric]:.3f}）",
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
    
    metrics_block_children = metric_rows.copy()
    if metrics_block_children:
        metrics_block_children[-1] = html.Div(
            metrics_block_children[-1].children,
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "padding": "4px 0",
                "fontSize": "0.85rem",
            },
        )
    else:
        metrics_block_children.append(
            html.Span(
                "指標情報を取得できませんでした。",
                style={"color": "#64748b", "fontSize": "0.8rem"},
            )
        )

    metrics_block_children.append(
        html.Span(
            config.normalization_note,
            style={"color": "#94a3b8", "fontSize": "0.75rem"},
        )
    )

    metrics_block = html.Div(
        metrics_block_children,
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "2px",
            "marginTop": "6px",
        },
    )

    # ネットワーク画像の取得
    image_path = ensure_overview_image(
        location_row,
        metric_summary,
        network_overviews_dir,
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
            metrics_block,
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
        metrics_block,
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

