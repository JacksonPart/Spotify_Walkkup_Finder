import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from mlb_teams import TEAMS_BY_ID
from deezer_lookup import enrich_tracks, tempo_norm as deezer_tempo_norm

MIN_ENERGY = 0.40
MIN_TEMPO = 85
TIME_WEIGHTS = {"short_term": 3.0, "medium_term": 2.0, "long_term": 1.0}

GENRE_BUCKETS = {
    "hip-hop":    ["hip hop", "hip-hop", "rap", "trap", "drill", "boom bap", "crunk", "chopped", "g-funk", "gangsta"],
    "rock":       ["rock", "alternative", "indie rock", "punk", "metal", "hard rock", "classic rock", "grunge", "emo", "post-punk"],
    "pop":        ["pop", "electropop", "indie pop", "synth-pop", "k-pop", "dance pop", "teen pop", "art pop"],
    "r&b":        ["r&b", "soul", "neo soul", "contemporary r&b", "funk", "motown", "quiet storm"],
    "country":    ["country", "outlaw country", "bro country", "bluegrass", "americana", "country road"],
    "electronic": ["electronic", "edm", "house", "techno", "dubstep", "drum and bass", "future bass", "lo-fi", "trance"],
    "latin":      ["latin", "reggaeton", "latin pop", "salsa", "bachata", "corridos", "banda", "cumbia"],
}

GENRE_DISPLAY_NAMES = {
    "hip-hop":    "Hip-Hop / Rap",
    "rock":       "Rock",
    "pop":        "Pop",
    "r&b":        "R&B / Soul",
    "country":    "Country",
    "electronic": "Electronic / EDM",
    "latin":      "Latin",
}

FALLBACK_GENRES = ["hip-hop", "rock", "pop"]


def _bucket_genre(genre_string):
    g = genre_string.lower()
    for bucket, keywords in GENRE_BUCKETS.items():
        if any(kw in g for kw in keywords):
            return bucket
    return None


def get_top_genres(sp, limit=3):
    try:
        results = sp.current_user_top_artists(limit=20, time_range="medium_term")
        counts = {}
        for artist in results.get("items", []):
            for genre in artist.get("genres", []):
                bucket = _bucket_genre(genre)
                if bucket:
                    counts[bucket] = counts.get(bucket, 0) + 1
        sorted_genres = [g for g, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)]
        for fb in FALLBACK_GENRES:
            if len(sorted_genres) >= limit:
                break
            if fb not in sorted_genres:
                sorted_genres.append(fb)
        return sorted_genres[:limit]
    except Exception:
        return FALLBACK_GENRES[:limit]


