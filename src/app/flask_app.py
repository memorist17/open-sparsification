#!/usr/bin/env python3
"""
Flaskアプリケーション - ホバー機能付きインタラクティブ可視化
"""

from flask import Flask, render_template, jsonify, request
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

app = Flask(__name__)

# データを読み込み
data_path = project_root / "data" / "processed" / "real_analysis_results.csv"
if not data_path.exists():
    # サンプルデータを生成
    df = pd.DataFrame({
        'location_id': range(100),
        'latitude': np.random.uniform(30.0, 46.0, 100),
        'longitude': np.random.uniform(129.0, 146.0, 100),
        'sparsity': np.random.uniform(0.1, 1.5, 100),
        'resilience': np.random.uniform(0.2, 0.9, 100),
        'multi_nodality': np.random.uniform(0.0, 1.0, 100),
        'permeability': np.random.uniform(0.3, 1.0, 100),
        'emergence': np.random.uniform(0.0, 0.8, 100),
        'overlap': np.zeros(100)
    })
else:
    df = pd.read_csv(data_path)

def create_scatter_plot():
    """散布図を作成"""
    fig = go.Figure()
    
    # 散布図のデータポイントを追加
    fig.add_trace(go.Scatter(
        x=df['sparsity'],
        y=df['resilience'],
        mode='markers',
        marker=dict(
            size=df['permeability'] * 20,
            color=df['multi_nodality'],
            colorscale='viridis',
            showscale=True,
            colorbar=dict(title="Polycentricity")
        ),
        customdata=df[['location_id', 'latitude', 'longitude', 'sparsity', 'resilience', 'multi_nodality', 'permeability', 'emergence', 'overlap']],
        hovertemplate='<b>地点 %{customdata[0]}</b><br>' +
                     '📍 座標: %{customdata[1]:.6f}, %{customdata[2]:.6f}<br>' +
                     '📊 Sparsity: %{customdata[3]:.3f}<br>' +
                     '🔄 Resilience: %{customdata[4]:.3f}<br>' +
                     '🏢 Polycentricity: %{customdata[5]:.3f}<br>' +
                     '🚶 Permeability: %{customdata[6]:.3f}<br>' +
                     '🌟 Emergence: %{customdata[7]:.3f}<br>' +
                     '🔗 Overlap: %{customdata[8]:.3f}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title='Urban Morphological Characteristics',
        xaxis_title='Sparsity',
        yaxis_title='Resilience',
        hovermode='closest',
        height=600
    )
    
    return fig

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/api/plot')
def get_plot():
    """散布図のデータを取得"""
    fig = create_scatter_plot()
    return jsonify(fig.to_dict())

@app.route('/api/location/<int:location_id>')
def get_location_info(location_id):
    """地点の詳細情報を取得"""
    if location_id not in df['location_id'].values:
        return jsonify({"error": "地点が見つかりません"})
    
    location_data = df[df['location_id'] == location_id].iloc[0]
    
    return jsonify({
        "location_id": int(location_data['location_id']),
        "latitude": float(location_data['latitude']),
        "longitude": float(location_data['longitude']),
        "sparsity": float(location_data['sparsity']),
        "resilience": float(location_data['resilience']),
        "multi_nodality": float(location_data['multi_nodality']),
        "permeability": float(location_data['permeability']),
        "emergence": float(location_data['emergence']),
        "overlap": float(location_data['overlap'])
    })

@app.route('/api/network_image/<int:location_id>')
def get_network_image(location_id):
    """ネットワーク画像のパスを取得"""
    # 画像ファイルのパスを確認
    corrected_image_path = project_root / "data" / "corrected_network_images" / f"corrected_network_{location_id:03d}.png"
    real_image_path = project_root / "data" / "real_network_images" / f"real_network_{location_id:03d}.png"
    network_image_path = project_root / "data" / "network_images" / f"network_{location_id:03d}.png"
    
    if corrected_image_path.exists():
        return jsonify({"image_path": str(corrected_image_path)})
    elif real_image_path.exists():
        return jsonify({"image_path": str(real_image_path)})
    elif network_image_path.exists():
        return jsonify({"image_path": str(network_image_path)})
    else:
        return jsonify({"error": "画像が見つかりません"})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
