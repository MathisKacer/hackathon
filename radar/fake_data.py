"""T5 — Fake data generator that follows the data contract (docs/ARCHITECTURE.md).

Goal: let the score (T30) and the app (T40…) start before the real collection exists.
Everything here is FAKE: invented companies, valid-looking but random SIRETs, URLs on
example.org, descriptions tagged "[DONNÉE FACTICE]". Never present it as real data.

Realism choices (so that the score has something to chew on):
- companies sit around ~25 French cities (Rennes over-weighted for the demo);
- only establishments with >= 10 employees (same filter as T20, tranche >= '11');
- offer counts are gamma-Poisson (lots of zeros, a few big recruiters), rising with size;
- the share of "data" offers depends on the NAF sector;
- each company has its own propensity to post internships → some recruit data profiles
  but never post an internship (the "hidden opportunity" the app looks for);
- Adzuna offers carry no SIRET (name variants, ~20 % not matched), La bonne alternance
  offers carry one.

- La bonne alternance "potential recruiters" (T7): companies without a published
  apprenticeship offer + small firms outside the reference, with real ROME codes.

`scores`, `candidatures_simulees` and `p_reponse` are PLACEHOLDERS with the right columns
so that the app can be built; their formulas are NOT the real model (T30/T31, T35/T36).

Entry point: `uv run python scripts/make_fake_data.py` (see that script for options).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
from scipy import stats

from radar.domains import load_domains
from radar.schemas import OFFRES_RAW

FAKE_TAG = "[DONNÉE FACTICE]"

# Domains: provisional keys, the real list lives in radar/domains.yaml (T6).
DOMAINS = ("data", "informatique", "finance", "marketing", "rh")
OTHER_DOMAIN = "autre"

# (city, postcode, lat, lon, weight, spread in degrees)
CITIES = [
    ("Paris", "75008", 48.8566, 2.3522, 30, 0.08),
    ("Lyon", "69003", 45.7640, 4.8357, 8, 0.05),
    ("Rennes", "35000", 48.1173, -1.6778, 8, 0.05),
    ("Toulouse", "31000", 43.6047, 1.4442, 5, 0.05),
    ("Nantes", "44000", 47.2184, -1.5536, 5, 0.05),
    ("Lille", "59000", 50.6292, 3.0573, 5, 0.05),
    ("Bordeaux", "33000", 44.8378, -0.5792, 5, 0.05),
    ("Marseille", "13001", 43.2965, 5.3698, 4, 0.05),
    ("Strasbourg", "67000", 48.5734, 7.7521, 3, 0.04),
    ("Montpellier", "34000", 43.6108, 3.8767, 3, 0.04),
    ("Nice", "06000", 43.7102, 7.2620, 2, 0.03),
    ("Grenoble", "38000", 45.1885, 5.7245, 2, 0.03),
    ("Brest", "29200", 48.3904, -4.4861, 2, 0.03),
    ("Vannes", "56000", 47.6582, -2.7608, 1, 0.03),
    ("Lorient", "56100", 47.7483, -3.3700, 1, 0.03),
    ("Saint-Malo", "35400", 48.6493, -2.0257, 1, 0.03),
    ("Angers", "49000", 47.4784, -0.5632, 1.5, 0.03),
    ("Tours", "37000", 47.3941, 0.6848, 1.5, 0.03),
    ("Dijon", "21000", 47.3220, 5.0415, 1.5, 0.03),
    ("Clermont-Ferrand", "63000", 45.7772, 3.0870, 1.5, 0.03),
    ("Rouen", "76000", 49.4432, 1.0999, 1.5, 0.03),
    ("Caen", "14000", 49.1829, -0.3707, 1.5, 0.03),
    ("Orléans", "45000", 47.9030, 1.9093, 1, 0.03),
    ("Reims", "51100", 49.2583, 4.0317, 1, 0.03),
]

# (NAF, label, weight in population, offer-rate multiplier,
#  domain weights {data, informatique, finance, marketing, rh, autre})
SECTORS = [
    ("62.01Z", "Programmation informatique", 6, 2.0, (30, 45, 2, 3, 3, 17)),
    ("62.02A", "Conseil en systèmes et logiciels informatiques", 5, 2.0, (30, 40, 3, 4, 3, 20)),
    (
        "63.11Z",
        "Traitement de données, hébergement et activités connexes",
        2,
        1.8,
        (40, 30, 2, 3, 3, 22),
    ),
    (
        "70.22Z",
        "Conseil pour les affaires et autres conseils de gestion",
        6,
        1.5,
        (15, 8, 20, 12, 8, 37),
    ),
    ("73.20Z", "Études de marché et sondages", 1, 1.2, (35, 5, 3, 30, 2, 25)),
    ("73.11Z", "Activités des agences de publicité", 2, 1.0, (8, 6, 3, 50, 3, 30)),
    ("64.19Z", "Autres intermédiations monétaires", 3, 1.5, (12, 15, 40, 8, 6, 19)),
    ("65.12Z", "Autres assurances", 2, 1.4, (15, 12, 30, 8, 6, 29)),
    (
        "66.19B",
        "Autres activités auxiliaires de services financiers",
        1,
        1.2,
        (12, 10, 45, 6, 5, 22),
    ),
    (
        "72.19Z",
        "Recherche-développement en autres sciences physiques et naturelles",
        2,
        1.0,
        (15, 10, 3, 2, 3, 67),
    ),
    ("78.10Z", "Activités des agences de placement de main-d'œuvre", 2, 3.0, (8, 15, 8, 8, 25, 36)),
    ("35.11Z", "Production d'électricité", 1, 1.0, (8, 8, 6, 3, 5, 70)),
    ("29.10Z", "Construction de véhicules automobiles", 1, 1.0, (6, 8, 5, 4, 5, 72)),
    ("86.10Z", "Activités hospitalières", 6, 0.6, (2, 3, 3, 1, 6, 85)),
    ("85.42Z", "Enseignement supérieur", 2, 0.6, (5, 5, 3, 4, 6, 77)),
    ("84.11Z", "Administration publique générale", 6, 0.4, (4, 5, 6, 3, 8, 74)),
    ("47.11F", "Hypermarchés", 5, 0.8, (2, 2, 3, 4, 5, 84)),
    (
        "46.90Z",
        "Commerce de gros (commerce interentreprises) non spécialisé",
        5,
        0.6,
        (3, 3, 6, 8, 4, 76),
    ),
    ("10.51A", "Fabrication de lait liquide et de produits frais", 2, 0.5, (2, 2, 4, 4, 4, 84)),
    ("41.20A", "Construction de maisons individuelles", 4, 0.4, (1, 1, 4, 2, 3, 89)),
    ("49.41A", "Transports routiers de fret interurbains", 5, 0.5, (2, 2, 3, 1, 4, 88)),
]

# INSEE "tranche d'effectif" codes (>= 10 employees), midpoint, relative frequency
HEADCOUNT_BANDS = [
    ("11", 15, 0.45),
    ("12", 35, 0.30),
    ("21", 75, 0.11),
    ("22", 150, 0.06),
    ("31", 225, 0.015),
    ("32", 375, 0.03),
    ("41", 750, 0.015),
    ("42", 1500, 0.008),
    ("51", 3500, 0.005),
    ("52", 7500, 0.0015),
    ("53", 12000, 0.0005),
]

# ROME 4.0 codes for data jobs (checked in docs/SOURCES.md). Other domains: left empty on
# purpose rather than inventing codes.
DATA_JOBS = [
    ("Data Analyst", "M1419"),
    ("Data Scientist", "M1405"),
    ("Data Engineer", "M1811"),
    ("Ingénieur statisticien", "M1414"),
    ("Chargé d'études statistiques", "M1403"),
    ("Consultant BI", "M1824"),
    ("Ingénieur IA / Machine Learning", "M1889"),
]
OTHER_JOBS = {
    "informatique": [
        "Développeur Python",
        "Développeur full-stack",
        "Administrateur systèmes",
        "DevOps",
    ],
    "finance": ["Contrôleur de gestion", "Analyste financier", "Comptable", "Auditeur"],
    "marketing": ["Chef de projet marketing", "Chargé de communication", "Growth marketer"],
    "rh": ["Chargé de recrutement", "Gestionnaire paie", "Chargé RH"],
    "autre": [
        "Commercial",
        "Technicien de maintenance",
        "Assistant administratif",
        "Chef de chantier",
        "Préparateur de commandes",
        "Infirmier",
    ],
}
SKILLS = {
    "data": "Python, SQL, statistiques, machine learning, visualisation",
    "informatique": "Python, Java, cloud, CI/CD",
    "finance": "Excel, reporting, IFRS",
    "marketing": "SEO, réseaux sociaux, CRM",
    "rh": "recrutement, SIRH, droit du travail",
    "autre": "rigueur, autonomie, travail en équipe",
}

NAME_PARTS_A = [
    "Nova",
    "Data",
    "Armor",
    "Breiz",
    "Hexa",
    "Lumen",
    "Opti",
    "Kerv",
    "Alto",
    "Sigma",
    "Vertex",
    "Atlas",
    "Orion",
    "Quanti",
    "Mare",
    "Terra",
    "Celt",
    "Azur",
    "Polar",
    "Iroise",
]
NAME_PARTS_B = [
    "lytics",
    "tech",
    "soft",
    "group",
    "conseil",
    "industries",
    "services",
    "logic",
    "metrics",
    "systèmes",
    "solutions",
    "lab",
    "partners",
    "data",
    "ouest",
    "énergie",
]
LEGAL_FORMS = ["SAS", "SA", "SARL", ""]


@dataclass
class FakeData:
    offres_raw: dict[str, pd.DataFrame]
    offres: pd.DataFrame
    entreprises: pd.DataFrame
    scores: pd.DataFrame
    candidatures_simulees: pd.DataFrame
    p_reponse: pd.DataFrame
    recruteurs_lba: pd.DataFrame


# --------------------------------------------------------------------------- helpers


def luhn_ok(number: str) -> bool:
    """Luhn check used by INSEE for SIREN (9 digits) and SIRET (14 digits)."""
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _luhn_complete(partial: str) -> str:
    """Append the digit that makes `partial` pass the Luhn check."""
    for d in "0123456789":
        if luhn_ok(partial + d):
            return partial + d
    raise AssertionError("unreachable")


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def _pct_rank(s: pd.Series) -> pd.Series:
    """Percentile rank in [0, 1] (missing values → 0.5, i.e. neutral)."""
    return s.rank(pct=True, method="average").fillna(0.5)


# --------------------------------------------------------------------------- companies


def make_entreprises(rng: np.random.Generator, n: int) -> pd.DataFrame:
    sirens = rng.choice(np.arange(10_000_000, 100_000_000), size=n, replace=False)
    siren = [_luhn_complete(str(s)) for s in sirens]
    siret = [_luhn_complete(s + f"{rng.integers(1, 1000):04d}") for s in siren]

    city_w = np.array([c[4] for c in CITIES], dtype=float)
    city_idx = rng.choice(len(CITIES), size=n, p=city_w / city_w.sum())
    sec_w = np.array([s[2] for s in SECTORS], dtype=float)
    sec_idx = rng.choice(len(SECTORS), size=n, p=sec_w / sec_w.sum())
    band_p = np.array([b[2] for b in HEADCOUNT_BANDS])
    band_idx = rng.choice(len(HEADCOUNT_BANDS), size=n, p=band_p / band_p.sum())

    spread = np.array([CITIES[i][5] for i in city_idx])
    lat = np.array([CITIES[i][2] for i in city_idx]) + rng.normal(0, 1, n) * spread
    lon = np.array([CITIES[i][3] for i in city_idx]) + rng.normal(0, 1, n) * spread * 1.4

    headcount = np.array([HEADCOUNT_BANDS[i][1] for i in band_idx], dtype=float)
    categorie = np.where(headcount < 250, "PME", np.where(headcount < 5000, "ETI", "GE"))

    names = [
        f"{rng.choice(NAME_PARTS_A)}{rng.choice(NAME_PARTS_B)} {rng.choice(LEGAL_FORMS)}".strip()
        for _ in range(n)
    ]

    # Revenue: ~150 k€ per employee, lognormal; ~40 % missing (finances are often absent).
    ca_n = headcount * 150_000 * rng.lognormal(0, 0.5, n)
    growth = rng.normal(0.04, 0.12, n)
    ca_n_1 = ca_n / (1 + growth)
    missing = rng.random(n) < 0.4
    ca_n[missing] = np.nan
    ca_n_1[missing] = np.nan

    # Stand-in for La Bonne Boîte `hiring_potential` (see note in docs: it is a score, not a proba).
    lbb = rng.beta(1.5, 4, n) * (0.6 + 0.4 * np.log10(headcount) / np.log10(12000))

    df = pd.DataFrame(
        {
            "siret": siret,
            "siren": siren,
            "nom": names,
            "naf": [SECTORS[i][0] for i in sec_idx],
            "naf_libelle": [SECTORS[i][1] for i in sec_idx],
            "tranche_effectif": [HEADCOUNT_BANDS[i][0] for i in band_idx],
            "categorie": categorie,
            "lat": lat.round(6),
            "lon": lon.round(6),
            "commune": [CITIES[i][0] for i in city_idx],
            "ca_n": np.round(ca_n, -3),
            "ca_n_1": np.round(ca_n_1, -3),
            "procedure_collective": rng.random(n) < 0.02,
            "lbb_proba": lbb.clip(0, 1).round(4),
        }
    )
    # Helper columns, not part of the contract (prefixed with "_", dropped before writing).
    df["_code_postal"] = [CITIES[i][1] for i in city_idx]
    df["_headcount"] = headcount
    df["_sector_idx"] = sec_idx
    return df


# --------------------------------------------------------------------------- offers


def make_offres(
    rng: np.random.Generator,
    ent: pd.DataFrame,
    collect_date: date,
    xrng: np.random.Generator | None = None,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Raw offers per source + "processed" offers.

    `xrng` draws the source-specific columns (T19, `_source_columns`): a separate generator, so
    that adding those columns did not change the other fake tables for a given seed.
    """
    n = len(ent)
    rate_mult = np.array([SECTORS[i][3] for i in ent["_sector_idx"]])
    # Company random effect (gamma, shape 0.5) → overdispersion: many zeros, a few big posters.
    lam = 0.05 * ent["_headcount"].to_numpy() ** 0.6 * rate_mult * rng.gamma(0.5, 2.0, n)
    lam[ent["procedure_collective"].to_numpy()] *= 0.1
    counts = rng.poisson(lam)

    # Per-company propensity to post internships / apprenticeships.
    p_stage = rng.beta(0.6, 3, n)
    p_alt = rng.beta(0.6, 4, n)

    rows = []
    domain_keys = DOMAINS + (OTHER_DOMAIN,)
    for i in np.flatnonzero(counts):
        e = ent.iloc[i]
        w = np.array(SECTORS[e["_sector_idx"]][4], dtype=float)
        for _ in range(counts[i]):
            domaine = domain_keys[rng.choice(len(domain_keys), p=w / w.sum())]
            u = rng.random()
            contrat = (
                "stage"
                if u < p_stage[i]
                else "alternance"
                if u < p_stage[i] + p_alt[i]
                else "emploi"
            )
            rows.append((i, domaine, contrat))

    offers = pd.DataFrame(rows, columns=["_ent", "domaine", "contrat"])
    m = len(offers)
    e = ent.iloc[offers["_ent"]].reset_index(drop=True)

    # Job title + ROME code
    job, rome = [], []
    for d in offers["domaine"]:
        if d == "data":
            t, r = DATA_JOBS[rng.integers(len(DATA_JOBS))]
        else:
            jobs = OTHER_JOBS[d]
            t, r = jobs[rng.integers(len(jobs))], None
        job.append(t)
        rome.append(r)
    prefix = offers["contrat"].map(
        {"stage": "Stage - ", "alternance": "Alternance - ", "emploi": ""}
    )
    titre = prefix + pd.Series(job) + " H/F"

    # Source: La bonne alternance only publishes apprenticeships.
    is_lba = (offers["contrat"] == "alternance").to_numpy() & (rng.random(m) < 0.7)
    source = np.where(is_lba, "lba", "adzuna")

    # Adzuna: contract_type rarely filled (cf. SOURCES.md: 14/50); LBA: contract kind.
    adz_brut = offers["contrat"].map(
        {"stage": "contract", "alternance": "contract", "emploi": "permanent"}
    )
    adz_brut = adz_brut.where(rng.random(m) < 0.28, None)
    lba_brut = pd.Series(rng.choice(["Apprentissage", "Professionnalisation"], m, p=[0.8, 0.2]))
    contrat_brut = np.where(is_lba, lba_brut, adz_brut)

    # Adzuna: company name sometimes in another spelling (uppercase, without legal form).
    name = e["nom"].copy()
    variant = (~is_lba) & (rng.random(m) < 0.3)
    name[variant] = name[variant].str.replace(r" (SAS|SA|SARL)$", "", regex=True).str.upper()

    # Publication date: mostly recent, some old ones (Adzuna keeps offers from early 2025).
    age = np.where(rng.random(m) < 0.85, rng.integers(0, 60, m), rng.integers(60, 330, m))
    pub = [collect_date - timedelta(days=int(a)) for a in age]

    # Location: Adzuna lat/lon not always there.
    has_ll = is_lba | (rng.random(m) < 0.9)
    jitter = rng.normal(0, 0.002, (m, 2))

    offre_id = [f"{s}-{k:07d}" for k, s in enumerate(source)]
    raw = pd.DataFrame(
        {
            "source": source,
            "offre_id": offre_id,
            # Dates en texte ISO, comme les vrais collecteurs (adzuna.py, lba.py) : un mélange
            # factice/réel dans data/raw/ ne doit pas casser les comparaisons de dates.
            "date_collecte": f"{collect_date.isoformat()}T00:00:00+00:00",
            "date_publication": [f"{d.isoformat()}T00:00:00Z" for d in pub],
            "titre": titre,
            "description": [
                f"{FAKE_TAG} {t}. Compétences : {SKILLS[d]}."
                for t, d in zip(titre, offers["domaine"], strict=True)
            ],
            "entreprise_nom": name,
            "commune": e["commune"],
            "code_postal": e["_code_postal"],
            "lat": np.where(has_ll, e["lat"] + jitter[:, 0], np.nan),
            "lon": np.where(has_ll, e["lon"] + jitter[:, 1], np.nan),
            "contrat_brut": contrat_brut,
            "code_rome": np.where(is_lba, rome, None),  # Adzuna gives no ROME code
            "url": [f"https://example.org/factice/{oid}" for oid in offre_id],
            "siret": np.where(is_lba, e["siret"], None),
        }
    )
    extra = _source_columns(
        xrng if xrng is not None else np.random.default_rng(0),
        e,
        offers,
        is_lba,
        pub,
        collect_date,
    )
    raw = pd.concat([raw, extra], axis=1)

    # --- "processed" offers: what process/ (T13 classify + T21 match) would output.
    true_siret = e["siret"].to_numpy()
    matched = is_lba | (rng.random(m) < 0.8)
    match_score = np.where(
        is_lba, 100.0, np.where(matched, rng.uniform(85, 100, m), rng.uniform(40, 85, m))
    ).round(1)
    offres = raw.copy()
    offres["domaine"] = offers["domaine"]
    offres["contrat"] = offers["contrat"]
    offres["siret_match"] = np.where(matched, true_siret, None)
    offres["match_score"] = match_score
    offres["match_methode"] = np.where(
        is_lba, "siret_source", np.where(matched, "nom_commune_fuzzy", "non_rapproche")
    )

    # Each raw file only has the contract columns + its own columns, like the real collectors.
    raw_by_source = {
        s: raw.loc[raw["source"] == s, OFFRES_RAW + extra_cols].reset_index(drop=True)
        for s, extra_cols in (("adzuna", ADZUNA_EXTRA), ("lba", LBA_EXTRA))
    }
    return raw_by_source, offres


