#!/bin/bash
# OpenSparsity - ダッシュボード起動スクリプト（仮想環境対応）

echo "=================================================="
echo "🚀 OpenSparsity Dashboard 起動"
echo "=================================================="
echo ""

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "⚠️  仮想環境が見つかりません"
    echo "セットアップスクリプトを実行します..."
    echo ""
    ./setup_venv.sh
    if [ $? -ne 0 ]; then
        echo "❌ セットアップに失敗しました"
        exit 1
    fi
fi

# 仮想環境をアクティベート
echo "🔄 仮想環境をアクティベート中..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ 仮想環境のアクティベートに失敗しました"
    exit 1
fi

echo "✓ 仮想環境アクティベート完了"
echo ""

# デモデータの確認と生成
if [ ! -d "demo_output" ] || [ -z "$(ls -A demo_output 2>/dev/null)" ]; then
    echo "📊 デモデータを生成中..."
    echo "=================================================="
    python quick_start_dashboard.py
else
    echo "✓ デモデータ確認済み"
    echo ""
    echo "=================================================="
    echo "🌐 ダッシュボードを起動中..."
    echo "=================================================="
    echo ""
    echo "ブラウザで以下を開いてください:"
    echo "  http://127.0.0.1:8050"
    echo ""
    echo "停止: Ctrl+C"
    echo "=================================================="
    echo ""
    
    python dashboard.py --data demo_output
fi

# 終了時に仮想環境を無効化
deactivate 2>/dev/null

