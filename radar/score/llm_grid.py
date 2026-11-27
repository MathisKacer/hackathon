"""T77 — Grille « secteur × taille × domaine » remplie par un LLM (note 0–3 + justification).

Piste d'Emma (`docs/PISTE_DOMAINES_LLM.md`) : pour chaque code NAF du référentiel, un LLM dit si
une entreprise de ce secteur recrute habituellement dans chacun des 5 domaines, pour chacune des
4 classes de taille de l'app. Le LLM **qualifie des secteurs réels** ; il ne crée aucune donnée
d'entreprise et ne voit aucun nom d'entreprise.

Reproductibilité :
- consigne versionnée (`prompts/grille_domaines_v1.txt`), température 0 ;
- une réponse par NAF, mise en cache dans `data/processed/llm_grille/<modèle>/<naf>.json` (hors
  Git) : relancer ne refait que les NAF manquants ou invalides ;
- sortie validée (4 tailles × 5 domaines, notes entières 0–3), sinon nouvel essai.

Backend : toute API compatible OpenAI (`/v1/chat/completions`) — Ollama sur CPU, vLLM sur GPU,
ou un service hébergé. Aucun secret n'est nécessaire en local.
"""

from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

from radar.config import PATHS
from radar.filters import TAILLES

log = logging.getLogger(__name__)

PROMPT_VERSION = "v1"
PROMPT_FILE = Path(__file__).parent / "prompts" / f"grille_domaines_{PROMPT_VERSION}.txt"
CACHE_DIR = PATHS.processed / "llm_grille"
GRID_FILE = PATHS.processed / "grille_domaines.parquet"

DOMAINS = ("data", "informatique", "finance", "marketing", "rh")
# clés de taille dans la réponse du LLM → libellés de l'app (radar/filters.py › TAILLES)
SIZE_KEYS = {"10-49": "10–49", "50-249": "50–249", "250-999": "250–999", "1000+": "1 000 et plus"}
_TRANCHE_TO_SIZE_KEY = {code: key for key, label in SIZE_KEYS.items() for code in TAILLES[label]}


def naf_table(ent: pd.DataFrame) -> pd.DataFrame:
    """Un NAF par ligne : libellé, nombre d'établissements (total et par classe de taille)."""
    e = ent.assign(taille=ent["tranche_effectif"].map(_TRANCHE_TO_SIZE_KEY))
    counts = e.pivot_table(index="naf", columns="taille", values="siret", aggfunc="size")
    counts = counts.reindex(columns=list(SIZE_KEYS)).fillna(0).astype(int)
    lib = e.groupby("naf")["naf_libelle"].first()
    out = counts.add_prefix("n_").assign(naf_libelle=lib, n_etab=counts.sum(axis=1))
    return out.sort_values("n_etab", ascending=False).reset_index()


def build_prompt(naf: str, libelle: str) -> str:
    # str.replace et pas str.format : la consigne contient des accolades JSON
    return (
        PROMPT_FILE.read_text(encoding="utf-8")
        .replace("{naf}", naf)
        .replace("{naf_libelle}", libelle)
    )


def _extract_json(text: str) -> dict:
    """Premier objet JSON de la réponse (certains modèles ajoutent ```json … ```)."""
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("pas de JSON dans la réponse")
    return json.loads(m.group(0))


def validate(obj: dict) -> dict:
    """Contrôle la forme et normalise (notes entières 0–3). Lève ValueError sinon."""
    grid = obj.get("grille")
    if not isinstance(grid, dict) or set(grid) != set(SIZE_KEYS):
        raise ValueError(f"tailles attendues {list(SIZE_KEYS)}, reçu {list(grid or {})}")
    clean = {}
    for size in SIZE_KEYS:
        row = grid[size]
        if not isinstance(row, dict) or set(row) != set(DOMAINS):
            raise ValueError(f"{size} : domaines attendus {DOMAINS}, reçu {list(row or {})}")
        clean[size] = {}
        for d in DOMAINS:
            v = row[d]
            if isinstance(v, str) and v.strip().isdigit():
                v = int(v)
            if not isinstance(v, int | float) or v != int(v) or not 0 <= v <= 3:
                raise ValueError(f"{size}/{d} : note invalide {v!r}")
            clean[size][d] = int(v)
    just = obj.get("justification") or {}
    return {
        "grille": clean,
        "justification": {d: str(just.get(d, ""))[:300] for d in DOMAINS},
    }


class LLMClient:
    """Client minimal d'une API compatible OpenAI (Ollama : http://localhost:11434/v1)."""

    def __init__(self, base_url: str, model: str, api_key: str | None = None, timeout: int = 600):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model = model
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "seed": 0,
            "response_format": {"type": "json_object"},
        }
        r = requests.post(self.url, json=body, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def _cache_path(model: str, naf: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", model)
    return CACHE_DIR / f"{safe}_{PROMPT_VERSION}" / f"{naf}.json"


def rate_naf(client: LLMClient, naf: str, libelle: str, retries: int = 2) -> dict:
    """Grille d'un NAF (cache disque d'abord ; jusqu'à `retries` nouveaux essais si invalide)."""
    path = _cache_path(client.model, naf)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    prompt = build_prompt(naf, libelle)
    err = None
    for _ in range(retries + 1):
        try:
            res = validate(_extract_json(client.complete(prompt)))
            break
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            err = e
    else:
        raise ValueError(f"{naf} : réponse invalide après {retries + 1} essais ({err})")
    res |= {"naf": naf, "naf_libelle": libelle, "modele": client.model, "consigne": PROMPT_VERSION}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def rate_all(client: LLMClient, nafs: pd.DataFrame, workers: int = 4) -> tuple[list[dict], list]:
    """Note tous les NAF (en parallèle). Renvoie (réponses valides, NAF en échec)."""
    done, failed = [], []
    with ThreadPoolExecutor(workers) as pool:
        futs = {
            pool.submit(rate_naf, client, r.naf, r.naf_libelle): r.naf for r in nafs.itertuples()
        }
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                done.append(fut.result())
            except Exception as e:  # noqa: BLE001 — on continue, le NAF sera relancé
                log.warning("échec %s : %s", futs[fut], e)
                failed.append(futs[fut])
            if i % 25 == 0:
                log.info("%d / %d NAF", i, len(futs))
    return done, failed


def to_long(responses: list[dict]) -> pd.DataFrame:
    """Format long : naf × taille (libellé de l'app) × domaine → note, justification."""
    rows = [
        {
            "naf": r["naf"],
            "naf_libelle": r["naf_libelle"],
            "taille": SIZE_KEYS[size],
            "domaine": d,
            "note_llm": r["grille"][size][d],
            "justification": r["justification"][d],
            "modele": r["modele"],
            "consigne": r["consigne"],
        }
        for r in responses
        for size in SIZE_KEYS
        for d in DOMAINS
    ]
    return pd.DataFrame(rows)


def size_class(tranche_effectif: pd.Series) -> pd.Series:
    """Code INSEE de tranche → libellé de taille de la grille (NaN si < 10 salariés)."""
    return tranche_effectif.map(_TRANCHE_TO_SIZE_KEY).map(SIZE_KEYS)
