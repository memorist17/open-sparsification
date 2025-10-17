# Dashboard Guide

## 概要

OpenSparsityプロジェクトでは、集落形態学的特性を視覚的に分析するための2種類のダッシュボードを提供しています。

**設計思想との関係:**

ダッシュボードの実装は、以下の設計思想に基づいています（`docs/philosophy.md`参照）：

- **🔄 再現性**: 設定ファイルでパラメータを管理し、表示条件を再現可能に
- **🧩 モジュール性**: グラフ生成・設定管理を独立したモジュールに分離
- **⚙️ 設定駆動**: `config/dashboard.yml` で見た目や動作をコード変更なしにカスタマイズ
- **📚 ドキュメント先行**: コード内に設計意図を明記し、利用者が理解しやすい構造に

## 📊 利用可能なダッシュボード

### 1. HTMLダッシュボード（推奨）

**特徴:**
- 依存パッケージ不要
- スタンドアロンHTMLファイル
- ブラウザで即座に表示可能
- 包括的ペアプロットを含む

**起動方法:**
```bash
# 推奨: 実行スクリプトを使用
python3 run_dashboard.py
# → オプション1を選択

# または直接実行
python3 src/app/html_dashboard.py
```

**生成されるファイル:**
- `dashboard.html` - プロジェクトルートに生成

**含まれる要素:**
- 📈 全指標の包括的ペアプロット
- 📊 データサマリー統計
- 📋 全地点の詳細データテーブル
- 📖 指標の説明

### 2. Dashインタラクティブアプリ

**特徴:**
- インタラクティブな地点選択
- ホバー機能による詳細表示
- 衛星画像・ネットワーク画像の表示
- 包括的ペアプロットの表示

**必要パッケージ:**
```bash
pip install dash plotly
```

**起動方法:**
```bash
# 推奨: 実行スクリプトを使用
python3 run_dashboard.py
# → オプション2を選択

# または直接実行
python3 src/app/dash_app.py
```

**アクセス:**
- URL: http://localhost:8051

## 📈 包括的ペアプロット

両方のダッシュボードには、全6指標の包括的ペアプロットが含まれています。

### 表示される指標

1. **Sparsity (疎性)**: 建物密度の低さ
2. **Resilience (レジリエンス)**: ネットワークの回復力
3. **Multi-nodality (多中心性)**: 複数中心の都市構造
4. **Permeability (流動性)**: 人の移動のしやすさ
5. **Emergence (創発性)**: 新機能の創出可能性
6. **Overlap (重なり)**: 機能の重複度

### ペアプロットの特徴

- **対角線**: 各指標のヒストグラム（分布の可視化）
- **下三角**: 指標間の散布図（相関関係の可視化）
- **区切り線**: 各指標間に濃い色の区切り線を追加（NEW）
  - 指標の境界が明確になり、見やすさが向上
  - 区切り線の色・幅は `config/dashboard.yml` で設定可能
- **シンプルな表示**: 統一色・サイズの点で可読性を重視
- **正規化表示**: すべての指標を0〜1の範囲に正規化して比較可能に

## 🎨 HTMLダッシュボードの構成

### 1. ヘッダー
- プロジェクトタイトル
- サブタイトル

### 2. データサマリー
- 分析地点数
- 各指標の平均値
- カード形式の表示

### 3. ペアプロットセクション
- 包括的ペアプロット画像
- 指標の詳細説明

### 4. データテーブル
- 全地点のデータ一覧
- スクロール可能なテーブル
- ソート機能（ブラウザ依存）

### 5. フッター
- プロジェクト情報
- データ統計

## 🔧 カスタマイズ

### 設定ファイルによるカスタマイズ（推奨）

**⚙️ 設定駆動アーキテクチャ**により、コード変更なしでカスタマイズ可能です：

**`config/dashboard.yml`を編集:**

```yaml
# 区切り線のカスタマイズ例
pairplot:
  separator:
    enabled: true          # 区切り線の表示ON/OFF
    color: "#2c3e50"       # 区切り線の色
    width: 2.5             # 区切り線の幅
    layer: "above"         # レイヤー

# 散布図のスタイルカスタマイズ例
pairplot:
  style:
    scatter:
      size: 6                           # マーカーサイズ
      color: "rgba(37, 99, 235, 0.4)"  # マーカー色
    histogram:
      bins: 16                          # ビン数
      color: "#60a5fa"                  # ヒストグラム色

# サーバー設定のカスタマイズ例
dash_app:
  server:
    host: "0.0.0.0"
    port: 8051
    debug: true
```