def get_debug_data(sp):
    top_genres = get_top_genres(sp)

    artist_genres = {}
    try:
        for tr in ["medium_term", "long_term"]:
            results = sp.current_user_top_artists(limit=20, time_range=tr)
            for artist in results.get("items", []):
                if artist["id"] not in artist_genres:
                    buckets = set()
                    for g in artist.get("genres", []):
                        b = _bucket_genre(g)
                        if b:
                            buckets.add(b)
                    artist_genres[artist["id"]] = list(buckets)
    except Exception:
        pass

    seen = set()
    weighted_tracks = []
    for time_range in ["short_term", "medium_term", "long_term"]:
        try:
            results = sp.current_user_top_tracks(limit=20, time_range=time_range)
            for track in results.get("items", []):
                if track["id"] not in seen:
                    seen.add(track["id"])
                    weighted_tracks.append((track, TIME_WEIGHTS[time_range], time_range))
        except Exception:
            pass

    if not weighted_tracks:
        return None

    track_ids = [t["id"] for t, _, _ in weighted_tracks[:50]]
    features_list = None
    try:
        features_list = sp.audio_features(track_ids)
    except Exception:
        pass

    has_features = bool(features_list and any(f for f in features_list))

    VIBES = ["auto", "intimidator", "crowd_pleaser", "closer"]

    tracks_data = []

    if has_features:
        for (track, time_weight, time_range), features in zip(weighted_tracks[:50], features_list):
            if not features:
                continue
            artist_id = track["artists"][0]["id"]
            track_genre_buckets = artist_genres.get(artist_id, [])
            pop = track.get("popularity", 50)
            filtered = features["energy"] < MIN_ENERGY or features["tempo"] < MIN_TEMPO

            scores = {}
            for vibe in VIBES:
                scores[vibe] = round(_score(features, vibe, "batter", time_weight, pop, None, [], []), 3)
            for g in top_genres:
                scores[f"genre_{g}"] = round(_score(features, "auto", "batter", time_weight, pop, g, track_genre_buckets, []), 3)

            tracks_data.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "time_range": time_range,
                "time_weight": time_weight,
                "energy": round(features["energy"] * 100),
                "tempo": round(features["tempo"]),
                "valence": round(features["valence"] * 100),
                "danceability": round(features["danceability"] * 100),
                "popularity": pop,
                "genres": track_genre_buckets,
                "scores": scores,
                "filtered": filtered,
            })
    else:
        # Fallback: no Spotify audio features -- enrich with Deezer BPM/gain
        raw_tracks = [t for t, _, _ in weighted_tracks[:50]]
        enriched = enrich_tracks(raw_tracks)
        enriched_map = {t["id"]: t for t in enriched}

        for track, time_weight, time_range in weighted_tracks[:50]:
            et = enriched_map.get(track["id"], track)
            artist_id = et["artists"][0]["id"]
            track_genre_buckets = artist_genres.get(artist_id, [])
            pop = et.get("popularity", 50)
            explicit = et.get("explicit", False)
            d_energy = et.get("deezer_energy")
            d_tempo_n = deezer_tempo_norm(et.get("deezer_bpm")) if et.get("deezer_bpm") else None

            filtered = False
            if d_energy is not None and d_energy < MIN_ENERGY:
                filtered = True
            if et.get("deezer_bpm") and et["deezer_bpm"] < MIN_TEMPO:
                filtered = True

            scores = {}
            for v in VIBES:
                scores[v] = round(_score_fallback(v, time_weight, pop, track_genre_buckets, None, [], explicit, d_energy, d_tempo_n), 3)
            for g in top_genres:
                scores[f"genre_{g}"] = round(_score_fallback("auto", time_weight, pop, track_genre_buckets, g, [], explicit, d_energy, d_tempo_n), 3)

            tracks_data.append({
                "name": et["name"],
                "artist": et["artists"][0]["name"],
                "time_range": time_range,
                "time_weight": time_weight,
                "energy": round(d_energy * 100) if d_energy is not None else None,
                "tempo": round(et["deezer_bpm"]) if et.get("deezer_bpm") else None,
                "valence": None,
                "danceability": None,
                "popularity": pop,
                "genres": track_genre_buckets,
                "scores": scores,
                "filtered": filtered,
            })

    VIBE_LABELS = {
        "auto": "Auto",
        "intimidator": "Intimidator",
        "crowd_pleaser": "Crowd Pleaser",
        "closer": "The Closer",
    }

    def top3(key):
        s = sorted(tracks_data, key=lambda x: x["scores"].get(key, 0), reverse=True)
        return [dict(rank=i + 1, **t) for i, t in enumerate(s[:3])]

    # Pre-sort by auto for the main table
    sorted_tracks = sorted(tracks_data, key=lambda x: x["scores"]["auto"], reverse=True)

    # Pre-compute max score per vibe for green highlight in table
    max_scores = {}
    for v in VIBES:
        vals = [t["scores"].get(v, 0) for t in tracks_data]
        max_scores[v] = max(vals) if vals else 0

    vibe_sections = [
        {"key": v, "label": VIBE_LABELS[v], "top3": top3(v)}
        for v in VIBES
    ]

    genre_sections = [
        {
            "key": g,
            "label": GENRE_DISPLAY_NAMES.get(g, g),
            "top3": top3(f"genre_{g}"),
        }
        for g in top_genres
    ]

    return {
        "sorted_tracks": sorted_tracks,
        "vibe_sections": vibe_sections,
        "genre_sections": genre_sections,
        "max_scores": max_scores,
        "vibes": VIBES,
    }


