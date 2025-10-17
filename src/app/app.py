"""
OpenSparsity Streamlitアプリケーション

集落形態の定量的分析と可視化のためのインタラクティブダッシュボード
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import networkx as nx
from typing import Dict, Any, List, Tuple, Optional
import sys
from pathlib import Path
import requests
import json

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.utils.config import load_config, get_config
from src.utils.logger import get_logger
from src.data_processing import load_spatial_data, preprocess_building_data, preprocess_road_data
from src.network_builder import create_urban_network, visualize_network
from src.metrics import (
    MultiNodalityCalculator,
    SparsityCalculator,
    PermeabilityCalculator,
    OverlapCalculator,
    EmergenceCalculator,
    ResilienceCalculator
)
from src.visualization.location_overview import (
    create_location_overview_figure,
    summarize_metrics,
)

# ログ設定
logger = get_logger(__name__)

# 住所情報を取得する関数（簡素化版）
@st.cache_data
def get_address_from_coordinates(lat: float, lon: float) -> str:
    """
    緯度経度から簡易的な住所情報を生成
    """
    try:
        # 簡易的な地域判定
        if 35.0 <= lat <= 36.0 and 139.0 <= lon <= 140.0:
            return "東京都周辺"
        elif 34.0 <= lat <= 35.0 and 135.0 <= lon <= 136.0:
            return "大阪府周辺"
        elif 35.0 <= lat <= 36.0 and 136.0 <= lon <= 137.0:
            return "愛知県周辺"
        elif 43.0 <= lat <= 44.0 and 141.0 <= lon <= 142.0:
            return "北海道周辺"
        elif 33.0 <= lat <= 34.0 and 130.0 <= lon <= 131.0:
            return "福岡県周辺"
        else:
            return f"緯度: {lat:.4f}, 経度: {lon:.4f}"
    except Exception as e:
        return f"緯度: {lat:.4f}, 経度: {lon:.4f}"

# ページ設定
st.set_page_config(
    page_title="OpenSparsity Dashboard",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .stSelectbox > div > div {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# メインヘッダー
st.markdown('<h1 class="main-header">🏙️ OpenSparsity Dashboard</h1>', unsafe_allow_html=True)
st.markdown("集落形態の定量的分析と可視化")

# 設定ファイルの読み込み
@st.cache_data
def load_app_config():
    """アプリケーション設定を読み込み"""
    try:
        config = load_config()
        return config
    except Exception as e:
        st.error(f"設定ファイルの読み込みエラー: {e}")
        return None

config = load_app_config()
if config is None:
    st.stop()

# 分析結果データの読み込み
@st.cache_data
def load_sample_data():
    """実際の分析結果データまたはサンプルデータを読み込み"""
    try:
        # 実際の分析結果データのパス
        real_data_path = project_root / "data" / "processed" / "real_analysis_results.csv"
        sample_data_path = project_root / "data" / "processed" / "sample_analysis_results.csv"
        
        # 実際のデータが存在する場合は優先的に使用
        if real_data_path.exists():
            df = pd.read_csv(real_data_path)
            st.info("✅ 実際の地理データから計算された指標を使用しています")
        elif sample_data_path.exists():
            df = pd.read_csv(sample_data_path)
            st.warning("⚠️ シミュレーションデータを使用しています。実際のデータを使用するには generate_real_sample_data.py を実行してください。")
        else:
            # データが存在しない場合は生成
            st.warning("分析結果データが見つかりません。生成中...")
            df = generate_sample_data()
        
        # 住所情報を追加（キャッシュ済み）
        if 'address' not in df.columns:
            df['address'] = df.apply(lambda row: get_address_from_coordinates(row['latitude'], row['longitude']), axis=1)
        
        return df
    except Exception as e:
        st.error(f"サンプルデータの読み込みエラー: {e}")
        return None

def generate_sample_data() -> pd.DataFrame:
    """サンプルデータを生成"""
    np.random.seed(42)
    
    # 日本全国の緯度経度範囲
    bounds = config["data"]["bounds"]
    num_locations = config["data"]["sampling"]["num_locations"]
    
    data = []
    for i in range(num_locations):
        lat = np.random.uniform(bounds["south"], bounds["north"])
        lon = np.random.uniform(bounds["west"], bounds["east"])
        
        # サンプル指標値を生成
        result = {
            'location_id': i,
            'latitude': lat,
            'longitude': lon,
            'sparsity': np.random.uniform(0.1, 2.0),
            'resilience': np.random.uniform(0.0, 1.0),
            'multi_nodality': np.random.uniform(0.0, 5.0),
            'permeability': np.random.uniform(0.0, 1.0),
            'overlap': 0.0,  # 実装不可
            'emergence': np.random.uniform(0.0, 2.0)
        }
        data.append(result)
    
    return pd.DataFrame(data)

# サンプルデータの読み込み
sample_df = load_sample_data()
if sample_df is None:
    st.stop()

sample_df = sample_df.copy()
if 'location_id' in sample_df.columns:
    try:
        sample_df['location_id'] = sample_df['location_id'].astype(int)
    except ValueError:
        sample_df['location_id'] = sample_df['location_id']

metric_summary = summarize_metrics(
    sample_df,
    ["sparsity", "resilience", "multi_nodality", "permeability"],
)

normalized_metrics = [
    "sparsity",
    "resilience",
    "multi_nodality",
    "permeability",
    "emergence",
    "overlap",
]

for metric in normalized_metrics:
    if metric not in sample_df.columns:
        continue
    series = sample_df[metric].astype(float)
    min_val = metric_summary.get(metric, {}).get("min", float(series.min()))
    max_val = metric_summary.get(metric, {}).get("max", float(series.max()))
    rng = max(max_val - min_val, 1e-9)
    normalized_values = (series - min_val) / rng
    sample_df[f"{metric}_normalized"] = normalized_values.clip(0.0, 1.0)

location_lookup = sample_df.set_index('location_id') if 'location_id' in sample_df.columns else None


def format_location_label(loc_id: int) -> str:
    """Format location labels with names when available."""
    if location_lookup is None:
        return f"Location {int(loc_id)}"
    try:
        loc_id_int = int(loc_id)
        if loc_id_int in location_lookup.index:
            row = location_lookup.loc[loc_id_int]
            if 'name' in row.index:
                name_value = row.get('name')
                if isinstance(name_value, str) and name_value.strip():
                    return f"{name_value} (ID {loc_id_int})"
        return f"Location {loc_id_int}"
    except Exception:
        return f"Location {loc_id}"


def format_location_with_metrics(loc_id: int) -> str:
    """Format location labels with key metric summaries."""
    base_label = format_location_label(loc_id)
    if location_lookup is None:
        return base_label
    try:
        loc_id_int = int(loc_id)
        if loc_id_int in location_lookup.index:
            row = location_lookup.loc[loc_id_int]
            sparsity = row.get('sparsity', float('nan'))
            resilience = row.get('resilience', float('nan'))
            return f"{base_label} | S: {sparsity:.3f}, R: {resilience:.3f}"
    except Exception:
        pass
    return base_label

# サイドバー設定
st.sidebar.title("⚙️ 分析設定")

# 分析説明
st.sidebar.markdown("""
### 📊 分析概要
このアプリケーションは、指定された緯度経度周辺の集落形態を定量的に分析し、
以下の指標を計算します：

