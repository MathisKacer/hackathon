"""T34 — Validation du score sans vérité terrain → data/processed/validation/

    uv run python scripts/validate_scores.py                    # 50 tirages, 50 jeux de poids (~15 min)
    uv run python scripts/validate_scores.py --boot 10 --poids 10   # essai rapide

Prérequis (vraies données) : entreprises.parquet, offres.parquet, scores.parquet,
data/raw/lbb.parquet, data/raw/lba_recruteurs.parquet, adzuna_couverture.json.
Produit : resultats.json, *.csv et 3 graphiques SVG (à mettre dans les slides).
Résultats commentés dans docs/VALIDATION.md.
"""

# ruff: noqa: E501  (gabarits SVG : lignes longues plus lisibles d'un bloc)
from __future__ import annotations

import argparse
import html
import json
import logging

import pandas as pd

import radar.validation as V
from radar.config import FILES, PATHS
from radar.recruteurs import mark_lba_recruiters
from radar.score.build import load_coverage
from radar.spontaneous import COMPONENTS, load_nearby

OUT = PATHS.processed / "validation"
INK, MUTED, GRID = "#1f2328", "#57606a", "#d0d7de"
BLUE, ORANGE, GREY = "#1f6feb", "#e8590c", "#8c959f"


def svg_bars(
    path, title, groups, series, colors, ymax=1.0, ylabel="", note="", fmt="{:.2f}", ref=None
):
    """Histogramme groupé SVG minimal. groups : libellés ; series : {nom: [valeurs]} ."""
    w, h, left, bottom, top = 760, 420, 70, 70, 60
    pw, ph = w - left - 20, h - top - bottom
    n_g, n_s = len(groups), len(series)
    gw = pw / n_g
    bw = gw * 0.8 / n_s
    y = lambda v: top + ph * (1 - v / ymax)  # noqa: E731
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" font-family="sans-serif">',
        f'<rect width="{w}" height="{h}" fill="white"/>',
        f'<text x="{left}" y="28" font-size="17" font-weight="bold" fill="{INK}">{html.escape(title)}</text>',
    ]
    for t in [i * ymax / 5 for i in range(6)]:
        out.append(
            f'<line x1="{left}" x2="{w - 20}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{GRID}"/>'
        )
        out.append(
            f'<text x="{left - 8}" y="{y(t) + 4:.1f}" font-size="11" text-anchor="end" fill="{MUTED}">{t:.1f}</text>'
        )
    if ref is not None:
        out.append(
            f'<line x1="{left}" x2="{w - 20}" y1="{y(ref):.1f}" y2="{y(ref):.1f}" stroke="{GREY}" stroke-dasharray="5,4"/>'
        )
    for gi, g in enumerate(groups):
        for si, vals in enumerate(series.values()):
            v = vals[gi]
            if v is None or v != v:
                continue
            x = left + gi * gw + gw * 0.1 + si * bw
            out.append(
                f'<rect x="{x:.1f}" y="{y(v):.1f}" width="{bw - 3:.1f}" height="{top + ph - y(v):.1f}" fill="{colors[si]}"/>'
            )
            out.append(
                f'<text x="{x + bw / 2 - 1.5:.1f}" y="{y(v) - 4:.1f}" font-size="10" text-anchor="middle" fill="{INK}">{fmt.format(v)}</text>'
            )
        out.append(
            f'<text x="{left + gi * gw + gw / 2:.1f}" y="{top + ph + 18}" font-size="12" text-anchor="middle" fill="{INK}">{html.escape(g)}</text>'
        )
    lx = left
    for si, name in enumerate(series):
        out.append(f'<rect x="{lx}" y="{h - 30}" width="12" height="12" fill="{colors[si]}"/>')
        out.append(
            f'<text x="{lx + 16}" y="{h - 20}" font-size="12" fill="{INK}">{html.escape(name)}</text>'
        )
        lx += 16 + 8 * len(name) + 24
    if ylabel:
        out.append(
            f'<text x="16" y="{top + ph / 2}" font-size="11" fill="{MUTED}" transform="rotate(-90 16 {top + ph / 2})" text-anchor="middle">{html.escape(ylabel)}</text>'
        )
    if note:
        out.append(
            f'<text x="{left}" y="46" font-size="11" fill="{MUTED}">{html.escape(note)}</text>'
        )
    out.append("</svg>")
    path.write_text("\n".join(out), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--boot", type=int, default=50, help="tirages bootstrap")
    p.add_argument(
        "--poids", type=int, default=50, help="jeux de poids aléatoires par ville × contrat"
    )
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    OUT.mkdir(parents=True, exist_ok=True)

    ent = pd.read_parquet(FILES["entreprises"])
    off = pd.read_parquet(FILES["offres"])
    scores = pd.read_parquet(FILES["scores"])
    lbb = pd.read_parquet(PATHS.raw / "lbb.parquet")
    lba_rec = pd.read_parquet(PATHS.raw / "lba_recruteurs.parquet", columns=["siret", "code_rome"])
    rec = V.ScoreRecomputer(ent, off, load_coverage(), lbb)
    nearby = {
        c.name: mark_lba_recruiters(load_nearby(c.lat, c.lon, V.RADIUS_KM, "data"), "data")
        for c in V.CITIES
    }

    # 1. Stabilité
    stab = V.stability(rec, nearby, args.boot)
    stab.to_csv(OUT / "stabilite.csv", index=False)
    s = stab.groupby(["ville", "contrat"])["overlap"].agg(
        ["mean", "min", lambda x: x.quantile(0.1)]
    )
    s.columns = ["moyenne", "min", "p10"]
    # 2. Poids
    rand, ofat = V.weight_sensitivity(rec, nearby, args.poids)
    rand.to_csv(OUT / "poids_aleatoires.csv", index=False)
    ofat.to_csv(OUT / "poids_un_a_la_fois.csv", index=False)
    r = rand.groupby(["ville", "contrat"])["overlap"].agg(["mean", "median", "min"])
    o = ofat.groupby(["composante", "poids"])["overlap"].mean().unstack()
    # 3. Cohérence externe
    coh, _ = V.external_coherence(rec, scores, lba_rec)
    coh.to_csv(OUT / "coherence.csv", index=False)

    res = {
        "parametres": {
            "tirages": args.boot,
            "jeux_de_poids": args.poids,
            "rayon_km": V.RADIUS_KM,
            "top_k": V.TOP_K,
            "villes": [c.name for c in V.CITIES],
            "offres_data_rapprochees": int(len(rec.usable_offers)),
        },
        "stabilite_top20": {f"{v} / {c}": row.round(3).to_dict() for (v, c), row in s.iterrows()},
        "poids_aleatoires_top20": {
            f"{v} / {c}": row.round(3).to_dict() for (v, c), row in r.iterrows()
        },
        "poids_un_a_la_fois_top20": {k: row.round(3).to_dict() for k, row in o.iterrows()},
        "coherence_auc": coh.round(3).to_dict(orient="records"),
    }
    (OUT / "resultats.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    cities = [c.name for c in V.CITIES]
    svg_bars(
        OUT / "1_stabilite_bootstrap.svg",
        f"Stabilité du top {V.TOP_K} quand les offres varient ({args.boot} tirages bootstrap)",
        cities,
        {f"{ct} (moyenne)": [s.loc[(c, ct), "moyenne"] for c in cities] for ct in V.CONTRACTS},
        [ORANGE, BLUE],
        ylabel=f"part du top {V.TOP_K} conservée",
        note="1 = même top 20 à chaque tirage ; rayon 20 km, poids par défaut",
    )
    labels = {k: COMPONENTS[k][0] for k in o.index}
    comps = list(o.index)
    svg_bars(
        OUT / "2_sensibilite_poids.svg",
        f"Top {V.TOP_K} conservé si on change UN curseur (moyenne 4 villes × 2 contrats)",
        [labels[k][:22] for k in comps],
        {
            "curseur à 0": [o.loc[k, 0] if 0 in o.columns else None for k in comps],
            "curseur à 5": [o.loc[k, 5] if 5 in o.columns else None for k in comps],
        },
        [GREY, ORANGE],
        ylabel=f"part du top {V.TOP_K} conservée",
        note=f"poids au hasard (0 à 5) : {rand['overlap'].mean():.2f} conservé en moyenne",
    )
    c2 = coh[coh["population"] == "sans offre data"]
    svg_bars(
        OUT / "3_coherence_externe.svg",
        "Retrouve-t-on les recruteurs signalés par des sources indépendantes ? (AUC)",
        ["La Bonne Boîte", "La bonne alternance"],
        {
            "intensité (notre modèle)": c2["auc_intensite"].tolist(),
            "taille seule (référence naïve)": c2["auc_effectif"].tolist(),
            "intensité × taille": c2["auc_intensite_x_effectif"].tolist(),
        },
        [ORANGE, GREY, BLUE],
        ref=0.5,
        ylabel="AUC (0,5 = hasard, 1 = parfait)",
        note="établissements SANS offre data (couche orange)",
    )
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n→ {OUT.relative_to(PATHS.root)}/")


if __name__ == "__main__":
    main()
