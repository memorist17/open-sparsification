# 1地点テスト手順

## 前提条件

以下の依存関係がインストールされている必要があります：

```bash
pip install -r requirements.txt
```

または個別に：

```bash
pip install numpy scipy pandas geopandas shapely pyproj rasterio fiona networkx matplotlib seaborn plotly tqdm joblib pyarrow
```

## テスト実行

### 1. 最小限のテスト（インポート確認）

```bash
python3 test_overture_minimal.py
```

このテストは：
- すべてのモジュールが正常にインポートできるか確認
- 基本機能が動作するか確認

### 2. 完全なテスト（サンプルデータ使用）

```bash
python3 test_overture_single_location.py
```

このテストは：
- サンプル建物データ（1000点）を生成
- サンプル道路データ（100セグメント）を生成
- ハイブリッドネットワークを構築
- 3つの指標（Lacunarity, Percolation, Multifractal）を計算
- 結果を保存・可視化

### 3. 実際のOvertureデータを使用する場合

```bash
python3 run_overture_parallel.py \
    --buildings path/to/buildings.parquet \
    --roads path/to/roads.parquet \
    --extent 139.7 35.6 139.8 35.7 \
    --output ./output \
    --cache-dir ./cache \
    --n-jobs 4 \
    --verbose
```

## テストの期待される出力

### ステップ1: データ生成
```
✓ 建物データ生成: 1000 点
✓ 道路データ生成: 100 セグメント
```

### ステップ2: ハイブリッドネットワーク構築
```
Building hybrid network...
  Road segments: 100
  Building centroids: 1000
Added X road edges
Added Y building-to-road edges
Added Z building edges
Network built: N nodes, M edges
```

### ステップ3: 指標計算
```
Running Lacunarity Analysis...
  Completed. Scales analyzed: 9
Running Percolation Analysis...
  Completed. Percolation threshold r_p = XX.XX m
Running Multifractal Analysis...
  Completed. Spectrum width Δα = X.XXXX
```

### ステップ4: 結果保存
```
Saved: ./test_output_single/test_location_lacunarity.csv
Saved: ./test_output_single/test_location_percolation.csv
Saved: ./test_output_single/test_location_multifractal.csv
...
```

## 出力ファイル構造

```
test_output_single/
├── test_location_lacunarity.csv
├── test_location_lacunarity_aggregation.json
├── test_location_percolation.csv
├── test_location_percolation_summary.json
├── test_location_multifractal.csv
├── test_location_multifractal_summary.json
├── test_location_summary.json
└── figures/
    ├── lacunarity.png
    ├── percolation.png
    ├── multifractal.png
    └── combined.png
```

## トラブルシューティング

### エラー: ModuleNotFoundError
- `pip install -r requirements.txt` を実行して依存関係をインストール

### エラー: GDAL関連
- macOS: `brew install gdal`
- Ubuntu: `apt-get install gdal-bin libgdal-dev`

### メモリ不足
- `generate_sample_buildings()` の `n_points` を減らす
- `generate_sample_roads()` の `n_segments` を減らす

### 並列処理が動作しない
- `n_jobs=1` を指定してシリアル実行にフォールバック

## 次のステップ

テストが成功したら：
1. 実際のOverture Parquetファイルでテスト
2. 複数地点のバッチ処理をテスト
3. パフォーマンス測定と最適化
