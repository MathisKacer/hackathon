"""T45, T80 — Compétences du CV et correspondance avec le profil recherché par chaque entreprise.

1. On lit le texte du CV (PDF, `pdf_text`) et on y repère des compétences d'une liste fermée
   (`SKILLS` : outils, langages, méthodes ; `detect_skills`). L'étudiant peut corriger la liste.
2. On repère les mêmes compétences dans les offres du domaine (titre + description).
3. Correspondance d'une entreprise (T80, **à part du score**) = part moyenne des compétences
   demandées par une offre du domaine que l'étudiant possède : offres de l'entreprise si elle
   en a, rapprochées de **son secteur** (division NAF), lui-même rapproché de l'ensemble du
   domaine quand il a peu d'offres (même idée que le score, D13). Les entreprises de la couche
   orange n'ont presque jamais d'offre : c'est surtout le profil « potentiellement recherché ».

    skills = detect_skills(pdf_text(open("cv.pdf", "rb").read()))       # ["Python", "SQL", …]
    prof = SkillProfile.build(offres, entreprises, "data")
    df = add_match(nearby, skills, prof)   # correspondance, correspondance_palier, …

Liste fermée plutôt qu'un modèle : explicable (« Python et SQL sont demandés dans ce secteur »),
rapide, sans téléchargement. Le CV n'est jamais écrit sur le disque (seule la liste des
compétences peut aller dans le profil, si l'étudiant est connecté).
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass

import numpy as np
import pandas as pd

# Libellé affiché → expression cherchée dans un texte en minuscules, sans accents.
# Choix prudents : pas « C » ni « Go » (trop ambigus) ; « R » cherché à part (majuscule isolée).
SKILLS: dict[str, str] = {
    # Langages et outils data
    "Python": r"\bpython\b",
    "R": r"",  # voir _R_LANG
    "SQL": r"\b(sql|t-sql|pl/sql|plsql)\b",
    "SAS": r"\bsas\b(?!\s*(au capital|unipersonnelle|a associe))",
    "Spark": r"\b(spark|pyspark)\b",
    "Hadoop": r"\b(hadoop|hive)\b",
    "Scala": r"\bscala\b",
    "Pandas": r"\bpandas\b",
    "NumPy": r"\bnumpy\b",
    "Scikit-learn": r"\b(scikit-learn|scikit learn|sklearn)\b",
    "TensorFlow": r"\b(tensorflow|keras)\b",
    "PyTorch": r"\bpytorch\b",
    "Machine learning": r"\b(machine learning|apprentissage automatique|ml engineer)\b",
    "Deep learning": r"\b(deep learning|apprentissage profond|reseaux? de neurones)\b",
    "IA générative / LLM": r"\b(llm|ia generative|genai|generative ai|gpt|rag|langchain)\b",
    "NLP": r"\b(nlp|traitement (automatique )?du langage)\b",
    "Statistiques": r"\b(statistiques?|statistician|statisticien(ne)?|statistical)\b",
    "Économétrie": r"\b(econometrie|econometrics|econometrique)\b",
    "Séries temporelles": r"\b(series? temporelles?|time series|forecasting|previsions?)\b",
    "Data visualisation": r"\b(data ?vi[sz]uali[sz]ation|dataviz|tableaux? de bord|dashboards?)\b",
    "Power BI": r"\bpower ?bi\b",
    "Tableau": r"\btableau (software|desktop|server)\b|\btableau\s*,|,\s*tableau\b",
    "Qlik": r"\bqlik(view| sense)?\b",
    "Looker": r"\blooker\b",
    "Excel": r"\bexcel\b",
    "VBA": r"\bvba\b",
    "ETL": r"\b(etl|elt)\b",
    "Talend": r"\btalend\b",
    "Airflow": r"\bairflow\b",
    "dbt": r"\bdbt\b",
    "Snowflake": r"\bsnowflake\b",
    "Databricks": r"\bdatabricks\b",
    "BigQuery": r"\bbig ?query\b",
    "NoSQL / MongoDB": r"\b(nosql|mongodb|cassandra|elasticsearch)\b",
    "PostgreSQL": r"\b(postgresql|postgres)\b",
    "MySQL": r"\bmysql\b",
    "Oracle": r"\boracle\b",
    # Informatique, développement
    "Java": r"\bjava\b(?!\s*script)",
    "JavaScript / TypeScript": r"\b(javascript|typescript|js)\b",
    "React": r"\breact(\.?js)?\b",
    "Angular": r"\bangular\b",
    "Node.js": r"\bnode(\.?js)?\b",
    "PHP": r"\bphp\b",
    "C++": r"(?<![\w+])c\+\+",
    "C#": r"(?<!\w)c#|\.net\b|\bdotnet\b",
    "HTML / CSS": r"\b(html5?|css3?)\b",
    "Git": r"\bgit(hub|lab)?\b",
    "Linux": r"\b(linux|unix|bash|shell)\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\b(kubernetes|k8s)\b",
    "Cloud AWS": r"\b(aws|amazon web services)\b",
    "Cloud Azure": r"\bazure\b",
    "Cloud GCP": r"\b(gcp|google cloud)\b",
    "DevOps / CI-CD": r"\b(devops|ci/cd|ci-cd|jenkins|gitlab ci)\b",
    "API REST": r"\b(apis? rest|rest apis?|restful)\b",
    "Cybersécurité": r"\b(cybersecurite|cyber ?securite|cybersecurity|securite informatique)\b",
    "Réseaux": r"\b(reseaux informatiques|administration reseau|tcp/ip|cisco)\b",
    "SAP": r"\bsap\b",
    # Finance, comptabilité
    "Comptabilité": r"\b(comptabilite|comptable|accounting)\b",
    "Contrôle de gestion": r"\b(controle de gestion|controleur de gestion|controlling)\b",
    "Analyse financière": r"\b(analyse financiere|financial analysis|modelisation financiere)\b",
    "Audit": r"\baudit\b",
    "Consolidation / IFRS": r"\b(consolidation|ifrs|us gaap)\b",
    "Fiscalité": r"\b(fiscalite|fiscal|tax)\b",
    "Trésorerie": r"\b(tresorerie|treasury|cash management)\b",
    "Gestion des risques": r"\b(gestion des risques|risk management|risques? de credit|bale)\b",
    "Actuariat": r"\b(actuariat|actuaire|actuarial|solvabilite)\b",
    # Marketing, communication
    "Marketing digital": r"\b(marketing digital|digital marketing|webmarketing|growth)\b",
    "SEO / SEA": r"\b(seo|sea|referencement)\b",
    "Google Analytics": r"\b(google analytics|ga4)\b",
    "CRM": r"\b(crm|salesforce|hubspot)\b",
    "Réseaux sociaux": r"\b(reseaux sociaux|social media|community manag\w*)\b",
    "Études de marché": r"\b(etudes? de marche|market research|etudes? quantitatives?)\b",
    "Suite Adobe": r"\b(adobe|photoshop|illustrator|indesign|premiere pro)\b",
    "Emailing": r"\b(e-?mailing|marketing automation)\b",
    # Ressources humaines
    "Paie": r"\b(paie|payroll)\b",
    # « recrutement » seul est surtout du texte de présentation (« cabinet de recrutement »,
    # « accompagne les entreprises dans leurs recrutements ») : on demande un contexte de métier,
    # ou le mot seul dans une liste (« Paie, recrutement, … » dans un CV).
    "Recrutement": (
        r"\b(talent acquisition|charge(e)?s? de recrutement|recruteur|recruteuse"
        r"|responsable (du )?recrutement|gestion (du|des) recrutements?"
        r"|sourcing de (candidats|profils))\b"
        r"|(^|[\n,;|\u2022\u00b7])\s*recrutement\s*($|[\n,;|\u2022\u00b7])"
    ),
    "Droit social": r"\b(droit social|droit du travail|relations sociales)\b",
    "SIRH": r"\bsirh\b|\b(workday|successfactors)\b",
    "Formation / GPEC": r"\b(gpec|gepp|plan de developpement des competences)\b",
    # Transversal
    "Anglais": r"\b(anglais|english|toeic|toefl|ielts)\b",
    "Gestion de projet": r"\b(gestion de projets?|project management|chef de projet)\b",
    "Agile / Scrum": r"\b(agile|scrum|kanban)\b",
    "Jira": r"\bjira\b",
}
SKILL_LABELS = list(SKILLS)
# « R » le langage : la lettre majuscule isolée dans le texte d'origine (pas « R&D », « R. »).
_R_LANG = re.compile(r"(?<![\w&'.+-])R(?![\w&'.+-])|\b(rstudio|r shiny|tidyverse|ggplot2?)\b", re.I)
_PATTERNS = {label: re.compile(p, re.M) for label, p in SKILLS.items() if p}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c)).replace("’", "'")


def detect_skills(*texts: str | None) -> list[str]:
    """Compétences de la liste citées dans des textes libres, dans l'ordre de `SKILLS`."""
    raw = " ".join(t for t in texts if isinstance(t, str))
    if not raw.strip():
        return []
    text = _normalize(raw)
    found = {label for label, p in _PATTERNS.items() if p.search(text)}
    # « R » : majuscule isolée, mais pas dans un texte tout en capitales (titre d'offre…)
    if _R_LANG.search(raw) and not raw.isupper():
        found.add("R")
    return [s for s in SKILL_LABELS if s in found]