def analyze_walkup_song(sp, vibe="auto", position="batter", genre=None, team=None):
    # Build artist -> genre bucket map from top artists
    artist_genres = {}
    try:
        for tr in ["medium_term", "long_term"]:
            results = sp.current_user_top_artists(limit=20, time_range=tr)
            for artist in results.get("items", []):
                if artist["id"] not in artist_genres:
                    buckets = set()
                    for g in artist.get("genres", []):
                        b = _bucket_genre(g)
                        if b:
                            buckets.add(b)
                    artist_genres[artist["id"]] = list(buckets)
    except Exception:
        pass

    # Collect top tracks with time-range weights (recent = highest)
    seen = set()
    weighted_tracks = []
    for time_range in ["short_term", "medium_term", "long_term"]:
        try:
            results = sp.current_user_top_tracks(limit=20, time_range=time_range)
            for track in results.get("items", []):
                if track["id"] not in seen:
                    seen.add(track["id"])
                    weighted_tracks.append((track, TIME_WEIGHTS[time_range]))
        except Exception:
            pass

    if not weighted_tracks:
        return {"error": "No listening data found. Listen more on Spotify and try again."}

    track_ids = [t["id"] for t, _ in weighted_tracks[:50]]

    features_list = None
    try:
        features_list = sp.audio_features(track_ids)
    except Exception:
        pass

    team_genres = TEAMS_BY_ID[team]["genres"] if team and team in TEAMS_BY_ID else []

    if features_list:
        candidates = _build_candidates(
            weighted_tracks[:50], features_list, vibe, position,
            genre, team_genres, artist_genres, hard_filter=True
        )
        if len(candidates) < 3:
            candidates = _build_candidates(
                weighted_tracks[:50], features_list, vibe, position,
                genre, team_genres, artist_genres, hard_filter=False
            )
    else:
        raw_tracks = [t for t, _ in weighted_tracks]
        enriched = enrich_tracks(raw_tracks)
        enriched_map = {t["id"]: t for t in enriched}

        candidates = []
        for t, w in weighted_tracks:
            et = enriched_map.get(t["id"], t)
            artist_id = et["artists"][0]["id"]
            track_genres = artist_genres.get(artist_id, [])
            d_energy = et.get("deezer_energy")
            d_tempo_n = deezer_tempo_norm(et.get("deezer_bpm")) if et.get("deezer_bpm") else None
            score = _score_fallback(vibe, w, et.get("popularity", 50), track_genres, genre, team_genres, et.get("explicit", False), d_energy, d_tempo_n)
            candidates.append({"track": et, "features": None, "score": score, "track_genres": track_genres})

    if not candidates:
        return {"error": "Could not analyze your tracks. Try again later."}

    candidates.sort(key=lambda x: x["score"], reverse=True)
    winner = candidates[0]
    track = winner["track"]
    features = winner["features"]
    track_id = track["id"]
    images = track["album"]["images"]

    team_data = TEAMS_BY_ID.get(team) if team else None

    return {
        "name": track["name"],
        "artist": track["artists"][0]["name"],
        "album_art": images[0]["url"] if images else None,
        "spotify_url": track["external_urls"]["spotify"],
        "embed_url": f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator&theme=0",
        "explanation": _explain(winner, vibe, position, team_data),
        "energy": (round(features["energy"] * 100) if features
                   else (round(track.get("deezer_energy") * 100) if track.get("deezer_energy") is not None else None)),
        "tempo": (round(features["tempo"]) if features
                  else (round(track.get("deezer_bpm")) if track.get("deezer_bpm") else None)),
        "team": team_data,
    }


def _build_candidates(weighted_tracks, features_list, vibe, position, genre, team_genres, artist_genres, hard_filter):
    candidates = []
    for (track, time_weight), features in zip(weighted_tracks, features_list):
        if not features:
            continue
        if hard_filter and (features["energy"] < MIN_ENERGY or features["tempo"] < MIN_TEMPO):
            continue
        primary_artist_id = track["artists"][0]["id"]
        track_genre_buckets = artist_genres.get(primary_artist_id, [])
        score = _score(features, vibe, position, time_weight, track.get("popularity", 50), genre, track_genre_buckets, team_genres)
        candidates.append({"track": track, "features": features, "score": score, "track_genres": track_genre_buckets})
    return candidates


def _score(features, vibe, position, time_weight, popularity, selected_genre, track_genre_buckets, team_genres):
    energy = features["energy"]
    valence = features["valence"]
    danceability = features["danceability"]
    tempo = features["tempo"]
    tempo_norm = max(0.0, min(1.0, (tempo - MIN_TEMPO) / 95))
    pop_norm = popularity / 100.0

    if vibe == "intimidator":
        # Darkness and intensity -- low valence carries heavy weight
        base = energy * 0.50 + (1 - valence) * 0.30 + tempo_norm * 0.15 + pop_norm * 0.05
    elif vibe == "crowd_pleaser":
        # Happy, danceable, recognizable -- popularity and valence dominate
        base = valence * 0.30 + danceability * 0.25 + pop_norm * 0.25 + energy * 0.15 + tempo_norm * 0.05
    elif vibe == "closer":
        # Pure rhythmic intensity -- tempo is king, energy second
        base = tempo_norm * 0.50 + energy * 0.40 + pop_norm * 0.05 + (1 - valence) * 0.05
    else:  # auto -- maximum personal pump-up
        base = energy * 0.55 + tempo_norm * 0.30 + danceability * 0.10 + pop_norm * 0.05

    if position == "pitcher":
        base += features.get("instrumentalness", 0) * 0.05
    elif position == "catcher":
        base += (1 - features.get("speechiness", 0)) * 0.03

    boost = 0.0
    if selected_genre and selected_genre in track_genre_buckets:
        boost += 0.35
    if team_genres and any(g in track_genre_buckets for g in team_genres):
        boost += 0.12

    return (base + boost) * time_weight


