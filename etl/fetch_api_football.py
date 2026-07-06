"""
Récupère les statistiques joueurs au grain "match" (nécessaire pour
Fact_Performances) via l'endpoint /fixtures/players de l'API-Football,
fixture par fixture.

IMPORTANT : l'API-Football ne fournit pas le xG nativement. Pour le xG,
il faudra enrichir via scrape_fbref.py et faire un merge sur (joueur, date)
ou (joueur, match_id) -- prochaine étape du pipeline.
"""
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}


def get_fixtures(league_id: int = 1, season: int = 2026) -> list[dict]:
    resp = requests.get(
        f"{BASE_URL}/fixtures", headers=HEADERS,
        params={"league": league_id, "season": season},
    )
    resp.raise_for_status()
    return resp.json()["response"]


def get_fixture_player_stats(fixture_id: int) -> list[dict]:
    resp = requests.get(
        f"{BASE_URL}/fixtures/players", headers=HEADERS,
        params={"fixture": fixture_id},
    )
    resp.raise_for_status()
    return resp.json()["response"]


def build_raw_table(league_id: int = 1, season: int = 2026) -> pd.DataFrame:
    fixtures = get_fixtures(league_id, season)
    rows = []
    for fx in fixtures:
        fixture_id = fx["fixture"]["id"]
        fixture_date = fx["fixture"]["date"][:10]
        time.sleep(1.2)  # respecte le rate-limit du plan API
        for team_block in get_fixture_player_stats(fixture_id):
            team = team_block["team"]
            for p in team_block["players"]:
                player, stats = p["player"], p["statistics"][0]
                rows.append({
                    "player_id": player["id"],
                    "nom": player["name"],
                    "nationalite": team["name"],
                    "photo_url": player["photo"],
                    "equipe_id": team["id"],
                    "equipe": team["name"],
                    "logo_equipe_url": team["logo"],
                    "drapeau_url": None,  # a enrichir : mapping equipe -> code ISO -> flagcdn
                    "match_id": fixture_id,
                    "date": fixture_date,
                    "buts": (stats.get("goals") or {}).get("total") or 0,
                    "passes_decisives": (stats.get("goals") or {}).get("assists") or 0,
                    "xg": None,  # cf. note en tete de fichier
                    "tirs": (stats.get("shots") or {}).get("total") or 0,
                    "minutes": (stats.get("games") or {}).get("minutes") or 0,
                })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("API_FOOTBALL_KEY manquante : copie .env.example en .env et renseigne ta cle.")
    df = build_raw_table()
    out_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "api_football_players_stats.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"OK : {len(df)} lignes -> {out_path}")
