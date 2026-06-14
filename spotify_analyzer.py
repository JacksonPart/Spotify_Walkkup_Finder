from mlb_teams import TEAMS_BY_ID

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
        candidates = [
            {"track": t, "features": None, "score": (t.get("popularity", 0) / 100.0) * w}
            for t, w in weighted_tracks
        ]

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
        "energy": round(features["energy"] * 100) if features else None,
        "tempo": round(features["tempo"]) if features else None,
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
        base = energy * 0.50 + tempo_norm * 0.30 + (1 - valence) * 0.12 + danceability * 0.03 + pop_norm * 0.05
    elif vibe == "crowd_pleaser":
        base = energy * 0.22 + tempo_norm * 0.13 + valence * 0.25 + danceability * 0.20 + pop_norm * 0.20
    elif vibe == "closer":
        base = energy * 0.45 + tempo_norm * 0.35 + (1 - valence) * 0.10 + danceability * 0.05 + pop_norm * 0.05
    else:  # auto
        base = energy * 0.50 + tempo_norm * 0.30 + danceability * 0.15 + pop_norm * 0.05

    if position == "pitcher":
        base += features.get("instrumentalness", 0) * 0.05
    elif position == "catcher":
        base += (1 - features.get("speechiness", 0)) * 0.03

    genre_boost = 0.0
    if selected_genre and selected_genre in track_genre_buckets:
        genre_boost += 0.20
    if team_genres and any(g in track_genre_buckets for g in team_genres):
        genre_boost += 0.08

    return (base + genre_boost) * time_weight


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

    if features:
        energy_pct = round(features["energy"] * 100)
        bpm = round(features["tempo"])
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

        return (
            f'"{name}" by {artist} is your walk-up song -- '
            f"{energy_pct}% energy, {bpm} BPM, a track that {phrase}."
            f"{pop_note}{city_note} "
            f"Walk out {pos_label} and own it."
        )
    else:
        return (
            f'"{name}" by {artist} is your walk-up song -- '
            f"a track that {phrase}. "
            f"Walk out {pos_label} and own it."
        )