def _score_fallback(vibe, time_weight, popularity, track_genre_buckets, selected_genre,
                    team_genres, explicit, deezer_energy=None, deezer_tempo_n=None):
    """
    Scoring when Spotify audio features are unavailable.
    Uses Deezer gain (energy proxy) + BPM when available, falls back to genre/explicit/popularity.
    """
    pop = popularity / 100.0

    aggressive = any(g in track_genre_buckets for g in ["hip-hop", "rock", "electronic"])
    feel_good  = any(g in track_genre_buckets for g in ["pop", "country", "r&b", "latin"])

    # Use Deezer data when available, otherwise fall back to genre proxies
    energy  = deezer_energy  if deezer_energy  is not None else (0.70 if aggressive else 0.45)
    tempo_n = deezer_tempo_n if deezer_tempo_n is not None else (0.60 if aggressive else 0.40)

    if vibe == "intimidator":
        base = (energy * 0.50
                + tempo_n * 0.20
                + (0.20 if explicit else 0.0)
                + (0.05 if aggressive else -0.10)
                + pop * 0.05)
    elif vibe == "crowd_pleaser":
        base = (energy * 0.20
                + tempo_n * 0.10
                + (0.25 if feel_good else 0.0)
                + pop * 0.35
                + (-0.10 if explicit else 0.0))
    elif vibe == "closer":
        base = (tempo_n * 0.45
                + energy * 0.35
                + pop * 0.15
                + (0.05 if aggressive else 0.0))
    else:  # auto
        base = (energy * 0.50
                + tempo_n * 0.25
                + pop * 0.15
                + (0.10 if explicit else 0.0))

    boost = 0.0
    if selected_genre and selected_genre in track_genre_buckets:
        boost += 0.35
    if team_genres and any(g in track_genre_buckets for g in team_genres):
        boost += 0.12

    return (base + boost) * time_weight


def _explain(winner, vibe, position, team_data):
    track = winner["track"]
    features = winner["features"]
    name = track["name"]
    artist = track["artists"][0]["name"]

    vibe_phrases = {
        "intimidator": "makes the other team nervous just hearing it",
        "crowd_pleaser": "gets the whole stadium on its feet",
        "closer": "signals the game is already over",
        "auto": "gets you locked in the moment it hits",
    }
    phrase = vibe_phrases.get(vibe, "fits your style")

    pos_labels = {
        "pitcher": "on the mound",
        "catcher": "behind the plate",
        "infielder": "in the infield",
        "outfielder": "in the outfield",
        "batter": "stepping to the plate",
        "dh": "stepping to the plate",
    }
    pos_label = pos_labels.get(position, "on the field")

    track_genres = winner.get("track_genres", [])

    pop = track.get("popularity", 0)
    if pop >= 70:
        pop_note = " The crowd will know every word."
    elif pop >= 40:
        pop_note = " A track with real presence."
    else:
        pop_note = " A deep cut that's entirely yours."

    city_note = ""
    if team_data and any(g in track_genres for g in team_data["genres"]):
        city_note = f" Sounds like {team_data['city']}."

    if features:
        energy_pct = round(features["energy"] * 100)
        bpm = round(features["tempo"])
        return (
            f'"{name}" by {artist} is your walk-up song -- '
            f"{energy_pct}% energy, {bpm} BPM, a track that {phrase}."
            f"{pop_note}{city_note} "
            f"Walk out {pos_label} and own it."
        )

    d_energy = track.get("deezer_energy")
    d_bpm = track.get("deezer_bpm")
    if d_energy is not None or d_bpm:
        parts = []
        if d_energy is not None:
            parts.append(f"{round(d_energy * 100)}% energy")
        if d_bpm:
            parts.append(f"{round(d_bpm)} BPM")
        data_str = ", ".join(parts)
        return (
            f'"{name}" by {artist} is your walk-up song -- '
            f"{data_str}, a track that {phrase}."
            f"{pop_note}{city_note} "
            f"Walk out {pos_label} and own it."
        )

    return (
        f'"{name}" by {artist} is your walk-up song -- '
        f"a track that {phrase}. "
        f"Walk out {pos_label} and own it."
    )


