# 📐 Metrics Reference Guide

**OpenSparsity Three-Indicator Framework — Technical Reference**

---

## Overview of Three Metrics

| Metric | Mathematical Definition | Scale Range | Key Output | Interpretation |
|--------|-------------------------|-------------|------------|----------------|
| **Lacunarity** | Λ(ε) = σ²(ε)/μ²(ε) + 1 | 10–600 m | Λ ∈ [1, ∞) | Spatial heterogeneity |
| **Percolation** | P(r) = S₁(r)/N | 10–800 m | r_p (meters) | Critical connectivity |
| **Multifractal** | D(q) = τ(q)/(q-1) | 10–1000 m | Δα ∈ [0, ∞) | Hierarchical complexity |

---

## 1. Lacunarity (Λ) — Local Vacancy Structure

### Mathematical Foundation

**Gliding Box Algorithm:**

For window size k:
1. Slide k×k window across binary raster
2. Count points S(i,j,k) in each window position
3. Calculate mean μ(k) = ⟨S⟩
4. Calculate variance σ²(k) = ⟨S²⟩ - ⟨S⟩²

**Lacunarity Formula:**
```
Λ(k) = σ²(k) / μ(k)² + 1
```

### Scale Interpretation

| Scale Category | Window Size (pixels) | Spatial Scale (m) | Urban Meaning |
|----------------|---------------------|-------------------|---------------|
| Small | 3–15 | 10–75 m | Individual buildings, local gaps |
| Medium | 21–41 | 100–200 m | Block structure, neighborhood spacing |
| Large | 51–101 | 250–600 m | District patterns, major open spaces |

### Output Values

- **Λ = 1.0**: Perfectly homogeneous (Poisson random or uniform grid)
- **Λ = 1.5–2.0**: Moderate clustering (typical urban cores)
- **Λ = 2.0–5.0**: High clustering (suburban sprawl patterns)
- **Λ > 5.0**: Extreme heterogeneity (sparse rural settlements)

### Research Applications

1. **Urban Morphology**: Quantify compactness vs. sprawl
2. **Land Use**: Detect transition zones and boundaries
3. **Temporal Analysis**: Track densification or dispersion over time
4. **Comparative Studies**: Compare cities or neighborhoods

### Implementation Details

**Raster Resolution:**
- Default: 5 m pixels
- Trade-off: Resolution vs. computational cost
- Recommendation: Match to minimum feature size

**Window Sizes:**
- Default: [3, 5, 7, 11, 15, 21, 31, 41, 51, 71, 101] pixels
- Log-like spacing to cover multiple scales
- Maximum: Limited by data extent

**Edge Effects:**
- Valid region excludes margin of k/2 pixels
- Larger windows → less valid data
- Consider data extent when choosing window sizes

---

## 2. Percolation (P) — Critical Connectivity

### Mathematical Foundation

**Network Construction:**
```
G(r) = (V, E)
where E = {(i,j) : d(i,j) ≤ r}
```

**Order Parameter:**
```
P(r) = S₁(r) / N
```
where:
- S₁(r): Size of largest connected component
- N: Total number of nodes
- r: Distance threshold

### Critical Phenomena

**Percolation Threshold r_p:**
- Defined: P(r_p) = 0.5
- Physical meaning: Distance where system transitions from fragmented to connected
- Universal behavior near threshold (phase transition analogy)

### Network Metrics

| Metric | Formula | Meaning |
|--------|---------|---------|
| Average degree | ⟨k⟩ = (2\|E\|)/\|V\| | Mean connections per node |
| Clustering | C = ⟨c_i⟩ | Tendency to form triangles |
| Path length | L = ⟨d(i,j)⟩ | Average shortest path |
| Components | n_c | Number of disconnected clusters |

### Interpretation

**Small r_p (High Permeability):**
- Nodes connect easily with minimal distance
- Continuous urban fabric
- High walkability/connectivity
- Example: Dense city centers

**Large r_p (Low Permeability):**
- Large distances needed for connectivity
- Fragmented structure
- Isolated clusters
- Example: Suburban developments, rural areas

### Scaling Behavior

```
P(r) ≈ (r - r_p)^β  for r → r_p⁺
```
- β ≈ 0.4–0.6 for 2D spatial networks
- Power-law behavior indicates criticality

### Research Applications

1. **Accessibility Analysis**: Quantify connectivity at various scales
2. **Network Resilience**: Identify critical connection distances
3. **Growth Simulation**: Parameterize urban expansion models
4. **Infrastructure Planning**: Optimize service coverage

### Implementation Details

**Distance Thresholds:**
- Default: [10, 25, 50, 100, 200, 400, 800] meters
- Log spacing to capture transition
- Range: Walking distance to neighborhood scale

**Network Methods:**
- `radius`: Connect all nodes within distance r
- `knn`: Connect k nearest neighbors (alternative)
- `delaunay`: Triangulation-based (future)

**Computational Complexity:**
- O(N²) worst case for distance matrix
- Optimization: Spatial indexing (KD-tree)
- Memory: Sparse graph storage

---

## 3. Multifractal (D, f) — Hierarchical Structure

### Mathematical Foundation

**Box-Counting Probability:**

For box size ε:
1. Partition space into boxes of size ε
2. Calculate probability p_i(ε) = n_i / N_total
3. Ensure normalization: Σ p_i = 1

**Moment Sum:**
```
χ(q, ε) = Σ p_i^q
```

**Mass Exponent:**
```
τ(q) = lim[ε→0] log χ(q,ε) / log ε
```

**Generalized Dimension:**
```
D(q) = τ(q) / (q - 1)
```

