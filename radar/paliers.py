"""Paliers de priorité du score orange : des mots et des couleurs au lieu du nombre (T65, D32).

    df = add_tiers(spontaneous)        # ajoute `palier` (1 = meilleur … 4) et `palier_libelle`

Règle **mixte** : une entreprise atteint un palier si elle est à la fois
- parmi les meilleures **de la recherche en cours** (part des résultats classés devant elle) ;
- au-dessus d'un **score minimal** (garde-fou : dans une zone ou pour un contrat où toutes les
  entreprises sont faibles, la meilleure n'est pas annoncée « prioritaire » pour autant) ;
- au-dessus d'un **besoin attendu minimal** (D47, valeur absolue : offres du domaine attendues
  sur la période observée, intensité a posteriori × effectif). Le score étant fait de rangs
  centiles, sa médiane vaut ~0,6 : sans ce seuil, 10 % d'une grande ville (1 000 entreprises à
  Lyon) étaient « prioritaires ». Avec lui, Rennes 20 km ≈ 55 cibles prioritaires, Lyon ≈ 190,
  Guéret aucune (zone sans besoin data mesurable : c'est la vérité à montrer).
Le score est une moyenne pondérée de rangs centiles, pas une probabilité : les libellés parlent
de **priorité**, jamais de « chance » (la chance de réponse simulée est affichée à part, D23).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Tier:
    rank: int
    label: str
    dots: str  # repère sans couleur (accessibilité, daltonisme)
    color: str  # du plus foncé au plus clair ; gris pour le dernier palier
    top_share: float  # part maximale des résultats classés devant (1.0 = pas de condition)
    min_score: float  # score minimal (0.0 = pas de condition)
    min_need: float = 0.0  # besoin attendu minimal (offres du domaine sur la période ; D47)


# Seuils calibrés sur des recherches réelles (Rennes, Lyon, Paris, Guéret ; 5 et 20 km ; stage ;
# poids par défaut). Besoin attendu ≥ 0,2 : à Rennes 20 km, 57 entreprises sur 3 700 qui portent
# 65 % du besoin data attendu ; ≥ 0,05 : 147 entreprises, 79 % du besoin.
TIERS: tuple[Tier, ...] = (
    Tier(1, "Cible prioritaire", "●●●", "#b93d06", 0.10, 0.60, 0.20),
    Tier(2, "Bonne cible", "●●○", "#e8590c", 0.30, 0.45, 0.05),
    Tier(3, "À considérer", "●○○", "#f4a06b", 0.60, 0.30, 0.01),
    Tier(4, "Moins indiquée", "○○○", "#9ca3af", 1.00, 0.00),
)
TIER_BY_RANK = {t.rank: t for t in TIERS}


def assign_tiers(scores: pd.Series, need: pd.Series | None = None) -> pd.Series:
    """Palier (1 à 4) de chaque score, selon la règle mixte, au sein de cette série.

    `need` : besoin attendu de chaque ligne (même index) ; None = pas de seuil absolu.

    « Classées devant » = nombre d'autres résultats de score supérieur ou égal, rapporté au
    total : la meilleure entreprise a 0 % devant elle ; des ex æquo sont traités ensemble et de
    façon prudente (aucun ne monte grâce à l'égalité).
    """
    s = pd.to_numeric(scores, errors="coerce")
    if s.empty:
        return pd.Series(dtype="int64", index=s.index)
    ahead = (s.rank(ascending=False, method="max") - 1) / len(s)
    b = None if need is None else pd.to_numeric(need, errors="coerce").fillna(0.0)
    tiers = pd.Series(TIERS[-1].rank, index=s.index, dtype="int64")
    for t in reversed(TIERS[:-1]):  # du moins exigeant au plus exigeant : le meilleur gagne
        ok = (ahead < t.top_share) & (s >= t.min_score)
        if b is not None:
            ok &= b >= t.min_need
        tiers[ok] = t.rank
    return tiers


def add_tiers(
    df: pd.DataFrame, score_col: str = "score", need_col: str = "besoin_attendu"
) -> pd.DataFrame:
    """Ajoute `palier` et `palier_libelle` (ex. « ●●● Cible prioritaire »).

    Seuil absolu sur `need_col` s'il est présent (D47), sinon règle relative seule."""
    out = df.copy()
    if out.empty or score_col not in out:
        return out.assign(palier=pd.Series(dtype="int64"), palier_libelle=pd.Series(dtype=str))
    out["palier"] = assign_tiers(out[score_col], out[need_col] if need_col in out else None)
    out["palier_libelle"] = out["palier"].map(lambda r: tier_text(r))
    return out


def tier_text(rank, with_dots: bool = True) -> str:
    """« ●●● Cible prioritaire » (ou sans les points) ; chaîne vide si palier inconnu."""
    t = TIER_BY_RANK.get(int(rank)) if pd.notna(rank) else None
    if t is None:
        return ""
    return f"{t.dots} {t.label}" if with_dots else t.label


def tier_color(rank) -> str:
    t = TIER_BY_RANK.get(int(rank)) if pd.notna(rank) else None
    return t.color if t else TIERS[-1].color


# Dégradé continu du score (demande de Maxence) : orange très clair (0) → orange foncé (1).
SCORE_GRADIENT: tuple[tuple[float, str], ...] = (
    (0.00, "#fdebdc"),
    (0.30, "#f9c39a"),
    (0.55, "#f28b4c"),
    (0.75, "#e8590c"),
    (1.00, "#8a2c04"),
)


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def score_color(score) -> str:
    """Couleur du dégradé pour un score dans [0, 1] (gris si inconnu)."""
    if score is None or pd.isna(score):
        return TIERS[-1].color
    x = min(max(float(score), 0.0), 1.0)
    for (x0, c0), (x1, c1) in zip(SCORE_GRADIENT, SCORE_GRADIENT[1:], strict=False):
        if x <= x1:
            t = (x - x0) / (x1 - x0)
            rgb = [round(a + (b - a) * t) for a, b in zip(_rgb(c0), _rgb(c1), strict=True)]
            return "#{:02x}{:02x}{:02x}".format(*rgb)
    return SCORE_GRADIENT[-1][1]


def text_color_on(background: str) -> str:
    """Noir ou blanc, le plus lisible sur ce fond (luminance relative)."""
    r, g, b = _rgb(background)
    return "#111111" if 0.299 * r + 0.587 * g + 0.114 * b > 150 else "#ffffff"


def rule_text() -> str:
    """Règle en une phrase, pour l'aide de l'app et la légende."""
    parts = [
        f"{t.dots} {t.label} : parmi les {round(100 * t.top_share)} % meilleures de ta "
        f"recherche, score ≥ {t.min_score:.2f} et besoin attendu ≥ {t.min_need:g}".replace(".", ",")
        for t in TIERS[:-1]
    ]
    return (
        " ; ".join(parts)
        + f" ; {TIERS[-1].dots} {TIERS[-1].label} : les autres. Besoin attendu = nombre d'offres"
        " du domaine qu'une entreprise de ce profil publie en moyenne sur deux mois."
    )
