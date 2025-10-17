#!/usr/bin/env python3
"""
ダッシュボード設定の読み込みと管理

設計思想: ⚙️ 設定駆動 (Configuration-Driven)
- すべての設定値を外部YAMLファイルから読み込み
- コード変更なしでダッシュボードの見た目や動作をカスタマイズ可能
"""

from pathlib import Path
from typing import Any, Dict, List
import yaml


class DashboardConfig:
    """ダッシュボード設定を管理するクラス"""
    
    def __init__(self, config_path: Path = None):
        """
        設定ファイルを読み込む
        
        Args:
            config_path: 設定ファイルのパス（省略時はデフォルトパス）
        """
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "dashboard.yml"
        
        self.config_path = config_path
        self._config = self._load_config()
        self.project_root = Path(__file__).parent.parent.parent
    
    def _load_config(self) -> Dict[str, Any]:
        """YAMLファイルから設定を読み込む"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    # === 指標関連 ===
    
    @property
    def metric_columns(self) -> List[str]:
        """表示する指標のリスト"""
        return self._config["metrics"]["display_order"]
    
    @property
    def metric_labels(self) -> Dict[str, str]:
        """指標の日本語ラベル"""
        return self._config["metrics"]["labels"]
    
    @property
    def metric_descriptions(self) -> Dict[str, str]:
        """指標の説明文"""
        return self._config["metrics"]["descriptions"]
    
    def get_metric_label(self, metric: str) -> str:
        """指標名から日本語ラベルを取得"""
        return self.metric_labels.get(metric, metric)
    
    # === ペアプロット設定 ===
    
    @property
    def scatter_size(self) -> int:
        """散布図のマーカーサイズ"""
        return self._config["pairplot"]["style"]["scatter"]["size"]
    
    @property
    def scatter_color(self) -> str:
        """散布図のマーカー色"""
        return self._config["pairplot"]["style"]["scatter"]["color"]
    
    @property
    def scatter_line_width(self) -> float:
        """散布図のマーカー線幅"""
        return self._config["pairplot"]["style"]["scatter"]["line_width"]
    
    @property
    def histogram_bins(self) -> int:
        """ヒストグラムのビン数"""
        return self._config["pairplot"]["style"]["histogram"]["bins"]
    
    @property
    def histogram_color(self) -> str:
        """ヒストグラムの色"""
        return self._config["pairplot"]["style"]["histogram"]["color"]
    
    @property
    def histogram_opacity(self) -> float:
        """ヒストグラムの透明度"""
        return self._config["pairplot"]["style"]["histogram"]["opacity"]
    
    @property
    def highlight_size(self) -> int:
        """ハイライトマーカーのサイズ"""
        return self._config["pairplot"]["style"]["highlight"]["size"]
    
    @property
    def highlight_color(self) -> str:
        """ハイライトマーカーの色"""
        return self._config["pairplot"]["style"]["highlight"]["color"]
    
    @property
    def highlight_line_color(self) -> str:
        """ハイライトマーカーの線色"""
        return self._config["pairplot"]["style"]["highlight"]["line_color"]
    
    @property
    def highlight_line_width(self) -> int:
        """ハイライトマーカーの線幅"""
        return self._config["pairplot"]["style"]["highlight"]["line_width"]
    
    @property
    def highlight_marker_color(self) -> str:
        """ハイライトマーカーの強調色"""
        return self._config["pairplot"]["style"]["highlight"]["marker_color"]
    
    @property
    def highlight_line_width_accent(self) -> int:
        """ハイライトラインの幅"""
        return self._config["pairplot"]["style"]["highlight"]["line_width_accent"]
    
    # === レイアウト設定 ===
    
    @property
    def height_per_metric(self) -> int:
        """指標あたりの高さ"""
        return self._config["pairplot"]["layout"]["height_per_metric"]
    
    @property
    def base_height(self) -> int:
        """ベース高さ"""
        return self._config["pairplot"]["layout"]["base_height"]
    
    @property
    def horizontal_spacing(self) -> float:
        """水平方向の間隔"""
        return self._config["pairplot"]["layout"]["spacing"]["horizontal"]
    
    @property
    def vertical_spacing(self) -> float:
        """垂直方向の間隔"""
        return self._config["pairplot"]["layout"]["spacing"]["vertical"]
    
    @property
    def margin_dict(self) -> Dict[str, int]:
        """マージン設定"""
        return self._config["pairplot"]["layout"]["margin"]
    
    # === 区切り線設定 ===
    
    @property
    def separator_enabled(self) -> bool:
        """区切り線を表示するか"""
        return self._config["pairplot"]["separator"]["enabled"]
    
    @property
    def separator_color(self) -> str:
        """区切り線の色"""
        return self._config["pairplot"]["separator"]["color"]
    
    @property
    def separator_width(self) -> float:
        """区切り線の幅"""
        return self._config["pairplot"]["separator"]["width"]
    
    @property
    def separator_layer(self) -> str:
        """区切り線のレイヤー"""
        return self._config["pairplot"]["separator"]["layer"]
    
    # === Dashアプリ設定 ===
    
    @property
    def server_host(self) -> str:
        """サーバーホスト"""
        return self._config["dash_app"]["server"]["host"]
    
    @property
    def server_port(self) -> int:
        """サーバーポート"""
        return self._config["dash_app"]["server"]["port"]
    
    @property
    def server_debug(self) -> bool:
        """デバッグモード"""
        return self._config["dash_app"]["server"]["debug"]
    
    @property
    def app_title(self) -> str:
        """アプリタイトル"""
        return self._config["dash_app"]["title"]
    
    @property
    def app_subtitle(self) -> str:
        """アプリサブタイトル"""
        return self._config["dash_app"]["subtitle"]
    
    @property
    def overlay_style(self) -> Dict[str, Any]:
        """オーバーレイのスタイル"""
        pos = self._config["dash_app"]["overlay"]["position"]
        width = self._config["dash_app"]["overlay"]["width"]
        style = self._config["dash_app"]["overlay"]["style"]
        
        return {
            "position": "absolute",
            "top": f"{pos['top']}px",
            "right": f"{pos['right']}px",
            "width": f"{width}px",
            "backgroundColor": style["background_color"],
            "border": style["border"],
            "borderRadius": f"{style['border_radius']}px",
            "boxShadow": style["box_shadow"],
            "padding": f"{style['padding']}px",
            "display": "flex",
            "flexDirection": "column",
            "gap": "10px",
            "boxSizing": "border-box",
        }
    
    @property
    def overlay_title(self) -> str:
        """オーバーレイタイトル"""
        return self._config["dash_app"]["messages"]["overlay_title"]
    
    @property
    def overlay_instruction(self) -> str:
        """オーバーレイの説明"""
        return self._config["dash_app"]["messages"]["overlay_instruction"]
    
    @property
    def awaiting_selection(self) -> str:
        """選択待機メッセージ"""
        return self._config["dash_app"]["messages"]["awaiting_selection"]
    
    @property
    def normalization_note(self) -> str:
        """正規化の注記"""
        return self._config["dash_app"]["messages"]["normalization_note"]
    
    # === データパス ===
    
    @property
    def analysis_results_path(self) -> Path:
        """分析結果CSVのパス"""
        return self.project_root / self._config["data_paths"]["analysis_results"]
    
    @property
    def network_overviews_dir(self) -> Path:
        """ネットワーク概要画像ディレクトリのパス"""
        return self.project_root / self._config["data_paths"]["network_overviews"]
    
    @property
    def pairplot_image_path(self) -> Path:
        """ペアプロット画像のパス"""
        return self.project_root / self._config["data_paths"]["pairplot_image"]


# シングルトンインスタンス
_config_instance = None


def get_dashboard_config() -> DashboardConfig:
    """
    ダッシュボード設定のシングルトンインスタンスを取得
    
    Returns:
        DashboardConfig: 設定オブジェクト
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = DashboardConfig()
    return _config_instance