設定を変更した後、ダッシュボードを再起動すると反映されます。

### コードによるカスタマイズ（上級者向け）

**モジュール化された構造**により、各機能を独立して修正可能です：

1. **設定管理**: `src/app/dashboard_config.py`
   - 設定の読み込みと管理
   - 新しい設定項目の追加

2. **グラフコンポーネント**: `src/app/dashboard_components.py`
   - ペアプロット生成ロジック
   - オーバーレイUI生成
   - 区切り線の描画ロジック

3. **メインアプリ**: `src/app/dash_app.py`
   - レイアウトとコールバック
   - データフローの管理

4. **HTMLダッシュボード**: `src/app/html_dashboard.py`
   - スタイル（CSSセクション）
   - HTMLテンプレート
   - データ処理

## 📝 使用例

### HTMLダッシュボードの使用

```bash
# 1. ダッシュボードを生成
python3 src/app/html_dashboard.py

# 2. ブラウザで開く
# 自動的にブラウザが開きます
# または手動で dashboard.html を開く
```

### Dashアプリの使用

```bash
# 1. アプリを起動
python3 src/app/dash_app.py

# 2. ブラウザでアクセス
# http://localhost:8051

# 3. 散布図の点をクリック/ホバー
# → 詳細情報が表示される
```

## 🐛 トラブルシューティング

### ペアプロットが表示されない

**原因**: ペアプロット画像が生成されていない

**解決方法**:
```bash
python3 scripts/create_comprehensive_pairplot.py
```

### Dashアプリが起動しない

**原因**: dash/plotlyがインストールされていない

**解決方法**:
```bash
pip install dash plotly
```

### データが表示されない

**原因**: 分析結果CSVが存在しない

**解決方法**:
```bash
python3 scripts/generate_real_sample_data_fixed.py
```

## 📚 関連ドキュメント

- [メトリクス定義](metrics_definition.md)
- [セットアップガイド](setup_guide.md)
- [README](../README.md)

## 🏗️ アーキテクチャ

### リファクタリング後の構造（2024-10）

```
src/app/
├── dash_app.py              # メインアプリケーション
│   └── create_dash_app()    # アプリ生成関数
│
├── dashboard_config.py      # 設定管理（NEW）
│   └── DashboardConfig      # 設定読み込みクラス
│       └── get_dashboard_config()  # シングルトン取得
│
├── dashboard_components.py  # グラフコンポーネント（NEW）
│   ├── normalize_metrics_frame()      # 指標正規化
│   ├── create_pairplot_figure()       # ペアプロット生成
│   ├── extract_location_id()          # ホバーデータ解析
│   ├── create_default_overlay_children()  # デフォルトUI
│   └── build_overlay_children()       # 地点詳細UI
│
└── html_dashboard.py        # HTML版ダッシュボード
    └── generate_html_dashboard()
```

**設計原則:**
- **単一責任**: 各モジュールは明確な責務を持つ
- **疎結合**: モジュール間の依存を最小化
- **テスト容易性**: 各関数を独立してテスト可能
- **設定駆動**: 動作パラメータを外部化

## 🔄 更新履歴

- **2024-10 (Latest)**: 
  - ✨ ペアプロット区切り線機能追加
  - ♻️ コードベースのリファクタリング（モジュール化）
  - ⚙️ 設定駆動アーキテクチャの導入 (`config/dashboard.yml`)
  - 📚 ドキュメント更新（philosophy.mdとの整合性確保）
- **2024-10**: HTMLダッシュボード追加
- **2024-10**: Dashアプリにペアプロット統合
- **2024-10**: 包括的ペアプロット対応

## 📖 関連ドキュメント

- [プロジェクトの設計思想](philosophy.md) - 4つの設計原則
- [指標定義](metrics_definition.md) - 各指標の詳細説明
- [README](../README.md) - プロジェクト全体の概要


