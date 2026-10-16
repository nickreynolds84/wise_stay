import json
from pathlib import Path
from time import perf_counter

from attraction_matcher import (
    load_overture_theaters,
    validate_attraction,
)

DATA_PATH = Path("data/generated/manhattan_theater_candidates.json")

with DATA_PATH.open(encoding="utf-8") as f:
    result = json.load(f)

start = perf_counter()
matcher = load_overture_theaters()
load_time = perf_counter() - start

print(f"Loaded {len(matcher.pois):,} Overture POIs")
print(f"Loading and indexing: {load_time:.3f}s")

start = perf_counter()

results = [
    validate_attraction(attraction, matcher) for attraction in result["attractions"]
]

matching_time = perf_counter() - start

print("\nVALIDATION RESULTS")

for item in results:
    print(f"\n{item['attraction']}")
    print(f"Status: {item['status'].upper()}")
    print(f"Reason: {item['reason']}")

    for candidate in item["candidates"][:3]:
        print(
            f"  {candidate['overture_name']}"
            f" | {candidate['similarity']:.1f}"
            f" | {candidate['category']}"
        )

print(f"\nMatching time: {matching_time:.3f}s")
