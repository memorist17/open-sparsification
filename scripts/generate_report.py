#!/usr/bin/env python3
"""
OpenSparsity レポート生成スクリプト

分析結果からレポートを生成します。
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.config import load_config
from src.utils.logger import setup_logger


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="OpenSparsity レポート生成")
    parser.add_argument("--input", type=str, required=True, 
                       help="分析結果CSVファイルのパス")
    parser.add_argument("--output", type=str, default="results/report.html",
                       help="出力レポートファイルのパス")
    parser.add_argument("--verbose", action="store_true", help="詳細ログ出力")
    
    args = parser.parse_args()
    
    # ログ設定
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logger(log_level=log_level)
    
    logger.info("OpenSparsity レポート生成開始")
    
    try:
        # 分析結果読み込み
        df = pd.read_csv(args.input)
        logger.info(f"分析結果読み込み完了: {len(df)}地点")
        
        # 出力ディレクトリ作成
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # HTMLレポート生成
        html_content = generate_html_report(df)
        
        # レポート保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"レポート生成完了: {output_path}")
        
    except Exception as e:
        logger.error(f"レポート生成エラー: {e}")
        sys.exit(1)


def generate_html_report(df: pd.DataFrame) -> str:
    """HTMLレポートを生成"""
    
    # 指標列を取得
    metric_columns = [col for col in df.columns 
                     if col not in ['location_id', 'latitude', 'longitude']]
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenSparsity 分析レポート</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #1f77b4; }}
            h2 {{ color: #2ca02c; }}
            .metric-card {{ 
                background-color: #f0f2f6; 
                padding: 20px; 
                margin: 10px 0; 
                border-radius: 5px;
                border-left: 4px solid #1f77b4;
            }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>🏙️ OpenSparsity 分析レポート</h1>
        
        <h2>📊 分析概要</h2>
        <div class="metric-card">
            <p><strong>分析対象地点数:</strong> {len(df)}</p>
            <p><strong>分析日時:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <h2>📈 指標統計</h2>
        <table>
            <tr>
                <th>指標</th>
                <th>平均</th>
                <th>標準偏差</th>
                <th>最小値</th>
                <th>最大値</th>
            </tr>
    """
    
    # 各指標の統計を追加
    for metric in metric_columns:
        stats = df[metric].describe()
        html += f"""
            <tr>
                <td>{metric.replace('_', ' ').title()}</td>
                <td>{stats['mean']:.4f}</td>
                <td>{stats['std']:.4f}</td>
                <td>{stats['min']:.4f}</td>
                <td>{stats['max']:.4f}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h2>🔗 指標間相関</h2>
        <table>
            <tr>
                <th>指標1</th>
                <th>指標2</th>
                <th>相関係数</th>
            </tr>
    """
    
    # 相関行列を計算
    correlation_matrix = df[metric_columns].corr()
    for i, metric1 in enumerate(metric_columns):
        for j, metric2 in enumerate(metric_columns):
            if i < j:  # 重複を避ける
                corr = correlation_matrix.loc[metric1, metric2]
                html += f"""
                    <tr>
                        <td>{metric1.replace('_', ' ').title()}</td>
                        <td>{metric2.replace('_', ' ').title()}</td>
                        <td>{corr:.4f}</td>
                    </tr>
                """
    
    html += """
        </table>
        
        <h2>📍 地理的分布</h2>
        <div class="metric-card">
            <p><strong>緯度範囲:</strong> {:.4f} - {:.4f}</p>
            <p><strong>経度範囲:</strong> {:.4f} - {:.4f}</p>
        </div>
        
        <footer>
            <p><em>OpenSparsity v0.1.0 - 地理空間データによる都市構造特性分析基盤</em></p>
        </footer>
    </body>
    </html>
    """.format(
        df['latitude'].min(),
        df['latitude'].max(),
        df['longitude'].min(),
        df['longitude'].max()
    )
    
    return html


if __name__ == "__main__":
    main()
