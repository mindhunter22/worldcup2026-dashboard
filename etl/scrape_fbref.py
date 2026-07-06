"""
Scraping FBref pour les stats de base de la Coupe du Monde 2026.

CONTEXTE IMPORTANT : depuis janvier 2026, FBref a perdu l'acces aux
statistiques avancees (xG, passes progressives, shot-creating actions...)
suite a un litige avec son fournisseur de donnees (Stats Perform/Opta),
devenu entre-temps fournisseur officiel exclusif de la FIFA pour le
Mondial 2026. Resultat : seules les stats "basiques" (buts, passes
decisives, presences, cartons) restent disponibles gratuitement. Pas de
xG gratuit possible actuellement pour cette competition -- la mesure DAX
Team_Efficiency sera adaptee en consequence (cf. discussion en cours).

FBref masque certaines tables dans des commentaires HTML pour freiner le
scraping naif -- ce script gere ce cas.

ETAPE 1 (ce fichier en mode decouverte) : on liste les tables reellement
presentes sur les pages cibles avant d'ecrire l'extraction definitive.
"""
import time
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment

HEADERS_SCRAPE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

STATS_URL = "https://fbref.com/en/comps/1/World-Cup-Stats"
SCHEDULE_URL = "https://fbref.com/en/comps/1/schedule/World-Cup-Scores-and-Fixtures"


def _get_soup(url: str) -> BeautifulSoup:
    time.sleep(3)  # throttle obligatoire, ne pas descendre en dessous
    session = requests.Session()
    session.headers.update(HEADERS_SCRAPE)
    session.get("https://fbref.com/en/", timeout=15)  # cookies avant la vraie requete
    time.sleep(1)
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def list_table_ids(url: str) -> list[str]:
    """Liste tous les ids de table presents sur la page, y compris ceux
    caches dans des commentaires HTML (technique anti-scraping de FBref)."""
    soup = _get_soup(url)
    ids = [t.get("id") for t in soup.find_all("table") if t.get("id")]

    comments = soup.find_all(string=lambda s: isinstance(s, Comment))
    for c in comments:
        inner = BeautifulSoup(c, "lxml")
        ids += [t.get("id") for t in inner.find_all("table") if t.get("id")]
    return ids


def scrape_table(url: str, table_id: str) -> Optional[pd.DataFrame]:
    """Recupere une table precise par son id, qu'elle soit visible
    directement ou planquee dans un commentaire HTML."""
    soup = _get_soup(url)
    table = soup.find("table", {"id": table_id})

    if table is None:
        comments = soup.find_all(string=lambda s: isinstance(s, Comment))
        for c in comments:
            if table_id in c:
                inner = BeautifulSoup(c, "lxml")
                table = inner.find("table", {"id": table_id})
                if table:
                    break

    if table is None:
        return None
    return pd.read_html(str(table))[0]


if __name__ == "__main__":
    print("Tables disponibles sur la page stats joueurs :")
    for tid in list_table_ids(STATS_URL):
        print(" -", tid)

    print("\nTables disponibles sur la page calendrier :")
    for tid in list_table_ids(SCHEDULE_URL):
        print(" -", tid)