def pdf_text(data: bytes) -> str:
    """Texte d'un PDF (vide si le PDF est une image scannée ou illisible)."""
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except (PdfReadError, ValueError, OSError):
        return ""


# Pseudo-effectif du lissage : un secteur avec M offres « à compétences » pèse autant que
# l'ensemble des offres du domaine ; une entreprise avec M offres, autant que son secteur.
M_SECTOR = 10
M_COMPANY = 3


@dataclass
class SkillProfile:
    """Compétences des offres d'un domaine, par division NAF et par SIRET (offres à ≥ 1
    compétence repérée seulement)."""

    matrix: np.ndarray  # offres × compétences (0/1)
    division: np.ndarray  # division NAF de chaque offre ("" si inconnue)
    siret: np.ndarray  # SIRET de chaque offre ("" si inconnu)

    @classmethod
    def build(cls, offres: pd.DataFrame, entreprises: pd.DataFrame, domaine: str) -> SkillProfile:
        """`offres` : offres.parquet (titre, description, domaine, siret_match) ;
        `entreprises` : siret, naf_division."""
        o = offres[offres["domaine"] == domaine]
        desc = o["description"] if "description" in o else pd.Series(None, index=o.index)
        skills = [detect_skills(t, d) for t, d in zip(o["titre"], desc, strict=True)]
        m = np.array([[s in sk for s in SKILL_LABELS] for sk in skills], dtype=float)
        m = m.reshape(len(skills), len(SKILL_LABELS))
        siret = o["siret_match"] if "siret_match" in o else o.get("siret", pd.Series(None, o.index))
        siret = siret.astype("string").fillna("").to_numpy(dtype=object)
        div_of = entreprises.set_index("siret")["naf_division"].astype("string")
        division = pd.Series(siret).map(div_of).fillna("").to_numpy(dtype=object)
        keep = m.sum(axis=1) > 0
        return cls(m[keep], division[keep], siret[keep])

    @property
    def n_offers(self) -> int:
        return len(self.matrix)

    def demand(self) -> pd.DataFrame:
        """Part des offres (à compétences) qui demandent chaque compétence, par division."""
        df = pd.DataFrame(self.matrix, columns=SKILL_LABELS)
        df["division"] = self.division
        return df.groupby("division").mean()


