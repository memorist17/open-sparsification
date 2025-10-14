#!/usr/bin/env python3
"""
Dashboardアプリケーションの実行スクリプト
"""

import sys
import subprocess
import webbrowser
from pathlib import Path

def run_html_dashboard():
    """HTMLダッシュボードを生成して開く"""
    print("🚀 HTMLダッシュボードを生成中...")
    
    try:
        result = subprocess.run([sys.executable, "src/app/html_dashboard.py"], 
                              capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode == 0:
            # ブラウザで開く
            dashboard_path = Path("dashboard.html").absolute()
            print(f"🌐 ブラウザでダッシュボードを開いています...")
            webbrowser.open(f"file://{dashboard_path}")
        else:
            print("❌ ダッシュボード生成に失敗しました")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def run_dash_app():
    """Dashアプリケーションを実行"""
    print("🚀 Dashアプリケーションを起動中...")
    print("📍 URL: http://localhost:8051")
    print("💡 ホバー機能: 散布図のポイントにマウスを合わせると詳細情報が表示されます")
    
    try:
        subprocess.run([sys.executable, "src/app/dash_app.py"])
    except KeyboardInterrupt:
        print("\n🛑 Dashアプリケーションを停止しました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print("💡 dash パッケージがインストールされていない可能性があります")
        print("   以下のコマンドでインストールしてください:")
        print("   pip install dash plotly")

def main():
    """メイン関数"""
    print("🏙️ OpenSparsity Dashboard")
    print("=" * 50)
    print("1. HTMLダッシュボード（推奨）- 依存パッケージ不要")
    print("2. Dashインタラクティブアプリ - dash/plotlyが必要")
    print("3. 終了")
    
    while True:
        choice = input("\n選択してください (1-3): ").strip()
        
        if choice == "1":
            run_html_dashboard()
            break
        elif choice == "2":
            run_dash_app()
            break
        elif choice == "3":
            print("👋 終了します")
            break
        else:
            print("❌ 無効な選択です。1-3を選択してください。")

if __name__ == "__main__":
    main()


