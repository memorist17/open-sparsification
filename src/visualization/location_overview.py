#!/usr/bin/env python3
"""ロケーションごとの比較可視化ユーティリティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

import geopandas as gpd
import networkx as nx
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from pyproj import Transformer
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString

from src.app.satellite_cache import satellite_cache
from src.data_fetcher import fetch_real_geographic_data
from src.network_builder import create_urban_network


MetricSummary = Dict[str, Dict[str, float]]


def summarize_metrics(
    df: gpd.GeoDataFrame | 'pd.DataFrame',
    metrics: Iterable[str],
) -> MetricSummary:
    """指標の最小値・最大値・中央値・四分位数を集計"""

    summary: MetricSummary = {}

    for metric in metrics:
        if metric not in df.columns:
            continue
        series = df[metric].dropna()
        if series.empty:
            continue

        summary[metric] = {
            "min": float(series.min()),
            "max": float(series.max()),
            "median": float(series.median()),
            "q1": float(series.quantile(0.25)),
            "q3": float(series.quantile(0.75)),
        }

    return summary


def create_location_overview_figure(
    location_row: 'pd.Series',
    metric_summary: MetricSummary,
    *,
    radius_meters: int = 2000,
    buildings_gdf: Optional[gpd.GeoDataFrame] = None,
    roads_gdf: Optional[gpd.GeoDataFrame] = None,
    network_graph: Optional[nx.Graph] = None,
    metric_order: Optional[Iterable[str]] = None,
    layout: str = "full",
) -> Tuple[Figure, Dict[str, gpd.GeoDataFrame]]:
    """チャート・衛星画像・建物配置・ネットワークを統合した図を生成"""

    import pandas as pd  # 遅延インポート

    if metric_order is None:
        metric_order = ["sparsity", "resilience", "multi_nodality", "permeability"]

    metric_order = [m for m in metric_order if m in metric_summary]

    lat = float(location_row["latitude"])
    lon = float(location_row["longitude"])

    # データ取得（必要に応じて）
    if buildings_gdf is None or roads_gdf is None:
        buildings_gdf, roads_gdf = fetch_real_geographic_data(lat, lon, radius_meters)

    if buildings_gdf is not None and not buildings_gdf.empty:
        buildings_gdf = buildings_gdf.explode(ignore_index=True)
    if roads_gdf is not None and not roads_gdf.empty:
        roads_gdf = roads_gdf.explode(ignore_index=True)

    if network_graph is None and (not buildings_gdf.empty or not roads_gdf.empty):
        network_graph = create_urban_network(buildings_gdf, roads_gdf)
    elif network_graph is None:
        network_graph = nx.Graph()

    # 投影座標系に変換して表示用データを準備
    buildings_plot = (
        buildings_gdf.to_crs(epsg=3857) if not buildings_gdf.empty else gpd.GeoDataFrame(geometry=[], crs="EPSG:3857")
    )
    roads_plot = (
        roads_gdf.to_crs(epsg=3857) if not roads_gdf.empty else gpd.GeoDataFrame(geometry=[], crs="EPSG:3857")
    )

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    center_x, center_y = transformer.transform(lon, lat)

    # 表示範囲を決定
    # 半径ベースで描画領域を固定（衛星画像と揃える）
    extent = float(radius_meters)
    x_min = center_x - extent
    x_max = center_x + extent
    y_min = center_y - extent
    y_max = center_y + extent

    transformer_to_latlon = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    west, south = transformer_to_latlon.transform(x_min, y_min)
    east, north = transformer_to_latlon.transform(x_max, y_max)
    bounds_latlon = (west, south, east, north)
    width_m = x_max - x_min
    height_m = y_max - y_min

    title = (
        f"Location {int(location_row['location_id'])} | Lat: {lat:.4f}, Lon: {lon:.4f}\n"
        f"Sparsity {location_row.get('sparsity', np.nan):.2f} · "
        f"Resilience {location_row.get('resilience', np.nan):.2f} · "
        f"Polycentricity {location_row.get('multi_nodality', np.nan):.2f} · "
        f"Permeability {location_row.get('permeability', np.nan):.2f}"
    )

    if layout == "hybrid":
        fig, axes = plt.subplots(2, 1, figsize=(8, 12))
        ax_sat, ax_network = axes

        _draw_satellite(ax_sat, bounds_latlon, width_m, height_m)
        ax_sat.set_title("Satellite imagery", fontsize=12)

        _draw_network(
            ax_network,
            buildings_plot,
            roads_plot,
            network_graph,
            (x_min, x_max, y_min, y_max),
        )
        ax_network.set_title("Road & Network topology", fontsize=12)

        fig.suptitle(title, fontsize=15, y=0.99)
        fig.tight_layout(rect=[0, 0, 1, 0.97])

    else:
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        ax_chart, ax_sat, ax_buildings, ax_network = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

        _draw_metric_chart(ax_chart, location_row, metric_order, metric_summary)
        _draw_satellite(ax_sat, bounds_latlon, width_m, height_m)
        _draw_buildings(ax_buildings, buildings_plot, center_x, center_y, x_min, x_max, y_min, y_max)
        _draw_network(
            ax_network,
            buildings_plot,
            roads_plot,
            network_graph,
            (x_min, x_max, y_min, y_max),
        )

        fig.suptitle(title, fontsize=16, y=0.98)
        fig.text(
            0.5,
            0.02,
            "Buildings: GSI/OSM polygons → centroid; Roads: GSI/OSM centerlines. Connections: building centroid to nearest road node, resilience uses mixed graph.",
            ha='center',
            fontsize=10,
            color='#444'
        )
        fig.tight_layout(rect=[0, 0, 1, 0.96])

    return fig, {"buildings": buildings_gdf, "roads": roads_gdf}


def _draw_metric_chart(
    ax: Axes,
    row: 'pd.Series',
    metric_order: Iterable[str],
    metric_summary: MetricSummary,
) -> None:
    display_names = {
        "sparsity": "Sparsity",
        "resilience": "Resilience",
        "multi_nodality": "Polycentricity",
        "permeability": "Permeability",
    }

    y_positions = np.arange(len(metric_order))
    ax.set_facecolor("#f7f9fb")

    for idx, metric in enumerate(metric_order):
        summary = metric_summary.get(metric)
        if summary is None:
            continue

        min_val = summary["min"]
        max_val = summary["max"]
        q1 = summary["q1"]
        q3 = summary["q3"]
        median = summary["median"]
        rng = max(max_val - min_val, 1e-9)

        q1_norm = np.clip((q1 - min_val) / rng, 0, 1)
        q3_norm = np.clip((q3 - min_val) / rng, 0, 1)
        median_norm = np.clip((median - min_val) / rng, 0, 1)

        ax.barh(
            y_positions[idx],
            1.0,
            color="#dce4f2",
            alpha=0.4,
            height=0.6,
            zorder=1,
        )
        ax.barh(
            y_positions[idx],
            q3_norm - q1_norm,
            left=q1_norm,
            color="#4ECDC4",
            alpha=0.45,
            height=0.6,
            zorder=2,
        )
        ax.vlines(median_norm, y_positions[idx] - 0.3, y_positions[idx] + 0.3, color="#1a535c", linewidth=2, zorder=3)

        value = row.get(metric, np.nan)
        if not np.isnan(value):
            value_norm = np.clip((value - min_val) / rng, 0, 1)
            ax.scatter(value_norm, y_positions[idx], color="#FF6B6B", s=60, zorder=4)
            ax.text(
                1.02,
                y_positions[idx],
                f"{value:.2f}",
                va="center",
                ha="left",
                fontsize=11,
            )

    ax.set_yticks(y_positions)
    ax.set_yticklabels([display_names.get(metric, metric) for metric in metric_order], fontsize=12)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Relative position in dataset", fontsize=11)
    ax.grid(axis="x", color="white", linewidth=1)
    ax.set_title("Metric Context", fontsize=14, pad=12)
    ax.tick_params(axis="x", labelsize=10)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x * 100)}%"))


def _draw_satellite(
    ax: Axes,
    bounds: Tuple[float, float, float, float],
    width_m: float,
    height_m: float,
) -> None:
    ax.set_title("Satellite Imagery", fontsize=14, pad=12)
    ax.axis("off")

    west, south, east, north = bounds
    center_lat = (south + north) / 2.0
    center_lon = (west + east) / 2.0

    img, zoom = satellite_cache.get_or_create_satellite_image(
        center_lat,
        center_lon,
        bounds=bounds,
        width_m=width_m,
        height_m=height_m,
        size=(512, 512),
    )
    if img:
        ax.imshow(img)
        ax.text(
            0.03,
            0.95,
            f"Zoom {zoom} · Span {int(width_m/2):,}m",
            transform=ax.transAxes,
            fontsize=10,
            color="white",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="black", alpha=0.4),
        )
    else:
        ax.text(0.5, 0.5, "Satellite image unavailable", ha="center", va="center", fontsize=12)


def _draw_buildings(
    ax: Axes,
    buildings_plot: gpd.GeoDataFrame,
    center_x: float,
    center_y: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    ax.set_title("Building Footprints", fontsize=14, pad=12)
    ax.set_facecolor("white")

    if buildings_plot.empty:
        ax.text(0.5, 0.5, "No building data", ha="center", va="center", fontsize=12)
    else:
        buildings_plot.plot(ax=ax, color="#4ECDC4", edgecolor="#1a535c", linewidth=0.2, alpha=0.85)

    ax.scatter(center_x, center_y, marker="+", color="#FF6B6B", s=80, zorder=3)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")


def _draw_network(
    ax: Axes,
    buildings_plot: gpd.GeoDataFrame,
    roads_plot: gpd.GeoDataFrame,
    network_graph: nx.Graph,
    bounds: Tuple[float, float, float, float],
) -> None:
    ax.set_title("Road & Network Topology", fontsize=14, pad=12)
    ax.set_facecolor("white")

    x_min, x_max, y_min, y_max = bounds

    if not roads_plot.empty:
        roads_plot.plot(ax=ax, color="#adb5bd", linewidth=1.0, alpha=0.6, zorder=1)

    building_centroids = None
    if not buildings_plot.empty:
        buildings_plot.plot(ax=ax, color="#4ECDC4", edgecolor="#1a535c", linewidth=0.2, alpha=0.4, zorder=2)
        building_centroids = buildings_plot.geometry.centroid
        ax.scatter(
            building_centroids.x,
            building_centroids.y,
            s=30,
            color="#e63946",
            alpha=0.9,
            zorder=3,
        )

    pos = nx.get_node_attributes(network_graph, "pos")

    building_nodes = [n for n, data in network_graph.nodes(data=True) if data.get("node_type") == "building"]
    road_nodes = [n for n, data in network_graph.nodes(data=True) if data.get("node_type") == "road"]

    if road_nodes:
        nx.draw_networkx_nodes(
            network_graph,
            pos,
            nodelist=road_nodes,
            node_size=10,
            node_color="#4dabf7",
            alpha=0.7,
            ax=ax,
        )

    if building_nodes:
        nx.draw_networkx_nodes(
            network_graph,
            pos,
            nodelist=building_nodes,
            node_size=30,
            node_color="#e63946",
            alpha=0.85,
            ax=ax,
        )

    # ネットワークエッジを種類ごとに描画
    edge_types = nx.get_edge_attributes(network_graph, "edge_type")
    road_edges = [edge for edge, edge_type in edge_types.items() if edge_type == "road"]
    building_edges = [edge for edge, edge_type in edge_types.items() if edge_type == "building_building"]
    connectors = [edge for edge, edge_type in edge_types.items() if edge_type == "building_road_connection"]

    if road_edges:
        nx.draw_networkx_edges(
            network_graph,
            pos,
            edgelist=road_edges,
            edge_color="#577590",
            width=1.0,
            alpha=0.6,
            ax=ax,
        )

    if building_edges:
        nx.draw_networkx_edges(
            network_graph,
            pos,
            edgelist=building_edges,
            edge_color="#f3722c",
            width=0.6,
            alpha=0.7,
            ax=ax,
        )

    if connectors:
        nx.draw_networkx_edges(
            network_graph,
            pos,
            edgelist=connectors,
            edge_color="#1d3557",
            width=0.8,
            alpha=0.85,
            ax=ax,
        )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
