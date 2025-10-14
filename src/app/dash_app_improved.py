#!/usr/bin/env python3
"""
改良されたDashアプリケーション - キャッシュ機能付き衛星画像 + 見やすいレイアウト
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

# 改良された衛星画像キャッシュをインポート
from src.app.satellite_cache import satellite_cache

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
    
    # 改良されたレイアウト
    app.layout = html.Div([
        html.H1("🏙️ OpenSparsity - インタラクティブ可視化（改良版）", 
                style={'textAlign': 'center', 'marginBottom': 30, 'color': '#2c3e50'}),
        
        # 左右分割レイアウト（改良版）
        html.Div([
            # 左側：散布図（改良版）
            html.Div([
                html.H3("都市形態学的特性", 
                       style={'textAlign': 'center', 'marginBottom': 20, 'color': '#34495e'}),
                dcc.Graph(
                    id='scatter-plot',
                    figure=create_improved_scatter_plot(df),
                    style={'height': '600px', 'width': '100%'}
                )
            ], style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '0 15px'}),
            
            # 右側：画像と詳細情報（改良版）
            html.Div([
                html.H3("地点詳細情報", 
                       style={'textAlign': 'center', 'marginBottom': 20, 'color': '#34495e'}),
                
                # ホバー情報表示エリア（改良版）
                html.Div(id='hover-info', 
                        style={'margin': '10px 0', 'padding': '20px', 'backgroundColor': '#ecf0f1', 
                               'borderRadius': '10px', 'border': '1px solid #bdc3c7'}),
                
                # 衛星画像表示エリア（改良版）
                html.Div(id='satellite-image', 
                        style={'margin': '10px 0', 'padding': '20px', 'backgroundColor': '#ecf0f1', 
                               'borderRadius': '10px', 'border': '1px solid #bdc3c7'}),
                
                # ネットワーク画像表示エリア（改良版）
                html.Div(id='network-image', 
                        style={'margin': '10px 0', 'padding': '20px', 'backgroundColor': '#ecf0f1', 
                               'borderRadius': '10px', 'border': '1px solid #bdc3c7'}),
                
                # 詳細情報表示エリア（改良版）
                html.Div(id='location-details', 
                        style={'margin': '10px 0', 'padding': '20px', 'backgroundColor': '#ecf0f1', 
                               'borderRadius': '10px', 'border': '1px solid #bdc3c7'})
            ], style={'width': '55%', 'display': 'inline-block', 'verticalAlign': 'top', 
                     'padding': '0 15px', 'height': '600px', 'overflowY': 'auto'})
        ], style={'display': 'flex', 'width': '100%', 'gap': '20px'})
    ])
    
    # ホバー情報を処理するコールバック（改良版）
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
                html.Div([
                    html.H4("💡 操作方法", style={'color': '#3498db'}),
                    html.P("散布図のポイントにマウスを合わせて詳細情報を表示してください。")
                ]),
                html.Div([
                    html.H4("🛰️ 衛星画像", style={'color': '#e74c3c'}),
                    html.P("地点を選択すると衛星画像が表示されます。")
                ]),
                html.Div([
                    html.H4("📍 ネットワーク構造", style={'color': '#9b59b6'}),
                    html.P("地点を選択するとネットワーク構造画像が表示されます。")
                ]),
                html.Div([
                    html.H4("📈 指標の解釈", style={'color': '#27ae60'}),
                    html.P("各指標の意味を確認できます。")
                ])
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
            
            # ホバー情報を表示（改良版）
            hover_info = html.Div([
                html.H4(f"🎯 地点 {location_id} の詳細情報", style={'color': '#2c3e50'}),
                html.P(f"📍 座標: 緯度 {location_data['latitude']:.6f}, 経度 {location_data['longitude']:.6f}"),
                html.Div([
                    html.Div([
                        html.Strong("📊 疎性 (Sparsity): "),
                        html.Span(f"{location_data['sparsity']:.3f}", style={'color': '#e74c3c'})
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Strong("🔄 レジリエンス (Resilience): "),
                        html.Span(f"{location_data['resilience']:.3f}", style={'color': '#3498db'})
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Strong("🏢 多中心性 (Multi-nodality): "),
                        html.Span(f"{location_data['multi_nodality']:.3f}", style={'color': '#9b59b6'})
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Strong("🚶 流動性 (Permeability): "),
                        html.Span(f"{location_data['permeability']:.3f}", style={'color': '#f39c12'})
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Strong("🌟 創発性 (Emergence): "),
                        html.Span(f"{location_data['emergence']:.3f}", style={'color': '#27ae60'})
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Strong("🔗 重なり (Overlap): "),
                        html.Span(f"{location_data['overlap']:.3f}", style={'color': '#95a5a6'})
                    ], style={'margin': '5px 0'})
                ])
            ])
            
            # 衛星画像を取得（改良版）
            satellite_image_component = get_improved_satellite_image_component(
                location_data['latitude'], 
                location_data['longitude']
            )
            
            # ネットワーク画像を取得（改良版）
            network_image_component = get_improved_network_image_component(location_id)
            
            # 詳細情報を表示（改良版）
            location_details = html.Div([
                html.H4("📈 指標の解釈", style={'color': '#2c3e50'}),
                html.Div([
                    html.Div([
                        html.Strong("• 疎性: "),
                        html.Span("建物密度の低さを示す指標")
                    ], style={'margin': '8px 0', 'padding': '5px', 'backgroundColor': '#fff', 'borderRadius': '5px'}),
                    html.Div([
                        html.Strong("• レジリエンス: "),
                        html.Span("ネットワークの回復力")
                    ], style={'margin': '8px 0', 'padding': '5px', 'backgroundColor': '#fff', 'borderRadius': '5px'}),
                    html.Div([
                        html.Strong("• 多中心性: "),
                        html.Span("複数の中心を持つ都市構造")
                    ], style={'margin': '8px 0', 'padding': '5px', 'backgroundColor': '#fff', 'borderRadius': '5px'}),
                    html.Div([
                        html.Strong("• 流動性: "),
                        html.Span("人の移動のしやすさ")
                    ], style={'margin': '8px 0', 'padding': '5px', 'backgroundColor': '#fff', 'borderRadius': '5px'}),
                    html.Div([
                        html.Strong("• 創発性: "),
                        html.Span("新しい機能が生まれる可能性")
                    ], style={'margin': '8px 0', 'padding': '5px', 'backgroundColor': '#fff', 'borderRadius': '5px'}),
                    html.Div([
                        html.Strong("• 重なり: "),
                        html.Span("機能の重複度")
                    ], style={'margin': '8px 0', 'padding': '5px', 'backgroundColor': '#fff', 'borderRadius': '5px'})
                ])
            ])
            
            return hover_info, satellite_image_component, network_image_component, location_details
            
        except Exception as e:
            error_msg = html.Div([
                html.H4("❌ エラー", style={'color': '#e74c3c'}),
                html.P(f"エラーが発生しました: {str(e)}")
            ])
            return error_msg, error_msg, error_msg, error_msg
    
    return app

def create_improved_scatter_plot(df):
    """改良された散布図を作成"""
    fig = go.Figure()
    
    # 散布図のデータポイントを追加（改良版）
    fig.add_trace(go.Scatter(
        x=df['sparsity'],
        y=df['resilience'],
        mode='markers',
        marker=dict(
            size=df['permeability'] * 25 + 10,  # サイズを調整
            color=df['multi_nodality'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title="多中心性",
                tickfont=dict(size=12)
            ),
            opacity=0.8,
            line=dict(width=1, color='white')
        ),
        customdata=df['location_id'].tolist(),
        hovertemplate='<b>地点 %{customdata}</b><br>' +
                     '📍 座標: %{x:.3f}, %{y:.3f}<br>' +
                     '📊 Sparsity: %{x:.3f}<br>' +
                     '🔄 Resilience: %{y:.3f}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='都市形態学的特性',
            font=dict(size=18, color='#2c3e50')
        ),
        xaxis=dict(
            title='疎性 (Sparsity)',
            tickfont=dict(size=12),
            gridcolor='#ecf0f1'
        ),
        yaxis=dict(
            title='レジリエンス (Resilience)',
            tickfont=dict(size=12),
            gridcolor='#ecf0f1'
        ),
        hovermode='closest',
        height=550,
        width=550,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

def get_improved_satellite_image_component(lat, lon):
    """改良された衛星画像のHTMLコンポーネントを取得"""
    try:
        # キャッシュシステムを使用して衛星画像を取得
        img_base64 = satellite_cache.get_satellite_image_base64(lat, lon, zoom=15, size=(500, 500))
        
        if img_base64:
            return html.Div([
                html.H4(f"🛰️ 衛星画像 (OpenStreetMap)", style={'color': '#e74c3c'}),
                html.P(f"座標: 緯度 {lat:.6f}, 経度 {lon:.6f}", style={'color': '#7f8c8d'}),
                html.Img(src=f"data:image/png;base64,{img_base64}", 
                        style={'maxWidth': '100%', 'height': '400px', 'objectFit': 'contain', 
                               'border': '3px solid #e74c3c', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
            ])
        else:
            return html.Div([
                html.H4(f"🛰️ 衛星画像", style={'color': '#e74c3c'}),
                html.P("衛星画像の取得に失敗しました。", style={'color': '#e74c3c'}),
                html.P("しばらく待ってから再試行してください。", style={'color': '#95a5a6'})
            ])
    except Exception as e:
        return html.Div([
            html.H4(f"🛰️ 衛星画像", style={'color': '#e74c3c'}),
            html.P(f"エラー: {str(e)}", style={'color': '#e74c3c'})
        ])

def get_improved_network_image_component(location_id):
    """改良されたネットワーク画像のHTMLコンポーネントを取得"""
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
            html.H4(f"📍 地点 {location_id} のネットワーク構造", style={'color': '#9b59b6'}),
            html.P(f"修正されたネットワーク画像: {corrected_image_path.name}", style={'color': '#7f8c8d'}),
            html.Img(src=f"data:image/png;base64,{img_base64}", 
                    style={'maxWidth': '100%', 'height': '400px', 'objectFit': 'contain', 
                           'border': '3px solid #9b59b6', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
        ])
    elif real_image_path.exists():
        # 画像をbase64エンコード
        with open(real_image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        return html.Div([
            html.H4(f"📍 地点 {location_id} のネットワーク構造", style={'color': '#9b59b6'}),
            html.P(f"実際のネットワーク画像: {real_image_path.name}", style={'color': '#7f8c8d'}),
            html.Img(src=f"data:image/png;base64,{img_base64}", 
                    style={'maxWidth': '100%', 'height': '400px', 'objectFit': 'contain', 
                           'border': '3px solid #9b59b6', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
        ])
    elif network_image_path.exists():
        # 画像をbase64エンコード
        with open(network_image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        return html.Div([
            html.H4(f"📍 地点 {location_id} のネットワーク構造", style={'color': '#9b59b6'}),
            html.P(f"ネットワーク画像: {network_image_path.name}", style={'color': '#7f8c8d'}),
            html.Img(src=f"data:image/png;base64,{img_base64}", 
                    style={'maxWidth': '100%', 'height': '400px', 'objectFit': 'contain', 
                           'border': '3px solid #9b59b6', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
        ])
    else:
        return html.Div([
            html.H4(f"📍 地点 {location_id} のネットワーク構造", style={'color': '#9b59b6'}),
            html.P("画像が見つかりません。", style={'color': '#e74c3c'})
        ])

if __name__ == "__main__":
    app = create_dash_app()
    app.run(debug=True, host='0.0.0.0', port=8053)
