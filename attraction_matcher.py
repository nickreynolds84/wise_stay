"""Indexed, conservative matching of LLM attraction candidates to Overture POIs."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from db import get_connection
from rapidfuzz import fuzz, process

OVERTURE_PATH = Path("data/raw/overture/manhattan_places.parquet")
THEATER_CATEGORIES = frozenset(
    {"theatre_venue", "performing_arts_venue", "performing_arts", "opera_house"}
)
AUTO_ACCEPT = 95.0
REVIEW_THRESHOLD = 85.0


def normalize_name(value):
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower().replace("&", " and ")
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\btheatre\b", "theater", value)
    value = re.sub(r"\s+", " ", value).strip()
    return re.sub(r"^the\s+", "", value)


def numeric_tokens(name):
    return tuple(re.findall(r"\d+", name))


def score_names(left, right):
    a, b = normalize_name(left), normalize_name(right)
    if not a or not b or numeric_tokens(a) != numeric_tokens(b):
        return 0.0
    return round(fuzz.ratio(a, b), 2)


def _names(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result = []
        for v in value.values():
            result.extend(_names(v))
        return result
    if isinstance(value, (tuple, list)):
        result = []
        for v in value:
            result.extend(_names(v))
        return result
    return []


@dataclass(frozen=True)
class POI:
    overture_id: str
    name: str
    category: str | None
    latitude: float | None
    longitude: float | None


class AttractionMatcher:
    """Load once per destination, then resolve many candidate names efficiently."""

    def __init__(self, records):
        self.pois = {}
        self.name_to_ids = defaultdict(set)
        for record in records:
            poi = POI(
                overture_id=str(record["id"]),
                name=record["name"],
                category=record.get("category"),
                latitude=record.get("latitude"),
                longitude=record.get("longitude"),
            )
            if not poi.name:
                continue
            self.pois[poi.overture_id] = poi
            for variant in [poi.name, *_names(record.get("all_names"))]:
                key = normalize_name(variant)
                if key:
                    self.name_to_ids[key].add(poi.overture_id)
        self.keys = list(self.name_to_ids)
        self.by_numbers = defaultdict(list)
        for key in self.keys:
            self.by_numbers[numeric_tokens(key)].append(key)

    @classmethod
    def from_parquet(cls, path=OVERTURE_PATH):
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Overture file not found: {path}")
        con = get_connection()
        try:
            rows = con.execute(
                """
                SELECT id, names.primary AS name, names AS all_names,
                       basic_category AS category,
                       ST_Y(geometry) AS latitude, ST_X(geometry) AS longitude
                FROM read_parquet(?)
                WHERE names.primary IS NOT NULL
                  AND operating_status IS DISTINCT FROM 'permanently_closed'
            """,
                [str(path)],
            ).fetchall()
        finally:
            con.close()
        fields = ("id", "name", "all_names", "category", "latitude", "longitude")
        records = [dict(zip(fields, row)) for row in rows]
        return cls(records)

    def find_matches(self, attraction, top_n=5):
        query_names = [attraction.get("name"), *(attraction.get("aliases") or [])]
        normalized = {normalize_name(n) for n in query_names if isinstance(n, str)}
        normalized.discard("")
        scores = {}
        matched = {}
        # Exact matching is O(1) against the index.
        for q in normalized:
            for poi_id in self.name_to_ids.get(q, ()):
                scores[poi_id] = 100.0
                matched[poi_id] = q
        # Only invoke fuzzy retrieval if no exact matches exist.
        if not scores:
            for q in normalized:
                # Number-based partitioning avoids Studio 54 -> Studio 42.
                pool = self.by_numbers.get(numeric_tokens(q), [])
                for key, raw_score, _ in process.extract(
                    q, pool, scorer=fuzz.ratio, limit=30, score_cutoff=REVIEW_THRESHOLD
                ):
                    for poi_id in self.name_to_ids[key]:
                        if raw_score > scores.get(poi_id, 0):
                            scores[poi_id] = round(raw_score, 2)
                            matched[poi_id] = key
        ordered = sorted(
            scores,
            key=lambda pid: (
                -scores[pid],
                self.pois[pid].category not in THEATER_CATEGORIES,
                self.pois[pid].name.casefold(),
                pid,
            ),
        )[:top_n]
        return [
            {
                "overture_id": pid,
                "overture_name": self.pois[pid].name,
                "matched_overture_name": matched[pid],
                "category": self.pois[pid].category,
                "latitude": self.pois[pid].latitude,
                "longitude": self.pois[pid].longitude,
                "similarity": scores[pid],
            }
            for pid in ordered
        ]

    def validate(self, attraction):
        candidates = self.find_matches(attraction)
        if not candidates:
            return {
                "attraction": attraction["name"],
                "status": "rejected",
                "reason": "No candidate meets the name threshold.",
                "candidates": [],
            }
        best = candidates[0]
        tied = [c for c in candidates if c["similarity"] == best["similarity"]]
        if best["similarity"] >= AUTO_ACCEPT and best["category"] in THEATER_CATEGORIES:
            # Do not silently choose between different POIs with equally strong names.
            if len(tied) > 1:
                status, reason = (
                    "review",
                    "Multiple Overture records share the best match.",
                )
            else:
                status, reason = (
                    "accepted",
                    "Strong name match and compatible category.",
                )
        elif best["similarity"] >= AUTO_ACCEPT:
            status, reason = (
                "review",
                "Strong name match but incompatible or missing category.",
            )
        elif best["category"] in THEATER_CATEGORIES:
            status, reason = (
                "review",
                "Fuzzy venue match requires identity confirmation.",
            )
        else:
            status, reason = "rejected", "No compatible venue category for fuzzy match."
        return {
            "attraction": attraction["name"],
            "status": status,
            "reason": reason,
            "best_match": best,
            "candidates": candidates,
        }


# Compatibility wrappers for existing callers.
def load_overture_theaters(path=OVERTURE_PATH):
    return AttractionMatcher.from_parquet(path)


def validate_attraction(attraction, overture_df):
    if not isinstance(overture_df, AttractionMatcher):
        raise TypeError(
            "Pass the AttractionMatcher returned by load_overture_theaters()."
        )
    return overture_df.validate(attraction)
