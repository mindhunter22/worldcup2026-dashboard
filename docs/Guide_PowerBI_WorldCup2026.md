# Guide Technique — World Cup 2026 Live Analytics (Power BI)

Stack : Python (acquisition) → Power Query (ETL) → Power BI (modèle + DAX + viz)

---

## 1. Stratégie d'acquisition de données

Deux sources complémentaires : **API-Football** (rapide, fiable, JSON propre, URLs d'images natives) pour le live/automatisation, et **FBref** (scraping) pour les stats avancées que l'API ne couvre pas toujours (xG détaillé, progressive passes, etc.).

### 1.1 API-Football (recommandé pour le refresh automatique)

```python
import requests
import pandas as pd

API_KEY = "VOTRE_CLE_API"  # RapidAPI ou api-sports.io direct
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

def get_players_stats(league_id=1, season=2026):
    """league_id=1 = World Cup sur API-Football"""
    url = f"{BASE_URL}/players"
    params = {"league": league_id, "season": season}
    data = requests.get(url, headers=HEADERS, params=params).json()["response"]

    rows = []
    for item in data:
        p, s = item["player"], item["statistics"][0]
        rows.append({
            "player_id": p["id"],
            "nom": p["name"],
            "nationalite": p["nationality"],
            "photo_url": p["photo"],                      # URL directe, prête pour Power BI
            "equipe": s["team"]["name"],
            "logo_equipe_url": s["team"]["logo"],          # idem
            "buts": s["goals"]["total"] or 0,
            "passes_decisives": s["goals"]["assists"] or 0,
            "xg": (s.get("expected") or {}).get("goals"),
            "minutes": s["games"]["minutes"] or 0,
        })
    return pd.DataFrame(rows)

def get_fixtures(league_id=1, season=2026):
    url = f"{BASE_URL}/fixtures"
    params = {"league": league_id, "season": season}
    return requests.get(url, headers=HEADERS, params=params).json()["response"]
```

**Pourquoi cette API pour les images** : chaque payload renvoie directement des champs `photo`, `logo`, `flag` en URL CDN stable (`media.api-sports.io`). Zéro hébergement à gérer côté toi, zéro poids ajouté au `.pbix`.

### 1.2 Scraping FBref (stats complémentaires)

FBref applique un rate-limit strict (historiquement ~10-20 req/min sur le réseau Sports-Reference, vérifie le `robots.txt` à jour avant de lancer un run massif). Pour un projet portfolio, reste raisonnable : throttle systématique + cache local.

```python
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd

HEADERS_SCRAPE = {"User-Agent": "Mozilla/5.0 (portfolio-project; contact: toi@mail.com)"}

def scrape_fbref_table(url: str, table_id: str) -> pd.DataFrame:
    time.sleep(3)  # throttle obligatoire, ne pas descendre en dessous
    resp = requests.get(url, headers=HEADERS_SCRAPE)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table", {"id": table_id})
    return pd.read_html(str(table))[0]

# Exemple : table "stats standard" d'une compétition
df_stats = scrape_fbref_table(
    "https://fbref.com/en/comps/...",
    table_id="stats_standard"
)
```

> Astuce : FBref encode parfois les tables en commentaires HTML (`<!-- ... -->`) pour bloquer le scraping naïf. Si `find()` retourne `None`, parse les commentaires avec `soup.find_all(string=lambda t: isinstance(t, Comment))` avant de re-passer chaque bloc dans BeautifulSoup.

### 1.3 URLs d'images — sources à connaître

| Type | Source | Format URL |
|---|---|---|
| Portrait joueur | API-Football | `https://media.api-sports.io/football/players/{id}.png` |
| Logo équipe/compétition | API-Football | `https://media.api-sports.io/football/teams/{id}.png` |
| Drapeau pays (HD, code ISO) | flagcdn.com | `https://flagcdn.com/w320/{iso2}.png` |

Stocke ces URLs comme de simples colonnes texte dans tes tables — c'est tout ce que Power BI a besoin pour le rendu (voir partie 2).

---

## 2. Modélisation — Schéma en étoile

```
                Dim_Calendrier
                      │
Dim_Joueurs ──── Fact_Performances ──── Dim_Equipes
```

### Dim_Calendrier
`Date_ID (PK)`, `Date`, `Jour_Semaine`, `Mois`, `Phase_Competition` (Groupes / Huitièmes / Quarts / Demi / Finale)

```dax
Dim_Calendrier = CALENDAR(DATE(2026,6,11), DATE(2026,7,19))
```

### Dim_Joueurs
`Joueur_ID (PK)`, `Nom`, `Poste`, `Nationalite`, `Equipe_ID (FK)`, **`URL_Photo`**

### Dim_Equipes
`Equipe_ID (PK)`, `Nom_Equipe`, `Code_ISO`, `Groupe`, **`URL_Logo`**, **`URL_Drapeau`**

### Fact_Performances
Grain = 1 ligne par joueur par match.
`Match_ID`, `Joueur_ID (FK)`, `Equipe_ID (FK)`, `Date_ID (FK)`, `Buts`, `Passes_Decisives`, `xG`, `Tirs`, `Minutes_Jouees`, `Cartons_Jaunes`, `Cartons_Rouges`

### Configurer "Catégorie de données : URL d'image"

1. Charge les colonnes `URL_Photo`, `URL_Logo`, `URL_Drapeau` via Power Query — vérifie que ce sont des URLs propres (pas de paramètres cassés en fin de chaîne).
2. Dans Power BI Desktop, sélectionne la colonne dans le volet **Données**.
3. Onglet **Outils de colonnes** (ribbon) → menu **Catégorie de données** → choisis **URL de l'image**.
4. Répète pour les 3 colonnes.
5. Dans un visuel Table/Matrice : **Format du visuel → Valeurs de cellule → Image** pour afficher la miniature au lieu du texte brut.
6. Pour un visuel dédié, glisse directement le champ dans un visuel **Image** — il se rendra nativement.

---

## 3. Design & UX — Dark Mode

### Palette

| Usage | Couleur | Hex |
|---|---|---|
| Fond global | Noir profond | `#0B0B0F` |
| Fond cartes/visuels | Gris très sombre | `#1A1A22` |
| Accent primaire | Violet | `#6F2DA8` |
| Accent KPI positif | Vert fluo | `#39FF14` |
| Texte principal | Blanc | `#FFFFFF` |
| Texte secondaire | Gris clair | `#B0B0B8` |

Applique la palette via un **thème JSON** (Affichage → Thèmes → Parcourir les thèmes) plutôt que visuel par visuel, pour la cohérence et la rapidité de maintenance.

### Logo FIFA en dynamique (haut à gauche)

But : ne pas embarquer l'image dans le `.pbix` (poids + maintenance), et permettre un swap (ex. variante de logo selon la phase de compétition sélectionnée).

```dax
Logo_URL = 
VAR PhaseSelectionnee = SELECTEDVALUE(Dim_Calendrier[Phase_Competition])
RETURN
SWITCH(
    TRUE(),
    PhaseSelectionnee = "Finale", "https://votre-cdn.com/logo_finale.png",
    "https://votre-cdn.com/logo_default.png"
)
```

Place cette mesure dans un visuel **Image** positionné en haut à gauche (verrouillé, pas de bordure, fond transparent). Le visuel Image accepte une mesure retournant une URL depuis les versions récentes de PBI Desktop — sinon, passe par le visuel custom **HTML Content** (AppSource) qui supporte nativement `<img src="##Logo_URL##">`.

### Fiche Joueur dynamique (change selon le Slicer)

1. Place un **Slicer** sur `Dim_Joueurs[Nom]`.
2. Ajoute un visuel **Image** branché sur `Dim_Joueurs[URL_Photo]` — il se filtre automatiquement avec le slicer (contexte de filtre standard, rien à coder).
3. Pour une vraie "carte" (photo + nom + stats en un seul bloc stylé), utilise le visuel custom **HTML Content** :

```html
<div style="background:#1A1A22; border-radius:12px; padding:16px; text-align:center;">
  <img src="##URL_Photo##" style="width:100px; border-radius:50%; border:2px solid #39FF14;"/>
  <h3 style="color:#FFFFFF;">##Nom##</h3>
  <p style="color:#39FF14;">⚽ ##Total_Buts## buts — 🎯 ##Goal_Involvement##%</p>
</div>
```

---

## 4. DAX Avancé

### Mesures de base (prérequis)

```dax
Total_Buts = SUM(Fact_Performances[Buts])
Total_Passes_Decisives = SUM(Fact_Performances[Passes_Decisives])
Total_xG = SUM(Fact_Performances[xG])
```

### 4.1 Dynamic Rank Buteur — s'adapte aux filtres de pays

```dax
Rank_Buteur = 
RANKX(
    ALLSELECTED(Dim_Joueurs[Nom]),
    [Total_Buts],
    ,
    DESC,
    DENSE
)
```
`ALLSELECTED` retire le filtre de contexte de ligne (le nom du joueur dans la table/matrice) tout en **conservant** les filtres externes (slicer pays, slicer phase). Résultat : si tu filtres sur "France", le classement se recalcule uniquement parmi les joueurs français.

### 4.2 Goal Involvement % — impact d'un joueur sur les buts de son équipe

```dax
Goal_Involvement_% = 
VAR ButsEtPassesJoueur = [Total_Buts] + [Total_Passes_Decisives]
VAR ButsEquipe = 
    CALCULATE(
        [Total_Buts],
        ALLEXCEPT(Fact_Performances, Dim_Equipes[Nom_Equipe])
    )
RETURN
DIVIDE(ButsEtPassesJoueur, ButsEquipe, 0)
```
`ALLEXCEPT` retire tous les filtres sauf celui de l'équipe — donc même si la ligne courante est filtrée sur un joueur précis, `ButsEquipe` reste le total de l'équipe entière.

### 4.3 Team Efficiency — Buts réels vs xG

```dax
Team_Efficiency_Ratio = 
DIVIDE([Total_Buts], [Total_xG], 0)

Team_Efficiency_Delta = 
[Total_Buts] - [Total_xG]
```
Ratio > 1 = surperformance (finition clinique) ; ratio < 1 = sous-performance par rapport aux occasions générées. Le Delta est plus lisible en KPI card (ex. "+3.2 buts au-dessus de l'attendu").

---

## 5. Pour aller plus loin

- Automatise le refresh avec **GitHub Actions** (cron quotidien) qui relance le script Python → push le CSV/Parquet vers un stockage (OneDrive/SharePoint/Azure Blob) → **Power BI Service** détecte le fichier via passerelle ou dataflow.
- Garde les credentials API hors du repo (`.env` + `.gitignore`).
