"""T45, T80 — compétences du CV et correspondance avec le profil recherché."""

import numpy as np
import pandas as pd
import pytest

from radar.competences import (
    SKILL_LABELS,
    SkillProfile,
    add_match,
    detect_skills,
    match_summary,
    match_tier,
    pdf_text,
)
from radar.spontaneous import COMPONENTS, DEFAULT_WEIGHTS, weighted_score


def _pdf(lines: list[str]) -> bytes:
    """PDF minimal d'une page avec du texte (sans dépendance pour l'écrire)."""
    text = "BT /F1 11 Tf 50 750 Td 14 TL " + " ".join(f"({s}) Tj T*" for s in lines) + " ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(text)} >>\nstream\n{text}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return out


def test_detect_skills_cv():
    cv = "Compétences : Python, R, SQL, Power BI, Excel. Anglais courant (TOEIC 900). Git"
    assert detect_skills(cv) == ["Python", "R", "SQL", "Power BI", "Excel", "Git", "Anglais"]


def test_detect_skills_avoids_false_positives():
    assert detect_skills("Service R&D, bac + 5, contrat CDI") == []
    assert "SAS" not in detect_skills("ACME SAS au capital de 10 000 euros")
    assert "Java" not in detect_skills("Développeur JavaScript")
    assert "JavaScript / TypeScript" in detect_skills("Développeur JavaScript")
    # « recrutement » de présentation (cabinets, forums) : pas une compétence
    assert detect_skills("Cabinet de recrutement spécialisé en data") == []
    assert detect_skills("accompagne les entreprises dans leurs recrutements") == []
    assert detect_skills("Paie, recrutement, droit social") == [
        "Paie",
        "Recrutement",
        "Droit social",
    ]
    assert "Recrutement" in detect_skills("Chargée de recrutement en alternance")
    # « R » dans un titre tout en capitales : ignoré
    assert detect_skills("STAGE R ET D") == []


def test_pdf_text_reads_text_and_tolerates_garbage():
    data = _pdf(["Emma - Etudiante en statistique", "Python, SQL, machine learning"])
    text = pdf_text(data)
    assert "Python" in text
    assert detect_skills(text) == ["Python", "SQL", "Machine learning", "Statistiques"]
    assert pdf_text(b"pas un pdf") == ""


def _profile() -> SkillProfile:
    offres = pd.DataFrame(
        {
            "titre": ["Data scientist", "Data analyst", "Data engineer", "Data analyst", "Chef"],
            "description": [
                "Python, machine learning",
                "SQL, Power BI",
                "Spark, Java",
                "Python, SQL",
                "Python",
            ],
            "domaine": ["data", "data", "data", "data", "autre"],
            "siret_match": ["A", "B", "C", None, "A"],
        }
    )
    ent = pd.DataFrame({"siret": ["A", "B", "C"], "naf_division": ["72", "72", "62"]})
    return SkillProfile.build(offres, ent, "data")


def test_profile_keeps_domain_offers_with_skills():
    p = _profile()
    assert p.n_offers == 4  # l'offre « autre » est écartée
    assert p.matrix.shape == (4, len(SKILL_LABELS))
    assert list(p.division) == ["72", "72", "62", ""]


def test_add_match_uses_company_then_sector():
    near = pd.DataFrame(
        {"siret": ["X", "Y", "A"], "naf": ["72.19Z", "62.01Z", "72.19Z"]}, index=[10, 11, 12]
    )
    out = add_match(near, ["Python", "Machine learning", "SQL"], _profile())
    part = out["correspondance"]
    assert part[10] > part[11]  # le secteur 72 demande Python/SQL/ML, le 62 Spark/Java
    assert part[12] > part[10]  # A a elle-même une offre qui demande exactement ces compétences
    assert part.between(0, 1).all()
    assert list(out["correspondance_source"]) == ["domaine", "domaine", "offres"]  # < 5 offres
    assert out.loc[10, "competences_demandees"].startswith("Python")
    assert "Spark" in out.loc[11, "competences_manquantes"]
    assert list(out.index) == [10, 11, 12]
    assert set(out["correspondance_palier"]) <= {"Forte", "Bonne", "Partielle", "Faible"}


def test_match_tiers_and_summary():
    tiers = [match_tier(x) for x in (0.4, 0.25, 0.2, 0.12, 0.05)]
    assert tiers == ["Forte", "Forte", "Bonne", "Partielle", "Faible"]
    assert match_tier(None) is None
    row = {
        "correspondance": 0.31,
        "correspondance_source": "secteur",
        "competences_demandees": "Python, SQL",
        "competences_manquantes": None,
    }
    assert match_summary(row) == {
        "palier": "Forte",
        "pourcentage": "31 %",
        "source": "d'après les offres de son secteur",
        "as": "Python, SQL",
    }
    assert match_summary({"correspondance": float("nan")}) is None


def test_match_is_not_in_score():
    assert "c_adequation" not in COMPONENTS
    near = pd.DataFrame({"siret": ["X"], "naf": ["72.19Z"]})
    out = add_match(near, [], _profile())
    assert out["correspondance"].isna().all()
    assert out["correspondance_palier"].isna().all()
    # une composante absente ou vide reste ignorée par le score pondéré
    df = pd.DataFrame({c: [0.5] for c in COMPONENTS}).assign(c_intensite=np.nan)
    assert weighted_score(df, DEFAULT_WEIGHTS)["score"].iloc[0] == pytest.approx(0.5)
