import streamlit as st
import streamlit.components.v1 as components

def hover_detector_component():
    """ホバー情報を検出するカスタムコンポーネント"""
    
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <div id="plotly-div"></div>
        <div id="hover-info"></div>
        
        <script>
        // ホバー情報を検出する関数
        function detectHover() {
            const plotlyDiv = document.getElementById('plotly-div');
            if (plotlyDiv && plotlyDiv.data) {
                plotlyDiv.on('plotly_hover', function(data) {
                    const point = data.points[0];
                    const locationId = point.customdata[0]; // 地点ID
                    
                    // ホバー情報を表示
                    document.getElementById('hover-info').innerHTML = 
                        '<p>ホバーされた地点ID: ' + locationId + '</p>';
                    
                    // Streamlitに情報を送信
                    window.parent.postMessage({
                        type: 'hover',
                        locationId: locationId
                    }, '*');
                });
            }
        }
        
        // ページ読み込み時に実行
        window.addEventListener('load', detectHover);
        </script>
    </body>
    </html>
    """
    
    return components.html(html_code, height=200)

def create_interactive_plot(df):
    """インタラクティブな散布図を作成"""
    import plotly.graph_objects as go
    
    # 散布図を作成
    fig = go.Figure()
    
    # データポイントを追加
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
        customdata=df['location_id'],
        hovertemplate='<b>地点 %{customdata}</b><br>' +
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
        hovermode='closest'
    )
    
    return fig