def _coverage(matrix: np.ndarray, cv: np.ndarray) -> np.ndarray:
    """Pour chaque offre : part de ses compétences demandées que le CV possède."""
    return (matrix @ cv) / matrix.sum(axis=1)


# T80 : paliers de correspondance (seuils fixes sur la part brute). Calés sur les vraies offres
# data : avec un CV data complet (Python, R, SQL, SAS, ML, deep learning, stats, Git, anglais),
# à Rennes comme à Paris, médiane 17 %, 90e centile 29 % → ~10 % des entreprises en « Forte ».
# Un CV plus mince (Excel, Power BI, SQL : médiane 8 %) reste surtout « Partielle » ou « Faible ».
MATCH_TIERS: list[tuple[float, str]] = [
    (0.25, "Forte"),
    (0.17, "Bonne"),
    (0.10, "Partielle"),
    (0.0, "Faible"),
]
MATCH_COLORS = {"Forte": "#2b8a3e", "Bonne": "#74b816", "Partielle": "#f59f00", "Faible": "#adb5bd"}
MIN_SECTOR_OFFERS = 5  # en dessous, on dit « d'après le domaine » plutôt que « son secteur »
SOURCE_LABELS = {
    "offres": "d'après ses offres",
    "secteur": "d'après les offres de son secteur",
    "domaine": "d'après l'ensemble des offres du domaine",
}


