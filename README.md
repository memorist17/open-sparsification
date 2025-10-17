# OpenSparsity: 地理空間データによる集落構造特性分析基盤

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

## プロジェクト概要

地理空間データを用いて集落の構造特性（多中心性、疎性、レジリエンス等）を定量的に評価し、その関係性を可視化・分析するための研究開発プロジェクト基盤です。集落を「連続的に変化する複合ネットワーク」として捉え、公共政策・研究・市民活動の意思決定を支援します。

### 設計思想

- **🔄 再現性 (Reproducibility)**: Dockerによる完全なコンテナ化
- **🧩 モジュール性 (Modularity)**: 機能別の明確な分離
- **⚙️ 設定駆動 (Configuration-Driven)**: パラメータの外部化
- **📚 ドキュメント先行 (Documentation-First)**: 仕様書による開発

## 主要機能

### 📊 指標計算

集落を多中心的で適応的なシステムとして捉え、以下の6つの指標で評価します：

- **疎性 (Sparsity)**: 道路・建物ネットワークの空間充填度。余白としての潜在力と公共サービスアクセスのバランスを評価
- **レジリエンス (Resilience)**: Fiedler値によるネットワークの回復力・適応性評価。災害時の迂回可能性を定量化
- **多中心性 (Multi-nodality)**: DBSCANで抽出した活動クラスターの分布。集落が複数の重心を持つか、単一中心に偏るかを測定
- **流動性 (Permeability)**: パーコレーション分析によるネットワークの連結性。集落内の移動がどこで途切れるかを評価
- **創発性 (Emergence)**: ネットワーク中心性と密度の関係。局所的な振る舞いが集落全体にもたらすパターンを読み解く
- **重なり (Overlap)**: 用途・属性が異なる建物群の共存度。地域の機能的多様性と脆弱性を定量化

### 🎨 可視化

- **包括的ペアプロット**: 全6指標の相関関係を一覧表示（区切り線付きで見やすく改善）
- **インタラクティブダッシュボード**: HTML版（依存なし）とDash版（ホバー機能付き）の2種類を提供
- **地点別ネットワーク図**: 選択地点のハイブリッドネットワーク構造を可視化
- **統計サマリー**: 各指標の分布と平均値をカード形式で表示

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
# 統合ランチャー（推奨）
python3 run_dashboard.py
# → オプション1: HTMLダッシュボード（依存パッケージ不要）
# → オプション2: Dashインタラクティブアプリ（ホバー機能付き）

# 直接実行する場合
python3 src/app/html_dashboard.py  # HTML版
python3 src/app/dash_app.py        # Dash版（要: dash, plotly）

# ペアプロット画像の再生成（区切り線付き）
python3 scripts/create_comprehensive_pairplot.py
```

**✨ 最新機能:**
- ペアプロット散布図に区切り線を追加し、指標間の境界を明確化
- 設定駆動アーキテクチャ: `config/dashboard.yml` で見た目や動作をカスタマイズ可能
- モジュール化されたコンポーネント: 保守性と再利用性の向上

## フォルダ構造

```
opensparsity/
├── config/                      # 設定ファイル
│   ├── parameters.yml           # 分析パラメータ（指標計算用）
│   └── dashboard.yml            # ダッシュボード設定（NEW）
├── data/                        # データファイル
│   ├── raw/                     # 生データ
│   ├── processed/               # 前処理済みデータ
│   ├── network_overviews/       # ネットワーク概要画像
│   └── cache/                   # キャッシュファイル
├── docs/                        # ドキュメント
│   ├── philosophy.md            # プロジェクトの設計思想
│   ├── metrics_definition.md   # 指標定義と計算式
│   └── dashboard_guide.md       # ダッシュボード利用ガイド
├── src/                         # ソースコード
│   ├── data/                    # データ取得・前処理
│   ├── metrics/                 # 指標計算
│   ├── app/                     # ダッシュボードアプリ
│   │   ├── dash_app.py          # Dashメインアプリ（リファクタリング済み）
│   │   ├── dashboard_config.py  # 設定読み込みモジュール（NEW）
│   │   ├── dashboard_components.py  # グラフコンポーネント（NEW）
│   │   └── html_dashboard.py    # HTML版ダッシュボード
│   ├── visualization/           # 可視化ユーティリティ
│   └── utils/                   # 共通ユーティリティ
├── tests/                       # テストコード
├── notebooks/                   # Jupyterノートブック
├── scripts/                     # 実行スクリプト
│   └── create_comprehensive_pairplot.py  # ペアプロット生成
├── figures/                     # 生成された図
├── run_dashboard.py             # ダッシュボード統合ランチャー
└── requirements.txt             # Python依存パッケージ
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
