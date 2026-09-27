#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Swiss Ephemeris (pyswisseph) 動作テスト
"""
import swisseph as swe
from datetime import datetime

def test_pyswisseph():
    print("=" * 60)
    print("Swiss Ephemeris (pyswisseph) 動作テスト")
    print("=" * 60)
    
    # エフェメリスファイルのパスを設定
    swe.set_ephe_path('/home/user/webapp/swisseph_data')
    
    # テストデータ: 1990年3月21日 15:30 UTC
    year, month, day = 1990, 3, 21
    hour = 15.5  # 15:30
    
    # ユリウス日の計算
    jd = swe.julday(year, month, day, hour)
    print(f"\n📅 テスト日時: {year}/{month}/{day} {hour}:00 UTC")
    print(f"   ユリウス日: {jd}")
    
    # 太陽の位置
    print("\n☀️ 太陽:")
    sun = swe.calc_ut(jd, swe.SUN)[0]
    print(f"   黄経: {sun[0]:.6f}°")
    print(f"   黄緯: {sun[1]:.6f}°")
    print(f"   距離: {sun[2]:.6f} AU")
    print(f"   速度: {sun[3]:.6f}°/日")
    
    # 月の位置
    print("\n🌙 月:")
    moon = swe.calc_ut(jd, swe.MOON)[0]
    print(f"   黄経: {moon[0]:.6f}°")
    print(f"   黄緯: {moon[1]:.6f}°")
    print(f"   距離: {moon[2]:.6f} AU")
    print(f"   速度: {moon[3]:.6f}°/日")
    
    # 水星の位置
    print("\n☿️ 水星:")
    mercury = swe.calc_ut(jd, swe.MERCURY)[0]
    print(f"   黄経: {mercury[0]:.6f}°")
    print(f"   逆行: {'Yes' if mercury[3] < 0 else 'No'}")
    
    # カイロン
    print("\n⚷ カイロン:")
    chiron = swe.calc_ut(jd, swe.CHIRON)[0]
    print(f"   黄経: {chiron[0]:.6f}°")
    
    # ドラゴンヘッド（True Node）
    print("\n☊ ドラゴンヘッド (True Node):")
    true_node = swe.calc_ut(jd, swe.TRUE_NODE)[0]
    print(f"   黄経: {true_node[0]:.6f}°")
    
    # ハウス計算（Placidus, 東京）
    print("\n🏠 ハウスカスプ (Placidus, 東京):")
    lat, lon = 35.6762, 139.6503
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')  # 'P' = Placidus
    print(f"   ASC (上昇点): {ascmc[0]:.6f}°")
    print(f"   MC (天頂): {ascmc[1]:.6f}°")
    print(f"   ARMC: {ascmc[2]:.6f}°")
    print(f"   第1ハウス: {cusps[1]:.6f}°")
    print(f"   第10ハウス: {cusps[10]:.6f}°")
    
    print("\n✅ すべてのテストが成功しました！")
    print("=" * 60)

if __name__ == '__main__':
    test_pyswisseph()
