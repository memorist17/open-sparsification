"""
並列処理ユーティリティ

指標計算の並列化と高速化を提供する。
"""

import multiprocessing as mp
from functools import partial
from typing import Callable, List, Dict, Any, Optional, Tuple
from joblib import Parallel, delayed
import numpy as np
from tqdm import tqdm
import warnings


def get_optimal_n_jobs(n_tasks: int, max_workers: Optional[int] = None) -> int:
    """
    最適な並列ワーカー数を決定。
    
    Parameters
    ----------
    n_tasks : int
        タスク数
    max_workers : int, optional
        最大ワーカー数（Noneの場合はCPU数）
    
    Returns
    -------
    n_jobs : int
        最適なワーカー数
    """
    cpu_count = mp.cpu_count()
    
    if max_workers is None:
        max_workers = cpu_count
    
    # タスク数が少ない場合は並列化しない
    if n_tasks <= 1:
        return 1
    
    # CPU数とタスク数の最小値
    n_jobs = min(n_tasks, max_workers, cpu_count)
    
    return max(1, n_jobs)


def parallel_map(
    func: Callable,
    items: List[Any],
    n_jobs: Optional[int] = None,
    verbose: bool = True,
    backend: str = 'threading',
    **kwargs
) -> List[Any]:
    """
    関数を並列実行してリストにマッピング。
    
    Parameters
    ----------
    func : callable
        実行する関数
    items : list
        処理するアイテムのリスト
    n_jobs : int, optional
        並列ワーカー数（Noneの場合は自動決定）
    verbose : bool
        進捗表示
    backend : str
        'threading' または 'multiprocessing'
    **kwargs
        関数に渡す追加引数
    
    Returns
    -------
    results : list
        処理結果のリスト
    """
    if len(items) == 0:
        return []
    
    if n_jobs is None:
        n_jobs = get_optimal_n_jobs(len(items))
    
    if n_jobs == 1:
        # 並列化しない場合
        if verbose:
            results = [func(item, **kwargs) for item in tqdm(items, desc="Processing")]
        else:
            results = [func(item, **kwargs) for item in items]
    else:
        # 並列実行
        if verbose:
            results = Parallel(n_jobs=n_jobs, backend=backend, verbose=0)(
                delayed(func)(item, **kwargs) for item in tqdm(items, desc="Processing")
            )
        else:
            results = Parallel(n_jobs=n_jobs, backend=backend, verbose=0)(
                delayed(func)(item, **kwargs) for item in items
            )
    
    return results


