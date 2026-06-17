import os
import time
import requests

_cache = {}
_last_call_time = [0.0]
_MIN_INTERVAL = 0.35  # seconds between calls to stay under rate limits

_BASE_URL = "https://api.reccobeats.com/v1/track/audio-feature"


def _rate_limit():
    elapsed = time.time() - _last_call_time[0]
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_call_time[0] = time.time()


def fetch_features(track_name, artist_name):
    """Return ReccoBeats audio features dict or None on miss/error."""
    key = f"{track_name.lower()}|||{artist_name.lower()}"
    if key in _cache:
        return _cache[key]

    _rate_limit()
    try:
        params = {"trackName": track_name, "artistName": artist_name}
        api_key = os.getenv("RECCOBEATS_API_KEY")
        if api_key:
            params["apiKey"] = api_key
        r = requests.get(_BASE_URL, params=params, timeout=5)
        data = r.json() if r.status_code == 200 else None
    except Exception:
        data = None

    _cache[key] = data
    return data


def enrich_tracks(tracks):
    """Add rb_energy, rb_valence, rb_danceability, rb_tempo, rb_tempo_n to each track dict.

    Works with both raw Spotify track objects (artists list) and simplified dicts (artist string).
    Only overwrites fields that are currently None/absent -- Deezer data is untouched.
    """
    for track in tracks:
        # Resolve artist name from either format
        if track.get("artists"):
            artist_name = track["artists"][0].get("name", "")
        else:
            artist_name = track.get("artist", "")

        features = fetch_features(track.get("name", ""), artist_name)

        if features:
            track["rb_energy"] = features.get("energy")
            track["rb_valence"] = features.get("valence")
            track["rb_danceability"] = features.get("danceability")
            raw_tempo = features.get("tempo")
            track["rb_tempo"] = raw_tempo
            track["rb_tempo_n"] = (
                max(0.0, min(1.0, (raw_tempo - 85) / 95)) if raw_tempo else None
            )
        else:
            track["rb_energy"] = None
            track["rb_valence"] = None
            track["rb_danceability"] = None
            track["rb_tempo"] = None
            track["rb_tempo_n"] = None

    return tracks
