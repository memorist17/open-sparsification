"""
ログ設定ユーティリティ

アプリケーション全体で統一されたログ設定を提供します。
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_size: str = "10MB",
    backup_count: int = 5
) -> None:
    """
    ログ設定を初期化する
    
    Args:
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR)
        log_file: ログファイルのパス
        max_size: ログファイルの最大サイズ
        backup_count: ローテーション時のバックアップ数
    """
    # 既存のハンドラーをクリア
    logger.remove()
    
    # コンソール出力の設定
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True
    )
    
    # ファイル出力の設定（指定された場合）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=max_size,
            retention=backup_count,
            compression="zip"
        )


def get_logger(name: str) -> logging.Logger:
    """
    指定された名前のロガーを取得する
    
    Args:
        name: ロガー名
        
    Returns:
        Loggerインスタンス
    """
    return logger.bind(name=name)


def configure_logger_from_config() -> None:
    """
    設定ファイルからログ設定を読み込んで適用する
    """
    try:
        from .config import get_config
        
        log_config = get_config("logging")
        setup_logger(
            log_level=log_config.get("level", "INFO"),
            log_file=log_config.get("file"),
            max_size=log_config.get("max_size", "10MB"),
            backup_count=log_config.get("backup_count", 5)
        )
    except Exception as e:
        # 設定ファイルの読み込みに失敗した場合はデフォルト設定を使用
        logger.warning(f"設定ファイルからのログ設定読み込みに失敗: {e}")
        setup_logger()


# デフォルトでログ設定を初期化
configure_logger_from_config()
