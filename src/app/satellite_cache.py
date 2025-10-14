#!/usr/bin/env python3
"""
衛星画像キャッシュシステム
事前に画像を取得・保存して即座に表示
"""

import requests
import io
import math
import base64
from PIL import Image
import numpy as np
from pathlib import Path
import logging
import time
import json
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class SatelliteImageCache:
    """衛星画像キャッシュシステム"""
    
    def __init__(self, cache_dir: Path = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "satellite_cache"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 複数のタイルサーバーを用意（フォールバック用）
        self.tile_servers = [
            "https://tile.openstreetmap.org",
            "https://tile.openstreetmap.org",  # バックアップ
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OpenSparsity/1.0 (Research Project)'
        })
        self.timeout = 15
        self.retry_delay = 1
        
    def deg2num(self, lat_deg, lon_deg, zoom):
        """緯度経度をタイル座標に変換"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y
    
    def get_cache_path(self, lat, lon, zoom=15, radius=None, bounds=None):
        """キャッシュファイルのパスを取得"""
        lat_key = f"{lat:.6f}"
        lon_key = f"{lon:.6f}"
        if bounds is not None:
            bounds_key = "_b_" + "_".join(f"{val:.6f}" for val in bounds)
        elif radius is not None:
            bounds_key = f"_{int(radius)}"
        else:
            bounds_key = ""
        return self.cache_dir / f"tile_{zoom}_{lat_key}_{lon_key}{bounds_key}.png"
    
    def num2deg(self, x, y, zoom):
        """タイル座標を緯度経度に変換"""
        n = 2.0 ** zoom
        lon_deg = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat_deg = math.degrees(lat_rad)
        return lat_deg, lon_deg

    def get_tile_with_retry(self, zoom: int, x: int, y: int):
        """リトライ機能付きタイル取得"""
        for server_idx, base_url in enumerate(self.tile_servers):
            try:
                url = f"{base_url}/{zoom}/{x}/{y}.png"
                response = self.session.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    return Image.open(io.BytesIO(response.content))
                elif response.status_code == 404:
                    logger.debug(f"タイル {zoom}/{x}/{y} は存在しません")
                    continue
                else:
                    logger.warning(f"タイル取得失敗: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"サーバー {server_idx} でタイル取得エラー: {e}")
                if server_idx < len(self.tile_servers) - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logger.error(f"全サーバーでタイル取得失敗: {e}")
                    return None
        
        return None
    
    def latlon_to_pixel(self, lat: float, lon: float, zoom: int) -> Tuple[float, float]:
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = (lon + 180.0) / 360.0 * n * 256.0
        y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * 256.0
        return x, y

    def estimate_zoom(self, lat: float, radius_m: int) -> int:
        meters_per_pixel_zoom0 = 156543.03392 * math.cos(math.radians(lat))
        target_m_per_px = max(radius_m * 2 / 256.0, 1.0)
        zoom = int(max(0, min(18, math.log2(meters_per_pixel_zoom0 / target_m_per_px))))
        return zoom

    def estimate_zoom_from_bounds(self, lat: float, width_m: float, height_m: float, size: Tuple[int, int]) -> int:
        meters_per_pixel_zoom0 = 156543.03392 * math.cos(math.radians(lat))
        target_m_per_px = max(width_m / size[0], height_m / size[1], 1.0)
        zoom = int(max(0, min(18, math.log2(meters_per_pixel_zoom0 / target_m_per_px))))
        return zoom

    def get_or_create_satellite_image(
        self,
        lat,
        lon,
        radius_m=1000,
        zoom=None,
        size=(400, 400),
        bounds: Optional[Tuple[float, float, float, float]] = None,
        width_m: Optional[float] = None,
        height_m: Optional[float] = None,
    ):
        """衛星画像を取得またはキャッシュから読み込み"""
        if bounds is not None:
            west, south, east, north = bounds
            lat = (south + north) / 2.0
            lon = (west + east) / 2.0
            if width_m is None or height_m is None:
                width_m = width_m or radius_m * 2
                height_m = height_m or radius_m * 2
            if zoom is None:
                zoom = self.estimate_zoom_from_bounds(lat, width_m, height_m, size)
        else:
            if zoom is None:
                zoom = self.estimate_zoom(lat, radius_m)

        cache_path = self.get_cache_path(lat, lon, zoom, radius=radius_m if bounds is None else None, bounds=bounds)

        # キャッシュが存在する場合は読み込み
        if cache_path.exists():
            try:
                img = Image.open(cache_path)
                img = img.resize(size, Image.Resampling.LANCZOS)
                return img, zoom
            except Exception as e:
                logger.warning(f"キャッシュ読み込みエラー: {e}")
                cache_path.unlink()  # 破損したキャッシュを削除

        if bounds is None:
            lat_offset = radius_m / 111000.0
            lon_offset = radius_m / (111000.0 * math.cos(math.radians(lat)))

            north = lat + lat_offset
            south = lat - lat_offset
            east = lon + lon_offset
            west = lon - lon_offset
        else:
            west, south, east, north = bounds

        # ピクセル範囲を計算
        px_west, py_north = self.latlon_to_pixel(north, west, zoom)
        px_east, py_south = self.latlon_to_pixel(south, east, zoom)

        tile_x_min = int(px_west // 256)
        tile_x_max = int(px_east // 256)
        tile_y_min = int(py_north // 256)
        tile_y_max = int(py_south // 256)

        stitched_width = (tile_x_max - tile_x_min + 1) * 256
        stitched_height = (tile_y_max - tile_y_min + 1) * 256
        stitched = Image.new('RGB', (stitched_width, stitched_height))

        for tx in range(tile_x_min, tile_x_max + 1):
            for ty in range(tile_y_min, tile_y_max + 1):
                tile_img = self.get_tile_with_retry(zoom, tx, ty)
                if tile_img is None:
                    continue
                offset_x = (tx - tile_x_min) * 256
                offset_y = (ty - tile_y_min) * 256
                stitched.paste(tile_img, (offset_x, offset_y))

        crop_left = int(px_west - tile_x_min * 256)
        crop_top = int(py_north - tile_y_min * 256)
        crop_right = int(px_east - tile_x_min * 256)
        crop_bottom = int(py_south - tile_y_min * 256)

        cropped = stitched.crop((crop_left, crop_top, crop_right, crop_bottom))
        resized = cropped.resize(size, Image.Resampling.LANCZOS)

        try:
            resized.save(cache_path, 'PNG')
            logger.info(f"タイルをキャッシュに保存: {cache_path}")
        except Exception as e:
            logger.warning(f"キャッシュ保存エラー: {e}")

        return resized, zoom
    
    def get_satellite_image_base64(self, lat, lon, radius_m=1000, zoom=None, size=(400, 400)):
        """衛星画像をbase64エンコードして返す"""
        img, zoom = self.get_or_create_satellite_image(lat, lon, radius_m=radius_m, zoom=zoom, size=size)
        if img:
            # オーバーレイ用の透明レイヤーを作成
            overlay = Image.new('RGBA', size, (0, 0, 0, 0))
            
            # 中心点をマーク
            center_x, center_y = size[0] // 2, size[1] // 2
            
            # 中心点にマーカーを描画
            from PIL import ImageDraw
            draw = ImageDraw.Draw(overlay)
            draw.ellipse([center_x-8, center_y-8, center_x+8, center_y+8], 
                        fill=(255, 0, 0, 200), outline=(255, 255, 255, 255), width=2)
            
            # 画像を合成
            img_rgba = img.convert('RGBA')
            combined = Image.alpha_composite(img_rgba, overlay)
            
            # base64エンコード
            buffer = io.BytesIO()
            combined.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
        
        return None
    
    def preload_satellite_images(self, locations: list, radius_m=1000, zoom=None):
        """複数地点の衛星画像を事前に取得"""
        logger.info(f"衛星画像の事前取得開始: {len(locations)}地点")

        successful = 0
        failed = 0

        for i, (lat, lon) in enumerate(locations):
            try:
                logger.info(f"事前取得中: {i+1}/{len(locations)} - 緯度: {lat:.3f}, 経度: {lon:.3f}")

                img, _ = self.get_or_create_satellite_image(lat, lon, radius_m=radius_m, zoom=zoom)
                if img:
                    successful += 1
                else:
                    failed += 1
                
                # レート制限対策
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"地点 {i+1} の事前取得エラー: {e}")
                failed += 1
        
        logger.info(f"事前取得完了: 成功 {successful}件, 失敗 {failed}件")
        return successful, failed

# グローバルインスタンス
satellite_cache = SatelliteImageCache()