# Source-specific columns, in the order of the real collectors (collect/adzuna.py, collect/lba.py;
# test_fake_data checks they stay identical).
ADZUNA_EXTRA = [
    "contrat_temps", "categorie", "salaire_min", "salaire_max", "salaire_predit",
    "zone", "requete", "region_requete",
]  # fmt: skip
LBA_EXTRA = [
    "partenaire", "naf", "naf_libelle", "taille", "adresse", "niveau_diplome",
    "nb_postes", "statut", "date_expiration", "date_debut", "duree_mois", "teletravail",
    "delegue_ecole",
]  # fmt: skip

# Adzuna category label by domain (real labels; "Unknown" is the most frequent one, ~43 %).
ADZUNA_CATEGORIES = {
    "data": ["Emplois Informatique", "Emplois Consultants", "Emplois Diplômés"],
    "informatique": ["Emplois Informatique", "Emplois Ingénierie"],
    "finance": ["Emplois Comptabilité et Finance"],
    "marketing": ["Emplois RP, Publicité et Marketing"],
    "rh": ["Emplois RH et Recrutement"],
    "autre": ["Emplois Autres/Général"],
}
# LBA partners (partner_label; real shares of the 2026-11-27 export, docs/SOURCES.md).
LBA_PARTNERS = (["Direct Emploi", "France Travail", "offres_emploi_lba", "Hellowork"],
                [0.50, 0.20, 0.16, 0.14])  # fmt: skip