def match_tier(part: float | None) -> str | None:
    """Palier en mots (« Forte »…) d'une part de correspondance ; None si inconnue."""
    if part is None or pd.isna(part):
        return None
    return next(label for seuil, label in MATCH_TIERS if part >= seuil)


def add_match(df: pd.DataFrame, skills: list[str], profile: SkillProfile) -> pd.DataFrame:
    """T80 — Correspondance entre le profil du CV et le profil recherché par l'entreprise.

    **N'entre pas dans le score** : indicateur à part. Ajoute :
    - `correspondance` : part (0 à 1) des compétences demandées par une offre que l'étudiant a,
      en moyenne sur les offres de l'entreprise si elle en a, rapprochée de son secteur (profil
      « potentiellement recherché »), lui-même rapproché de l'ensemble du domaine ;
    - `correspondance_palier` : « Forte », « Bonne », « Partielle », « Faible » (`MATCH_TIERS`) ;
    - `correspondance_source` : « offres », « secteur » ou « domaine » (`SOURCE_LABELS`) ;
    - `competences_demandees` / `competences_manquantes` : jusqu'à 3 compétences du CV demandées
      dans son secteur / 3 compétences souvent demandées qu'il n'a pas (« Python, SQL »).
    Sans compétence ou sans offre : colonnes vides (NaN / None).
    """
    out = df.copy()
    cv = np.array([s in set(skills) for s in SKILL_LABELS], dtype=float)
    cols = ["correspondance_palier", "correspondance_source"]
    cols += ["competences_demandees", "competences_manquantes"]
    if not cv.any() or profile.n_offers == 0 or out.empty:
        out["correspondance"] = np.nan
        for c in cols:
            out[c] = None
        return out
    cov = pd.Series(_coverage(profile.matrix, cv))
    overall = float(cov.mean())
    by_div = cov.groupby(profile.division).agg(["sum", "size"])
    by_div = by_div[by_div.index != ""]
    div_cov = (by_div["sum"] + M_SECTOR * overall) / (by_div["size"] + M_SECTOR)
    known = profile.siret != ""
    by_siret = cov[known].groupby(profile.siret[known]).agg(["sum", "size"])

    division = (
        out["naf_division"].astype("string")
        if "naf_division" in out
        else out["naf"].astype("string").str[:2]
    )
    prior = division.map(div_cov).astype(float).fillna(overall)
    sirets = out["siret"].astype("string")
    s_sum = sirets.map(by_siret["sum"]).astype(float).fillna(0.0)
    s_n = sirets.map(by_siret["size"]).astype(float).fillna(0.0)
    part = ((s_sum + M_COMPANY * prior) / (s_n + M_COMPANY)).clip(0, 1)
    out["correspondance"] = part
    out["correspondance_palier"] = part.map(match_tier).astype(object)
    n_div = division.map(by_div["size"]).astype(float).fillna(0.0)
    source = np.where(s_n > 0, "offres", np.where(n_div >= MIN_SECTOR_OFFERS, "secteur", "domaine"))
    out["correspondance_source"] = pd.Series(source, index=out.index, dtype=object)

    # Compétences demandées dans le secteur (part des offres, lissée vers le domaine).
    m = pd.DataFrame(profile.matrix, columns=SKILL_LABELS)
    overall_d = m.mean()
    grp = m.groupby(profile.division)
    sector_d = (grp.sum() + M_SECTOR * overall_d) / (grp.size().to_numpy()[:, None] + M_SECTOR)
    mine = [s for s in SKILL_LABELS if s in set(skills)]
    others = [s for s in SKILL_LABELS if s not in set(skills)]

    def top(d: pd.Series) -> str | None:
        d = d[d >= 0.10].sort_values(ascending=False).head(3)
        return ", ".join(d.index) or None

    have: dict[str, str | None] = {}
    lack: dict[str, str | None] = {}
    for div in division.dropna().unique():
        d = sector_d.loc[div] if div in sector_d.index and div != "" else overall_d
        have[div], lack[div] = top(d[mine]), top(d[others])
    known_div = division.notna()
    out["competences_demandees"] = (
        division.map(have).astype(object).where(known_div, top(overall_d[mine]))
    )
    out["competences_manquantes"] = (
        division.map(lack).astype(object).where(known_div, top(overall_d[others]))
    )
    return out