# ---------------------------------------------------------------------------
# Guest mode (no Spotify login) -- search catalog by quiz answers
# ---------------------------------------------------------------------------

_VIBE_SEARCH_TERMS = {
    "intimidator":   ["aggressive hype anthem", "hard hitting intense"],
    "crowd_pleaser": ["feel good party hit", "crowd anthem sing along"],
    "closer":        ["locked in pump up clutch", "focused intense power"],
    "auto":          ["pump up walkup anthem", "hype energy banger"],
}

_GENRE_SEARCH_TERMS = {
    "hip-hop":    "rap hip-hop",
    "rock":       "rock",
    "pop":        "pop",
    "r&b":        "r&b soul",
    "country":    "country",
    "electronic": "electronic edm",
    "latin":      "latin",
}


def guest_recommend(vibe="auto", position="batter", genre=None, team=None,
                    energy_pref="any", allow_explicit=True):
    """Recommend a walk-up song without Spotify user auth, using catalog search + Deezer enrichment."""
    try:
        cc = SpotifyClientCredentials(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        )
        sp = spotipy.Spotify(client_credentials_manager=cc)
    except Exception:
        return {"error": "Could not connect to Spotify. Try again later."}

    vibe_terms = _VIBE_SEARCH_TERMS.get(vibe, _VIBE_SEARCH_TERMS["auto"])
    genre_term = _GENRE_SEARCH_TERMS.get(genre, "") if genre else ""

    all_tracks = []
    seen_ids = set()
    for term in vibe_terms[:2]:
        q = f"{term} {genre_term}".strip()
        try:
            results = sp.search(q=q, type="track", limit=20)
            for t in results["tracks"]["items"]:
                if t["id"] not in seen_ids:
                    seen_ids.add(t["id"])
                    all_tracks.append(t)
        except Exception:
            continue

    if not all_tracks:
        return {"error": "Couldn't find matching songs. Try different settings."}

    if not allow_explicit:
        filtered = [t for t in all_tracks if not t.get("explicit", False)]
        if filtered:
            all_tracks = filtered

    enriched = enrich_tracks(all_tracks)

    if energy_pref == "high":
        hi = [t for t in enriched if t.get("deezer_energy") is not None and t["deezer_energy"] >= 0.55]
        if hi:
            enriched = hi
    elif energy_pref == "mid":
        mid = [t for t in enriched if t.get("deezer_energy") is None or 0.30 <= t["deezer_energy"] <= 0.70]
        if mid:
            enriched = mid

    team_genres = TEAMS_BY_ID[team]["genres"] if team and team in TEAMS_BY_ID else []
    track_genre_buckets = [genre] if genre else []

    candidates = []
    for t in enriched:
        d_energy = t.get("deezer_energy")
        d_tempo_n = deezer_tempo_norm(t.get("deezer_bpm")) if t.get("deezer_bpm") else None
        score = _score_fallback(
            vibe, 1.0, t.get("popularity", 50),
            track_genre_buckets, genre, team_genres,
            t.get("explicit", False), d_energy, d_tempo_n
        )
        candidates.append({"track": t, "features": None, "score": score, "track_genres": track_genre_buckets})

    if not candidates:
        return {"error": "Couldn't find a good match. Try different settings."}

    candidates.sort(key=lambda x: x["score"], reverse=True)
    winner = candidates[0]
    track = winner["track"]
    track_id = track["id"]
    images = track["album"]["images"]
    team_data = TEAMS_BY_ID.get(team) if team else None

    return {
        "name": track["name"],
        "artist": track["artists"][0]["name"],
        "album_art": images[0]["url"] if images else None,
        "spotify_url": track["external_urls"]["spotify"],
        "embed_url": f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator&theme=0",
        "explanation": _explain(winner, vibe, position, team_data),
        "energy": (round(track.get("deezer_energy") * 100) if track.get("deezer_energy") is not None else None),
        "tempo": (round(track.get("deezer_bpm")) if track.get("deezer_bpm") else None),
        "team": team_data,
        "guest_mode": True,
    }