# Targeted diploma (offer.target_diploma.european: "3" CAP … "6" Bac+3, "7" Bac+5), or None.
DIPLOMA_LEVELS = [None, "3", "4", "5", "6", "7"]
DIPLOMA_P = {
    "data": [0.08, 0.0, 0.02, 0.15, 0.30, 0.45],
    "other": [0.10, 0.08, 0.15, 0.27, 0.22, 0.18],
}  # noqa: E501


def _source_columns(
    rng: np.random.Generator,
    e: pd.DataFrame,
    offers: pd.DataFrame,
    is_lba: np.ndarray,
    pub: list[date],
    collect_date: date,
) -> pd.DataFrame:
    """Adzuna and LBA specific columns (T19), with the formats of the real collectors.

    One row per offer; Adzuna columns are left empty on LBA rows and vice versa (each source's
    file keeps only its own). Formats checked on the real Adzuna collection and on the LBA
    OpenAPI spec. `delegue_ecole` is always False: the fake LBA SIRET is the company's.
    """
    from radar.geo import region_of

    m = len(offers)
    adz = ~is_lba
    domaine = offers["domaine"].to_numpy()
    contrat = offers["contrat"].to_numpy()
    cp = e["_code_postal"].astype(str)
    region = cp.str[:2].map(region_of)

    # --- Adzuna
    contrat_temps = rng.choice(["full_time", "part_time", None], m, p=[0.39, 0.01, 0.60])
    categorie = [
        "Unknown" if rng.random() < 0.43 else rng.choice(ADZUNA_CATEGORIES[d]) for d in domaine
    ]
    has_salary = rng.random(m) < 0.37
    yearly = np.where(
        contrat == "emploi", rng.lognormal(np.log(45_000), 0.3, m), rng.uniform(7_000, 20_000, m)
    )
    sal_min = np.where(has_salary, np.round(yearly, -3), np.nan)
    sal_max = np.where(has_salary, np.round(yearly * rng.uniform(1.0, 1.4, m), -3), np.nan)
    # Real zones: "France > Bretagne > Ille-et-Vilaine > Rennes" (the department level is skipped).
    zone = "France > " + region.fillna("") + " > " + e["commune"]

    # --- LBA
    partenaire = rng.choice(LBA_PARTNERS[0], m, p=LBA_PARTNERS[1])
    niveau = [
        DIPLOMA_LEVELS[rng.choice(6, p=DIPLOMA_P["data" if d == "data" else "other"])]
        for d in domaine
    ]
    start = [
        (collect_date + timedelta(days=int(rng.integers(0, 120)))).isoformat()
        if rng.random() < 0.7
        else None
        for _ in range(m)
    ]
    duree = rng.choice([12, 24, 36, -1], m, p=[0.35, 0.45, 0.10, 0.10])
    teletravail = rng.choice(["onsite", "hybrid", "remote", None], m, p=[0.45, 0.25, 0.03, 0.27])
    numero = rng.integers(1, 200, m)

    def only(mask, values):
        return pd.Series(values, dtype=object).where(mask, None)

    return pd.DataFrame(
        {
            "contrat_temps": only(adz, contrat_temps),
            "categorie": only(adz, categorie),
            "salaire_min": np.where(adz, sal_min, np.nan),
            "salaire_max": np.where(adz, sal_max, np.nan),
            "salaire_predit": only(adz, [False] * m),
            "zone": only(adz, zone),
            "requete": only(adz, ["data"] * m),  # the only Adzuna query collected so far
            "region_requete": only(adz, region),
            "partenaire": only(is_lba, partenaire),
            "naf": only(is_lba, e["naf"]),
            "naf_libelle": only(is_lba, e["naf_libelle"]),
            "taille": only(is_lba, e["tranche_effectif"].map(LBA_SIZE)),
            "adresse": only(
                is_lba,
                [
                    f"{n} rue Factice {c} {v}"
                    for n, c, v in zip(numero, cp, e["commune"], strict=True)
                ],
            ),  # noqa: E501
            "niveau_diplome": only(is_lba, niveau),
            "nb_postes": np.where(is_lba, rng.choice([1, 2, 3], m, p=[0.88, 0.09, 0.03]), np.nan),
            "statut": only(is_lba, ["Active"] * m),
            "date_expiration": only(
                is_lba, [f"{(d + timedelta(days=60)).isoformat()}T00:00:00Z" for d in pub]
            ),  # noqa: E501
            "date_debut": only(is_lba, start),
            "duree_mois": np.where(is_lba & (duree > 0), duree, np.nan),
            "teletravail": only(is_lba, teletravail),
            "delegue_ecole": only(is_lba, [False] * m),
        }
    )


