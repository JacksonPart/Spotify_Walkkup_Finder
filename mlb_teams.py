MLB_TEAMS = [
    # AL East
    {"id": "bal", "name": "Baltimore Orioles",     "city": "Baltimore",    "genres": ["hip-hop", "r&b"]},
    {"id": "bos", "name": "Boston Red Sox",         "city": "Boston",       "genres": ["rock", "pop"]},
    {"id": "nyy", "name": "New York Yankees",       "city": "New York",     "genres": ["hip-hop", "pop"]},
    {"id": "tb",  "name": "Tampa Bay Rays",         "city": "Tampa Bay",    "genres": ["hip-hop", "pop"]},
    {"id": "tor", "name": "Toronto Blue Jays",      "city": "Toronto",      "genres": ["pop", "hip-hop"]},
    # AL Central
    {"id": "chw", "name": "Chicago White Sox",      "city": "Chicago",      "genres": ["hip-hop", "r&b"]},
    {"id": "cle", "name": "Cleveland Guardians",    "city": "Cleveland",    "genres": ["rock", "hip-hop"]},
    {"id": "det", "name": "Detroit Tigers",         "city": "Detroit",      "genres": ["hip-hop", "rock"]},
    {"id": "kc",  "name": "Kansas City Royals",     "city": "Kansas City",  "genres": ["country", "rock"]},
    {"id": "min", "name": "Minnesota Twins",        "city": "Minneapolis",  "genres": ["rock", "pop"]},
    # AL West
    {"id": "hou", "name": "Houston Astros",         "city": "Houston",      "genres": ["hip-hop", "country"]},
    {"id": "laa", "name": "Los Angeles Angels",     "city": "Anaheim",      "genres": ["pop", "hip-hop"]},
    {"id": "oak", "name": "Athletics",              "city": "Sacramento",   "genres": ["hip-hop", "rock"]},
    {"id": "sea", "name": "Seattle Mariners",       "city": "Seattle",      "genres": ["rock", "electronic"]},
    {"id": "tex", "name": "Texas Rangers",          "city": "Arlington",    "genres": ["country", "hip-hop"]},
    # NL East
    {"id": "atl", "name": "Atlanta Braves",         "city": "Atlanta",      "genres": ["hip-hop", "r&b"]},
    {"id": "mia", "name": "Miami Marlins",          "city": "Miami",        "genres": ["latin", "hip-hop"]},
    {"id": "nym", "name": "New York Mets",          "city": "New York",     "genres": ["hip-hop", "pop"]},
    {"id": "phi", "name": "Philadelphia Phillies",  "city": "Philadelphia", "genres": ["hip-hop", "r&b"]},
    {"id": "wsh", "name": "Washington Nationals",   "city": "Washington DC","genres": ["hip-hop", "r&b"]},
    # NL Central
    {"id": "chc", "name": "Chicago Cubs",           "city": "Chicago",      "genres": ["hip-hop", "rock"]},
    {"id": "cin", "name": "Cincinnati Reds",        "city": "Cincinnati",   "genres": ["rock", "country"]},
    {"id": "mil", "name": "Milwaukee Brewers",      "city": "Milwaukee",    "genres": ["rock", "country"]},
    {"id": "pit", "name": "Pittsburgh Pirates",     "city": "Pittsburgh",   "genres": ["hip-hop", "rock"]},
    {"id": "stl", "name": "St. Louis Cardinals",    "city": "St. Louis",    "genres": ["country", "rock"]},
    # NL West
    {"id": "ari", "name": "Arizona Diamondbacks",   "city": "Phoenix",      "genres": ["country", "hip-hop"]},
    {"id": "col", "name": "Colorado Rockies",       "city": "Denver",       "genres": ["country", "rock"]},
    {"id": "lad", "name": "Los Angeles Dodgers",    "city": "Los Angeles",  "genres": ["hip-hop", "pop"]},
    {"id": "sd",  "name": "San Diego Padres",       "city": "San Diego",    "genres": ["hip-hop", "pop"]},
    {"id": "sf",  "name": "San Francisco Giants",   "city": "San Francisco","genres": ["rock", "hip-hop"]},
]

TEAMS_BY_ID = {t["id"]: t for t in MLB_TEAMS}


def logo_url(team_id):
    return f"https://a.espncdn.com/i/teamlogos/mlb/500/{team_id}.png"
