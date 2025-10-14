#!/usr/bin/env python3
"""
代替アプリケーションの実行スクリプト
"""

import sys
import subprocess
from pathlib import Path

def run_dash_app():
    """Dashアプリケーションを実行"""
    print("🚀 Dashアプリケーションを起動中...")
    print("📍 URL: http://localhost:8050")
    print("💡 ホバー機能: 散布図のポイントにマウスを合わせると詳細情報が表示されます")
    
    try:
        subprocess.run([sys.executable, "src/app/dash_app.py"])
    except KeyboardInterrupt:
        print("\n🛑 Dashアプリケーションを停止しました")

def run_gradio_app():
    """Gradioアプリケーションを実行"""
    print("🚀 Gradioアプリケーションを起動中...")
    print("📍 URL: http://localhost:7860")
    print("💡 ホバー機能: 散布図のポイントにマウスを合わせると詳細情報が表示されます")
    
    try:
        subprocess.run([sys.executable, "src/app/gradio_app.py"])
    except KeyboardInterrupt:
        print("\n🛑 Gradioアプリケーションを停止しました")

def run_flask_app():
    """Flaskアプリケーションを実行"""
    print("🚀 Flaskアプリケーションを起動中...")
    print("📍 URL: http://localhost:5000")
    print("💡 ホバー機能: 散布図のポイントにマウスを合わせると詳細情報が表示されます")
    
    try:
        subprocess.run([sys.executable, "src/app/flask_app.py"])
    except KeyboardInterrupt:
        print("\n🛑 Flaskアプリケーションを停止しました")

def main():
    """メイン関数"""
    print("🏙️ OpenSparsity - 代替アプリケーション選択")
    print("=" * 50)
    print("1. Dash (推奨) - ホバー機能完備")
    print("2. Gradio - 簡単な実装")
    print("3. Flask - 完全制御")
    print("4. 終了")
    
    while True:
        choice = input("\n選択してください (1-4): ").strip()
        
        if choice == "1":
            run_dash_app()
            break
        elif choice == "2":
            run_gradio_app()
            break
        elif choice == "3":
            run_flask_app()
            break
        elif choice == "4":
            print("👋 終了します")
            break
        else:
            print("❌ 無効な選択です。1-4を選択してください。")

if __name__ == "__main__":
    main()
