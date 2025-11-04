# 🚀 ここから始めましょう！

**OpenSparsity Metrics — 完全セットアップ済み**

---

## ✅ セットアップ完了！

仮想環境が作成され、すべての依存関係がインストールされました。

---

## 🎯 今すぐダッシュボードを起動

ターミナルで以下を実行：

```bash
cd "/Users/kotaronomac/SFC-CNS Dropbox/Iwata Kotaro/Mac/Documents/SFC/atakalab/谷life/three_indicator"

./run_dashboard_venv.sh
```

**または**

```bash
cd "/Users/kotaronomac/SFC-CNS Dropbox/Iwata Kotaro/Mac/Documents/SFC/atakalab/谷life/three_indicator"

source venv/bin/activate
python quick_start_dashboard.py
```

### ダッシュボードにアクセス

ブラウザで以下のURLを開く：

```
http://127.0.0.1:8050
```

---

## 📊 何が見られるか

### インタラクティブダッシュボード

1. **パターン選択**
   - clustered（クラスター型）
   - random（ランダム型）
   - grid（グリッド型）

2. **3つの指標**
   - **Lacunarity**: 空間の「空白構造」
   - **Percolation**: 臨界的「連結構造」  
   - **Multifractal**: スケール的「階層構造」

3. **インタラクティブ機能**
   - ズーム・パン
   - ホバーで詳細表示
   - パターン比較
   - 画像エクスポート

---

## 📚 ドキュメント

| ファイル | 読むべきタイミング |
|---------|-------------------|
| **START_HERE.md** | ← 今ここ！ |
| **仮想環境ガイド.md** | 仮想環境の詳細を知りたい |
| **QUICKSTART.md** | 5分で基本を学びたい |
| **DASHBOARD_README.md** | ダッシュボードの全機能を知りたい |
| **README.md** | 完全なドキュメント |
| **METRICS_REFERENCE.md** | 数学的背景を学びたい |

---

## 🎓 チュートリアル

### ステップ1: ダッシュボードを起動

```bash
./run_dashboard_venv.sh
```

### ステップ2: ブラウザで開く

```
http://127.0.0.1:8050
```

### ステップ3: パターンを選択

チェックボックスで比較したいパターンを選択：
- ☑ clustered
- ☑ random  
- ☑ grid

### ステップ4: グラフを探索

- **ホバー**: データポイントに詳細表示
- **ドラッグ**: 領域をズーム
- **ダブルクリック**: ズームリセット
- **📷**: 画像として保存

---

## 💻 コマンド早見表

```bash
# ダッシュボード起動（最も簡単）
./run_dashboard_venv.sh

# 仮想環境をアクティベート
source venv/bin/activate

# デモを実行
python main.py demo

# ダッシュボードを起動
python dashboard.py

# 独自データを分析
python main.py analyze your_data.gpkg --output results/

# ヘルプ
python main.py --help

# 仮想環境を終了
deactivate
```

---

## 🌟 主な機能

### ✅ 完全実装済み

- 3つのコア指標（Lacunarity, Percolation, Multifractal）
- インタラクティブWebダッシュボード
- バッチ処理
- 複数パターン比較
- 高品質ビジュアライゼーション
- 完全な日本語ドキュメント

---

## 🔍 実行例

### デモデータ分析

```bash
source venv/bin/activate
python main.py demo
```

→ `demo_output/` にデータが生成される

### ダッシュボードで確認

```bash
python dashboard.py --data demo_output
```

→ ブラウザで http://127.0.0.1:8050

### 独自データで実行

```bash
# 分析
python main.py analyze buildings.gpkg --output results/tokyo

# ダッシュボード
python dashboard.py --data results/tokyo
```

---

## ❓ よくある質問

### Q: 仮想環境とは？

A: Pythonパッケージを隔離された環境で管理する仕組み。システムのPythonに影響を与えません。

### Q: ダッシュボードが起動しない

A: 
```bash
# 仮想環境を確認
source venv/bin/activate
which python  # venv/bin/pythonと表示されればOK

# データを確認
ls demo_output/

# 再生成
python quick_start_dashboard.py
```

### Q: ポートが使用中

A:
```bash
python dashboard.py --port 8888
```
→ http://127.0.0.1:8888 で開く

### Q: 独自データの形式は？

A: GeoPackage (`.gpkg`)、Shapefile (`.shp`)、GeoJSON対応。点データ（建物の重心など）が必要。

---

## 📂 プロジェクト構成

```
three_indicator/
├── 📂 venv/              # 仮想環境（作成済み）
├── 📂 src/               # ソースコード
│   ├── metrics/          # 3指標の実装
│   ├── utils/            # ユーティリティ
│   └── visualization/    # プロット機能
├── 📄 main.py            # メインCLI
├── 📄 dashboard.py       # ダッシュボード
├── 📄 setup_venv.sh      # セットアップスクリプト
├── 📄 run_dashboard_venv.sh  # 起動スクリプト
└── 📚 ドキュメント各種
```

---

## 🎉 次のステップ

1. **今すぐ起動**
   ```bash
   ./run_dashboard_venv.sh
   ```

2. **ブラウザで開く**
   ```
   http://127.0.0.1:8050
   ```

3. **インタラクティブに探索**
   - パターンを比較
   - グラフをズーム
   - データをホバー
   - 結果を理解

4. **独自データで実行**
   - データを準備
   - 分析を実行
   - ダッシュボードで確認

---

## 📞 サポート

詳細なガイドは以下を参照：

- **基本操作**: `仮想環境ガイド.md`
- **ダッシュボード**: `DASHBOARD_README.md`
- **全機能**: `README.md`
- **数理背景**: `METRICS_REFERENCE.md`

---

## ✨ すぐに試す

**1行で起動：**

```bash
./run_dashboard_venv.sh
```

**ブラウザで開く：**

```
http://127.0.0.1:8050
```

---

**🎊 準備完了！今すぐ始めましょう！**

---

*OpenSparsity Project — Three-Indicator Framework v2.0.0*