# --------------------------------------------------------------------------- LBA recruiters (T7)

# LBA size bands (text, cf. docs/SOURCES.md: "0-0", "10-19"…), keyed by INSEE band code.
LBA_SIZE = {"11": "10-19", "12": "20-49", "21": "50-99", "22": "100-199", "31": "200-249",
            "32": "250-499", "41": "500-999", "42": "1000-1999", "51": "2000-4999",
            "52": "5000-9999", "53": "10000+"}  # fmt: skip
SMALL_LBA_SIZES = ["0-0", "1-2", "3-5", "6-9"]
OPCOS = ["ATLAS", "AKTO", "OPCO 2i", "OPCO EP", "OPCOMMERCE", "OPCO Santé", "Constructys",
         "Uniformation", "AFDAS", "OCAPIAT", "OPCO Mobilités"]  # fmt: skip


def make_recruteurs(
    rng: np.random.Generator, ent: pd.DataFrame, offres: pd.DataFrame, share: float = 0.3
) -> pd.DataFrame:
    """Fake La bonne alternance "potential recruiters" (schema `recruteurs_lba`).

    - mostly companies of `entreprises` WITHOUT a published apprenticeship offer (that is what
      LBA recruiters are), more likely when bigger;
    - plus ~15 % small firms (< 10 employees) that are NOT in `entreprises`, as in the real
      export (sizes "0-0"…), to exercise joins that do not match;
    - `code_rome`: 1 to 4 real ROME 4.0 codes taken from radar/domains.yaml, drawn according to
      the sector's domain mix (so data recruiters are mostly in IT / consulting / finance).
    """
    domains = load_domains()
    domain_keys = list(domains) + ["autre"]
    rome_by_domain = {k: list(d.rome) for k, d in domains.items()}

    with_alt = set(offres.loc[offres["contrat"] == "alternance", "siret_match"].dropna())
    pool = ent[~ent["siret"].isin(with_alt) & ~ent["procedure_collective"]]
    p_pick = share * (0.5 + 0.5 * np.log10(pool["_headcount"]) / np.log10(12000))
    picked = pool[rng.random(len(pool)) < p_pick]

    # Small firms outside the reference (new SIRETs, same cities and sectors).
    n_small = int(0.15 / 0.85 * len(picked))
    small = make_entreprises(rng, n_small)
    small = small[~small["siret"].isin(ent["siret"])]

    def rome_codes(sector_idx: int) -> str | None:
        w = np.array(SECTORS[sector_idx][4], dtype=float)
        drawn = rng.choice(len(domain_keys), size=rng.integers(1, 5), p=w / w.sum())
        codes = {
            rome_by_domain[domain_keys[k]][rng.integers(len(rome_by_domain[domain_keys[k]]))]
            for k in drawn
            if domain_keys[k] != "autre"
        }
        return ",".join(sorted(codes)) or None

    rows = []
    for kind, df in (("ref", picked), ("small", small)):
        # itertuples() renames "_"-prefixed columns: give them plain names first.
        df = df.rename(columns={"_code_postal": "code_postal", "_sector_idx": "sector_idx"})
        for e in df.itertuples(index=False):
            k = len(rows)
            rows.append(
                {
                    "source": "lba",
                    "recruteur_id": f"rec-{k:07d}",
                    "siret": e.siret,
                    "nom": e.nom,
                    "raison_sociale": e.nom.upper(),
                    "naf": e.naf,
                    "naf_libelle": e.naf_libelle,
                    "taille": LBA_SIZE[e.tranche_effectif]
                    if kind == "ref"
                    else SMALL_LBA_SIZES[rng.integers(len(SMALL_LBA_SIZES))],
                    "adresse": f"{rng.integers(1, 200)} rue Factice {e.code_postal} {e.commune}",
                    "code_postal": e.code_postal,
                    "commune": e.commune,
                    "lat": e.lat,
                    "lon": e.lon,
                    "site_web": f"https://example.org/factice/{e.siret}"
                    if rng.random() < 0.4
                    else None,
                    "opco": OPCOS[rng.integers(len(OPCOS))],
                    "idcc": int(rng.choice([1486, 2120, 1672, 2098, 2216, 1597, 3248, 1527])),
                    "code_rome": rome_codes(e.sector_idx),
                    "url": f"https://example.org/factice/recruteur/{k}",
                }
            )
    rec = pd.DataFrame(rows)
    rec.insert(2, "date_collecte", offres["date_collecte"].iloc[0] if len(offres) else pd.NaT)
    return rec


