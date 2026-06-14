import urllib.request
import json

# In-memory cache so we don't re-fetch the same ISRC twice per session
_cache = {}

GAIN_MIN = -20.0
GAIN_MAX = -5.0


def fetch_track(isrc):
    """Return Deezer track dict for an ISRC, or None if not found."""
    if isrc in _cache:
        return _cache[isrc]

    url = f"https://api.deezer.com/track/isrc:{isrc}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WalkUpSongFinder/1.0"})
        resp = urllib.request.urlopen(req, timeout=4)
        data = json.loads(resp.read())
        result = None if "error" in data else data
    except Exception:
        result = None

    _cache[isrc] = result
    return result


def enrich_tracks(spotify_tracks):
    """
    Given a list of Spotify track dicts, add Deezer data to each.
    Returns a list of dicts with added keys: deezer_bpm, deezer_gain, deezer_energy.
    Runs lookups sequentially with per-ISRC caching.
    """
    enriched = []
    for track in spotify_tracks:
        isrc = track.get("external_ids", {}).get("isrc", "")
        d = fetch_track(isrc) if isrc else None

        raw_bpm  = d.get("bpm", 0)   if d else 0
        raw_gain = d.get("gain", None) if d else None

        # bpm of 0 means Deezer doesn't have it
        bpm = raw_bpm if (raw_bpm and raw_bpm > 0) else None

        # Normalize gain to 0-1 energy proxy (less negative = louder = more energetic)
        if raw_gain is not None:
            energy = max(0.0, min(1.0, (raw_gain - GAIN_MIN) / (GAIN_MAX - GAIN_MIN)))
        else:
            energy = None

        enriched.append({
            **track,
            "deezer_bpm":    bpm,
            "deezer_gain":   raw_gain,
            "deezer_energy": round(energy, 3) if energy is not None else None,
        })
    return enriched


def tempo_norm(bpm):
    """Normalize BPM to 0-1 scale. Same range as the Spotify scorer: 85-180 BPM."""
    if not bpm:
        return None
    return round(max(0.0, min(1.0, (bpm - 85) / 95)), 3)
