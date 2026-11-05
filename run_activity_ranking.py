"""Run geographic hotel ranking against local Manhattan Overture data."""
from time import perf_counter
from activity_ranking import load_places, rank_hotels

# Change the activities/weights to simulate different traveler preferences.
PREFERENCES = {'theater': 1, 'museums': 1}

start = perf_counter()
places = load_places()
print(f'Loaded {len(places):,} POIs in {perf_counter()-start:.2f}s')

start = perf_counter()
ranked, diagnostics = rank_hotels(places, PREFERENCES, top_n=15)
print(f'Ranked hotels in {perf_counter()-start:.2f}s')
print('Diagnostics:', diagnostics)
print('\nTop geographic matches (NOT bookable hotel recommendations):')
print(ranked.to_string(index=False))

# Optionally save a compact artifact for comparison and regression testing.
# ranked.to_csv('hotel_activity_ranking.csv', index=False)