def match_summary(row) -> dict[str, str] | None:
    """Textes d'affichage de la correspondance (carte, fiche) ; None si pas de CV.

    {"palier": "Forte", "pourcentage": "31 %", "source": "d'après les offres de son secteur",
     "as": "Python, SQL", "manque": "Cloud GCP, Spark"} (clés « as » / « manque » absentes si vides)
    """
    part = row.get("correspondance")
    if part is None or pd.isna(part):
        return None
    out = {
        "palier": match_tier(float(part)) or "",
        "pourcentage": f"{100 * float(part):.0f} %",
        "source": SOURCE_LABELS.get(str(row.get("correspondance_source")), ""),
    }
    for key, col in (("as", "competences_demandees"), ("manque", "competences_manquantes")):
        v = row.get(col)
        if isinstance(v, str) and v:
            out[key] = v
    return out


# --- T83 : compétences ajoutées à la main (hors de la liste) -----------------------------------

MAX_SKILL_LENGTH = 40
MAX_SKILLS = 60
_CANONICAL = {_normalize(s): s for s in SKILL_LABELS}


def clean_skill(text: object) -> str | None:
    """Compétence saisie à la main → libellé propre, ou None si vide / trop long.

    Espaces superflus retirés ; une compétence de la liste écrite autrement (« python »,
    « power bi ») reprend son libellé (« Python », « Power BI ») ; sinon le texte est gardé tel
    quel (« QGIS », « Stata »), première lettre en majuscule si tout est en minuscules."""
    if not isinstance(text, str):
        return None
    t = " ".join(text.split()).strip(" ,;")
    if not t or len(t) > MAX_SKILL_LENGTH:
        return None
    if (canon := _CANONICAL.get(_normalize(t))) is not None:
        return canon
    return t[0].upper() + t[1:] if t.islower() else t


def clean_skills(skills: list | None) -> list[str]:
    """Liste nettoyée : sans vide ni doublon (casse et accents ignorés), au plus MAX_SKILLS."""
    out: list[str] = []
    seen: set[str] = set()
    for s in skills or []:
        c = clean_skill(s)
        if c is not None and _normalize(c) not in seen:
            seen.add(_normalize(c))
            out.append(c)
    return out[:MAX_SKILLS]


def custom_skills(skills: list | None) -> list[str]:
    """Compétences ajoutées à la main, hors de la liste `SKILLS`."""
    return [s for s in clean_skills(skills) if s not in _CANONICAL.values()]


def match_skills(skills: list | None) -> list[str]:
    """Compétences de la liste utilisées pour la correspondance (T80) : celles choisies, plus
    celles qu'on reconnaît dans une compétence ajoutée à la main (« SQL Server » → SQL).
    Une compétence inconnue (« QGIS ») est affichée mais ne compte pas : on ne sait pas la
    chercher de façon fiable dans les offres."""
    cleaned = clean_skills(skills)
    found = {s for s in cleaned if s in _CANONICAL.values()}
    for s in custom_skills(cleaned):
        found.update(detect_skills(s))
    return [s for s in SKILL_LABELS if s in found]
