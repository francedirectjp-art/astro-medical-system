#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rectification API — 出生時刻レクティフィケーション用エンドポイント

astro-rectify (francedirectjp-art/astro-rectify) のバックエンド。
既存 swisseph_api の Placidus/天体計算基盤を活用し、以下の 4 endpoint を提供:

  POST /api/rectification/scan             — 候補時刻 sweep + 3 技法統合スコア
  POST /api/rectification/primary-directions — 単一時刻の Primary Directions 一覧
  POST /api/rectification/asc-probability   — 身体・性格特徴から ASC 確率分布
  GET  /api/rectification/event-types       — イベント種別マスター

計算アルゴリズム:
  1. Primary Directions (Placidus semi-arc, Naibod key 0.9856°/year)
  2. Solar Arc Directions (sun mean motion ~ 0.9856°/day = 1°/year)
  3. Secondary Progressions (1 day = 1 year)

参考仕様: astro-rectify/docs/api/rectification-api-spec.md
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta
from typing import Any
import os
import math

rectification_api = Blueprint("rectification_api", __name__)

# ─────────────────────────────────────────────
# Ephemeris path setup
# ─────────────────────────────────────────────
EPHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "swisseph_data"
)
if os.path.exists(EPHE_PATH):
    swe.set_ephe_path(EPHE_PATH)

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
SIGN_KEYS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
]

PLANETS = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
    "north_node": swe.TRUE_NODE,
}

# Major aspects (angle, orb, weight)
ASPECTS = {
    "conjunction": (0.0, 8.0, 1.0),
    "opposition":  (180.0, 8.0, 1.0),
    "square":      (90.0, 7.0, 0.9),
    "trine":       (120.0, 7.0, 0.85),
    "sextile":     (60.0, 5.0, 0.7),
    "quincunx":    (150.0, 3.0, 0.4),
}

# Naibod key: mean daily solar motion (deg/day) ≒ deg/year in symbolic direction
NAIBOD_KEY = 0.9856473

# Prefecture coord table (subset for MVP — extend via atlas_lib in prod)
PREFECTURES: dict[str, tuple[float, float]] = {
    "北海道": (43.0642, 141.3469),
    "青森県": (40.8244, 140.7400),
    "岩手県": (39.7036, 141.1527),
    "宮城県": (38.2682, 140.8721),
    "秋田県": (39.7186, 140.1022),
    "山形県": (38.2404, 140.3633),
    "福島県": (37.7503, 140.4677),
    "茨城県": (36.3418, 140.4468),
    "栃木県": (36.5658, 139.8836),
    "群馬県": (36.3906, 139.0608),
    "埼玉県": (35.8617, 139.6455),
    "千葉県": (35.6074, 140.1065),
    "東京都": (35.6762, 139.6503),
    "神奈川県": (35.4478, 139.6425),
    "新潟県": (37.9026, 139.0232),
    "富山県": (36.6959, 137.2137),
    "石川県": (36.5946, 136.6256),
    "福井県": (36.0652, 136.2216),
    "山梨県": (35.6642, 138.5681),
    "長野県": (36.6513, 138.1809),
    "岐阜県": (35.3912, 136.7223),
    "静岡県": (34.9756, 138.3827),
    "愛知県": (35.1802, 136.9066),
    "三重県": (34.7302, 136.5086),
    "滋賀県": (35.0045, 135.8686),
    "京都府": (35.0211, 135.7556),
    "大阪府": (34.6937, 135.5023),
    "兵庫県": (34.6913, 135.1830),
    "奈良県": (34.6851, 135.8329),
    "和歌山県": (34.2260, 135.1675),
    "鳥取県": (35.5039, 134.2377),
    "島根県": (35.4723, 133.0505),
    "岡山県": (34.6618, 133.9350),
    "広島県": (34.3966, 132.4596),
    "山口県": (34.1859, 131.4706),
    "徳島県": (34.0658, 134.5593),
    "香川県": (34.3401, 134.0434),
    "愛媛県": (33.8416, 132.7660),
    "高知県": (33.5597, 133.5311),
    "福岡県": (33.6064, 130.4181),
    "佐賀県": (33.2494, 130.2989),
    "長崎県": (32.7448, 129.8737),
    "熊本県": (32.7898, 130.7417),
    "大分県": (33.2382, 131.6126),
    "宮崎県": (31.9111, 131.4239),
    "鹿児島県": (31.5602, 130.5581),
    "沖縄県": (26.2124, 127.6810),
}

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _normalize_lon(deg: float) -> float:
    return deg % 360.0

