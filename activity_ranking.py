"""Wise Stay: transparent, geographic-only hotel ranking baseline.

Requires numpy, pandas, scipy, duckdb and the existing db.get_connection().
No live hotel prices, availability, or travel-time claims are made.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

DEFAULT_PARQUET = Path('data/raw/overture/manhattan_places.parquet')
# These are starter mappings; inspect actual categories/counts before trusting coverage.
ACTIVITY_CATEGORIES = {
    'theater': {'theatre_venue', 'performing_arts_venue', 'opera_house'},
    'museums': {'museum', 'art_gallery'},
    'nightlife': {'bar', 'pub', 'nightclub', 'cocktail_bar'},
    'restaurants': {'restaurant'},
    'parks': {'park', 'garden'},
}
HOTEL_CATEGORIES = {'hotel'}
EARTH_RADIUS_M = 6_371_000.0


@dataclass(frozen=True)
class RankConfig:
    nearest_n: int = 8
    distance_scale_m: float = 900.0
    duplicate_radius_m: float = 1.0
    min_pois_per_activity: int = 3


def _xy_m(lat: np.ndarray, lon: np.ndarray, lat0: float) -> np.ndarray:
    """Local equirectangular projection; suitable for NYC-sized regions."""
    rlat = np.deg2rad(lat)
    rlon = np.deg2rad(lon)
    return np.column_stack((
        EARTH_RADIUS_M * rlon * np.cos(np.deg2rad(lat0)),
        EARTH_RADIUS_M * rlat,
    ))


def load_places(path: str | Path = DEFAULT_PARQUET) -> pd.DataFrame:
    """Read only columns needed for scoring; no spatial extension required."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Overture dataset not found: {path}')
    import duckdb
    con = duckdb.connect()
    try:
        # DuckDB can extract coordinates from WKB without a spatial extension via
        # ST_* only if spatial is loaded. Reuse the project's connection helper.
        con.close()
        from db import get_connection
        con = get_connection()
        df = con.execute('''
            SELECT id, names.primary AS name, basic_category AS category,
                   ST_Y(geometry) AS latitude, ST_X(geometry) AS longitude
            FROM read_parquet(?)
            WHERE operating_status IS DISTINCT FROM 'permanently_closed'
              AND basic_category IS NOT NULL
        ''', [str(path)]).df()
    finally:
        con.close()
    df = df.dropna(subset=['latitude', 'longitude', 'category'])
    df = df.loc[df.latitude.between(-90, 90) & df.longitude.between(-180, 180)].copy()
    df['category'] = df['category'].astype(str)
    return df


def dedupe_coordinates(df: pd.DataFrame, radius_m: float = 1.0) -> pd.DataFrame:
    """Conservatively remove exact/near-identical POI points within one category.

    This is NOT venue identity deduplication. For dense groups, a greedy
    representative rule avoids transitive chaining across a whole street.
    """
    if df.empty or radius_m <= 0:
        return df.copy()
    kept = []
    lat0 = float(df.latitude.median())
    for _, group in df.groupby('category', sort=False):
        coords = _xy_m(group.latitude.to_numpy(), group.longitude.to_numpy(), lat0)
        tree = cKDTree(coords)
        suppressed = np.zeros(len(group), dtype=bool)
        for i in range(len(group)):
            if suppressed[i]:
                continue
            kept.append(group.index[i])
            for j in tree.query_ball_point(coords[i], r=radius_m):
                suppressed[j] = True
    return df.loc[kept].copy()


def rank_hotels(
    places: pd.DataFrame,
    activity_weights: dict[str, float],
    config: RankConfig = RankConfig(),
    top_n: int = 20,
) -> tuple[pd.DataFrame, dict]:
    """Rank by mean activity access, equalized across user-selected activities.

    Score for each activity is mean exp(-distance / scale) over the nearest
    N unique POI coordinates, with missing neighbors contributing zero.
    This rewards access to several destinations without raw POI count domination.
    """
    if not activity_weights:
        raise ValueError('Select at least one activity.')
    unknown = set(activity_weights) - set(ACTIVITY_CATEGORIES)
    if unknown:
        raise ValueError(f'Unknown activities: {sorted(unknown)}')
    if any(not np.isfinite(w) or w < 0 for w in activity_weights.values()):
        raise ValueError('Activity weights must be finite and nonnegative.')
    total_weight = sum(activity_weights.values())
    if total_weight <= 0:
        raise ValueError('At least one activity must have positive weight.')
    if config.nearest_n < 1 or config.distance_scale_m <= 0:
        raise ValueError('nearest_n and distance_scale_m must be positive.')

    hotels = places[places.category.isin(HOTEL_CATEGORIES)].copy()
    hotels = dedupe_coordinates(hotels, config.duplicate_radius_m)
    if hotels.empty:
        raise ValueError('No hotel POIs found in this dataset.')
    lat0 = float(places.latitude.median())
    hotel_xy = _xy_m(hotels.latitude.to_numpy(), hotels.longitude.to_numpy(), lat0)
    scores = np.zeros(len(hotels), dtype=float)
    details = {'hotel_count': len(hotels), 'activity_counts': {}, 'warnings': []}
    active_weights = {k: v / total_weight for k, v in activity_weights.items() if v > 0}

    for activity, weight in active_weights.items():
        pois = places[places.category.isin(ACTIVITY_CATEGORIES[activity])].copy()
        pois = dedupe_coordinates(pois, config.duplicate_radius_m)
        details['activity_counts'][activity] = len(pois)
        if len(pois) < config.min_pois_per_activity:
            raise ValueError(
                f'Insufficient {activity} POIs ({len(pois)}). '
                'Check Overture category mapping before ranking.'
            )
        poi_xy = _xy_m(pois.latitude.to_numpy(), pois.longitude.to_numpy(), lat0)
        tree = cKDTree(poi_xy)
        k = min(config.nearest_n, len(pois))
        d, _ = tree.query(hotel_xy, k=k, workers=-1)
        d = np.asarray(d).reshape(len(hotels), k)
        per_activity = np.exp(-d / config.distance_scale_m).sum(axis=1) / config.nearest_n
        scores += weight * per_activity
        hotels[f'{activity}_score'] = np.round(100 * per_activity, 2)
        hotels[f'{activity}_nearest_m'] = np.round(d[:, 0]).astype(int)

    hotels['activity_score'] = np.round(100 * scores, 2)
    hotels = hotels.sort_values(['activity_score', 'name'], ascending=[False, True])
    columns = ['id', 'name', 'latitude', 'longitude', 'activity_score']
    for activity in active_weights:
        columns += [f'{activity}_score', f'{activity}_nearest_m']
    return hotels[columns].head(top_n).reset_index(drop=True), details
