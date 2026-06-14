import os
from flask import Flask, session, redirect, request, url_for, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from dotenv import load_dotenv
from spotify_analyzer import analyze_walkup_song, get_top_genres, get_debug_data, GENRE_DISPLAY_NAMES
from mlb_teams import MLB_TEAMS, logo_url

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-in-production")

SCOPE = "user-top-read"


def make_oauth():
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope=SCOPE,
        cache_handler=FlaskSessionCacheHandler(session),
        show_dialog=True,
    )


def get_sp():
    oauth = make_oauth()
    token_info = oauth.validate_token(session.get("token_info"))
    if not token_info:
        return None
    session["token_info"] = token_info
    return spotipy.Spotify(auth=token_info["access_token"])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return redirect(make_oauth().get_authorize_url())


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("index"))
    token_info = make_oauth().get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for("quiz"))


@app.route("/quiz")
def quiz():
    if "token_info" not in session:
        return redirect(url_for("index"))
    sp = get_sp()
    if not sp:
        return redirect(url_for("login"))

    top_genres = get_top_genres(sp)
    genre_options = [{"key": g, "label": GENRE_DISPLAY_NAMES.get(g, g.title())} for g in top_genres]

    teams_with_logos = [{"id": t["id"], "name": t["name"], "logo": logo_url(t["id"])} for t in MLB_TEAMS]

    return render_template("quiz.html", genre_options=genre_options, teams=teams_with_logos)


@app.route("/analyze", methods=["POST"])
def analyze():
    if "token_info" not in session:
        return redirect(url_for("index"))
    sp = get_sp()
    if not sp:
        return redirect(url_for("login"))

    vibe = request.form.get("vibe", "auto")
    position = request.form.get("position", "batter")
    genre = request.form.get("genre") or None
    team = request.form.get("team") or None

    result = analyze_walkup_song(sp, vibe=vibe, position=position, genre=genre, team=team)
    if "error" in result:
        return render_template("index.html", error=result["error"])

    return render_template("result.html", result=result)


@app.route("/debug")
def debug():
    if "token_info" not in session:
        return redirect(url_for("index"))
    sp = get_sp()
    if not sp:
        return redirect(url_for("login"))
    data = get_debug_data(sp)
    if not data:
        return render_template("index.html", error="Could not load debug data.")
    return render_template("debug.html", data=data)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