# --------------------------------------------------------------------------- placeholder scores


def make_scores(
    ent: pd.DataFrame, offres: pd.DataFrame, prior_strength: float = 10.0
) -> pd.DataFrame:
    """PLACEHOLDER for T30/T31: naive beta-binomial with a fixed prior strength per NAF."""
    o = offres.dropna(subset=["siret_match"])
    grid = pd.MultiIndex.from_product([ent["siret"], DOMAINS], names=["siret", "domaine"]).to_frame(
        index=False
    )
    n_tot = o.groupby("siret_match").size().rename("n_offres")
    by_dom = (
        o.assign(
            stage=o["contrat"].eq("stage"),
            alt=o["contrat"].eq("alternance"),
        )
        .groupby(["siret_match", "domaine"])
        .agg(
            n_offres_domaine=("offre_id", "size"),
            n_stage_domaine=("stage", "sum"),
            n_alternance_domaine=("alt", "sum"),
        )
    )
    by_dom.index.names = ["siret", "domaine"]
    s = (
        grid.merge(n_tot, left_on="siret", right_index=True, how="left")
        .merge(by_dom, left_on=["siret", "domaine"], right_index=True, how="left")
        .merge(ent[["siret", "naf", "ca_n", "ca_n_1", "lbb_proba"]], on="siret")
    )
    count_cols = ["n_offres", "n_offres_domaine", "n_stage_domaine", "n_alternance_domaine"]
    s[count_cols] = s[count_cols].fillna(0).astype(int)

    # Prior mean per (NAF, domain) = pooled share in the sector, fallback = global share.
    pooled = s.groupby(["naf", "domaine"])[["n_offres_domaine", "n_offres"]].transform("sum")
    glob = s.groupby("domaine")[["n_offres_domaine", "n_offres"]].transform("sum")
    m_glob = glob["n_offres_domaine"] / glob["n_offres"].clip(lower=1)
    m = (pooled["n_offres_domaine"] / pooled["n_offres"].where(pooled["n_offres"] > 0)).fillna(
        m_glob
    )
    m = m.clip(0.005, 0.995)
    a = m * prior_strength + s["n_offres_domaine"]
    b = (1 - m) * prior_strength + s["n_offres"] - s["n_offres_domaine"]
    s["intensite_post"] = (a / (a + b)).round(4)
    s["intensite_ic_bas"] = stats.beta.ppf(0.05, a, b).round(4)
    s["intensite_ic_haut"] = stats.beta.ppf(0.95, a, b).round(4)

    s["c_intensite"] = s.groupby("domaine")["intensite_post"].transform(_pct_rank)
    growth = s["ca_n"] / s["ca_n_1"] - 1
    s["c_dynamisme"] = _pct_rank(growth)
    s["c_embauche"] = _pct_rank(s["lbb_proba"])
    cols = [
        "siret",
        "domaine",
        "c_intensite",
        "c_dynamisme",
        "c_embauche",
        *count_cols,
        "intensite_post",
        "intensite_ic_bas",
        "intensite_ic_haut",
    ]
    return s[cols]


