#!/usr/bin/env python3
"""
横一列レイアウトのDashアプリケーション - 一覧性を最大化
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
    
    # 横一列レイアウト（一覧性最大化）
    app.layout = html.Div([
        html.H1("🏙️ OpenSparsity - 横一列可視化（一覧性最大化）", 
                style={'textAlign': 'center', 'marginBottom': 20, 'color': '#2c3e50', 'fontSize': '24px'}),
        
        # 横一列レイアウト
        html.Div([
            # 左側：散布図（コンパクト）
            html.Div([
                html.H3("散布図", style={'textAlign': 'center', 'marginBottom': 10, 'color': '#34495e', 'fontSize': '16px'}),
                dcc.Graph(
                    id='scatter-plot',
                    figure=create_compact_scatter_plot(df),
                    style={'height': '400px', 'width': '100%'}
                )
            ], style={'width': '25%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '0 10px'}),
            
            # 中央左：詳細情報（コンパクト）
            html.Div([
                html.H3("詳細情報", style={'textAlign': 'center', 'marginBottom': 10, 'color': '#34495e', 'fontSize': '16px'}),
                html.Div(id='hover-info', 
                        style={'margin': '5px 0', 'padding': '10px', 'backgroundColor': '#ecf0f1', 
                               'borderRadius': '5px', 'fontSize': '12px', 'height': '350px', 'overflowY': 'auto'})
            ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '0 10px'}),
            
            # 中央：衛星画像（コンパクト）
            html.Div([
                html.H3("衛星画像", style={'textAlign': 'center', 'marginBottom': 10, 'color': '#34495e', 'fontSize': '16px'}),
                html.Div(id='satellite-image', 
                        style={'margin': '5px 0', 'padding': '10px', 'backgroundColor': '#ecf0f1', 
                               'borderRadius': '5px', 'height': '350px', 'overflowY': 'auto'})
            ], style={'width': '25%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '0 10px'}),
            
            # 右側：ネットワーク画像（コンパクト）
            html.Div([
                html.H3("ネットワーク", style={'textAlign': 'center', 'marginBottom': 10, 'color': '#34495e', 'fontSize': '16px'}),
                html.Div(id='network-image', 
                        style={'margin': '5px 0', 'padding': '10px', 'backgroundColor': '#ecf0f1', 
                               'borderRadius': '5px', 'height': '350px', 'overflowY': 'auto'})
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '0 10px'})
        ], style={'display': 'flex', 'width': '100%', 'gap': '5px', 'marginBottom': '20px'}),
        
        # 下部：指標解釈（横一列）
        html.Div([
            html.H3("指標解釈", style={'textAlign': 'center', 'marginBottom': 10, 'color': '#34495e', 'fontSize': '16px'}),
            html.Div(id='location-details', 
                    style={'margin': '5px 0', 'padding': '15px', 'backgroundColor': '#ecf0f1', 
                           'borderRadius': '5px', 'fontSize': '12px'})
        ], style={'width': '100%'})
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
                html.Div([
                    html.P("💡 散布図のポイントにマウスを合わせてください", style={'textAlign': 'center', 'color': '#7f8c8d'})
                ]),
                html.Div([
                    html.P("🛰️ 衛星画像が表示されます", style={'textAlign': 'center', 'color': '#7f8c8d'})
                ]),
                html.Div([
                    html.P("📍 ネットワーク構造が表示されます", style={'textAlign': 'center', 'color': '#7f8c8d'})
                ]),
                html.Div([
                    html.P("📈 指標の解釈が表示されます", style={'textAlign': 'center', 'color': '#7f8c8d'})
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
            
            # ホバー情報を表示（コンパクト版）
            hover_info = html.Div([
                html.H4(f"地点 {location_id}", style={'color': '#2c3e50', 'fontSize': '14px', 'marginBottom': '10px'}),
                html.Div([
                    html.Div([
                        html.Strong("📍 座標:", style={'fontSize': '11px'}),
                        html.Br(),
                        html.Span(f"緯度: {location_data['latitude']:.4f}", style={'fontSize': '10px', 'color': '#7f8c8d'}),
                        html.Br(),
                        html.Span(f"経度: {location_data['longitude']:.4f}", style={'fontSize': '10px', 'color': '#7f8c8d'})
                    ], style={'margin': '5px 0', 'padding': '5px', 'backgroundColor': '#fff', 'borderRadius': '3px'}),
                    
                    html.Div([
                        html.Strong("📊 疎性:", style={'fontSize': '11px', 'color': '#e74c3c'}),
                        html.Span(f" {location_data['sparsity']:.3f}", style={'fontSize': '11px'})
                    ], style={'margin': '3px 0'}),
                    
                    html.Div([
                        html.Strong("🔄 レジリエンス:", style={'fontSize': '11px', 'color': '#3498db'}),
                        html.Span(f" {location_data['resilience']:.3f}", style={'fontSize': '11px'})
                    ], style={'margin': '3px 0'}),
                    
                    html.Div([
                        html.Strong("🏢 多中心性:", style={'fontSize': '11px', 'color': '#9b59b6'}),
                        html.Span(f" {location_data['multi_nodality']:.3f}", style={'fontSize': '11px'})
                    ], style={'margin': '3px 0'}),
                    
                    html.Div([
                        html.Strong("🚶 流動性:", style={'fontSize': '11px', 'color': '#f39c12'}),
                        html.Span(f" {location_data['permeability']:.3f}", style={'fontSize': '11px'})
                    ], style={'margin': '3px 0'}),
                    
                    html.Div([
                        html.Strong("🌟 創発性:", style={'fontSize': '11px', 'color': '#27ae60'}),
                        html.Span(f" {location_data['emergence']:.3f}", style={'fontSize': '11px'})
                    ], style={'margin': '3px 0'}),
                    
                    html.Div([
                        html.Strong("🔗 重なり:", style={'fontSize': '11px', 'color': '#95a5a6'}),
                        html.Span(f" {location_data['overlap']:.3f}", style={'fontSize': '11px'})
                    ], style={'margin': '3px 0'})
                ])
            ])
            
            # 衛星画像を取得（コンパクト版）
            satellite_image_component = get_compact_satellite_image_component(
                location_data['latitude'], 
                location_data['longitude']
            )
            
            # ネットワーク画像を取得（コンパクト版）
            network_image_component = get_compact_network_image_component(location_id)
            
            # 詳細情報を表示（コンパクト版）
            location_details = html.Div([
                html.Div([
                    html.Div([
                        html.Strong("疎性: ", style={'color': '#e74c3c'}),
                        html.Span("建物密度の低さを示す指標", style={'fontSize': '11px'})
                    ], style={'display': 'inline-block', 'margin': '5px 10px 5px 0', 'padding': '3px 8px', 'backgroundColor': '#fff', 'borderRadius': '3px', 'border': '1px solid #e74c3c'}),
                    
                    html.Div([
                        html.Strong("レジリエンス: ", style={'color': '#3498db'}),
                        html.Span("ネットワークの回復力", style={'fontSize': '11px'})
                    ], style={'display': 'inline-block', 'margin': '5px 10px 5px 0', 'padding': '3px 8px', 'backgroundColor': '#fff', 'borderRadius': '3px', 'border': '1px solid #3498db'}),
                    
                    html.Div([
                        html.Strong("多中心性: ", style={'color': '#9b59b6'}),
                        html.Span("複数の中心を持つ都市構造", style={'fontSize': '11px'})
                    ], style={'display': 'inline-block', 'margin': '5px 10px 5px 0', 'padding': '3px 8px', 'backgroundColor': '#fff', 'borderRadius': '3px', 'border': '1px solid #9b59b6'}),
                    
                    html.Div([
                        html.Strong("流動性: ", style={'color': '#f39c12'}),
                        html.Span("人の移動のしやすさ", style={'fontSize': '11px'})
                    ], style={'display': 'inline-block', 'margin': '5px 10px 5px 0', 'padding': '3px 8px', 'backgroundColor': '#fff', 'borderRadius': '3px', 'border': '1px solid #f39c12'}),
                    
                    html.Div([
                        html.Strong("創発性: ", style={'color': '#27ae60'}),
                        html.Span("新しい機能が生まれる可能性", style={'fontSize': '11px'})
                    ], style={'display': 'inline-block', 'margin': '5px 10px 5px 0', 'padding': '3px 8px', 'backgroundColor': '#fff', 'borderRadius': '3px', 'border': '1px solid #27ae60'}),
                    
                    html.Div([
                        html.Strong("重なり: ", style={'color': '#95a5a6'}),
                        html.Span("機能の重複度", style={'fontSize': '11px'})
                    ], style={'display': 'inline-block', 'margin': '5px 10px 5px 0', 'padding': '3px 8px', 'backgroundColor': '#fff', 'borderRadius': '3px', 'border': '1px solid #95a5a6'})
                ])
            ])
            
            return hover_info, satellite_image_component, network_image_component, location_details
            
        except Exception as e:
            error_msg = html.Div([
                html.P(f"❌ エラー: {str(e)}", style={'color': '#e74c3c', 'fontSize': '11px'})
            ])
            return error_msg, error_msg, error_msg, error_msg
    
    return app

def create_compact_scatter_plot(df):
    """コンパクトな散布図を作成"""
    fig = go.Figure()
    
    # 散布図のデータポイントを追加（コンパクト版）
    fig.add_trace(go.Scatter(
        x=df['sparsity'],
        y=df['resilience'],
        mode='markers',
        marker=dict(
            size=df['permeability'] * 15 + 8,  # サイズを小さく
            color=df['multi_nodality'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title="多中心性",
                tickfont=dict(size=10)
            ),
            opacity=0.8,
            line=dict(width=0.5, color='white')
        ),
        customdata=df['location_id'].tolist(),
        hovertemplate='<b>地点 %{customdata}</b><br>' +
                     '疎性: %{x:.3f}<br>' +
                     'レジリエンス: %{y:.3f}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='都市形態学的特性',
            font=dict(size=14, color='#2c3e50')
        ),
        xaxis=dict(
            title='疎性',
            tickfont=dict(size=10),
            gridcolor='#ecf0f1'
        ),
        yaxis=dict(
            title='レジリエンス',
            tickfont=dict(size=10),
            gridcolor='#ecf0f1'
        ),
        hovermode='closest',
        height=350,
        width=350,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

def get_compact_satellite_image_component(lat, lon):
    """コンパクトな衛星画像のHTMLコンポーネントを取得"""
    try:
        # キャッシュシステムを使用して衛星画像を取得
        img_base64 = satellite_cache.get_satellite_image_base64(lat, lon, zoom=15, size=(300, 300))
        
        if img_base64:
            return html.Div([
                html.P(f"座標: {lat:.4f}, {lon:.4f}", style={'fontSize': '10px', 'color': '#7f8c8d', 'marginBottom': '5px'}),
                html.Img(src=f"data:image/png;base64,{img_base64}", 
                        style={'maxWidth': '100%', 'height': '250px', 'objectFit': 'contain', 
                               'border': '2px solid #e74c3c', 'borderRadius': '5px'})
            ])
        else:
            return html.Div([
                html.P("衛星画像の取得に失敗しました", style={'color': '#e74c3c', 'fontSize': '11px', 'textAlign': 'center'})
            ])
    except Exception as e:
        return html.Div([
            html.P(f"エラー: {str(e)}", style={'color': '#e74c3c', 'fontSize': '11px'})
        ])

def get_compact_network_image_component(location_id):
    """コンパクトなネットワーク画像のHTMLコンポーネントを取得"""
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
            html.P(f"修正版: {corrected_image_path.name}", style={'fontSize': '10px', 'color': '#7f8c8d', 'marginBottom': '5px'}),
            html.Img(src=f"data:image/png;base64,{img_base64}", 
                    style={'maxWidth': '100%', 'height': '250px', 'objectFit': 'contain', 
                           'border': '2px solid #9b59b6', 'borderRadius': '5px'})
        ])
    elif real_image_path.exists():
        # 画像をbase64エンコード
        with open(real_image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        return html.Div([
            html.P(f"実際版: {real_image_path.name}", style={'fontSize': '10px', 'color': '#7f8c8d', 'marginBottom': '5px'}),
            html.Img(src=f"data:image/png;base64,{img_base64}", 
                    style={'maxWidth': '100%', 'height': '250px', 'objectFit': 'contain', 
                           'border': '2px solid #9b59b6', 'borderRadius': '5px'})
        ])
    elif network_image_path.exists():
        # 画像をbase64エンコード
        with open(network_image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        return html.Div([
            html.P(f"標準版: {network_image_path.name}", style={'fontSize': '10px', 'color': '#7f8c8d', 'marginBottom': '5px'}),
            html.Img(src=f"data:image/png;base64,{img_base64}", 
                    style={'maxWidth': '100%', 'height': '250px', 'objectFit': 'contain', 
                           'border': '2px solid #9b59b6', 'borderRadius': '5px'})
        ])
    else:
        return html.Div([
            html.P("画像が見つかりません", style={'color': '#e74c3c', 'fontSize': '11px', 'textAlign': 'center'})
        ])

if __name__ == "__main__":
    app = create_dash_app()
    app.run(debug=True, host='0.0.0.0', port=8054)