def _angular_diff(a: float, b: float) -> float:
    """Smallest angle between two longitudes (0..180)."""
    return abs((a - b + 180.0) % 360.0 - 180.0)

def _sign_index(longitude: float) -> int:
    return int(_normalize_lon(longitude) // 30)

def _sign_key(longitude: float) -> str:
    return SIGN_KEYS[_sign_index(longitude)]

def _degree_in_sign(longitude: float) -> float:
    return _normalize_lon(longitude) % 30.0

def _jd_from_datetime_jst(dt: datetime) -> float:
    """Convert JST datetime → Julian Day (UT)."""
    utc = dt - timedelta(hours=9)
    return swe.julday(
        utc.year, utc.month, utc.day, utc.hour + utc.minute / 60.0
    )

def _planet_longitude(jd: float, planet_id: int) -> float:
    swe.set_ephe_path(EPHE_PATH)
    res, _flag = swe.calc_ut(jd, planet_id)
    return _normalize_lon(res[0])

def _houses_and_angles(jd: float, lat: float, lon: float) -> tuple[list[float], float, float]:
    cusps, ascmc = swe.houses(jd, lat, lon, b"P")
    asc = _normalize_lon(ascmc[0])
    mc = _normalize_lon(ascmc[1])
    return list(cusps), asc, mc

def _lookup_prefecture(name: str) -> tuple[float, float] | None:
    return PREFECTURES.get(name)


# ─────────────────────────────────────────────
# Scoring helpers
# ─────────────────────────────────────────────

def _date_proximity_score(delta_days: int) -> float:
    a = abs(delta_days)
    if a <= 7:
        return 1.0
    if a <= 30:
        return 0.8
    if a <= 90:
        return 0.5
    if a <= 365:
        return 0.3
    return 0.0

def _importance_multiplier(importance: str) -> float:
    return {"high": 1.5, "medium": 1.0, "low": 0.5}.get(importance, 1.0)


# ─────────────────────────────────────────────
# Primary Directions (Naibod key)
# ─────────────────────────────────────────────

def _primary_direction_dates(
    natal_asc: float,
    natal_mc: float,
    natal_planets: dict[str, float],
    birth_date: datetime,
    year_range: tuple[int, int],
    aspects: list[str],
) -> list[dict[str, Any]]:
    """
    Simplified Primary Directions using Naibod key (1° arc ≒ 1 year).
    Computes direction dates when significators (ASC/MC) form aspects
    with natal planets as promissors.
    """
    entries: list[dict[str, Any]] = []
    significators = {"ASC": natal_asc, "MC": natal_mc}

    for sig_name, sig_lon in significators.items():
        for prom_name, prom_lon in natal_planets.items():
            for asp_name in aspects:
                if asp_name not in ASPECTS:
                    continue
                asp_angle, _orb, _w = ASPECTS[asp_name]

                for sign in (1, -1):
                    target = _normalize_lon(sig_lon + sign * asp_angle)
                    arc = (target - prom_lon) % 360.0
                    if arc == 0 or arc > 100:
                        continue
                    years = arc / NAIBOD_KEY
                    if not (0.0 < years <= (year_range[1] - year_range[0] + 5)):
                        continue
                    direction_date = birth_date + timedelta(days=years * 365.25)
                    if not (year_range[0] <= direction_date.year <= year_range[1]):
                        continue
                    entries.append({
                        "significator": sig_name,
                        "promissor": prom_name,
                        "aspect": asp_name,
                        "date": direction_date.strftime("%Y-%m-%d"),
                        "arc_degrees": round(arc, 4),
                        "method": "placidus_semi_arc",
                    })

    entries.sort(key=lambda e: e["date"])
    return entries


# ─────────────────────────────────────────────
# Solar Arc
# ─────────────────────────────────────────────

def _solar_arc_hit_dates(
    natal_planets: dict[str, float],
    birth_date: datetime,
    year_range: tuple[int, int],
    aspects: list[str],
) -> list[tuple[datetime, str, str]]:
    hits: list[tuple[datetime, str, str]] = []
    for target_year in range(year_range[0], year_range[1] + 1):
        age = target_year - birth_date.year
        if age < 0:
            continue
        arc = age * NAIBOD_KEY
        for prom_name, prom_lon in natal_planets.items():
            directed = _normalize_lon(prom_lon + arc)
            for other_name, other_lon in natal_planets.items():
                if prom_name == other_name:
                    continue
                diff = _angular_diff(directed, other_lon)
                for asp_name in aspects:
                    if asp_name not in ASPECTS:
                        continue
                    asp_angle, orb, _ = ASPECTS[asp_name]
                    if abs(diff - asp_angle) <= orb:
                        hit_date = birth_date + timedelta(days=age * 365.25)
                        hits.append((hit_date, f"{prom_name}→{other_name}", asp_name))
    return hits


# ─────────────────────────────────────────────
# Secondary Progressions (Progressed Moon)
# ─────────────────────────────────────────────

def _progressed_moon_dates(
    natal_planets: dict[str, float],
    birth_date: datetime,
    year_range: tuple[int, int],
    aspects: list[str],
) -> list[tuple[datetime, str, str]]:
    hits: list[tuple[datetime, str, str]] = []
    moon_id = swe.MOON
    for target_year in range(year_range[0], year_range[1] + 1):
        age = target_year - birth_date.year
        if age < 0:
            continue
        progressed_date = birth_date + timedelta(days=age)
        jd_prog = _jd_from_datetime_jst(progressed_date)
        moon_lon = _planet_longitude(jd_prog, moon_id)
        for target_name, target_lon in natal_planets.items():
            if target_name == "moon":
                continue
            diff = _angular_diff(moon_lon, target_lon)
            for asp_name in aspects:
                if asp_name not in ASPECTS:
                    continue
                asp_angle, orb, _ = ASPECTS[asp_name]
                if abs(diff - asp_angle) <= orb:
                    hit_date = birth_date + timedelta(days=age * 365.25)
                    hits.append((hit_date, f"prog_moon→{target_name}", asp_name))
    return hits


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@rectification_api.route("/api/rectification/health", methods=["GET"])
def rectification_health():
    return jsonify({
        "status": "ok",
        "service": "rectification-api",
        "endpoints": [
            "/api/rectification/scan",
            "/api/rectification/primary-directions",
            "/api/rectification/asc-probability",
            "/api/rectification/event-types",
        ],
        "engine": "Swiss Ephemeris (pyswisseph)",
    })


@rectification_api.route("/api/rectification/event-types", methods=["GET"])
def event_types():
    """イベント種別マスター (静的 JSON レスポンス)。"""
    return jsonify({
        "categories": [
            {
                "id": "relationship",
                "label": "人間関係",
                "events": [
                    {"id": "marriage", "label": "結婚", "impact_house": [7]},
                    {"id": "divorce", "label": "離婚", "impact_house": [7]},
                    {"id": "birth_child", "label": "子供の誕生", "impact_house": [5]},
                    {"id": "significant_other", "label": "重要な出会い", "impact_house": [7, 5]},
                ],
            },
            {
                "id": "career",
                "label": "キャリア",
                "events": [
                    {"id": "job_change", "label": "転職・就職", "impact_house": [10, 6]},
                    {"id": "promotion", "label": "昇進・成功", "impact_house": [10]},
                    {"id": "business_start", "label": "起業", "impact_house": [10, 2]},
                ],
            },
            {
                "id": "life_change",
                "label": "生活の変化",
                "events": [
                    {"id": "move", "label": "引越", "impact_house": [4]},
                    {"id": "buy_home", "label": "住宅購入", "impact_house": [4, 2]},
                    {"id": "immigration", "label": "海外移住", "impact_house": [9, 4]},
                ],
            },
            {
                "id": "health",
                "label": "健康・危機",
                "events": [
                    {"id": "illness", "label": "重病", "impact_house": [6, 8]},
                    {"id": "accident", "label": "事故", "impact_house": [8]},
                    {"id": "surgery", "label": "手術", "impact_house": [6, 8]},
                ],
            },
            {
                "id": "family",
                "label": "家族",
                "events": [
                    {"id": "parent_death", "label": "親の死去", "impact_house": [4, 10, 8]},
                    {"id": "sibling_event", "label": "兄弟姉妹の重大事", "impact_house": [3]},
                ],
            },
        ],
    })


SIGN_KEYWORDS = {
    "aries":       ["athletic", "intense", "square", "short", "extroverted"],
    "taurus":      ["full", "round", "wavy", "gentle", "introverted"],
    "gemini":      ["slim", "oval", "curly", "average", "quick"],
    "cancer":      ["full", "round", "wavy", "gentle", "sensitive"],
    "leo":         ["athletic", "square", "wavy", "tall", "expressive"],
    "virgo":       ["slim", "oval", "straight", "average", "analytical"],
    "libra":       ["standard", "oval", "wavy", "average", "harmonious"],
    "scorpio":     ["athletic", "long", "straight", "intense", "deep"],
    "sagittarius": ["athletic", "long", "wavy", "tall", "extroverted"],
    "capricorn":   ["slim", "long", "straight", "tall", "structured"],
    "aquarius":    ["slim", "square", "curly", "tall", "unconventional"],
    "pisces":      ["full", "round", "wavy", "average", "sensitive"],
}


@rectification_api.route("/api/rectification/asc-probability", methods=["POST"])
def asc_probability():
    data = request.get_json(silent=True) or {}
    physical = data.get("physical_traits") or {}
    personality = data.get("personality_traits") or {}

    tags: list[str] = []
    for k in ("body_type", "face_shape", "hair_texture", "height", "eye_expression"):
        v = physical.get(k)
        if v:
            tags.append(v)

    if personality:
        e = personality.get("energy_level", 3)
        s = personality.get("social_style", 3)
        d = personality.get("decision_style", 3)
        x = personality.get("expression_style", 3)
        b = personality.get("boundary_style", 3)
        if e >= 4:
            tags.append("extroverted")
        if e <= 2:
            tags.append("introverted")
        if s >= 4:
            tags.append("harmonious")
        if d >= 4:
            tags.append("analytical")
        if d <= 2:
            tags.append("intense")
        if x >= 4:
            tags.append("expressive")
        if b >= 4:
            tags.append("structured")

    raw = {sign: 1 + sum(1 for k in kws if k in tags)
           for sign, kws in SIGN_KEYWORDS.items()}
    total = sum(raw.values())
    probs = {sign: round(v / total, 4) for sign, v in raw.items()}

    top_signs = sorted(probs.keys(), key=lambda k: probs[k], reverse=True)[:3]
    max_prob = probs[top_signs[0]]
    confidence = "high" if max_prob >= 0.15 else "medium" if max_prob >= 0.10 else "low"

    return jsonify({
        "sign_probabilities": probs,
        "top_signs": top_signs,
        "confidence": confidence,
    })


@rectification_api.route("/api/rectification/primary-directions", methods=["POST"])
def primary_directions():
    try:
        data = request.get_json(force=True)
        bd = data["birth_data"]
        yr = data["year_range"]
        method = data.get("method", "placidus_semi_arc")
        aspects = data.get("aspects", ["conjunction", "opposition", "square", "trine", "sextile"])

        pref = _lookup_prefecture(bd["birth_place"])
        if not pref:
            return jsonify({"error": f"Unknown birth_place: {bd['birth_place']}"}), 400
        lat, lon = pref

        birth_dt = datetime(
            bd["birth_year"], bd["birth_month"], bd["birth_day"],
            bd["birth_hour"], bd["birth_minute"],
        )
        jd = _jd_from_datetime_jst(birth_dt)
        _cusps, asc, mc = _houses_and_angles(jd, lat, lon)

        natal_planets = {
            name: _planet_longitude(jd, pid) for name, pid in PLANETS.items()
        }

        directions = _primary_direction_dates(
            asc, mc, natal_planets, birth_dt,
            (yr["start_year"], yr["end_year"]),
            aspects,
        )

        return jsonify({
            "birth_time": f"{bd['birth_hour']:02d}:{bd['birth_minute']:02d}",
            "directions": directions,
            "total_directions": len(directions),
            "method": method,
        })
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@rectification_api.route("/api/rectification/scan", methods=["POST"])
def scan():
    """候補時刻 sweep + 3 技法統合スコアリング (Top 3 返却)。"""
    try:
        data = request.get_json(force=True)
        bd = data["birth_data"]
        tr = data["time_range"]
        events = data.get("events", [])
        asc_hints = (data.get("asc_hints") or {}).get("sign_probabilities", {})
        weights = data.get("weights") or {
            "primary_directions": 0.4,
            "solar_arc": 0.3,
            "secondary_progressions": 0.3,
            "asc_multiplier": True,
        }
        aspects = ["conjunction", "opposition", "square", "trine", "sextile"]

        pref = _lookup_prefecture(bd["birth_place"])
        if not pref:
            return jsonify({"error": f"Unknown birth_place: {bd['birth_place']}"}), 400
        lat, lon = pref

        if not events:
            return jsonify({"error": "Events list is empty; need at least 1 event"}), 422

        birth_date_only = datetime(bd["birth_year"], bd["birth_month"], bd["birth_day"])
        event_dates = [datetime.strptime(e["date"], "%Y-%m-%d") for e in events]
        yr_min = min(d.year for d in event_dates) - 2
        yr_max = max(d.year for d in event_dates) + 2

        start_min = tr["start_hour"] * 60 + tr["start_minute"]
        end_min = tr["end_hour"] * 60 + tr["end_minute"]
        step_min = tr["step_minutes"]
        if end_min < start_min:
            candidate_minutes = (
                list(range(start_min, 24 * 60, step_min))
                + list(range(0, end_min + 1, step_min))
            )
        else:
            candidate_minutes = list(range(start_min, end_min + 1, step_min))

        computed_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        start_wall = datetime.utcnow()

        all_scores: list[dict[str, Any]] = []
        top: list[dict[str, Any]] = []

        for cm in candidate_minutes:
            h, m = divmod(cm, 60)
            birth_dt = birth_date_only.replace(hour=h, minute=m)
            jd = _jd_from_datetime_jst(birth_dt)
            _cusps, asc, mc = _houses_and_angles(jd, lat, lon)
            natal_planets = {
                name: _planet_longitude(jd, pid) for name, pid in PLANETS.items()
            }

            pd_entries = _primary_direction_dates(
                asc, mc, natal_planets, birth_dt, (yr_min, yr_max), aspects,
            )
            sa_hits = _solar_arc_hit_dates(
                natal_planets, birth_dt, (yr_min, yr_max), aspects,
            )
            pm_hits = _progressed_moon_dates(
                natal_planets, birth_dt, (yr_min, yr_max), aspects,
            )

            pd_score = 0.0
            sa_score = 0.0
            pm_score = 0.0
            event_matches: list[dict[str, Any]] = []

            for ev, ev_date in zip(events, event_dates):
                imp_mult = _importance_multiplier(ev["importance"])

                # Primary Directions best match
                best_pd = None
                best_pd_prox = 0.0
                for entry in pd_entries:
                    entry_dt = datetime.strptime(entry["date"], "%Y-%m-%d")
                    delta = (entry_dt - ev_date).days
                    prox = _date_proximity_score(delta)
                    if prox > best_pd_prox:
                        best_pd_prox = prox
                        best_pd = (entry, delta)
                if best_pd:
                    entry, delta = best_pd
                    contrib = best_pd_prox * imp_mult * 20
                    pd_score += contrib
                    event_matches.append({
                        "event_id": ev["id"],
                        "technique": "primary_directions",
                        "matched_direction": f"{entry['significator']} → {entry['promissor']} ({entry['aspect']})",
                        "date_delta_days": delta,
                        "contribution": round(contrib, 2),
                    })

                # Solar Arc best match
                best_sa = None
                best_sa_prox = 0.0
                for hit_date, promissor, asp in sa_hits:
                    delta = (hit_date - ev_date).days
                    prox = _date_proximity_score(delta)
                    if prox > best_sa_prox:
                        best_sa_prox = prox
                        best_sa = (hit_date, promissor, asp, delta)
                if best_sa:
                    _hd, prom, asp, delta = best_sa
                    contrib = best_sa_prox * imp_mult * 15
                    sa_score += contrib
                    event_matches.append({
                        "event_id": ev["id"],
                        "technique": "solar_arc",
                        "matched_direction": f"{prom} ({asp})",
                        "date_delta_days": delta,
                        "contribution": round(contrib, 2),
                    })

                # Progressed Moon best match
                best_pm = None
                best_pm_prox = 0.0
                for hit_date, promissor, asp in pm_hits:
                    delta = (hit_date - ev_date).days
                    prox = _date_proximity_score(delta)
                    if prox > best_pm_prox:
                        best_pm_prox = prox
                        best_pm = (hit_date, promissor, asp, delta)
                if best_pm:
                    _hd, prom, asp, delta = best_pm
                    contrib = best_pm_prox * imp_mult * 12
                    pm_score += contrib
                    event_matches.append({
                        "event_id": ev["id"],
                        "technique": "secondary_progressions",
                        "matched_direction": f"{prom} ({asp})",
                        "date_delta_days": delta,
                        "contribution": round(contrib, 2),
                    })

            asc_sign_key = _sign_key(asc)
            asc_prob = asc_hints.get(asc_sign_key, 1 / 12) if asc_hints else 1 / 12
            asc_mult = 0.8 + (asc_prob * 12) * 0.4
            asc_mult = max(0.7, min(1.3, asc_mult))

            weighted = (
                pd_score * weights["primary_directions"]
                + sa_score * weights["solar_arc"]
                + pm_score * weights["secondary_progressions"]
            )
            if weights.get("asc_multiplier", True):
                weighted *= asc_mult

            all_scores.append({
                "birth_time": f"{h:02d}:{m:02d}",
                "score": round(weighted, 2),
            })

            top.append({
                "birth_time": f"{h:02d}:{m:02d}",
                "score": round(weighted, 2),
                "asc": {"sign": asc_sign_key, "degree": round(_degree_in_sign(asc), 2)},
                "mc": {"sign": _sign_key(mc), "degree": round(_degree_in_sign(mc), 2)},
                "score_breakdown": {
                    "primary_directions": round(pd_score * weights["primary_directions"], 2),
                    "solar_arc": round(sa_score * weights["solar_arc"], 2),
                    "secondary_progressions": round(pm_score * weights["secondary_progressions"], 2),
                    "asc_adjustment": round(asc_mult, 3),
                },
                "event_matches": event_matches,
            })

        top.sort(key=lambda c: c["score"], reverse=True)
        top3 = top[:3]

        def _confidence(rank_idx: int, s: float, prev_s: float | None) -> str:
            if s >= 80 and (prev_s is None or s - prev_s >= 5):
                return "high"
            if s >= 50:
                return "medium"
            return "low"

        for i, c in enumerate(top3):
            c["rank"] = i + 1
            prev = top3[i - 1]["score"] if i > 0 else None
            c["confidence"] = _confidence(i, c["score"], prev)

        elapsed_ms = int((datetime.utcnow() - start_wall).total_seconds() * 1000)

        return jsonify({
            "scan_id": f"scan-{birth_date_only.strftime('%Y%m%d')}-{start_wall.strftime('%H%M%S')}",
            "computed_at": computed_at,
            "total_candidates": len(candidate_minutes),
            "top_candidates": top3,
            "all_scores": all_scores,
            "computation_time_ms": elapsed_ms,
        })
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
