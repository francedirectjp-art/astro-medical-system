"""Metaphysica Atlas (self-contained lite version for grand-vision).

将来的に PyPI 公開された metaphysica-atlas パッケージに置き換える予定.
現状は self-contained で /atlas_data/ から読み込む.

API は metaphysica_atlas Python SDK と同じ.
"""

from __future__ import annotations

import gzip
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

_DATA_DIR = Path(__file__).parent / "atlas_data"


@dataclass(frozen=True)
class City:
    id: int
    name: str
    ascii: str
    name_ja: Optional[str]
    name_zh: Optional[str]
    name_ko: Optional[str]
    lat: float
    lon: float
    country: str
    admin1: str
    tz: str
    pop: int


@dataclass(frozen=True)
class Prefecture:
    code: str
    name_ja: str
    name_en: str
    capital_name_ja: str
    lat: float
    lon: float
    tz: str


@dataclass(frozen=True)
class TimezoneInfo:
    name: str
    offset_minutes: int
    offset_label: str
    is_dst: bool


@lru_cache(maxsize=1)
def _load_cities() -> list[City]:
    gz_path = _DATA_DIR / "cities15000.json.gz"
    raw_path = _DATA_DIR / "cities15000.json"
    if gz_path.exists():
        with gzip.open(gz_path, "rb") as f:
            data = json.loads(f.read().decode("utf-8"))
    else:
        with open(raw_path, encoding="utf-8") as f:
            data = json.load(f)
    return [City(**c) for c in data]


@lru_cache(maxsize=1)
def _load_prefectures() -> list[Prefecture]:
    with open(_DATA_DIR / "prefectures-jp.json", encoding="utf-8") as f:
        raw = json.load(f)
    return [Prefecture(**p) for p in raw]


def search_cities(
    query: str, limit: int = 10, country: Optional[str] = None
) -> list[City]:
    q = query.strip().lower()
    if not q:
        return []
    country_upper = country.upper() if country else None

    exact: list[City] = []
    prefix: list[City] = []
    partial: list[City] = []

    for c in _load_cities():
        if country_upper and c.country != country_upper:
            continue
        fields = [c.name, c.ascii, c.name_ja, c.name_zh, c.name_ko]
        lower_fields = [f.lower() for f in fields if f]

        matched = None
        for f in lower_fields:
            if f == q:
                matched = "exact"
                break
            if f.startswith(q):
                matched = "prefix"
            elif q in f and matched is None:
                matched = "partial"

        if matched == "exact":
            exact.append(c)
        elif matched == "prefix":
            prefix.append(c)
        elif matched == "partial":
            partial.append(c)

    exact.sort(key=lambda c: -c.pop)
    prefix.sort(key=lambda c: -c.pop)
    partial.sort(key=lambda c: -c.pop)
    return (exact + prefix + partial)[:limit]


def get_prefectures() -> list[Prefecture]:
    return list(_load_prefectures())


def get_timezone_at(city_or_tz, date: datetime) -> TimezoneInfo:
    tz_name = city_or_tz if isinstance(city_or_tz, str) else city_or_tz.tz
    tz = ZoneInfo(tz_name)
    aware = date if date.tzinfo else date.replace(tzinfo=timezone.utc)
    local = aware.astimezone(tz)
    offset = local.utcoffset()
    offset_min = int(offset.total_seconds() / 60) if offset else 0
    sign = "+" if offset_min >= 0 else "-"
    abs_min = abs(offset_min)
    dst = local.dst()
    is_dst = bool(dst and dst.total_seconds() != 0)
    return TimezoneInfo(
        name=tz_name,
        offset_minutes=offset_min,
        offset_label=f"{sign}{abs_min // 60:02d}:{abs_min % 60:02d}",
        is_dst=is_dst,
    )


def local_to_utc(local_datetime: datetime, city_or_tz) -> datetime:
    tz_name = city_or_tz if isinstance(city_or_tz, str) else city_or_tz.tz
    tz = ZoneInfo(tz_name)
    aware = (
        local_datetime.replace(tzinfo=tz)
        if local_datetime.tzinfo is None
        else local_datetime.astimezone(tz)
    )
    return aware.astimezone(timezone.utc)


def city_to_dict(city: City) -> dict:
    """City dataclass → JSON serializable dict."""
    return asdict(city)