def make_response(
    rng: np.random.Generator, ent: pd.DataFrame, scores: pd.DataFrame, n_profiles: int = 300
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """PLACEHOLDER for T35/T36 (D6): simulated replies, NOT the documented rule of params.yaml."""
    e = ent.set_index("siret")
    log_size = np.log10(e["_headcount"])
    coef = {"const": -1.0, "intensite": 1.5, "log_taille": -0.4, "distance": -0.01}

    # Simulated applications: each fake student applies to 10 companies around their city.
    rows = []
    sc = scores.set_index(["siret", "domaine"])["c_intensite"]
    for p in range(n_profiles):
        home = ent.iloc[rng.integers(len(ent))]
        dist = _haversine_km(home["lat"], home["lon"], ent["lat"].to_numpy(), ent["lon"].to_numpy())
        near = np.argsort(dist)[:200]
        targets = rng.choice(near, size=10, replace=False)
        dom = DOMAINS[rng.choice(len(DOMAINS), p=[0.5, 0.2, 0.1, 0.1, 0.1])]
        cv = "stage" if rng.random() < 0.6 else "alternance"
        for t in targets:
            siret = ent["siret"].iat[t]
            rows.append((siret, f"P{p:04d}", dom, cv, round(float(dist[t]), 2), sc[(siret, dom)]))
    cand = pd.DataFrame(
        rows,
        columns=["siret", "profil_id", "domaine", "contrat_vise", "distance_km", "c_intensite"],
    )
    cand["log_taille"] = log_size.loc[cand["siret"]].to_numpy()
    lin = (
        coef["const"]
        + coef["intensite"] * cand["c_intensite"]
        + coef["log_taille"] * cand["log_taille"]
        + coef["distance"] * cand["distance_km"]
    )
    cand["p_vraie"] = (1 / (1 + np.exp(-lin))).round(4)
    cand["repondu"] = rng.random(len(cand)) < cand["p_vraie"]

    # "Model" output: here simply the true rule without distance (user-dependent).
    pr = scores[["siret", "domaine", "c_intensite"]].copy()
    pr["log_taille"] = log_size.loc[pr["siret"]].to_numpy()
    pr = pr.merge(pd.DataFrame({"contrat_vise": ["stage", "alternance"]}), how="cross")
    pr["contrib_intensite"] = (coef["intensite"] * pr["c_intensite"]).round(4)
    pr["contrib_taille"] = (coef["log_taille"] * pr["log_taille"]).round(4)
    lin = coef["const"] + pr["contrib_intensite"] + pr["contrib_taille"]
    pr["p_reponse"] = (1 / (1 + np.exp(-lin))).round(4)
    pr = pr[
        ["siret", "domaine", "contrat_vise", "p_reponse", "contrib_intensite", "contrib_taille"]
    ]
    return cand, pr


# --------------------------------------------------------------------------- main entry


def generate(
    n_entreprises: int = 3000, seed: int = 42, collect_date: date | None = None
) -> FakeData:
    """Build every fake table in memory (reproducible for a given seed)."""
    rng = np.random.default_rng(seed)
    collect_date = collect_date or date(2026, 11, 27)
    ent = make_entreprises(rng, n_entreprises)
    # Source-specific columns: own generator (see make_offres), the tables above stay identical.
    raw, offres = make_offres(rng, ent, collect_date, np.random.default_rng([seed, 19]))
    scores = make_scores(ent, offres)
    cand, p_rep = make_response(rng, ent, scores)
    # Drawn last, so that the tables above stay identical for a given seed.
    recruteurs = make_recruteurs(rng, ent, offres)
    public = [c for c in ent.columns if not c.startswith("_")]
    return FakeData(
        offres_raw=raw,
        offres=offres,
        entreprises=ent[public],
        scores=scores,
        candidatures_simulees=cand,
        p_reponse=p_rep,
        recruteurs_lba=recruteurs,
    )
