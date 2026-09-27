#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rectification API tests.

pytest -q test_rectification_api.py
"""
from __future__ import annotations

import json
import unittest
from datetime import datetime

# Flask test client (via app.py の main app)
try:
    from app import app  # type: ignore
except ImportError:
    app = None

from rectification_api import (
    _normalize_lon,
    _angular_diff,
    _sign_index,
    _sign_key,
    _degree_in_sign,
    _date_proximity_score,
    _importance_multiplier,
    NAIBOD_KEY,
    SIGN_KEYS,
    PREFECTURES,
)


class TestHelpers(unittest.TestCase):
    def test_normalize_lon(self):
        self.assertEqual(_normalize_lon(0), 0)
        self.assertAlmostEqual(_normalize_lon(360), 0)
        self.assertAlmostEqual(_normalize_lon(720), 0)
        self.assertAlmostEqual(_normalize_lon(-10), 350)

    def test_angular_diff(self):
        self.assertAlmostEqual(_angular_diff(0, 180), 180)
        self.assertAlmostEqual(_angular_diff(10, 350), 20)
        self.assertAlmostEqual(_angular_diff(0, 90), 90)

    def test_sign_index(self):
        self.assertEqual(_sign_index(0), 0)  # 0° = Aries
        self.assertEqual(_sign_index(29.9), 0)
        self.assertEqual(_sign_index(30), 1)  # 30° = Taurus
        self.assertEqual(_sign_index(359.9), 11)  # end of Pisces

    def test_sign_key(self):
        self.assertEqual(_sign_key(0), "aries")
        self.assertEqual(_sign_key(45), "taurus")
        self.assertEqual(_sign_key(180), "libra")

    def test_degree_in_sign(self):
        self.assertAlmostEqual(_degree_in_sign(45), 15)
        self.assertAlmostEqual(_degree_in_sign(0.5), 0.5)

    def test_date_proximity_score(self):
        self.assertEqual(_date_proximity_score(0), 1.0)
        self.assertEqual(_date_proximity_score(7), 1.0)
        self.assertEqual(_date_proximity_score(-8), 0.8)
        self.assertEqual(_date_proximity_score(30), 0.8)
        self.assertEqual(_date_proximity_score(365), 0.3)
        self.assertEqual(_date_proximity_score(400), 0.0)

    def test_importance_multiplier(self):
        self.assertEqual(_importance_multiplier("high"), 1.5)
        self.assertEqual(_importance_multiplier("medium"), 1.0)
        self.assertEqual(_importance_multiplier("low"), 0.5)
        self.assertEqual(_importance_multiplier("unknown"), 1.0)

    def test_signs_and_prefectures(self):
        self.assertEqual(len(SIGN_KEYS), 12)
        self.assertGreaterEqual(len(PREFECTURES), 47)
        self.assertIn("東京都", PREFECTURES)


@unittest.skipIf(app is None, "Flask app not importable")
class TestEndpoints(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_event_types(self):
        res = self.client.get("/api/rectification/event-types")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("categories", data)
        self.assertEqual(len(data["categories"]), 5)

    def test_health(self):
        res = self.client.get("/api/rectification/health")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "ok")

    def test_asc_probability_empty(self):
        res = self.client.post(
            "/api/rectification/asc-probability",
            json={},
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("sign_probabilities", data)
        total = sum(data["sign_probabilities"].values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_asc_probability_extrovert(self):
        res = self.client.post(
            "/api/rectification/asc-probability",
            json={
                "physical_traits": {
                    "body_type": "athletic",
                    "height": "tall",
                    "eye_expression": "intense",
                },
                "personality_traits": {
                    "energy_level": 5,
                    "social_style": 3,
                    "decision_style": 1,
                    "expression_style": 3,
                    "boundary_style": 3,
                },
            },
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("top_signs", data)
        self.assertEqual(len(data["top_signs"]), 3)

    def test_primary_directions_minimal(self):
        res = self.client.post(
            "/api/rectification/primary-directions",
            json={
                "birth_data": {
                    "birth_year": 1990,
                    "birth_month": 3,
                    "birth_day": 15,
                    "birth_hour": 14,
                    "birth_minute": 32,
                    "birth_place": "東京都",
                },
                "year_range": {"start_year": 1990, "end_year": 2050},
            },
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("directions", data)
        self.assertEqual(data["birth_time"], "14:32")

    def test_primary_directions_bad_place(self):
        res = self.client.post(
            "/api/rectification/primary-directions",
            json={
                "birth_data": {
                    "birth_year": 1990,
                    "birth_month": 3,
                    "birth_day": 15,
                    "birth_hour": 14,
                    "birth_minute": 32,
                    "birth_place": "Neverland",
                },
                "year_range": {"start_year": 1990, "end_year": 2050},
            },
        )
        self.assertEqual(res.status_code, 400)

    def test_scan_small_range(self):
        """Small range + 1 event to check no crash and top-3 returned."""
        res = self.client.post(
            "/api/rectification/scan",
            json={
                "birth_data": {
                    "name": "Test",
                    "birth_year": 1990,
                    "birth_month": 3,
                    "birth_day": 15,
                    "birth_place": "東京都",
                },
                "time_range": {
                    "start_hour": 14,
                    "start_minute": 0,
                    "end_hour": 14,
                    "end_minute": 30,
                    "step_minutes": 10,
                },
                "events": [
                    {"id": "evt-1", "type": "marriage", "date": "2015-06-20", "importance": "high"},
                ],
            },
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("top_candidates", data)
        self.assertLessEqual(len(data["top_candidates"]), 3)
        self.assertGreaterEqual(len(data["top_candidates"]), 1)
        self.assertIn("all_scores", data)
        self.assertIn("computation_time_ms", data)


if __name__ == "__main__":
    unittest.main()
