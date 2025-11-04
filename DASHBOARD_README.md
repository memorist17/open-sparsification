# 🎨 Interactive Dashboard Guide

**OpenSparsity Metrics — Web-based Interactive Dashboard**

---

## Overview

インタラクティブなWebダッシュボードで、3つの指標（Lacunarity、Percolation、Multifractal）を統合的に探索できます。

**主な機能:**
- 📊 リアルタイムでパターンを比較
- 🔍 インタラクティブなグラフ（ズーム、パン、ホバー）
- 📈 3指標の統合ビュー
- 📋 サマリー統計テーブル
- 🎯 複数パターンの同時表示

---

## Quick Start

### 方法1: 自動スクリプト（推奨）

```bash
./run_demo_and_dashboard.sh
```

このスクリプトは：
1. デモデータを生成（まだない場合）
2. 必要な依存関係をインストール
3. ダッシュボードを起動

### 方法2: 手動実行

```bash
# 1. 依存関係をインストール
pip install dash plotly

# 2. デモデータを生成（まだない場合）
python3 main.py demo

# 3. ダッシュボードを起動
python3 dashboard.py --data demo_output
```

---

## 使い方

### ダッシュボードの起動

```bash
# デフォルト設定（ポート8050）
python3 dashboard.py

# カスタムデータディレクトリ
python3 dashboard.py --data results/my_analysis

# カスタムポート
python3 dashboard.py --port 8888

# デバッグモード
python3 dashboard.py --debug
```

### アクセス

ブラウザで以下のURLを開く:
```
http://127.0.0.1:8050
```

または表示されたURLをクリック

---

## Dashboard Features

### 1️⃣ パターン選択

- チェックボックスで比較するパターンを選択
- 複数パターンの同時表示が可能
- リアルタイムで更新

### 2️⃣ サマリーテーブル

各パターンの主要統計値:
- **Λ (small/large)**: 小/大スケールのLacunarity
- **r_p**: Percolation閾値（メートル）
- **Max S₁/N**: 最大接続率
- **Δα**: Multifractalスペクトル幅
- **D₀**: Box-counting次元

### 3️⃣ Lacunarityプロット

- X軸: スケール（対数表示）
- Y軸: Lacunarity値
- ホバー: 詳細データ表示
- ズーム/パン可能

### 4️⃣ Percolationプロット

**左パネル: Percolation遷移**
- S₁/N vs. 距離閾値
- 破線: 臨界値（0.5）

**右パネル: ネットワーク位相**
- 平均次数 vs. 距離閾値

### 5️⃣ Multifractalプロット

**左パネル: 一般化次元**
- D(q) スペクトル

**右パネル: 特異スペクトル**
- f(α) 曲線

---

## データ形式

ダッシュボードは以下の構造を期待:

```
data_directory/
├── pattern1/
│   ├── pattern1_lacunarity.csv
│   ├── pattern1_percolation.csv
│   ├── pattern1_multifractal.csv
│   └── pattern1_summary.json
├── pattern2/
│   └── ...
└── pattern3/
    └── ...
```

または:

```
data_directory/
├── pattern1/
│   ├── lacunarity.csv
│   ├── percolation.csv
│   ├── multifractal.csv
│   └── summary.json
└── ...
```

---

## インタラクティブ機能

### グラフ操作

| 操作 | アクション |
|------|-----------|
| **ホバー** | データポイントの詳細表示 |
| **ドラッグ** | 領域をズーム |
| **ダブルクリック** | ズームリセット |
| **Shift+ドラッグ** | パン |
| **スクロール** | ズームイン/アウト |

### ツールバー

各グラフの右上にツールバー:
- 📷 画像として保存
- 🔍 ズームツール
- 📐 パンツール
- ↺ リセット

---

## コマンドライン オプション

```bash
python3 dashboard.py --help
```

### オプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--data`, `-d` | `demo_output` | データディレクトリ |
| `--port`, `-p` | `8050` | ポート番号 |
| `--host` | `127.0.0.1` | ホストアドレス |
| `--debug` | `False` | デバッグモード |

### 例

```bash
# カスタムデータとポート
python3 dashboard.py --data results/cities --port 8888

# ネットワーク公開（注意: セキュリティリスクあり）
python3 dashboard.py --host 0.0.0.0

# デバッグモード（開発用）
python3 dashboard.py --debug
```

