# 指標定義と計算式

## 概要

OpenSparsityプロジェクトで使用する都市構造特性指標の定義、計算式、および`parameters.yml`で設定可能なパラメータについて説明します。

## 1. 多中心性 (Multi-nodality)

### 定義
都市空間における複数の中心（核）の存在とその分布特性を定量化する指標。単一の中心を持つ都市と比較して、多中心都市の特性を評価します。

### 計算式
```
多中心性 = 核の数 × 核の分散度 × 核の多様性
```

### 計算手順
1. **DBSCANクラスタリング**: 建物密度の高い地点をクラスターとして検出
2. **核の数**: 検出されたクラスター数
3. **核の分散度**: クラスター間の距離の分散
4. **核の多様性**: クラスターサイズの多様性（シャノン多様性指数）

### 設定パラメータ
```yaml
multi_nodality:
  dbscan:
    eps: 0.5              # クラスター半径（度）
    min_samples: 5        # 最小サンプル数
    metric: "euclidean"   # 距離メトリック
  dispersion:
    method: "variance"    # 分散度計算方法
  diversity:
    method: "shannon"     # 多様性計算方法
```

## 2. 疎性 (Sparsity)

### 定義
空間の充填度と建物数の関係から都市の密度特性を評価する指標。高密度都市と低密度都市の特性を定量化します。

### 計算式
```
疎性 = 空間充填率（フラクタル次元数） / 建物数
```

### 計算手順
1. **フラクタル次元計算**: ボックスカウンティング法による空間充填率
2. **建物数カウント**: 指定面積以上の建物数を計算
3. **疎性指標**: フラクタル次元を建物数で正規化

### 設定パラメータ
```yaml
sparsity:
  fractal:
    method: "box_counting"
    box_sizes: [1, 2, 4, 8, 16, 32, 64]  # ボックスサイズ（メートル）
  building_count:
    min_area: 10.0        # 最小建物面積（m²）
```

## 3. 流動性 (Permeability)

### 定義
オープンスペースの連結性を通じて都市の移動可能性を評価する指標。パーコレーション理論に基づいて計算されます。

### 計算式
```
流動性 = 最大オープンスペース面積 / 全オープンスペースの総面積
```

### 計算手順
1. **空間離散化**: 指定グリッドサイズで空間を分割
2. **オープンスペース判定**: 建物密度閾値による判定
3. **パーコレーション解析**: 連結成分の分析
4. **流動性計算**: 最大連結成分の面積比率

### 設定パラメータ
```yaml
permeability:
  grid_size: 50.0                    # グリッドサイズ（メートル）
  open_space:
    building_density_threshold: 0.3  # 建物密度閾値
    min_road_width: 3.0              # 最小道路幅
    min_green_area: 100.0            # 最小緑地面積
  percolation_threshold: 0.5927      # パーコレーション閾値
```

## 4. 重なり (Overlap)

### 定義
複数の機能や属性を持つ建物の割合を評価する指標。都市の機能的多様性を定量化します。

### 計算式
```
重なり = 複数の属性をもった建物総数 / 総建物数
```

### 計算手順
1. **属性分類**: 建物を住宅、商業、工業、公共に分類
2. **重複判定**: 複数属性を持つ建物を特定
3. **重なり計算**: 重複建物の割合

### 設定パラメータ
```yaml
overlap:
  attributes:
    - "residential"  # 住宅
    - "commercial"   # 商業
    - "industrial"   # 工業
    - "public"       # 公共
  overlap_threshold: 0.1  # 重複判定閾値
```

## 5. 創発性 (Emergence)

### 定義
ネットワーク中心性と建物密度の関係から、都市空間における創発的現象の可能性を評価する指標。

### 計算式
```
創発性 = (各余白地点のネットワーク中心性 / (1 + 建物密度))の平均
```

### 計算手順
1. **ネットワーク構築**: 建物間の接続関係を構築
2. **中心性計算**: 各地点のネットワーク中心性を計算
3. **密度正規化**: 建物密度で正規化
4. **創発性計算**: 正規化された中心性の平均

### 設定パラメータ
```yaml
emergence:
  centrality:
    - "betweenness"  # 媒介中心性
    - "closeness"    # 近接中心性
    - "eigenvector"  # 固有ベクトル中心性
  density:
    radius: 200.0    # 密度計算半径（メートル）
    method: "gaussian"  # 密度計算方法
```

## 6. 適応性 (Resilience)

### 定義
ネットワークのFiedler値（代数的連結度）を用いて都市の適応性・レジリエンスを評価する指標。

### 計算式
```
適応性 = Fiedler値（グラフの代数的連結度）
```

### 計算手順
1. **ネットワーク構築**: 建物・道路の接続関係を構築
2. **ラプラシアン行列**: グラフのラプラシアン行列を計算
3. **固有値計算**: ラプラシアン行列の固有値を計算
4. **Fiedler値**: 2番目に小さい固有値（Fiedler値）を取得

### 設定パラメータ
```yaml
resilience:
  fiedler:
    distance_threshold: 100.0  # グラフ構築閾値（メートル）
    weight_method: "distance"  # 重み付け方法
  network_type:
    - "road"      # 道路ネットワーク
    - "building"  # 建物ネットワーク
    - "mixed"     # 混合ネットワーク
```

## パラメータ設定のガイドライン

### 1. スケール依存性
- **グリッドサイズ**: 分析対象のスケールに応じて調整
- **距離閾値**: 都市の密度に応じて調整

### 2. データ品質
- **最小面積**: データの解像度に応じて調整
- **密度閾値**: 地域特性に応じて調整

### 3. 計算効率
- **並列処理**: CPU数に応じて調整
- **キャッシュ**: メモリ使用量に応じて調整

## 参考文献

1. Batty, M. (2007). Cities and complexity: Understanding cities with cellular automata, agent-based models, and fractals. The MIT Press.
2. Raimbault, J. (2020). Cities as they could be: Artificial Life and Urban Systems. arXiv preprint arXiv:2002.12926.
3. Newman, M. E. (2003). The structure and function of complex networks. SIAM review, 45(2), 167-256.
4. Stauffer, D., & Aharony, A. (2018). Introduction to percolation theory. CRC press.
