#!/usr/bin/env python3
"""
Dashアプリケーション - 実際のデータ + OpenStreetMap衛星画像
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import base64

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 衛星画像ユーティリティをインポート
from src.app.satellite_utils import tile_fetcher

def create_dash_app():
    """Dashアプリケーションを作成"""
    
    # 実際のデータを読み込み
    real_data_path = project_root / "data" / "processed" / "real_analysis_results.csv"
    sample_data_path = project_root / "data" / "processed" / "sample_analysis_results.csv"
    
    if real_data_path.exists():
        df = pd.read_csv(real_data_path)
        print(f"✅ 実際の地理データを読み込みました: {len(df)}地点")
    elif sample_data_path.exists():
        df = pd.read_csv(sample_data_path)
        print(f"⚠️ サンプルデータを読み込みました: {len(df)}地点")
    else:
        # フォールバック：サンプルデータを生成
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
        print(f"⚠️ フォールバック：ランダムデータを生成しました: {len(df)}地点")
    
    # Dashアプリケーションを作成
    app = dash.Dash(__name__)
    
    # 静的ファイルの設定
    app.css.config.serve_locally = True
    app.scripts.config.serve_locally = True
    
    # レイアウト
    app.layout = html.Div([
        html.H1("🏙️ OpenSparsity - インタラクティブ可視化（実際のデータ + 衛星画像）", 
                style={'textAlign': 'center', 'marginBottom': 30}),
        
        # 左右分割レイアウト
        html.Div([
            # 左側：散布図
            html.Div([
                html.H3("都市形態学的特性", style={'textAlign': 'center', 'marginBottom': 20}),
                dcc.Graph(
                    id='scatter-plot',
                    figure=create_scatter_plot(df),
                    style={'height': '700px', 'width': '100%'}
                )
            ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '0 10px'}),
            
            # 右側：衛星画像と詳細情報
            html.Div([
                html.H3("地点詳細情報", style={'textAlign': 'center', 'marginBottom': 20}),
                
                # ホバー情報表示エリア
                html.Div(id='hover-info', style={'margin': '10px 0', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
                
                # 衛星画像表示エリア
                html.Div(id='satellite-image', style={'margin': '10px 0', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
                
                # ネットワーク画像表示エリア
                html.Div(id='network-image', style={'margin': '10px 0', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
                
                # 詳細情報表示エリア
                html.Div(id='location-details', style={'margin': '10px 0', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
            ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '0 10px', 'height': '700px', 'overflowY': 'auto'})
        ], style={'display': 'flex', 'width': '100%'})
    ])
    
    # ホバー情報を処理するコールバック
    @app.callback(
        Output('hover-info', 'children'),
        Output('satellite-image', 'children'),
        Output('network-image', 'children'),
        Output('location-details', 'children'),
        Input('scatter-plot', 'hoverData')
    )
    def update_hover_info(hover_data):
        """ホバー情報を処理して詳細情報と画像を表示"""
        
        if hover_data is None:
            return (
                "💡 散布図のポイントにマウスを合わせて詳細情報を表示",
                "",
                "",
                ""
            )
        
        try:
            # ホバーされたポイントの情報を取得
            point = hover_data['points'][0]
            
            # customdataが存在するかチェック
            if 'customdata' in point and point['customdata'] is not None:
                location_id = point['customdata']
            else:
                # customdataが存在しない場合は、pointのインデックスを使用
                point_index = point.get('pointIndex', 0)
                location_id = df.iloc[point_index]['location_id']
            
            # データから該当する地点の情報を取得
            location_data = df[df['location_id'] == location_id].iloc[0]
            
            # ホバー情報を表示
            hover_info = f"""
            🎯 地点 {location_id} の詳細情報
            
            📍 座標: 緯度 {location_data['latitude']:.6f}, 経度 {location_data['longitude']:.6f}
            📊 疎性 (Sparsity): {location_data['sparsity']:.3f}
            🔄 レジリエンス (Resilience): {location_data['resilience']:.3f}
            🏢 多中心性 (Multi-nodality): {location_data['multi_nodality']:.3f}
            🚶 流動性 (Permeability): {location_data['permeability']:.3f}
            🌟 創発性 (Emergence): {location_data['emergence']:.3f}
            🔗 重なり (Overlap): {location_data['overlap']:.3f}
            """
            
            # 衛星画像を取得
            satellite_image_component = get_satellite_image_component(
                location_data['latitude'], 
                location_data['longitude']
            )
            
            # ネットワーク画像を取得
            network_image_component = get_network_image_component(location_id)
            
            # 詳細情報を表示
            location_details = """
            📈 指標の解釈
            
            • 疎性: 建物密度の低さを示す指標
            • レジリエンス: ネットワークの回復力
            • 多中心性: 複数の中心を持つ都市構造
            • 流動性: 人の移動のしやすさ
            • 創発性: 新しい機能が生まれる可能性
            • 重なり: 機能の重複度
            """
            
            return hover_info, satellite_image_component, network_image_component, location_details
            
        except Exception as e:
            return f"エラーが発生しました: {str(e)}", "", "", ""
    
    return app

def create_scatter_plot(df):
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
        customdata=df['location_id'].tolist(),
        hovertemplate='<b>地点 %{customdata}</b><br>' +
                     '📍 座標: %{x:.3f}, %{y:.3f}<br>' +
                     '📊 Sparsity: %{x:.3f}<br>' +
                     '🔄 Resilience: %{y:.3f}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title='Urban Morphological Characteristics',
        xaxis_title='Sparsity',
        yaxis_title='Resilience',
        hovermode='closest',
        height=600,
        width=600,
        showlegend=False
    )
    
    return fig

def get_satellite_image_component(lat, lon):
    """衛星画像のHTMLコンポーネントを取得"""
    try:
        # OpenStreetMapタイルを取得
        img_base64 = tile_fetcher.get_satellite_image_base64(lat, lon, zoom=15)
        
        if img_base64:
            return html.Div([
                html.H4(f"🛰️ 衛星画像 (OpenStreetMap)"),
                html.P(f"座標: 緯度 {lat:.6f}, 経度 {lon:.6f}"),
                html.Img(src=f"data:image/png;base64,{img_base64}", 
                        style={'maxWidth': '100%', 'height': '400px', 'objectFit': 'contain', 'border': '2px solid #ddd', 'borderRadius': '5px'})
            ])
        else:
            return html.Div([
                html.H4(f"🛰️ 衛星画像"),
                html.P("衛星画像の取得に失敗しました。", style={'color': 'red'})
            ])
    except Exception as e:
        return html.Div([
            html.H4(f"🛰️ 衛星画像"),
            html.P(f"エラー: {str(e)}", style={'color': 'red'})
        ])

def get_network_image_component(location_id):
    """ネットワーク画像のHTMLコンポーネントを取得"""
    import base64
    
    # 画像ファイルのパスを確認
    corrected_image_path = project_root / "data" / "corrected_network_images" / f"corrected_network_{location_id:03d}.png"
    real_image_path = project_root / "data" / "real_network_images" / f"real_network_{location_id:03d}.png"
    network_image_path = project_root / "data" / "network_images" / f"network_{location_id:03d}.png"
    
    if corrected_image_path.exists():
        # 画像をbase64エンコード
        with open(corrected_image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        return html.Div([
            html.H4(f"📍 地点 {location_id} のネットワーク構造"),
            html.P(f"修正されたネットワーク画像: {corrected_image_path.name}"),
            html.Img(src=f"data:image/png;base64,{img_base64}", 
                    style={'maxWidth': '100%', 'height': '500px', 'objectFit': 'contain', 'border': '2px solid #ddd', 'borderRadius': '5px'})
        ])
    elif real_image_path.exists():
        # 画像をbase64エンコード
        with open(real_image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        return html.Div([
            html.H4(f"📍 地点 {location_id} のネットワーク構造"),
            html.P(f"実際のネットワーク画像: {real_image_path.name}"),
            html.Img(src=f"data:image/png;base64,{img_base64}", 
                    style={'maxWidth': '100%', 'height': '500px', 'objectFit': 'contain', 'border': '2px solid #ddd', 'borderRadius': '5px'})
        ])
    elif network_image_path.exists():
        # 画像をbase64エンコード
        with open(network_image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        return html.Div([
            html.H4(f"📍 地点 {location_id} のネットワーク構造"),
            html.P(f"ネットワーク画像: {network_image_path.name}"),
            html.Img(src=f"data:image/png;base64,{img_base64}", 
                    style={'maxWidth': '100%', 'height': '500px', 'objectFit': 'contain', 'border': '2px solid #ddd', 'borderRadius': '5px'})
        ])
    else:
        return html.Div([
            html.H4(f"📍 地点 {location_id} のネットワーク構造"),
            html.P("画像が見つかりません。")
        ])

if __name__ == "__main__":
    app = create_dash_app()
    app.run(debug=True, host='0.0.0.0', port=8052)