---

## トラブルシューティング

### ❌ "ModuleNotFoundError: No module named 'dash'"

```bash
pip install dash plotly
```

### ❌ "No patterns found in ..."

データディレクトリを確認:
```bash
python3 main.py demo  # デモデータを生成
python3 dashboard.py --data demo_output
```

### ❌ "Address already in use"

ポートを変更:
```bash
python3 dashboard.py --port 8888
```

### ❌ グラフが表示されない

1. ブラウザのキャッシュをクリア
2. データファイルの存在を確認
3. デバッグモードで実行:
   ```bash
   python3 dashboard.py --debug
   ```

---

## カスタマイズ

### 配色の変更

`dashboard.py`内の以下を編集:

```python
colors = px.colors.qualitative.Set2  # 他のカラーパレットに変更
```

利用可能なパレット:
- `px.colors.qualitative.Plotly`
- `px.colors.qualitative.D3`
- `px.colors.qualitative.Set1`
- など

### レイアウトの調整

`app.layout`セクションでHTML/CSSをカスタマイズ可能。

---

## パフォーマンス

### 推奨環境

- **パターン数**: 1-10（同時表示3-5推奨）
- **データポイント**: 各指標100-1000ポイント
- **メモリ**: 最低512MB
- **ブラウザ**: Chrome, Firefox, Safari（最新版）

### 大規模データセット

多数のパターンがある場合:
1. サブセットを選択
2. 別ディレクトリにコピー
3. そのディレクトリでダッシュボードを起動

---

## デプロイ

### ローカルネットワーク

```bash
python3 dashboard.py --host 0.0.0.0 --port 8050
```

同じネットワーク上の他のデバイスからアクセス:
```
http://<your-ip-address>:8050
```

### 本番環境（Heroku, AWS等）

`dashboard.py`は標準のDashアプリなので、通常のDashデプロイ手順に従う。

参考: https://dash.plotly.com/deployment

---

## 技術スタック

- **Dash** — Webフレームワーク
- **Plotly** — インタラクティブグラフ
- **Pandas** — データ処理
- **Flask** — Dashのバックエンド

---

## ショートカット

### macOS/Linux

```bash
# デモ+ダッシュボード起動
./run_demo_and_dashboard.sh

# または直接
python3 dashboard.py
```

### Windows

```cmd
python dashboard.py
```

---

## FAQ

**Q: ダッシュボードを停止するには？**  
A: ターミナルで `Ctrl+C`

**Q: 自動更新されますか？**  
A: いいえ。データが更新されたら再起動が必要です。

**Q: 複数のデータセットを切り替えられますか？**  
A: `--data`オプションで異なるディレクトリを指定して再起動してください。

**Q: プロットを保存できますか？**  
A: 各グラフの📷アイコンで画像保存が可能です。

**Q: カスタムメトリクスを追加できますか？**  
A: `dashboard.py`を編集して新しいプロット関数を追加してください。

---

## スクリーンショット例

起動すると以下のような画面が表示されます:

```
┌─────────────────────────────────────────────┐
│  🧩 OpenSparsity Metrics Dashboard          │
│  Interactive Three-Indicator Framework      │
├─────────────────────────────────────────────┤
│  Select Patterns:                           │
│  ☑ clustered  ☑ random  ☑ grid             │
├─────────────────────────────────────────────┤
│  Summary Statistics Table                   │
│  Pattern | Λ(small) | r_p | Δα | ...       │
├─────────────────────────────────────────────┤
│  Lacunarity Analysis                        │
│  [Interactive plot with multiple lines]     │
├─────────────────────────────────────────────┤
│  Percolation Analysis                       │
│  [Two-panel plot: S1/N and topology]        │
├─────────────────────────────────────────────┤
│  Multifractal Analysis                      │
│  [Two-panel plot: D(q) and f(α)]           │
└─────────────────────────────────────────────┘
```

---

## さらなる情報

- **メインドキュメント**: [README.md](README.md)
- **メトリクス詳細**: [METRICS_REFERENCE.md](METRICS_REFERENCE.md)
- **システム設計**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

**OpenSparsity Project**  
*Interactive Dashboard v2.0.0*