- **疎性**: 空間充填率と建物数の関係
- **適応性**: ネットワークのFiedler値によるレジリエンス
- **多中心性**: DBSCANクラスタリングによる核の分布
- **流動性**: パーコレーション分析によるオープンスペース連結性
- **創発性**: ネットワーク中心性と建物密度の関係
""")

# 緯度経度入力
st.sidebar.subheader("📍 分析地点指定")
col1, col2 = st.sidebar.columns(2)

with col1:
    input_lat = st.number_input(
        "緯度", 
        value=35.6762, 
        format="%.6f",
        help="分析対象地点の緯度を入力してください"
    )

with col2:
    input_lon = st.number_input(
        "経度", 
        value=139.6503, 
        format="%.6f",
        help="分析対象地点の経度を入力してください"
    )

# 分析実行ボタン
analyze_button = st.sidebar.button("🔍 分析実行", type="primary")

# メインコンテンツ
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📈 集落構造特性散布図")

    col_chart, col_image = st.columns([2, 1])

    with col_chart:
        tab_scatter, tab_pair = st.tabs(["Scatter Plot", "Pair Plot"])

        with tab_scatter:
            x_metric = 'sparsity_normalized' if 'sparsity_normalized' in sample_df.columns else 'sparsity'
            y_metric = 'resilience_normalized' if 'resilience_normalized' in sample_df.columns else 'resilience'
            color_metric = 'multi_nodality_normalized' if 'multi_nodality_normalized' in sample_df.columns else 'multi_nodality'
            size_metric = 'permeability_normalized' if 'permeability_normalized' in sample_df.columns else 'permeability'

            size_series = sample_df[size_metric].astype(float).fillna(0.0)
            if size_metric.endswith("_normalized"):
                size_series = size_series.clip(0.0, 1.0)
            size_display_col = f"_{size_metric}_marker"
            sample_df[size_display_col] = (size_series * 0.8) + 0.2

            hover_data = {}
            for field, formatter in [
                ('location_id', True),
                ('name', True),
                ('latitude', ':.4f'),
                ('longitude', ':.4f'),
                ('sparsity', ':.3f'),
                ('resilience', ':.3f'),
                ('multi_nodality', ':.3f'),
                ('permeability', ':.3f'),
                ('emergence', ':.3f'),
                ('address', True),
            ]:
                if field in sample_df.columns:
                    hover_data[field] = formatter
            hover_data[size_display_col] = False

            def _label(metric: str, base_label: str) -> str:
                return f"{base_label} (Normalized)" if metric.endswith("_normalized") else base_label

            scatter_fig = px.scatter(
                sample_df,
                x=x_metric,
                y=y_metric,
                color=color_metric,
                size=size_display_col,
                hover_data=hover_data,
                title='Urban Morphological Characteristics',
                labels={
                    x_metric: _label(x_metric, "Sparsity"),
                    y_metric: _label(y_metric, "Resilience"),
                    color_metric: _label(color_metric, "Polycentricity"),
                    size_display_col: "Marker size (scaled)",
                },
                color_continuous_scale='viridis',
                size_max=25
            )

            scatter_fig.update_traces(customdata=sample_df['location_id'])
            scatter_fig.update_layout(
                font=dict(family="Arial", size=12, color="black"),
                plot_bgcolor="white",
                paper_bgcolor="white",
                title=dict(
                    text="Urban Morphological Characteristics",
                    font=dict(size=16, color="black", family="Arial"),
                    x=0.5,
                    xanchor='center'
                ),
                showlegend=False,
                margin=dict(l=60, r=150, t=60, b=60),
                height=520,
                xaxis=dict(
                    showgrid=True,
                    gridcolor="lightgray",
                    gridwidth=0.5,
                    showline=True,
                    linecolor="black",
                    linewidth=1,
                    mirror=True,
                    title_font=dict(size=14, color="black", family="Arial"),
                    tickfont=dict(size=12, color="black", family="Arial"),
                    zeroline=False
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="lightgray",
                    gridwidth=0.5,
                    showline=True,
                    linecolor="black",
                    linewidth=1,
                    mirror=True,
                    title_font=dict(size=14, color="black", family="Arial"),
                    tickfont=dict(size=12, color="black", family="Arial"),
                    zeroline=False
                )
            )

            scatter_fig.update_coloraxes(
                colorbar=dict(
                    title=dict(
                        text="Polycentricity<br>(Normalized)",
                        font=dict(size=12, color="black", family="Arial")
                    ),
                    tickfont=dict(size=10, color="black", family="Arial"),
                    len=0.6,
                    thickness=15,
                    x=1.02,
                    y=0.7,
                    yanchor="middle",
                    bgcolor="white",
                    bordercolor="black",
                    borderwidth=1
                )
            )

            scatter_fig.add_annotation(
                x=1.02,
                y=0.25,
                xref="paper",
                yref="paper",
                text="<b>Point Size:</b><br>Permeability (Normalized)<br>(larger = higher)",
                showarrow=False,
                font=dict(size=10, color="black", family="Arial"),
                bgcolor="white",
                bordercolor="black",
                borderwidth=1,
                xanchor="left"
            )

            if analyze_button:
                distances = np.sqrt(
                    (sample_df['latitude'] - input_lat) ** 2 +
                    (sample_df['longitude'] - input_lon) ** 2
                )
                closest_idx = distances.idxmin()
                closest_point = sample_df.iloc[closest_idx]

                scatter_fig.add_trace(go.Scatter(
                    x=[closest_point[x_metric]],
                    y=[closest_point[y_metric]],
                    mode='markers',
                    marker=dict(
                        size=20,
                        color='red',
                        symbol='star',
                        line=dict(width=2, color='white')
                    ),
                    name='Selected location',
                    hovertemplate=(
                        "選択地点<br>"
                        "疎性(正規化): %{x:.3f}<br>"
                        "レジリエンス(正規化): %{y:.3f}<br>"
                        f"疎性(raw): {closest_point.get('sparsity', float('nan')):.3f}<br>"
                        f"レジリエンス(raw): {closest_point.get('resilience', float('nan')):.3f}"
                        "<extra></extra>"
                    )
                ))

            if x_metric.endswith("_normalized"):
                scatter_fig.update_xaxes(range=[0, 1])
            if y_metric.endswith("_normalized"):
                scatter_fig.update_yaxes(range=[0, 1])

            st.plotly_chart(scatter_fig, use_container_width=True, key="main_scatter")
            sample_df.drop(columns=[size_display_col], inplace=True, errors='ignore')

        with tab_pair:
            base_metrics = ['sparsity', 'resilience', 'multi_nodality', 'permeability']
            metric_label_map = {
                'sparsity': 'Sparsity',
                'resilience': 'Resilience',
                'multi_nodality': 'Polycentricity',
                'permeability': 'Permeability'
            }
            pair_dimensions = []
            pair_labels = {}

            for metric in base_metrics:
                normalized_col = f"{metric}_normalized"
                if normalized_col in sample_df.columns:
                    pair_dimensions.append(normalized_col)
                    pair_labels[normalized_col] = f"{metric_label_map[metric]} (Normalized)"
                elif metric in sample_df.columns:
                    pair_dimensions.append(metric)
                    pair_labels[metric] = metric_label_map[metric]

            color_metric_pair = 'multi_nodality_normalized' if 'multi_nodality_normalized' in sample_df.columns else 'multi_nodality'

            pair_hover_data = {}
            for field, formatter in [
                ('location_id', True),
                ('name', True),
                ('latitude', ':.4f'),
                ('longitude', ':.4f'),
                ('sparsity', ':.3f'),
                ('resilience', ':.3f'),
                ('multi_nodality', ':.3f'),
                ('permeability', ':.3f'),
                ('emergence', ':.3f'),
                ('address', True),
            ]:
                if field in sample_df.columns:
                    pair_hover_data[field] = formatter

            if pair_dimensions:
                pair_fig = px.scatter_matrix(
                    sample_df,
                    dimensions=pair_dimensions,
                    color=color_metric_pair,
                    hover_data=pair_hover_data,
                    labels=pair_labels,
                    color_continuous_scale='viridis'
                )
                pair_fig.update_traces(diagonal_visible=False)
                if any(dim.endswith("_normalized") for dim in pair_dimensions):
                    pair_fig.update_xaxes(range=[0, 1])
                    pair_fig.update_yaxes(range=[0, 1])
                colorbar_title = "Polycentricity (Normalized)" if color_metric_pair.endswith("_normalized") else "Polycentricity"
                pair_fig.update_layout(
                    height=520,
                    font=dict(family="Arial", size=11, color="black"),
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    coloraxis_colorbar=dict(
                        title=dict(text=colorbar_title, font=dict(size=12)),
                        tickfont=dict(size=10)
                    ),
                    dragmode='select'
                )
                st.plotly_chart(pair_fig, use_container_width=True, key="pair_plot")
            else:
                st.info("表示可能な指標がありません。データ列を確認してください。")

        st.subheader("🧭 Location Metric Overview")
        if location_lookup is not None:
            display_columns = [
                'location_id',
                'name',
                'latitude',
                'longitude',
                'sparsity',
                'resilience',
                'multi_nodality',
                'permeability',
                'emergence',
                'overlap'
            ]
            available_columns = [col for col in display_columns if col in sample_df.columns]
            if available_columns and len(sample_df) > 0:
                row_limit = st.slider(
                    "表示行数",
                    min_value=1,
                    max_value=len(sample_df),
                    value=min(15, len(sample_df)),
                    key="location_table_row_limit"
                )
                display_df = sample_df[available_columns].head(row_limit).copy()
                if 'latitude' in display_df.columns:
                    display_df['latitude'] = display_df['latitude'].map(lambda v: f"{v:.4f}")
                if 'longitude' in display_df.columns:
                    display_df['longitude'] = display_df['longitude'].map(lambda v: f"{v:.4f}")
                for metric_col in ['sparsity', 'resilience', 'multi_nodality', 'permeability', 'emergence', 'overlap']:
                    if metric_col in display_df.columns:
                        display_df[metric_col] = display_df[metric_col].map(lambda v: f"{v:.4f}")

                header_values = [col.replace('_', ' ').title() for col in available_columns]
                cell_values = [display_df[col].tolist() for col in available_columns]

                table_fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(
                                values=header_values,
                                fill_color="#1f77b4",
                                font=dict(color="white", size=12),
                                align="left"
                            ),
                            cells=dict(
                                values=cell_values,
                                fill_color="#f0f2f6",
                                align="left",
                                font=dict(size=11)
                            ),
                            columnwidth=[70] + [120] * (len(available_columns) - 1)
                        )
                    ]
                )
                table_fig.update_layout(
                    margin=dict(l=10, r=10, t=40, b=10),
                    height=320
                )
                st.plotly_chart(table_fig, use_container_width=True, key="location_metric_table")
            elif available_columns:
                st.info("表示するデータがありません。")
            else:
                st.info("表示可能な指標データが見つかりません。")
        else:
            st.info("位置情報が利用できないため一覧を表示できませんでした。")


    with col_image:
        st.subheader("🔍 Location Details")
        
        # 地点選択用のセレクトボックス（右側用）
        location_options = sample_df['location_id'].tolist()
        selected_location_right = st.selectbox(
            "Select a location to view details:",
            options=location_options,
            format_func=format_location_label,
            key="right_location_selector"
        )
        
        # 選択された地点の情報を表示
        if selected_location_right is not None:
            try:
                selected_row_right = location_lookup.loc[int(selected_location_right)]
            except Exception:
                selected_row_right = sample_df[sample_df['location_id'] == selected_location_right].iloc[0]
            
            st.write(f"**{format_location_label(selected_location_right)}**")
            st.write(f"**地点名**: {selected_row_right.get('name', '地点名なし')}")
            st.write(f"**住所**: {selected_row_right.get('address', '住所情報なし')}")
            st.write(f"**緯度**: {selected_row_right['latitude']:.4f}")
            st.write(f"**経度**: {selected_row_right['longitude']:.4f}")
            st.write(f"**疎性**: {selected_row_right['sparsity']:.3f}")
            st.write(f"**適応性**: {selected_row_right['resilience']:.3f}")
            st.write(f"**多中心性**: {selected_row_right['multi_nodality']:.3f}")
            st.write(f"**流動性**: {selected_row_right['permeability']:.3f}")
            st.write(f"**創発性**: {selected_row_right['emergence']:.3f}")
            
            metric_columns = [
                col for col in [
                    'sparsity',
                    'resilience',
                    'multi_nodality',
                    'permeability',
                    'emergence',
                    'overlap'
                ] if col in sample_df.columns
            ]

            if metric_columns:
                metric_fig = px.bar(
                    x=[col.replace('_', ' ').title() for col in metric_columns],
                    y=[selected_row_right[col] for col in metric_columns],
                    labels={'x': 'Metric', 'y': 'Value'},
                    title="Metric Profile"
                )
                metric_fig.update_layout(
                    height=320,
                    margin=dict(l=40, r=10, t=60, b=40),
                    yaxis=dict(title="Value"),
                    xaxis=dict(title=None)
                )
                st.plotly_chart(
                    metric_fig,
                    use_container_width=True,
                    key=f"metric_profile_{selected_location_right}"
                )
            
            with st.spinner("Comparative view rendering..."):
                try:
                    overview_fig, _ = create_location_overview_figure(
                        selected_row_right,
                        metric_summary,
                        radius_meters=int(config['analysis_radius_meters']),
                    )
                    st.pyplot(overview_fig, use_container_width=True)
                    plt.close(overview_fig)
                except Exception as viz_error:  # pragma: no cover - UI only path
                    st.warning(f"可視化の生成に失敗しました: {viz_error}")

            st.caption("📁 Exported images (if previously generated)")

            # 対応する画像を表示
            real_network_images_dir = project_root / "data" / "real_network_images"
            real_image_path = real_network_images_dir / f"real_network_{int(selected_location_right):03d}.png"
            
            if real_image_path.exists():
                st.image(str(real_image_path), 
                       caption=f"Location {int(selected_location_right)} - Real Geographic Analysis",
                       width='stretch')
            else:
                # フォールバック: 通常のネットワーク画像
                network_images_dir = project_root / "data" / "network_images"
                image_path = network_images_dir / f"network_{int(selected_location_right):03d}.png"
                
                if image_path.exists():
                    st.image(str(image_path), 
                           caption=f"Location {int(selected_location_right)} - Network Structure",
                           width='stretch')
                else:
                    st.image("https://via.placeholder.com/300x200/cccccc/666666?text=Image+Not+Available", 
                            caption=f"Image for location {int(selected_location_right)} not available", 
                            width='stretch')
    
    # 選択された地点のネットワーク画像表示エリア
    st.subheader("🔍 Selected Location Network")
    
    # 地点選択用のセレクトボックス
    location_options = sample_df['location_id'].tolist()
    selected_location = st.selectbox(
        "Select a location to view its network structure:",
        options=location_options,
        format_func=format_location_with_metrics
    )
    
    # 選択された地点の詳細情報とネットワーク画像を表示
    if selected_location is not None:
        try:
            selected_row = location_lookup.loc[int(selected_location)]
        except Exception:
            selected_row = sample_df[sample_df['location_id'] == selected_location].iloc[0]
        
        # 詳細情報の表示
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Sparsity", f"{selected_row['sparsity']:.3f}")
        with col_info2:
            st.metric("Resilience", f"{selected_row['resilience']:.3f}")
        with col_info3:
            st.metric("Polycentricity", f"{selected_row['multi_nodality']:.3f}")
        
        # 対応するネットワーク画像の表示（実際の地理データ対応画像を優先）
        real_network_images_dir = project_root / "data" / "real_network_images"
        real_image_path = real_network_images_dir / f"real_network_{int(selected_location):03d}.png"
        
        if real_image_path.exists():
            st.image(str(real_image_path), 
                   caption=f"Real Geographic Analysis for Location {int(selected_location)}",
                   width='stretch')
        else:
            # フォールバック: 通常のネットワーク画像
            network_images_dir = project_root / "data" / "network_images"
            image_path = network_images_dir / f"network_{int(selected_location):03d}.png"
            
            if image_path.exists():
                st.image(str(image_path), 
                       caption=f"Network Structure for Location {int(selected_location)}",
                       width='stretch')
            else:
                # 画像が存在しない場合は、その地点の情報を表示
                st.info(f"{format_location_label(selected_location)} の詳細情報:")
                st.write(f"**地点名**: {selected_row.get('name', '地点名なし')}")
                st.write(f"**住所**: {selected_row.get('address', '住所情報なし')}")
                st.write(f"**緯度**: {selected_row['latitude']:.4f}")
                st.write(f"**経度**: {selected_row['longitude']:.4f}")
                st.write(f"**疎性**: {selected_row['sparsity']:.3f}")
                st.write(f"**適応性**: {selected_row['resilience']:.3f}")
                st.write(f"**多中心性**: {selected_row['multi_nodality']:.3f}")
                st.write(f"**流動性**: {selected_row['permeability']:.3f}")
                st.write(f"**創発性**: {selected_row['emergence']:.3f}")
                
                # プレースホルダー画像を表示
                st.image("https://via.placeholder.com/400x300/cccccc/666666?text=Network+Image+Not+Available", 
                        caption=f"Network image for location {int(selected_location)} not available", 
                        width='stretch')
    
    # 実際の地理データ対応ネットワーク画像の表示
    st.subheader("🗺️ Real Geographic Network Analysis")
    st.write("Detailed network analysis with actual geographic data (2x2 grid showing buildings, roads, and network structures):")
    
    # 実際の地理データ対応ネットワーク画像ディレクトリの確認
    real_network_images_dir = project_root / "data" / "real_network_images"
    if real_network_images_dir.exists():
        # 画像ファイルの一覧を取得
        real_image_files = sorted(list(real_network_images_dir.glob("*.png")))
        
        if real_image_files:
            # 2列のグリッドで表示（大きな画像のため）
            cols = st.columns(2)
            for i, image_file in enumerate(real_image_files):
                with cols[i % 2]:
                    # 画像の読み込みと表示
                    try:
                        st.image(str(image_file), 
                               caption=f"Location {image_file.stem.split('_')[2]} - Real Geographic Analysis",
                               width='stretch')
                    except Exception as e:
                        st.error(f"画像読み込みエラー: {e}")
        else:
            st.warning("実際の地理データ対応ネットワーク画像が見つかりません。")
    else:
        st.warning("実際の地理データ対応ネットワーク画像ディレクトリが見つかりません。")
    
    # 従来のネットワーク画像ギャラリーの表示
    st.subheader("📊 Network Structure Gallery")
    st.write("Representative network structures across different urban characteristics:")
    
    # ネットワーク画像ディレクトリの確認
    network_images_dir = project_root / "data" / "network_images"
    if network_images_dir.exists():
        # 画像ファイルの一覧を取得
        image_files = sorted(list(network_images_dir.glob("*.png")))
        
        if image_files:
            # 4列のグリッドで表示
            cols = st.columns(4)
            for i, image_file in enumerate(image_files):
                with cols[i % 4]:
                    # 画像の読み込みと表示
                    try:
                        st.image(str(image_file), 
                               caption=f"Location {image_file.stem.split('_')[1]}",
                               width='stretch')
                    except Exception as e:
                        st.error(f"画像読み込みエラー: {e}")
        else:
            st.warning("ネットワーク画像が見つかりません。")
    else:
        st.warning("ネットワーク画像ディレクトリが見つかりません。")

with col2:
    st.header("📊 統計情報")
    
    # 基本統計
    st.subheader("基本統計")
    col2_1, col2_2 = st.columns(2)
    
    with col2_1:
        st.metric("データ点数", len(sample_df))
        st.metric("平均疎性", f"{sample_df['sparsity'].mean():.3f}")
        st.metric("平均適応性", f"{sample_df['resilience'].mean():.3f}")
    
    with col2_2:
        st.metric("相関係数", f"{sample_df['sparsity'].corr(sample_df['resilience']):.3f}")
        st.metric("最大疎性", f"{sample_df['sparsity'].max():.3f}")
        st.metric("最大適応性", f"{sample_df['resilience'].max():.3f}")
    
    # 分布ヒストグラム
    st.subheader("疎性分布")
    fig_hist = px.histogram(
        sample_df, 
        x='sparsity', 
        nbins=20,
        title="疎性の分布"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# 分析実行時の詳細表示
if analyze_button:
    st.header("🔍 詳細分析結果")
    
    with st.spinner("分析を実行中..."):
        try:
            # データ取得
            building_gdf, road_gdf = load_spatial_data(input_lat, input_lon)
            
            # データ前処理
            building_gdf = preprocess_building_data(building_gdf)
            road_gdf = preprocess_road_data(road_gdf)
            
            # ネットワーク構築
            network_graph = create_urban_network(building_gdf, road_gdf)
            
            # 指標計算
            calculators = {
                'multi_nodality': MultiNodalityCalculator(),
                'sparsity': SparsityCalculator(),
                'permeability': PermeabilityCalculator(),
                'overlap': OverlapCalculator(),
                'emergence': EmergenceCalculator(),
                'resilience': ResilienceCalculator()
            }
            
            results = {}
            for name, calculator in calculators.items():
                if name == 'permeability':
                    results[name] = calculator.calculate(building_gdf, road_gdf)
                elif name == 'emergence':
                    results[name] = calculator.calculate(building_gdf, network_graph)
                elif name == 'resilience':
                    results[name] = calculator.calculate(building_gdf, road_gdf, network_graph)
                else:
                    results[name] = calculator.calculate(building_gdf)
            
            # 結果表示
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 計算結果")
                for metric_name, result in results.items():
                    if isinstance(result, dict):
                        main_value = result.get(metric_name, 0.0)
                        st.metric(
                            metric_name.replace('_', ' ').title(),
                            f"{main_value:.4f}"
                        )
            
            with col2:
                st.subheader("🏗️ データ統計")
                st.metric("建物数", len(building_gdf))
                st.metric("道路数", len(road_gdf))
                st.metric("ネットワークノード数", network_graph.number_of_nodes())
                st.metric("ネットワークエッジ数", network_graph.number_of_edges())
            
            # ネットワーク可視化
            st.subheader("🕸️ ネットワーク構造")
            
            # ネットワークの可視化データを準備
            viz_data = visualize_network(network_graph, building_gdf, road_gdf)
            
            # Matplotlibでネットワークを描画
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # ノードの描画
            node_positions = viz_data['nodes']['positions']
            node_types = viz_data['nodes']['types']
            
            # 建物ノード
            building_nodes = [node for node, node_type in node_types.items() 
                            if node_type == 'building']
            building_positions = {node: pos for node, pos in node_positions.items() 
                                if node in building_nodes}
            
            if building_positions:
                nx.draw_networkx_nodes(
                    network_graph, 
                    building_positions, 
                    nodelist=building_nodes,
                    node_color='lightblue', 
                    node_size=50, 
                    alpha=0.7,
                    ax=ax
                )
            
            # 道路ノード
            road_nodes = [node for node, node_type in node_types.items() 
                         if node_type == 'road']
            road_positions = {node: pos for node, pos in node_positions.items() 
                            if node in road_nodes}
            
            if road_positions:
                nx.draw_networkx_nodes(
                    network_graph, 
                    road_positions, 
                    nodelist=road_nodes,
                    node_color='lightgreen', 
                    node_size=20, 
                    alpha=0.7,
                    ax=ax
                )
            
            # エッジの描画
            nx.draw_networkx_edges(
                network_graph, 
                node_positions, 
                alpha=0.3, 
                width=0.5,
                ax=ax
            )
            
            ax.set_title(f"集落ネットワーク構造 (緯度: {input_lat:.4f}, 経度: {input_lon:.4f})")
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"分析実行エラー: {e}")
            logger.error(f"分析実行エラー: {e}")

# フッター
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        OpenSparsity Dashboard v0.1.0 | 
        集落形態の定量的分析と可視化
    </div>
    """,
    unsafe_allow_html=True
)
