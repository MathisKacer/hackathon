"""T62 — Compte de démo avec des candidatures variées (vidéo : scripts/demo_video_complet.py).

    uv run python scripts/demo_compte.py      # (re)crée le compte « demo.compass »

Le compte est recréé à chaque fois (seul ce compte est touché, dans data/app/radar.db, hors Git).
Son mot de passe est tiré au hasard et écrit dans data/demo/.compte_demo (hors Git) : il ne sert
qu'à la vidéo, jamais en public. Entreprises réelles des résultats de Rennes (stage, data).
"""

from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path

from radar import accounts

ROOT = Path(__file__).resolve().parents[1]
CRED_FILE = ROOT / "data" / "demo" / ".compte_demo"
USERNAME = "demo.compass"

# (libellé, siret, siren, commune, secteur, taille, statut, envoyée il y a N jours, note)
CANDIDATURES = [
    ("HELLOWORK", "42884313000140", "428843130", "RENNES",
     "Traitement de données, hébergement et activités connexes", "250 à 499 salariés",
     "Entretien", 9, "Entretien jeudi 10 h avec l'équipe data"),
    ("SPIKEELABS", "82368602700041", "823686027", "RENNES",
     "Conseil en systèmes et logiciels informatiques", "20 à 49 salariés",
     "Envoyée", 18, "Candidature spontanée, stage data 6 mois"),
    ("SAFRAN.AI", "81850314600057", "818503146", "PACE",
     "Recherche-développement en autres sciences physiques et naturelles", "20 à 49 salariés",
     "Réponse positive", 21, "Stage accepté, à confirmer"),
    ("IFIP-INSTITUT DU PORC", "77568132300124", "775681323", "PACE",
     "Recherche-développement en autres sciences physiques et naturelles", "50 à 99 salariés",
     "Relancée", 25, "Relancé par mail"),
    ("MGEN", "77568539904759", "775685399", "CESSON-SEVIGNE",
     "Autres assurances", "250 à 499 salariés",
     "Envoyée", 4, ""),
    ("ZENIKA", "48968200500140", "489682005", "RENNES",
     "Conseil en systèmes et logiciels informatiques", "20 à 49 salariés",
     "Réponse négative", 30, "Pas de stage cette année"),
]  # fmt: skip


def new_password() -> str:
    while True:
        pw = f"Cps-{secrets.token_urlsafe(12)}-9a"
        if not accounts.password_problems(pw, USERNAME):
            return pw


def main() -> None:
    con = accounts.connect()
    old = con.execute(
        "SELECT id FROM users WHERE username = ?", (accounts.normalize_username(USERNAME),)
    ).fetchone()
    if old:
        accounts.delete_user(con, old[0])
    password = new_password()
    uid = accounts.create_user(con, USERNAME, password)
    now = datetime.now(UTC)
    for label, siret, siren, commune, secteur, taille, statut, days, note in CANDIDATURES:
        sent = now - timedelta(days=days)
        details = {"commune": commune, "siren": siren, "secteur": secteur, "taille": taille}
        accounts.add_favorite(con, uid, "entreprise", siret, label, details, now=sent)
        accounts.update_favorite(con, uid, "entreprise", siret, candidate=True, now=sent)
        if statut == "Relancée":
            accounts.update_favorite(
                con, uid, "entreprise", siret, statut=statut, now=now - timedelta(days=3)
            )
        elif statut != "Envoyée":
            accounts.update_favorite(con, uid, "entreprise", siret, statut=statut)
        if note:
            accounts.update_favorite(con, uid, "entreprise", siret, note=note)
    CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
    CRED_FILE.write_text(json.dumps({"identifiant": USERNAME, "mot_de_passe": password}))
    CRED_FILE.chmod(0o600)
    print(f"Compte « {USERNAME} » : {len(CANDIDATURES)} candidatures ; identifiants → {CRED_FILE}")


if __name__ == "__main__":
    main()
