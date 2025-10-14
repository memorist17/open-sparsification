"""
OpenSparsity Streamlitメインアプリケーション

地理空間データによる都市構造特性分析のインタラクティブダッシュボード
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from typing import Dict, Any, List, Tuple
import json

# プロジェクトモジュールのインポート
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.config import get_config, load_config
from src.utils.logger import get_logger
from src.data.fetcher import VectorTileFetcher
from src.data.preprocessor import DataPreprocessor
from src.metrics import (
    MultiNodalityCalculator,
    SparsityCalculator,
    PermeabilityCalculator,
    OverlapCalculator,
    EmergenceCalculator,
    ResilienceCalculator
)

# ログ設定
logger = get_logger(__name__)

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
    }
    .stSelectbox > div > div {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# メインヘッダー
st.markdown('<h1 class="main-header">🏙️ OpenSparsity Dashboard</h1>', unsafe_allow_html=True)
st.markdown("地理空間データによる都市構造特性分析")

# サイドバー設定
st.sidebar.title("⚙️ 設定")

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

# サイドバー設定項目
st.sidebar.subheader("📊 分析設定")

# 分析対象地点数
num_locations = st.sidebar.slider(
    "分析対象地点数",
    min_value=50,
    max_value=500,
    value=config.get("data", {}).get("sampling", {}).get("num_locations", 300),
    step=50
)

# 表示指標の選択
available_metrics = ["sparsity", "resilience", "multi_nodality", "permeability", "overlap", "emergence"]
selected_metrics = st.sidebar.multiselect(
    "表示指標",
    options=available_metrics,
    default=config.get("app", {}).get("default", {}).get("selected_metrics", ["sparsity", "resilience"])
)

# 地図の中心とズーム
map_center = config.get("app", {}).get("default", {}).get("map_center", [35.6762, 139.6503])
map_zoom = config.get("app", {}).get("default", {}).get("map_zoom", 10)

col1, col2 = st.sidebar.columns(2)
with col1:
    center_lat = st.number_input("地図中心緯度", value=map_center[0], format="%.4f")
with col2:
    center_lon = st.number_input("地図中心経度", value=map_center[1], format="%.4f")

# メインコンテンツ
tab1, tab2, tab3 = st.tabs(["📈 散布図分析", "🗺️ 地図表示", "📊 詳細分析"])

# データ取得と分析（キャッシュ）
@st.cache_data
def get_analysis_data(num_locations: int) -> Dict[str, Any]:
    """分析データを取得"""
    try:
        logger.info(f"分析データ取得開始: {num_locations}地点")
        
        # データ取得
        fetcher = VectorTileFetcher()
        preprocessor = DataPreprocessor()
        
        # サンプル地点を生成
        bounds = config["data"]["bounds"]
        locations = preprocessor.sample_locations(
            (bounds["west"], bounds["south"], bounds["east"], bounds["north"]),
            num_locations
        )
        
        # 各地点の指標を計算（簡略化）
        results = []
        for i, (lat, lon) in enumerate(locations):
            if i % 50 == 0:
                logger.info(f"進捗: {i}/{num_locations}")
            
            # サンプルデータを生成（実際の実装では各地点のデータを取得・分析）
            result = {
                'location_id': i,
                'latitude': lat,
                'longitude': lon,
                'sparsity': np.random.uniform(0.1, 2.0),
                'resilience': np.random.uniform(0.0, 1.0),
                'multi_nodality': np.random.uniform(0.0, 5.0),
                'permeability': np.random.uniform(0.0, 1.0),
                'overlap': np.random.uniform(0.0, 0.5),
                'emergence': np.random.uniform(0.0, 2.0)
            }
            results.append(result)
        
        df = pd.DataFrame(results)
        logger.info(f"分析データ取得完了: {len(df)}地点")
        return {"dataframe": df, "locations": locations}
        
    except Exception as e:
        logger.error(f"分析データ取得エラー: {e}")
        st.error(f"データ取得エラー: {e}")
        return None

# データ取得
with st.spinner("分析データを取得中..."):
    analysis_data = get_analysis_data(num_locations)

if analysis_data is None:
    st.error("データの取得に失敗しました。")
    st.stop()

df = analysis_data["dataframe"]

# タブ1: 散布図分析
with tab1:
    st.header("📈 都市構造特性散布図")
    
    if len(selected_metrics) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            x_metric = st.selectbox("X軸指標", selected_metrics, index=0)
        with col2:
            y_metric = st.selectbox("Y軸指標", selected_metrics, index=1)
        
        # 散布図を作成
        fig = px.scatter(
            df,
            x=x_metric,
            y=y_metric,
            color='resilience',
            size='multi_nodality',
            hover_data=['latitude', 'longitude'],
            title=f"{x_metric} vs {y_metric}",
            labels={
                x_metric: x_metric.replace('_', ' ').title(),
                y_metric: y_metric.replace('_', ' ').title()
            }
        )
        
        fig.update_layout(
            height=600,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 統計情報
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                f"平均 {x_metric.replace('_', ' ').title()}",
                f"{df[x_metric].mean():.3f}"
            )
        with col2:
            st.metric(
                f"平均 {y_metric.replace('_', ' ').title()}",
                f"{df[y_metric].mean():.3f}"
            )
        with col3:
            correlation = df[x_metric].corr(df[y_metric])
            st.metric("相関係数", f"{correlation:.3f}")
        with col4:
            st.metric("データ点数", len(df))
    
    else:
        st.warning("散布図を表示するには、少なくとも2つの指標を選択してください。")

# タブ2: 地図表示
with tab2:
    st.header("🗺️ 地理的分布")
    
    # 地図を作成
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=map_zoom,
        tiles='OpenStreetMap'
    )
    
    # データポイントを地図に追加
    for _, row in df.iterrows():
        # 色を指標値に基づいて決定
        if 'resilience' in selected_metrics:
            color_value = row['resilience']
            color = 'red' if color_value < 0.3 else 'orange' if color_value < 0.7 else 'green'
        else:
            color = 'blue'
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            popup=f"""
            <b>Location {row['location_id']}</b><br>
            Lat: {row['latitude']:.4f}<br>
            Lon: {row['longitude']:.4f}<br>
            Sparsity: {row['sparsity']:.3f}<br>
            Resilience: {row['resilience']:.3f}
            """,
            color=color,
            fill=True,
            fillOpacity=0.7
        ).add_to(m)
    
    # 地図を表示
    st_folium(m, width=700, height=500)
    
    # 地図統計
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("表示地点数", len(df))
    with col2:
        st.metric("緯度範囲", f"{df['latitude'].min():.3f} - {df['latitude'].max():.3f}")
    with col3:
        st.metric("経度範囲", f"{df['longitude'].min():.3f} - {df['longitude'].max():.3f}")

# タブ3: 詳細分析
with tab3:
    st.header("📊 詳細分析")
    
    # 指標別の詳細統計
    st.subheader("指標別統計")
    
    metric_stats = df[selected_metrics].describe()
    st.dataframe(metric_stats, use_container_width=True)
    
    # ヒートマップ
    if len(selected_metrics) > 1:
        st.subheader("指標間相関")
        correlation_matrix = df[selected_metrics].corr()
        
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            title="指標間相関マトリックス"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 分布ヒストグラム
    st.subheader("指標分布")
    
    cols = st.columns(min(len(selected_metrics), 3))
    for i, metric in enumerate(selected_metrics):
        with cols[i % 3]:
            fig = px.histogram(
                df,
                x=metric,
                title=f"{metric.replace('_', ' ').title()} 分布",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)

# フッター
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        OpenSparsity Dashboard v0.1.0 | 
        地理空間データによる都市構造特性分析基盤
    </div>
    """,
    unsafe_allow_html=True
)
