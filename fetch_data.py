import pandas as pd
import requests
from bs4 import BeautifulSoup
import time


def scrape_world_cup_stats():
    print("⏳ Connexion à FBref en cours...")

    # URL des statistiques des joueurs (Standard Stats)
    # Note: On utilise l'URL générique de la Coupe du Monde sur FBref
    url = "https://fbref.com/en/comps/1/stats/World-Cup-Stats"

    # Un "User-Agent" pour dire à FBref qu'on est un navigateur normal, pas un robot malveillant
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # On utilise Pandas pour lire directement tous les tableaux HTML de la page
        tables = pd.read_html(response.text)

        # Le tableau des joueurs est généralement le 3ème sur cette page (index 2)
        # Mais on va chercher celui qui s'appelle 'stats_standard'
        soup = BeautifulSoup(response.text, "lxml")
        table_html = soup.find("table", {"id": "stats_standard"})

        if table_html is None:
            print("⚠️ Impossible de trouver le tableau des joueurs. FBref a peut-être bloqué la requête.")
            return

        df = pd.read_html(str(table_html))[0]

        print("✅ Données brutes récupérées ! Nettoyage en cours...")

        # FBref utilise des "doubles en-têtes" (MultiIndex), on les aplatit
        df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns.values]

        # On nettoie les noms de colonnes pour Power BI
        colonnes_a_garder = {
            'Unnamed: 1_level_0_Player': 'nom',
            'Unnamed: 2_level_0_Nation': 'nationalite',
            'Unnamed: 3_level_0_Pos': 'poste',
            'Unnamed: 4_level_0_Squad': 'equipe',
            'Unnamed: 5_level_0_Age': 'age',
            'Playing Time_Min': 'minutes',
            'Performance_Gls': 'buts',
            'Performance_Ast': 'passes_decisives',
            'Expected_xG': 'xG'
        }

        df = df.rename(columns=colonnes_a_garder)

        # On ne garde que les colonnes qui nous intéressent
        df_final = df[list(colonnes_a_garder.values())].copy()

        # Suppression des lignes de séparation que FBref insère tous les 20 joueurs
        df_final = df_final[df_final['nom'] != 'Player']

        # Création du CSV
        df_final.to_csv("players_stats_2026.csv", index=False, encoding='utf-8-sig')
        print(f"🎉 Succès absolu ! Fichier CSV généré avec {len(df_final)} joueurs de la Coupe du Monde.")

    except Exception as e:
        print(f"❌ Une erreur est survenue lors du scraping : {e}")


if __name__ == "__main__":
    scrape_world_cup_stats()