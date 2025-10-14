#!/usr/bin/env python3
"""
OpenStreetMapタイル取得ユーティリティ
"""

import requests
import io
import math
import base64
from PIL import Image
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class OpenStreetMapTileFetcher:
    """OpenStreetMapタイルを取得するクラス"""
    
    def __init__(self):
        self.base_url = "https://tile.openstreetmap.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OpenSparsity/1.0 (Research Project)'
        })
        self.timeout = 10
        
    def deg2num(self, lat_deg, lon_deg, zoom):
        """緯度経度をタイル座標に変換"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y
    
    def get_tile_image(self, lat, lon, zoom=15):
        """指定された緯度経度のタイル画像を取得"""
        try:
            x, y = self.deg2num(lat, lon, zoom)
            url = f"{self.base_url}/{zoom}/{x}/{y}.png"
            
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            else:
                logger.warning(f"タイル取得失敗: {url} (HTTP {response.status_code})")
                return None
        except Exception as e:
            logger.error(f"タイル取得エラー: {e}")
            return None
    
    def get_satellite_image_base64(self, lat, lon, zoom=15):
        """衛星画像をbase64エンコードして返す"""
        img = self.get_tile_image(lat, lon, zoom)
        if img:
            # 画像をリサイズ（表示用）
            img = img.resize((400, 400), Image.Resampling.LANCZOS)
            
            # base64エンコード
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            return img_base64
        return None
    
    def create_satellite_overlay(self, lat, lon, zoom=15, size=(400, 400)):
        """衛星画像とオーバーレイを作成"""
        img = self.get_tile_image(lat, lon, zoom)
        if img:
            # リサイズ
            img = img.resize(size, Image.Resampling.LANCZOS)
            
            # オーバーレイ用の透明レイヤーを作成
            overlay = Image.new('RGBA', size, (0, 0, 0, 0))
            
            # 中心点をマーク
            center_x, center_y = size[0] // 2, size[1] // 2
            
            # 中心点にマーカーを描画
            from PIL import ImageDraw
            draw = ImageDraw.Draw(overlay)
            draw.ellipse([center_x-5, center_y-5, center_x+5, center_y+5], 
                        fill=(255, 0, 0, 200), outline=(255, 255, 255, 255))
            
            # 画像を合成
            img_rgba = img.convert('RGBA')
            combined = Image.alpha_composite(img_rgba, overlay)
            
            # base64エンコード
            buffer = io.BytesIO()
            combined.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
        
        return None

# グローバルインスタンス
tile_fetcher = OpenStreetMapTileFetcher()