**Singularity Spectrum (Legendre Transform):**
```
α(q) = dτ/dq
f(α) = q·α - τ(q)
```

### Key Dimensions

| Dimension | q | Formula | Meaning |
|-----------|---|---------|---------|
| D₀ | 0 | Box-counting | Capacity/coverage |
| D₁ | 1 | Information | Entropy-weighted |
| D₂ | 2 | Correlation | Pair correlation |

**Monofractal:** D₀ = D₁ = D₂ (all dimensions equal)  
**Multifractal:** D₀ > D₁ > D₂ (hierarchy of dimensions)

### Spectrum Width

```
Δα = α_max - α_min
```

**Interpretation:**
- **Δα ≈ 0**: Uniform, monofractal (e.g., regular grid)
- **Δα = 0.2–0.5**: Moderate hierarchy (typical cities)
- **Δα > 0.5**: Strong multi-scale structure (polycentric megacities)

### f(α) Curve Shape

**Convex Parabola:**
- Peak at α₀ (most frequent singularity)
- Width Δα indicates diversity
- Symmetry indicates balance of dense/sparse regions

**Asymmetric:**
- Right-skewed: More sparse than dense regions
- Left-skewed: More dense than sparse regions

### Research Applications

1. **Urban Hierarchy**: Identify multi-scale centers
2. **Complexity Metrics**: Quantify organizational complexity
3. **Comparative Analysis**: Compare self-similarity across cities
4. **Theoretical Models**: Validate fractal growth models

### Implementation Details

**Box Sizes:**
- Default: [10, 25, 50, 100, 200, 400, 800, 1000] meters
- Need: At least 3 sizes for linear regression
- Range: Cover 2+ orders of magnitude

**Moment Orders:**
- Default: q ∈ [-5, +5]
- Positive q: Emphasize dense regions
- Negative q: Emphasize sparse regions
- q = 0: Pure geometry (box-counting)

**Numerical Stability:**
- Avoid q too large/small (numerical overflow)
- Filter empty boxes before probability calculation
- Use log-space arithmetic for stability

---

## Cross-Metric Relationships

### Conceptual Mapping

| Lacunarity | Percolation | Multifractal | Urban Pattern |
|------------|-------------|--------------|---------------|
| Low Λ | Small r_p | Small Δα | Homogeneous, uniform |
| High Λ | Large r_p | Large Δα | Heterogeneous, hierarchical |
| Medium Λ | Medium r_p | Medium Δα | Structured, polycentric |

### Scale Alignment

All three metrics operate on comparable scales:
- **10–50 m**: Local structure (building spacing)
- **50–200 m**: Neighborhood structure (block patterns)
- **200–1000 m**: District structure (urban morphology)

### Complementary Information

- **Lacunarity**: "Where are the gaps?"
- **Percolation**: "How do things connect?"
- **Multifractal**: "How is complexity organized?"

---

## Validation and Quality Control

### Expected Relationships

1. **Clustered Pattern:**
   - High Λ (large gaps between clusters)
   - Large r_p (clusters far apart)
   - Large Δα (multi-scale clusters)

2. **Random Pattern:**
   - Λ ≈ 1 (Poisson)
   - Medium r_p (no structure)
   - Small Δα (no hierarchy)

3. **Grid Pattern:**
   - Λ ≈ 1 (uniform)
   - Small r_p (regular spacing)
   - Δα ≈ 0 (monofractal)

### Data Quality Checks

**Before Analysis:**
- CRS is projected (meters, not degrees)
- No duplicate points
- Points within analysis bounds
- Sufficient point density (>100 points recommended)

**After Analysis:**
- Lacunarity values positive and finite
- Percolation curve monotonically increasing
- Multifractal spectrum convex

---

## Parameter Selection Guide

### When to Adjust Defaults

**High-Density Urban Core:**
- Smaller pixel_size (2–3 m)
- Smaller window_sizes (3–21)
- Smaller thresholds (5–200 m)

**Suburban/Rural:**
- Larger pixel_size (10 m)
- Larger window_sizes (11–151)
- Larger thresholds (50–2000 m)

**Large Study Area (>10 km²):**
- Tile-based processing
- Coarser resolutions
- Parallel processing

---

## Computational Performance

### Time Complexity

| Metric | Complexity | Typical Time (1000 pts) |
|--------|-----------|-------------------------|
| Lacunarity | O(n × k²) | ~1–5 seconds |
| Percolation | O(n² + m log m) | ~5–15 seconds |
| Multifractal | O(n × q × s) | ~10–30 seconds |

*n = points, k = window sizes, m = edges, q = moments, s = scales*

### Memory Requirements

| Component | Size | Recommendation |
|-----------|------|----------------|
| Raster | (width × height) bytes | <1000 × 1000 for speed |
| Distance matrix | n² × 8 bytes | Use sparse for n > 5000 |
| Network | O(edges) | Depends on threshold |

---

## Literature References

### Foundational Papers

**Lacunarity:**
- Plotnick et al. (1996) *Physical Review E*
- Allain & Cloitre (1991) *Physical Review A*

**Percolation:**
- Stauffer & Aharony (1994) *Introduction to Percolation Theory*
- Makse et al. (1995, 1998) *Nature*, *Physical Review E*

**Multifractal:**
- Halsey et al. (1986) *Physical Review A*
- Chhabra & Jensen (1989) *Physical Review Letters*

### Urban Applications

- Batty & Longley (1994) *Fractal Cities*
- Frankhauser (1994) *La Fractalité des Structures Urbaines*
- Murcio et al. (2015) *Physical Review E*
- Arcaute et al. (2015, 2016) *Journal of the Royal Society Interface*

---

**OpenSparsity Project**  
*Metrics Reference v2.0.0*

