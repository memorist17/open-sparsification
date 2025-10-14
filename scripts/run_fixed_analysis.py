#!/usr/bin/env python3
"""
修正された分析を実行するスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.utils.logger import get_logger
from scripts.generate_real_sample_data_fixed import generate_real_sample_data

logger = get_logger(__name__)

def main():
    """修正された分析を実行"""
    logger.info("修正された実際の地理データ分析を開始")
    
    try:
        # 実際の地理データから指標を計算
        generate_real_sample_data()
        logger.info("分析完了")
        
    except Exception as e:
        logger.error(f"分析エラー: {e}")
        raise

if __name__ == "__main__":
    main()

