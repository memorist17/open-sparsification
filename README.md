# OpenSparsity: 地理空間データによる都市構造特性分析基盤

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

## プロジェクト概要

地理空間データを用いて都市の構造特性（多中心性、疎性、レジリエンス等）を定量的に評価し、その関係性を可視化・分析するための研究開発プロジェクト基盤です。

### 設計思想

- **🔄 再現性 (Reproducibility)**: Dockerによる完全なコンテナ化
- **🧩 モジュール性 (Modularity)**: 機能別の明確な分離
- **⚙️ 設定駆動 (Configuration-Driven)**: パラメータの外部化
- **📚 ドキュメント先行 (Documentation-First)**: 仕様書による開発

## 主要機能

### 📊 指標計算
- **多中心性**: DBSCANによるクラスタリング分析
- **疎性**: 空間充填率と建物数の関係
- **流動性**: パーコレーション分析
- **重なり**: 複数属性建物の割合
- **創発性**: ネットワーク中心性と密度の関係
- **適応性**: Fiedler値によるレジリエンス評価

### 🎨 可視化
- 日本全国300地点の散布図表示
- 指定地点のネットワーク構造可視化
- インタラクティブダッシュボード（HTML/Dash対応）
- 全指標の包括的ペアプロット表示

## セットアップ

### 前提条件
- Docker & Docker Compose
- Git

### インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd opensparsity

# Docker環境の構築
docker-compose build

# サービスの起動
docker-compose up -d
```

### アクセス
- **Streamlitアプリ**: http://localhost:8501
- **Jupyter Notebook**: http://localhost:8888

## 使用方法

### 1. 設定ファイルの編集
`config/parameters.yml`で分析パラメータを設定

```yaml
# 例: DBSCANパラメータの変更
multi_nodality:
  dbscan:
    eps: 0.5        # クラスター半径
    min_samples: 5  # 最小サンプル数
```

### 2. データ分析の実行
```bash
# 分析の実行
docker-compose exec app python scripts/run_analysis.py

# レポート生成
docker-compose exec app python scripts/generate_report.py
```

### 3. インタラクティブ分析とダッシュボード

```bash
# HTMLダッシュボード（推奨）
python3 run_dashboard.py

# または直接実行
python3 src/app/html_dashboard.py

# Dashインタラクティブアプリ（要: dash, plotly）
python3 src/app/dash_app.py
```

## フォルダ構造

```
opensparsity/
├── config/              # 設定ファイル
│   └── parameters.yml   # 分析パラメータ
├── data/                # データファイル
│   ├── raw/            # 生データ
│   ├── processed/      # 前処理済みデータ
│   └── cache/          # キャッシュファイル
├── docs/               # ドキュメント
│   ├── metrics_definition.md  # 指標定義
│   └── setup_guide.md         # セットアップガイド
├── src/                # ソースコード
│   ├── data/           # データ取得・前処理
│   ├── metrics/        # 指標計算
│   ├── app/            # Streamlitアプリ
│   └── utils/          # 共通ユーティリティ
├── tests/              # テストコード
├── notebooks/          # Jupyterノートブック
└── scripts/            # 実行スクリプト
```

## 開発

### テスト実行
```bash
docker-compose exec app python -m pytest tests/
```

### コード品質チェック
```bash
docker-compose exec app flake8 src/
docker-compose exec app black src/
```

### 開発環境での実行
```bash
# バッチ処理用コンテナの起動
docker-compose --profile batch up -d batch

# コンテナ内でコマンド実行
docker-compose exec batch python scripts/run_analysis.py
```

## データソース

- **国土地理院ベクトルタイル**: https://github.com/gsi-cyberjapan/optimal_bvmap
- **OpenStreetMap**: 道路ネットワークデータ

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 関連研究

このプロジェクトは以下の研究に基づいています：
- Batty, M. (2007). Cities and complexity: Understanding cities with cellular automata, agent-based models, and fractals
- Raimbault, J. (2020). Cities as they could be: Artificial Life and Urban Systems

## 連絡先

プロジェクトに関する質問や提案は、GitHubのIssuesまでお願いします。
