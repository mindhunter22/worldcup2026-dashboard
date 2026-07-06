"""
Génère un jeu de données fictif au même format que la sortie attendue de
fetch_api_football.py. Objectif : développer et tester tout le pipeline
(build_star_schema.py) ainsi que le modèle Power BI sans dépendre d'une
clé API pendant la phase de construction.
"""
import random
from pathlib import Path

import pandas as pd

TEAMS = [
    {"id": 1, "name": "France", "iso": "fr"},
    {"id": 2, "name": "Bresil", "iso": "br"},
    {"id": 3, "name": "Argentine", "iso": "ar"},
    {"id": 4, "name": "Espagne", "iso": "es"},
    {"id": 5, "name": "Angleterre", "iso": "gb-eng"},
    {"id": 6, "name": "Maroc", "iso": "ma"},
    {"id": 7, "name": "Allemagne", "iso": "de"},
    {"id": 8, "name": "Portugal", "iso": "pt"},
]

FIRST_NAMES = ["Karim", "Luis", "Mateo", "Youssef", "Jude", "Achraf", "Jamal", "Kylian",
               "Erling", "Vinicius", "Pedri", "Bukayo", "Florian", "Jonathan", "Nico", "Lamine"]
LAST_NAMES = ["Benzema", "Diaz", "Fernandez", "El Khalfi", "Bellingham", "Hakimi",
              "Musiala", "Mbappe", "Haaland", "Junior", "Gonzalez", "Saka", "Wirtz",
              "David", "Williams", "Yamal"]


def generate_raw_player_stats(n_players: int = 32, n_matches: int = 4, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    rows = []
    player_id = 1000
    for _ in range(n_players):
        team = random.choice(TEAMS)
        nom = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        photo_url = f"https://media.api-sports.io/football/players/{player_id}.png"
        for match_num in range(1, n_matches + 1):
            rows.append({
                "player_id": player_id,
                "nom": nom,
                "nationalite": team["name"],
                "photo_url": photo_url,
                "equipe_id": team["id"],
                "equipe": team["name"],
                "logo_equipe_url": f"https://media.api-sports.io/football/teams/{team['id']}.png",
                "drapeau_url": f"https://flagcdn.com/w320/{team['iso']}.png",
                "match_id": match_num,
                "date": f"2026-06-{10 + match_num}",
                "buts": random.choices([0, 1, 2, 3], weights=[55, 30, 10, 5])[0],
                "passes_decisives": random.choices([0, 1, 2], weights=[70, 25, 5])[0],
                "xg": round(random.uniform(0, 1.8), 2),
                "tirs": random.randint(0, 6),
                "minutes": random.choice([90, 90, 90, 60, 45, 75]),
            })
        player_id += 1
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_raw_player_stats()
    out_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "mock_players_stats.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"OK : {len(df)} lignes generees -> {out_path}")
