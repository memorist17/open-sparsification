#!/usr/bin/env python3
"""
Gradioアプリケーション - ホバー機能付きインタラクティブ可視化
"""

import gradio as gr
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

def create_gradio_app():
    """Gradioアプリケーションを作成"""
    
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
    
    def get_location_info(location_id):
        """地点の詳細情報を取得"""
        if location_id not in df['location_id'].values:
            return "地点が見つかりません。"
        
        location_data = df[df['location_id'] == location_id].iloc[0]
        
        info = f"""
        🎯 地点 {location_id} の詳細情報
        
        📍 座標: 緯度 {location_data['latitude']:.6f}, 経度 {location_data['longitude']:.6f}
        📊 疎性 (Sparsity): {location_data['sparsity']:.3f}
        🔄 レジリエンス (Resilience): {location_data['resilience']:.3f}
        🏢 多中心性 (Multi-nodality): {location_data['multi_nodality']:.3f}
        🚶 流動性 (Permeability): {location_data['permeability']:.3f}
        🌟 創発性 (Emergence): {location_data['emergence']:.3f}
        🔗 重なり (Overlap): {location_data['overlap']:.3f}
        """
        
        return info
    
    def get_network_image(location_id):
        """ネットワーク画像のパスを取得"""
        # 画像ファイルのパスを確認
        corrected_image_path = project_root / "data" / "corrected_network_images" / f"corrected_network_{location_id:03d}.png"
        real_image_path = project_root / "data" / "real_network_images" / f"real_network_{location_id:03d}.png"
        network_image_path = project_root / "data" / "network_images" / f"network_{location_id:03d}.png"
        
        if corrected_image_path.exists():
            return str(corrected_image_path)
        elif real_image_path.exists():
            return str(real_image_path)
        elif network_image_path.exists():
            return str(network_image_path)
        else:
            return None
    
    # Gradioインターフェースを作成
    with gr.Blocks(title="OpenSparsity - インタラクティブ可視化") as demo:
        gr.Markdown("# 🏙️ OpenSparsity - インタラクティブ可視化")
        
        with gr.Row():
            with gr.Column(scale=2):
                # 散布図
                plot = gr.Plot(create_scatter_plot(), label="散布図")
                
                # 地点選択
                location_input = gr.Number(
                    label="地点IDを入力してください",
                    value=0,
                    minimum=0,
                    maximum=len(df)-1,
                    step=1
                )
                
            with gr.Column(scale=1):
                # 詳細情報表示
                location_info = gr.Textbox(
                    label="地点詳細情報",
                    value="地点IDを入力してください",
                    lines=10
                )
                
                # ネットワーク画像表示
                network_image = gr.Image(
                    label="ネットワーク画像",
                    type="filepath"
                )
        
        # イベントハンドラー
        location_input.change(
            fn=get_location_info,
            inputs=[location_input],
            outputs=[location_info]
        )
        
        location_input.change(
            fn=get_network_image,
            inputs=[location_input],
            outputs=[network_image]
        )
    
    return demo

if __name__ == "__main__":
    demo = create_gradio_app()
    demo.launch(server_name="0.0.0.0", server_port=7860)
