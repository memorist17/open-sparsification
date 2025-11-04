#!/bin/bash
# OpenSparsity - 仮想環境セットアップスクリプト

echo "=================================================="
echo "🔧 OpenSparsity 仮想環境セットアップ"
echo "=================================================="
echo ""

# Pythonの確認
if command -v python3 &> /dev/null; then
    PYTHON=python3
else
    echo "❌ Python3が見つかりません"
    exit 1
fi

echo "✓ Python: $($PYTHON --version)"
echo ""

# 仮想環境の作成
if [ -d "venv" ]; then
    echo "⚠️  仮想環境 'venv' が既に存在します"
    read -p "削除して再作成しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  既存の仮想環境を削除中..."
        rm -rf venv
    else
        echo "既存の仮想環境を使用します"
        source venv/bin/activate
        echo "✓ 仮想環境をアクティベート"
        echo ""
        echo "=================================================="
        echo "✅ セットアップ完了"
        echo "=================================================="
        echo ""
        echo "次のコマンドで使用できます:"
        echo "  source venv/bin/activate"
        echo "  python main.py demo"
        echo "  python dashboard.py"
        echo ""
        exit 0
    fi
fi

echo "📦 仮想環境を作成中..."
$PYTHON -m venv venv

if [ ! -d "venv" ]; then
    echo "❌ 仮想環境の作成に失敗しました"
    exit 1
fi

echo "✓ 仮想環境作成完了"
echo ""

# 仮想環境のアクティベート
echo "🔄 仮想環境をアクティベート中..."
source venv/bin/activate

echo "✓ 仮想環境アクティベート完了"
echo ""

# pipのアップグレード
echo "📦 pipをアップグレード中..."
pip install --upgrade pip --quiet

echo "✓ pip アップグレード完了"
echo ""

# 依存関係のインストール
echo "📚 依存関係をインストール中..."
echo "   (これには数分かかる場合があります)"
echo ""

pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 一部のパッケージのインストールに失敗しました"
    echo "個別にインストールを試みます..."
    echo ""
    
    # 必須パッケージを個別にインストール
    pip install numpy scipy pandas
    pip install geopandas shapely pyproj rasterio fiona
    pip install networkx
    pip install matplotlib seaborn plotly
    pip install tqdm
    pip install dash
fi

echo ""
echo "=================================================="
echo "✅ セットアップ完了！"
echo "=================================================="
echo ""
echo "仮想環境が作成され、すべての依存関係がインストールされました。"
echo ""
echo "📝 使用方法:"
echo ""
echo "1. 仮想環境をアクティベート:"
echo "   source venv/bin/activate"
echo ""
echo "2. デモを実行:"
echo "   python main.py demo"
echo ""
echo "3. ダッシュボードを起動:"
echo "   python dashboard.py"
echo ""
echo "4. 仮想環境を終了:"
echo "   deactivate"
echo ""
echo "=================================================="

