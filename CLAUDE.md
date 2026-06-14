# Walk-Up Song Finder

## Project Overview
A web app that reads a user's Spotify listening history and determines their baseball walk-up song.
Users connect via Spotify OAuth, choose between fully automatic analysis or a short quiz (position + vibe),
and receive one song recommendation with an explanation.

Beta testing uses the owner's Spotify account. Public launch allows anyone to connect their Spotify.

Two modes:
- Auto: pure data, scored by energy / tempo / top tracks
- Quiz: user picks their position, team, and vibe (intimidator, crowd pleaser -- add more later)

## Goals
- Users open a link, connect Spotify, and get their walk-up song in under 60 seconds
- Output: one song, one explanation, an embedded Spotify player
- Deploy for free on Render, source hosted on GitHub

## Tech Stack
- Python + Flask (server-rendered)
- spotipy (Spotify Web API wrapper)
- Hosted on Render (free tier)
- python-dotenv for local env var loading

## File Structure
```
app.py                  -- Flask routes and OAuth flow
spotify_analyzer.py     -- Scoring algorithm and explanation builder
templates/
  layout.html           -- Base template
  index.html            -- Landing / connect page
  quiz.html             -- Mode toggle + position/vibe quiz
  result.html           -- Walk-up song result
requirements.txt
Procfile                -- gunicorn start command for Render
.env.example            -- Template for required env vars
.gitignore
```

## Environment Variables (never hardcode these)
| Variable | Description |
|---|---|
| `SPOTIPY_CLIENT_ID` | From Spotify Developer Dashboard |
| `SPOTIPY_CLIENT_SECRET` | From Spotify Developer Dashboard |
| `SPOTIPY_REDIRECT_URI` | Must match exactly in Spotify Dashboard |
| `FLASK_SECRET_KEY` | Any long random string -- signs session cookies |
| `FLASK_ENV` | Set to `development` locally, omit in production |

## Spotify Scopes
- `user-top-read` -- reads top tracks across three time windows (short/medium/long term)

## Algorithm
Pulls up to 50 unique top tracks, fetches audio features (energy, tempo, valence, danceability),
scores each track by vibe weights, returns the winner.

Vibes and their scoring weights:
- `auto` -- energy 40%, tempo 30%, valence 20%, danceability 10%
- `intimidator` -- energy 50%, tempo 30%, low-valence 15%, danceability 5%
- `crowd_pleaser` -- valence 35%, energy 25%, danceability 25%, tempo 15%
- `closer` -- energy 45%, tempo 35%, low-valence 10%, danceability 10%

Fallback: if audio features API is unavailable (Spotify restriction on new apps),
score by track popularity instead.

## Known Constraints
- Spotify restricted audio features access for apps created after Nov 2023.
  If features are unavailable, the fallback returns the most popular top track.
- Render free tier spins down after inactivity -- first load after idle takes ~30s.

## Conventions
- Never hardcode credentials -- always use os.getenv()
- Keep scoring logic in spotify_analyzer.py, routing in app.py
- Add new vibes or positions in spotify_analyzer.py first, then mirror in quiz.html
- No database -- sessions are cookie-based (Flask session)

## Deployment (Render)
1. Push code to GitHub
2. Create new Web Service on Render, connect the repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add all env vars in Render dashboard
6. Copy the Render URL, add `https://<your-app>.onrender.com/callback` to Spotify Dashboard redirect URIs
7. Update `SPOTIPY_REDIRECT_URI` env var on Render to match
