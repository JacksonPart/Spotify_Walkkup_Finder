import urllib.request
import json

# --- Deezer (free, no API key needed) ---
print("=== DEEZER ===")
deezer_url = "https://api.deezer.com/search?q=Do+It+Again+Steely+Dan&limit=3"
req = urllib.request.urlopen(deezer_url, timeout=8)
data = json.loads(req.read())
track = data["data"][0]
track_id = track["id"]

detail_url = f"https://api.deezer.com/track/{track_id}"
req2 = urllib.request.urlopen(detail_url, timeout=8)
detail = json.loads(req2.read())

fields = ["title", "duration", "rank", "bpm", "gain", "explicit_lyrics"]
print(json.dumps({k: detail.get(k, "NOT PRESENT") for k in fields}, indent=2))

# --- MusicBrainz (free, open source, no key) ---
print("\n=== MUSICBRAINZ ===")
import urllib.parse
query = urllib.parse.quote('recording:"Do It Again" AND artist:"Steely Dan"')
mb_url = f"https://musicbrainz.org/ws/2/recording/?query={query}&limit=1&fmt=json"
req3 = urllib.request.Request(mb_url, headers={"User-Agent": "WalkUpSongFinder/1.0"})
req3 = urllib.request.urlopen(req3, timeout=8)
mb_data = json.loads(req3.read())
rec = mb_data["recordings"][0]
print(json.dumps({
    "title": rec.get("title"),
    "score": rec.get("score"),
    "length_ms": rec.get("length"),
    "disambiguation": rec.get("disambiguation", ""),
    "first_release_date": rec.get("first-release-date"),
}, indent=2))
