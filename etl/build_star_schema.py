"""
Transforme une table brute "1 ligne = 1 perf joueur/match" en schéma en
étoile pret pour Power BI : Dim_Joueurs, Dim_Equipes, Dim_Calendrier,
Fact_Performances. Fonctionne avec n'importe quelle source brute qui
respecte les colonnes attendues (mock, API-Football, FBref normalisé).
"""
import sys
from pathlib import Path

import pandas as pd
import pycountry

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "processed"

# Alias pour les noms d'equipe qui ne matchent pas le nom officiel ISO
# (a completer si la console affiche un avertissement "drapeau introuvable")
COUNTRY_ALIASES = {
    "usa": "US",
    "united states": "US",
    "south korea": "KR",
    "korea republic": "KR",
    "north korea": "KP",
    "iran": "IR",
    "ivory coast": "CI",
    "cote d'ivoire": "CI",
    "czech republic": "CZ",
    "england": "GB-ENG",
    "scotland": "GB-SCT",
    "wales": "GB-WLS",
    "russia": "RU",
    "bolivia": "BO",
    "venezuela": "VE",
    "tanzania": "TZ",
    "drc": "CD",
    "dr congo": "CD",
    "congo dr": "CD",
    "bosnia & herzegovina": "BA",
    "cape verde islands": "CV",
    "cape verde": "CV",
}


def get_iso2(country_name: str) -> str | None:
    key = country_name.strip().lower()
    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key]
    try:
        match = pycountry.countries.search_fuzzy(country_name)
        return match[0].alpha_2
    except LookupError:
        print(f"[WARN] drapeau introuvable pour : {country_name!r} -- ajoute un alias dans COUNTRY_ALIASES")
        return None


def build_dim_joueurs(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df[["player_id", "nom", "nationalite", "photo_url", "equipe_id"]]
        .drop_duplicates(subset="player_id")
        .rename(columns={
            "player_id": "Joueur_ID", "nom": "Nom", "nationalite": "Nationalite",
            "photo_url": "URL_Photo", "equipe_id": "Equipe_ID",
        })
    )


def build_dim_equipes(df: pd.DataFrame) -> pd.DataFrame:
    dim = (
        df[["equipe_id", "equipe", "logo_equipe_url"]]
        .drop_duplicates(subset="equipe_id")
        .rename(columns={
            "equipe_id": "Equipe_ID", "equipe": "Nom_Equipe",
            "logo_equipe_url": "URL_Logo",
        })
    )
    dim["ISO2"] = dim["Nom_Equipe"].apply(get_iso2)
    dim["URL_Drapeau"] = dim["ISO2"].apply(
        lambda iso: f"https://flagcdn.com/w320/{iso.lower()}.png" if pd.notna(iso) else None
    )
    return dim.drop(columns="ISO2")


def build_dim_calendrier(df: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(df["date"].unique())
    cal = pd.DataFrame({"Date": sorted(dates)})
    cal["Date_ID"] = cal["Date"].dt.strftime("%Y%m%d").astype(int)
    cal["Jour_Semaine"] = cal["Date"].dt.day_name()
    cal["Mois"] = cal["Date"].dt.month_name()
    return cal[["Date_ID", "Date", "Jour_Semaine", "Mois"]]


def build_fact_performances(df: pd.DataFrame) -> pd.DataFrame:
    fact = df.copy()
    fact["Date_ID"] = pd.to_datetime(fact["date"]).dt.strftime("%Y%m%d").astype(int)
    return fact.rename(columns={
        "match_id": "Match_ID", "player_id": "Joueur_ID", "equipe_id": "Equipe_ID",
        "buts": "Buts", "passes_decisives": "Passes_Decisives", "xg": "xG",
        "tirs": "Tirs", "minutes": "Minutes_Jouees",
    })[[
        "Match_ID", "Joueur_ID", "Equipe_ID", "Date_ID",
        "Buts", "Passes_Decisives", "xG", "Tirs", "Minutes_Jouees",
    ]]


def main(raw_filename: str = "mock_players_stats.csv"):
    raw_path = ROOT / "data" / "raw" / raw_filename
    df = pd.read_csv(raw_path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    tables = {
        "Dim_Joueurs": build_dim_joueurs(df),
        "Dim_Equipes": build_dim_equipes(df),
        "Dim_Calendrier": build_dim_calendrier(df),
        "Fact_Performances": build_fact_performances(df),
    }
    for name, table in tables.items():
        path = OUT_DIR / f"{name}.csv"
        table.to_csv(path, index=False)
        print(f"OK : {name} -> {len(table)} lignes -> {path}")


if __name__ == "__main__":
    # Permet : python build_star_schema.py api_football_players_stats.csv
    filename = sys.argv[1] if len(sys.argv) > 1 else "mock_players_stats.csv"
    main(filename)
