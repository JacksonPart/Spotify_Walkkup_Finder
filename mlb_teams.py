MLB_TEAMS = [
    # AL East
    {"id": "bal", "name": "Baltimore Orioles",     "city": "Baltimore",    "genres": ["hip-hop", "r&b"],       "primary": "#DF4601", "secondary": "#EFB21E"},
    {"id": "bos", "name": "Boston Red Sox",         "city": "Boston",       "genres": ["rock", "pop"],          "primary": "#BD3039", "secondary": "#0C2340"},
    {"id": "nyy", "name": "New York Yankees",       "city": "New York",     "genres": ["hip-hop", "pop"],       "primary": "#132448", "secondary": "#C4CED4"},
    {"id": "tb",  "name": "Tampa Bay Rays",         "city": "Tampa Bay",    "genres": ["hip-hop", "pop"],       "primary": "#092C5C", "secondary": "#8FBCE6"},
    {"id": "tor", "name": "Toronto Blue Jays",      "city": "Toronto",      "genres": ["pop", "hip-hop"],       "primary": "#134A8E", "secondary": "#E8291C"},
    # AL Central
    {"id": "chw", "name": "Chicago White Sox",      "city": "Chicago",      "genres": ["hip-hop", "r&b"],       "primary": "#27251F", "secondary": "#C4CED4"},
    {"id": "cle", "name": "Cleveland Guardians",    "city": "Cleveland",    "genres": ["rock", "hip-hop"],      "primary": "#00385D", "secondary": "#E31937"},
    {"id": "det", "name": "Detroit Tigers",         "city": "Detroit",      "genres": ["hip-hop", "rock"],      "primary": "#0C2340", "secondary": "#FA4616"},
    {"id": "kc",  "name": "Kansas City Royals",     "city": "Kansas City",  "genres": ["country", "rock"],      "primary": "#004687", "secondary": "#C09A5B"},
    {"id": "min", "name": "Minnesota Twins",        "city": "Minneapolis",  "genres": ["rock", "pop"],          "primary": "#002B5C", "secondary": "#D31145"},
    # AL West
    {"id": "hou", "name": "Houston Astros",         "city": "Houston",      "genres": ["hip-hop", "country"],   "primary": "#002D62", "secondary": "#EB6E1F"},
    {"id": "laa", "name": "Los Angeles Angels",     "city": "Anaheim",      "genres": ["pop", "hip-hop"],       "primary": "#BA0021", "secondary": "#003263"},
    {"id": "oak", "name": "Athletics",              "city": "Sacramento",   "genres": ["hip-hop", "rock"],      "primary": "#003831", "secondary": "#EFB21E"},
    {"id": "sea", "name": "Seattle Mariners",       "city": "Seattle",      "genres": ["rock", "electronic"],   "primary": "#0C2C56", "secondary": "#005C5C"},
    {"id": "tex", "name": "Texas Rangers",          "city": "Arlington",    "genres": ["country", "hip-hop"],   "primary": "#003278", "secondary": "#C0111F"},
    # NL East
    {"id": "atl", "name": "Atlanta Braves",         "city": "Atlanta",      "genres": ["hip-hop", "r&b"],       "primary": "#CE1141", "secondary": "#13274F"},
    {"id": "mia", "name": "Miami Marlins",          "city": "Miami",        "genres": ["latin", "hip-hop"],     "primary": "#00A3E0", "secondary": "#FF6600"},
    {"id": "nym", "name": "New York Mets",          "city": "New York",     "genres": ["hip-hop", "pop"],       "primary": "#002D72", "secondary": "#FF5910"},
    {"id": "phi", "name": "Philadelphia Phillies",  "city": "Philadelphia", "genres": ["hip-hop", "r&b"],       "primary": "#E81828", "secondary": "#002D72"},
    {"id": "wsh", "name": "Washington Nationals",   "city": "Washington DC","genres": ["hip-hop", "r&b"],       "primary": "#AB0003", "secondary": "#14225A"},
    # NL Central
    {"id": "chc", "name": "Chicago Cubs",           "city": "Chicago",      "genres": ["hip-hop", "rock"],      "primary": "#0E3386", "secondary": "#CC3433"},
    {"id": "cin", "name": "Cincinnati Reds",        "city": "Cincinnati",   "genres": ["rock", "country"],      "primary": "#C6011F", "secondary": "#000000"},
    {"id": "mil", "name": "Milwaukee Brewers",      "city": "Milwaukee",    "genres": ["rock", "country"],      "primary": "#12284B", "secondary": "#FFC52F"},
    {"id": "pit", "name": "Pittsburgh Pirates",     "city": "Pittsburgh",   "genres": ["hip-hop", "rock"],      "primary": "#27251F", "secondary": "#FDB827"},
    {"id": "stl", "name": "St. Louis Cardinals",    "city": "St. Louis",    "genres": ["country", "rock"],      "primary": "#C41E3A", "secondary": "#FEDB00"},
    # NL West
    {"id": "ari", "name": "Arizona Diamondbacks",   "city": "Phoenix",      "genres": ["country", "hip-hop"],   "primary": "#A71930", "secondary": "#E3D4AD"},
    {"id": "col", "name": "Colorado Rockies",       "city": "Denver",       "genres": ["country", "rock"],      "primary": "#33006F", "secondary": "#C4CED4"},
    {"id": "lad", "name": "Los Angeles Dodgers",    "city": "Los Angeles",  "genres": ["hip-hop", "pop"],       "primary": "#005A9C", "secondary": "#EF3E42"},
    {"id": "sd",  "name": "San Diego Padres",       "city": "San Diego",    "genres": ["hip-hop", "pop"],       "primary": "#2F241D", "secondary": "#FFC425"},
    {"id": "sf",  "name": "San Francisco Giants",   "city": "San Francisco","genres": ["rock", "hip-hop"],      "primary": "#FD5A1E", "secondary": "#27251F"},
]

TEAMS_BY_ID = {t["id"]: t for t in MLB_TEAMS}


def logo_url(team_id):
    return f"https://a.espncdn.com/i/teamlogos/mlb/500/{team_id}.png"
