"""Configuration commune : chemins du projet, secrets (.env) et constantes.

Usage :
    from radar.config import PATHS, settings
    df = pd.read_parquet(PATHS.processed / "entreprises.parquet")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Paths:
    root: Path = ROOT
    data: Path = ROOT / "data"
    raw: Path = ROOT / "data" / "raw"
    processed: Path = ROOT / "data" / "processed"
    cache: Path = ROOT / "data" / "cache"  # cache HTTP (requests-cache), indispensable pour Adzuna

    def ensure(self) -> Paths:
        for p in (self.raw, self.processed, self.cache):
            p.mkdir(parents=True, exist_ok=True)
        return self


PATHS = Paths().ensure()

# Fichiers du contrat entre modules (voir docs/ARCHITECTURE.md)
FILES = {
    "entreprises": PATHS.processed / "entreprises.parquet",
    "offres": PATHS.processed / "offres.parquet",
    "scores": PATHS.processed / "scores.parquet",
    "candidatures_simulees": PATHS.processed / "candidatures_simulees.parquet",
    "p_reponse": PATHS.processed / "p_reponse.parquet",
}


def _env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


@dataclass(frozen=True)
class Settings:
    # France Travail (OAuth2 client_credentials)
    ft_client_id: str | None = field(default_factory=lambda: _env("FT_CLIENT_ID"))
    ft_client_secret: str | None = field(default_factory=lambda: _env("FT_CLIENT_SECRET"))
    ft_token_url: str | None = field(default_factory=lambda: _env("FT_TOKEN_URL"))
    ft_scopes: str | None = field(default_factory=lambda: _env("FT_SCOPES"))
    # Adzuna
    adzuna_app_id: str | None = field(default_factory=lambda: _env("ADZUNA_APP_ID"))
    adzuna_app_key: str | None = field(default_factory=lambda: _env("ADZUNA_APP_KEY"))
    # La bonne alternance
    lba_api_token: str | None = field(default_factory=lambda: _env("LBA_API_TOKEN"))
    # LLM (bonus)
    anthropic_api_key: str | None = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))

    def require(self, *names: str) -> None:
        """Lève une erreur claire si une clé manque (sans jamais afficher les valeurs)."""
        missing = [n for n in names if not getattr(self, n)]
        if missing:
            raise RuntimeError(
                f"Variables manquantes dans .env : {', '.join(n.upper() for n in missing)} "
                "(voir .env.example)"
            )

    def __repr__(self) -> str:  # ne jamais afficher les secrets
        filled = {k: bool(v) for k, v in self.__dict__.items()}
        return f"Settings(renseignées={filled})"


settings = Settings()

# Constantes métier
USER_AGENT = "radar-hackathon"
MIN_TRANCHE_EFFECTIF = "11"  # >= 10 salariés (codes INSEE)
DEFAULT_DOMAIN = "data"
