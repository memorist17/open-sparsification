"""
設定ファイル読み込みユーティリティ

parameters.ymlから設定を読み込み、アプリケーション全体で
使用できるようにします。
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        設定管理クラスの初期化
        
        Args:
            config_path: 設定ファイルのパス（デフォルト: config/parameters.yml）
        """
        if config_path is None:
            # プロジェクトルートからの相対パス
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "parameters.yml"
        
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> Dict[str, Any]:
        """
        設定ファイルを読み込む
        
        Returns:
            設定辞書
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            yaml.YAMLError: YAMLファイルの解析エラー
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            return self._config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"YAMLファイルの解析エラー: {e}")
    
    def get_config(self, key: Optional[str] = None) -> Any:
        """
        設定値を取得する
        
        Args:
            key: 取得する設定のキー（例: 'data.source'）
                 Noneの場合は全設定を返す
        
        Returns:
            設定値
            
        Raises:
            KeyError: 指定されたキーが存在しない場合
        """
        if self._config is None:
            self.load_config()
        
        if key is None:
            return self._config
        
        # ドット記法でのネストしたキーアクセス
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if not isinstance(value, dict) or k not in value:
                raise KeyError(f"設定キーが見つかりません: {key}")
            value = value[k]
        
        return value
    
    def update_config(self, key: str, value: Any) -> None:
        """
        設定値を更新する
        
        Args:
            key: 更新する設定のキー
            value: 新しい値
        """
        if self._config is None:
            self.load_config()
        
        keys = key.split('.')
        config = self._config
        
        # ネストした辞書の最後のキー以外を取得
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 最後のキーに値を設定
        config[keys[-1]] = value
    
    def save_config(self, output_path: Optional[str] = None) -> None:
        """
        設定をファイルに保存する
        
        Args:
            output_path: 保存先パス（デフォルト: 元の設定ファイル）
        """
        if self._config is None:
            raise ValueError("保存する設定がありません")
        
        save_path = Path(output_path) if output_path else self.config_path
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)


# グローバル設定インスタンス
_config_manager = ConfigManager()


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    設定ファイルを読み込む（グローバル関数）
    
    Args:
        config_path: 設定ファイルのパス
        
    Returns:
        設定辞書
    """
    global _config_manager
    if config_path:
        _config_manager = ConfigManager(config_path)
    return _config_manager.load_config()


def get_config(key: Optional[str] = None) -> Any:
    """
    設定値を取得する（グローバル関数）
    
    Args:
        key: 取得する設定のキー
        
    Returns:
        設定値
    """
    return _config_manager.get_config(key)


def update_config(key: str, value: Any) -> None:
    """
    設定値を更新する（グローバル関数）
    
    Args:
        key: 更新する設定のキー
        value: 新しい値
    """
    _config_manager.update_config(key, value)


def save_config(output_path: Optional[str] = None) -> None:
    """
    設定をファイルに保存する（グローバル関数）
    
    Args:
        output_path: 保存先パス
    """
    _config_manager.save_config(output_path)
