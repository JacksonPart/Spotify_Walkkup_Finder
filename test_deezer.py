import urllib.request
import json
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
))

# Test tracks covering different genres and energy levels
TEST_TRACKS = [
    "Do It Again - Steely Dan",
    "HUMBLE. - Kendrick Lamar",
    "Shake It Off - Taylor Swift",
    "Enter Sandman - Metallica",
    "Blinding Lights - The Weeknd",
    "God's Plan - Drake",
    "Bohemian Rhapsody - Queen",
    "industry baby - Lil Nas X",
    "Levitating - Dua Lipa",
    "Rich Flex - Drake",
]

def deezer_by_isrc(isrc):
    url = f"https://api.deezer.com/track/isrc:{isrc}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WalkUpSongFinder/1.0"})
        resp = urllib.request.urlopen(req, timeout=6)
        data = json.loads(resp.read())
        if "error" in data:
            return None
        return data
    except Exception:
        return None

print(f"{'Track':<35} {'Artist':<20} {'BPM':>5} {'Gain':>7} {'Rank':>8} {'Explicit':>8}")
print("-" * 90)

for query in TEST_TRACKS:
    try:
        results = sp.search(q=query, type="track", limit=1)
        items = results["tracks"]["items"]
        if not items:
            continue
        track = items[0]
        isrc = track.get("external_ids", {}).get("isrc", "")
        name = track["name"][:33]
        artist = track["artists"][0]["name"][:18]

        if not isrc:
            print(f"{name:<35} {artist:<20} {'no ISRC':>5}")
            continue

        d = deezer_by_isrc(isrc)
        if not d:
            print(f"{name:<35} {artist:<20} {'not found':>5}")
            continue

        bpm    = d.get("bpm", 0)
        gain   = d.get("gain", "?")
        rank   = d.get("rank", "?")
        expl   = "yes" if d.get("explicit_lyrics") else "no"

        print(f"{name:<35} {artist:<20} {bpm:>5} {str(gain):>7} {str(rank):>8} {expl:>8}")

    except Exception as e:
        print(f"Error on {query}: {e}")
