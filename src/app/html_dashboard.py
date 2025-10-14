#!/usr/bin/env python3
"""
シンプルなHTML Dashboardを生成
"""

import base64
from pathlib import Path
import pandas as pd
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

def generate_html_dashboard():
    """HTMLダッシュボードを生成"""
    
    # データを読み込み
    data_path = project_root / "data" / "processed" / "real_analysis_results.csv"
    if not data_path.exists():
        print("❌ データファイルが見つかりません")
        return
    
    df = pd.read_csv(data_path)
    
    # ペアプロット画像をbase64エンコード
    pairplot_path = project_root / "figures" / "comprehensive_urban_metrics_pairplot.png"
    if pairplot_path.exists():
        with open(pairplot_path, "rb") as img_file:
            pairplot_base64 = base64.b64encode(img_file.read()).decode()
    else:
        print("❌ ペアプロット画像が見つかりません")
        return
    
    # データテーブルのHTML生成
    table_rows = ""
    for idx, row in df.iterrows():
        table_rows += f"""
        <tr>
            <td>{int(row['location_id'])}</td>
            <td>{row.get('name', 'N/A')}</td>
            <td>{row['latitude']:.6f}</td>
            <td>{row['longitude']:.6f}</td>
            <td>{row['sparsity']:.3f}</td>
            <td>{row['resilience']:.3f}</td>
            <td>{row['multi_nodality']:.3f}</td>
            <td>{row['permeability']:.3f}</td>
            <td>{row['emergence']:.3f}</td>
            <td>{row['overlap']:.3f}</td>
        </tr>
        """
    
    # HTML生成
    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenSparsity Dashboard - 都市形態学的特性分析</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8rem;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .pairplot-container {{
            text-align: center;
            margin: 20px 0;
        }}
        
        .pairplot-container img {{
            max-width: 100%;
            height: auto;
            border: 2px solid #ddd;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9rem;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .data-table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .data-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        .data-table tr:hover {{
            background: #f5f5f5;
        }}
        
        .data-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .metric-description {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }}
        
        .metric-description h3 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .metric-description ul {{
            list-style: none;
            padding: 0;
        }}
        
        .metric-description li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .metric-description li:last-child {{
            border-bottom: none;
        }}
        
        footer {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9rem;
        }}
        
        .table-container {{
            overflow-x: auto;
            border-radius: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏙️ OpenSparsity Dashboard</h1>
            <p class="subtitle">都市形態学的特性の包括的分析</p>
        </header>
        
        <div class="content">
            <!-- 統計サマリー -->
            <div class="section">
                <h2>📊 データサマリー</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">分析地点数</div>
                        <div class="stat-value">{len(df)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">平均疎性</div>
                        <div class="stat-value">{df['sparsity'].mean():.3f}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">平均レジリエンス</div>
                        <div class="stat-value">{df['resilience'].mean():.3f}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">平均多中心性</div>
                        <div class="stat-value">{df['multi_nodality'].mean():.3f}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">平均流動性</div>
                        <div class="stat-value">{df['permeability'].mean():.3f}</div>
                    </div>
                </div>
            </div>
            
            <!-- ペアプロット -->
            <div class="section">
                <h2>📈 包括的メトリクス ペアプロット</h2>
                <div class="pairplot-container">
                    <img src="data:image/png;base64,{pairplot_base64}" alt="Comprehensive Urban Metrics Pair Plot">
                </div>
                
                <div class="metric-description">
                    <h3>指標の説明</h3>
                    <ul>
                        <li><strong>Sparsity (疎性)</strong>: 建物密度の低さを示す指標。値が高いほど建物が疎らに配置されている</li>
                        <li><strong>Resilience (レジリエンス)</strong>: ネットワークの回復力と適応性を示す指標</li>
                        <li><strong>Multi-nodality (多中心性)</strong>: 複数の中心を持つ都市構造の度合い</li>
                        <li><strong>Permeability (流動性)</strong>: 人の移動のしやすさを示す指標</li>
                        <li><strong>Emergence (創発性)</strong>: 新しい機能が生まれる可能性を示す指標</li>
                        <li><strong>Overlap (重なり)</strong>: 機能の重複度を示す指標</li>
                    </ul>
                </div>
            </div>
            
            <!-- データテーブル -->
            <div class="section">
                <h2>📋 詳細データ</h2>
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>地点ID</th>
                                <th>地点名</th>
                                <th>緯度</th>
                                <th>経度</th>
                                <th>疎性</th>
                                <th>レジリエンス</th>
                                <th>多中心性</th>
                                <th>流動性</th>
                                <th>創発性</th>
                                <th>重なり</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <footer>
            <p>© 2024 OpenSparsity Project - 都市形態学的特性分析基盤</p>
            <p>データポイント数: {len(df)} | 生成日時: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # HTMLファイルを保存
    output_path = project_root / "dashboard.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ HTMLダッシュボードを生成しました: {output_path}")
    print(f"🌐 ブラウザで開いてください: file://{output_path.absolute()}")
    
    return output_path

if __name__ == "__main__":
    generate_html_dashboard()