def parallel_batch_analysis(
    analysis_func: Callable,
    data_dict: Dict[str, Any],
    n_jobs: Optional[int] = None,
    verbose: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    バッチ解析を並列実行。
    
    Parameters
    ----------
    analysis_func : callable
        解析関数（data, **kwargs）を受け取り結果を返す
    data_dict : dict
        {name: data} の辞書
    n_jobs : int, optional
        並列ワーカー数
    verbose : bool
        進捗表示
    **kwargs
        解析関数に渡す追加引数
    
    Returns
    -------
    results : dict
        {name: result} の辞書
    """
    if len(data_dict) == 0:
        return {}
    
    if n_jobs is None:
        n_jobs = get_optimal_n_jobs(len(data_dict))
    
    # タスクを準備
    tasks = [(name, data) for name, data in data_dict.items()]
    
    def process_task(task):
        name, data = task
        try:
            result = analysis_func(data, **kwargs)
            return name, result
        except Exception as e:
            warnings.warn(f"Error processing {name}: {e}")
            return name, None
    
    # 並列実行
    if n_jobs == 1:
        if verbose:
            results_list = [process_task(task) for task in tqdm(tasks, desc="Batch analysis")]
        else:
            results_list = [process_task(task) for task in tasks]
    else:
        if verbose:
            results_list = Parallel(n_jobs=n_jobs, backend='multiprocessing', verbose=0)(
                delayed(process_task)(task) for task in tqdm(tasks, desc="Batch analysis")
            )
        else:
            results_list = Parallel(n_jobs=n_jobs, backend='multiprocessing', verbose=0)(
                delayed(process_task)(task) for task in tasks
            )
    
    # 結果を辞書に変換
    results = {name: result for name, result in results_list if result is not None}
    
    return results


def vectorized_distance_matrix(
    coords1: np.ndarray,
    coords2: Optional[np.ndarray] = None,
    max_distance: Optional[float] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    ベクトル化された距離行列計算（メモリ効率的）。
    
    Parameters
    ----------
    coords1 : np.ndarray
        座標配列 (N, 2)
    coords2 : np.ndarray, optional
        座標配列 (M, 2)（Noneの場合はcoords1同士）
    max_distance : float, optional
        最大距離（この距離を超えるペアは計算しない）
    
    Returns
    -------
    distances : np.ndarray
        距離配列
    indices : np.ndarray
        インデックス配列 (i, j)
    """
    if coords2 is None:
        coords2 = coords1
    
    n1, n2 = len(coords1), len(coords2)
    
    # メモリ効率的な計算
    if max_distance is not None:
        # KDTreeを使用して近接ペアのみ計算
        from scipy.spatial import cKDTree
        
        tree = cKDTree(coords1)
        if coords2 is coords1:
            pairs = tree.query_pairs(max_distance, output_type='ndarray')
            if len(pairs) == 0:
                return np.array([]), np.array([])
            distances = np.linalg.norm(
                coords1[pairs[:, 0]] - coords1[pairs[:, 1]],
                axis=1
            )
            return distances, pairs
        else:
            # 異なる座標セットの場合
            distances_list = []
            indices_list = []
            for i, coord in enumerate(coords2):
                indices = tree.query_ball_point(coord, max_distance)
                if len(indices) > 0:
                    dists = np.linalg.norm(coords1[indices] - coord, axis=1)
                    distances_list.extend(dists)
                    indices_list.extend([(idx, i) for idx in indices])
            if len(distances_list) == 0:
                return np.array([]), np.array([])
            return np.array(distances_list), np.array(indices_list)
    else:
        # 全ペアを計算（メモリ使用量に注意）
        if n1 * n2 > 1e6:
            warnings.warn(
                f"Large distance matrix ({n1} x {n2} = {n1*n2} pairs). "
                "Consider using max_distance parameter."
            )
        
        # ブロックごとに計算してメモリ使用量を抑制
        block_size = 1000
        distances_list = []
        indices_list = []
        
        for i in range(0, n1, block_size):
            end_i = min(i + block_size, n1)
            block1 = coords1[i:end_i]
            
            for j in range(0, n2, block_size):
                end_j = min(j + block_size, n2)
                block2 = coords2[j:end_j]
                
                # 距離を計算
                diff = block1[:, np.newaxis, :] - block2[np.newaxis, :, :]
                block_distances = np.linalg.norm(diff, axis=2)
                
                # インデックスと距離を保存
                for ii, idx_i in enumerate(range(i, end_i)):
                    for jj, idx_j in enumerate(range(j, end_j)):
                        distances_list.append(block_distances[ii, jj])
                        indices_list.append((idx_i, idx_j))
        
        return np.array(distances_list), np.array(indices_list)


def cached_computation(
    cache_key: str,
    compute_func: Callable,
    cache_dir: Optional[str] = None,
    force_recompute: bool = False,
    **kwargs
) -> Any:
    """
    計算結果をキャッシュするデコレータ風の関数。
    
    Parameters
    ----------
    cache_key : str
        キャッシュキー
    compute_func : callable
        計算関数
    cache_dir : str, optional
        キャッシュディレクトリ
    force_recompute : bool
        強制的に再計算
    **kwargs
        計算関数に渡す引数
    
    Returns
    -------
    result : Any
        計算結果
    """
    import pickle
    from pathlib import Path
    
    if cache_dir and not force_recompute:
        cache_path = Path(cache_dir) / f"{cache_key}.pkl"
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                warnings.warn(f"Failed to load cache: {e}")
    
    # 計算実行
    result = compute_func(**kwargs)
    
    # キャッシュ保存
    if cache_dir:
        cache_path = Path(cache_dir) / f"{cache_key}.pkl"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            warnings.warn(f"Failed to save cache: {e}")
    
    return result


# Example usage
if __name__ == "__main__":
    # テスト
    def test_func(x):
        return x ** 2
    
    items = list(range(10))
    results = parallel_map(test_func, items, n_jobs=2, verbose=True)
    print(f"Results: {results}")
