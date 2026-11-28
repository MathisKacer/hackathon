"""T62 — Vidéo de démo « parcours complet » : intro → accueil → carte → Entreprises → Mon compte.

    uv run python scripts/demo_compte.py     # compte de démo + candidatures (une fois)
    uv run --with playwright --with imageio-ffmpeg python scripts/demo_video_complet.py
    # → data/demo/demo_complet.mp4 (avec data/demo/intro.mp4 devant, si elle existe)
    # --essai : captures d'écran de chaque étape, sans vidéo

Parcours (compte « moussaillon » déjà connecté, hors vidéo) :
1. accueil déjà rempli (Rennes, stage, data) → « Rechercher » → carte ;
2. zoom sur Rennes, clic sur un point orange (fenêtre de l'entreprise) ;
3. « Entreprises » (en haut à droite) → « AVISIA » → résultats → clic sur la 1re fiche ;
4. « Mon compte » (en haut à droite) : les candidatures (statuts variés, une à relancer) ;
5. outro (scripts/demo_outro.js) : le « O » boussole du logo grossit, monte dans un bateau,
   l'aiguille se fixe quand le bateau démarre, puis logo et slogan.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from demo_video import INIT_JS, Demo, H, W, fill, launch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTRO_JS = Path(__file__).with_name("demo_outro.js")
LOGO_SVG = ROOT / "app" / "static" / "logo-compass-clair.svg"
DEMO_DIR = ROOT / "data" / "demo"
CRED_FILE = DEMO_DIR / ".compte_demo"
ORANGE_JS = """
els => els.map((e, i) => {
  const r = e.getBoundingClientRect();
  const x = r.x + r.width / 2, y = r.y + r.height / 2;
  return {i, x, y, w: r.width, top: document.elementFromPoint(x, y) === e,
          fill: (e.getAttribute('fill') || '').toLowerCase()};
})
"""


def login(d: Demo, url: str) -> None:
    cred = json.loads(CRED_FILE.read_text())
    pg = d.page
    pg.goto(url.rstrip("/") + "/connexion", wait_until="networkidle")
    pg.get_by_label("Identifiant").fill(cred["identifiant"])
    pg.get_by_label("Mot de passe").fill(cred["mot_de_passe"])
    pg.get_by_role("button", name="Se connecter").click()
    pg.get_by_role("link", name="Mon compte").first.wait_for(timeout=60_000)
    d.idle()


def click_orange(d: Demo) -> None:
    """Clique sur un point orange visible, le plus gros près du centre de la carte."""
    pg = d.page
    iframe = pg.locator('iframe[title*="folium"]').first
    box = iframe.bounding_box()
    frame = iframe.content_frame
    pts = frame.locator("path.leaflet-interactive").evaluate_all(ORANGE_JS)
    cx, cy = box["width"] / 2, box["height"] / 2
    blue = ("#1f6fd1", "#1d4ed8", "#2563eb", "#3b82f6")
    pts = [
        p
        for p in pts
        if p["top"] and p["fill"] and p["fill"] not in blue and 40 < p["x"] < box["width"] - 40
        and 40 < p["y"] < box["height"] - 40
    ]  # fmt: skip
    if not pts:
        raise SystemExit("Aucun point orange visible sur la carte après le zoom.")
    best = max(
        pts, key=lambda p: p["w"] * 3 - ((p["x"] - cx) ** 2 + (p["y"] - cy) ** 2) ** 0.5 / 20
    )
    x, y = box["x"] + best["x"], box["y"] + best["y"]
    pg.mouse.move(x, y, steps=30)
    d.pause(0.6)
    pg.mouse.down()
    pg.mouse.up()
    popup = frame.locator(".leaflet-popup-content").first
    try:
        popup.wait_for(timeout=3_000)
    except Exception:  # noqa: BLE001 — clic intercepté : on clique sur le point lui-même
        frame.locator("path.leaflet-interactive").nth(best["i"]).dispatch_event("click")
        popup.wait_for(timeout=10_000)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", default="http://localhost:8501/")
    p.add_argument("--out", type=Path, default=DEMO_DIR / "demo_complet.mp4")
    p.add_argument("--intro", type=Path, default=DEMO_DIR / "intro.mp4")
    p.add_argument("--fondu", type=float, default=0.5)
    p.add_argument("--ville", default="Rennes")
    p.add_argument("--contrat", default="Stage")
    p.add_argument("--entreprise", default="AVISIA")
    p.add_argument("--zoom", type=int, default=2, help="niveaux de zoom sur la carte")
    p.add_argument("--pause-compte", type=float, default=6)
    p.add_argument("--pause-accueil", type=float, default=2)
    p.add_argument("--pause-carte", type=float, default=4, help="avant le zoom")
    p.add_argument("--pause-point", type=float, default=7, help="fenêtre de l'entreprise")
    p.add_argument("--pause-entreprises", type=float, default=3, help="liste des résultats")
    p.add_argument("--ligne", type=int, default=0, help="ligne cliquée dans les résultats")
    p.add_argument("--pause-fiche", type=float, default=6, help="fiche de l'entreprise")
    p.add_argument("--sans-outro", action="store_true")
    p.add_argument("--essai", action="store_true", help="captures d'écran seulement")
    a = p.parse_args()
    if not CRED_FILE.exists():
        raise SystemExit("Compte de démo absent : lancer d'abord scripts/demo_compte.py")

    shots = DEMO_DIR / "captures_complet" if a.essai else None
    if shots:
        shutil.rmtree(shots, ignore_errors=True)
        shots.mkdir(parents=True)
    raw_dir = DEMO_DIR / "brut_complet"
    shutil.rmtree(raw_dir, ignore_errors=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        warm = browser.new_page(viewport={"width": W, "height": H})  # caches de l'appli
        warm.goto(a.url, wait_until="networkidle")
        fill(wd := Demo(warm, None), a.ville, a.contrat)
        launch(wd)
        warm.close()

        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=None if a.essai else str(raw_dir),
            record_video_size={"width": W, "height": H},
        )
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()
        t_page = time.monotonic()
        d = Demo(page, shots)
        # Hors vidéo : connexion, puis accueil rempli
        login(d, a.url)
        page.get_by_role("link", name="Compass").first.click()
        page.get_by_role("button", name="Rechercher").wait_for(timeout=60_000)
        d.idle()
        fill(d, a.ville, a.contrat)
        page.mouse.move(W * 0.5, H * 0.75)
        t0 = time.monotonic() - t_page

        # 1. Accueil → Rechercher → carte, zoom, point orange
        d.snap("accueil")
        d.pause(a.pause_accueil)
        launch(d)
        d.snap("carte")
        d.pause(a.pause_carte)
        iframe = page.locator('iframe[title*="folium"]').first
        x, y = d.move_to(iframe, 0.52, 0.5)
        for _ in range(a.zoom):
            page.mouse.wheel(0, -60)  # Leaflet : 60 px de molette = 1 niveau de zoom
            d.pause(1.2)
        d.pause(0.8)
        d.snap("zoom")
        click_orange(d)
        d.pause(0.8)
        d.snap("point")
        d.pause(a.pause_point)
        # 3. Entreprises → AVISIA
        d.click(page.get_by_role("link", name="Entreprises").first)
        d.idle()
        d.click(page.get_by_label("Entreprise", exact=True))
        d.type(a.entreprise)
        page.keyboard.press("Enter")
        d.idle()
        page.locator('[data-testid="stDataFrame"]').first.wait_for(timeout=60_000)
        d.pause(0.8)
        d.snap("entreprises")
        d.pause(a.pause_entreprises)
        grid = page.locator('[data-testid="stDataFrame"]').first
        box = grid.bounding_box()
        y = 35 + 35 * (a.ligne + 0.5)  # tableau sur canvas : en-tête et lignes ~35 px
        d.click(grid, dx=min(160 / box["width"], 0.3), dy=min(y / box["height"], 0.95))
        dialog = page.get_by_role("dialog")
        dialog.wait_for(timeout=60_000)
        d.idle()
        d.snap("fiche")
        d.pause(a.pause_fiche)
        page.keyboard.press("Escape")
        try:
            dialog.wait_for(state="hidden", timeout=5_000)
        except Exception:  # noqa: BLE001 — sinon, la croix de la fenêtre
            dialog.get_by_role("button").first.click()
            dialog.wait_for(state="hidden", timeout=10_000)
        d.idle()
        # 4. Mon compte : les candidatures
        d.click(page.get_by_role("link", name="Mon compte").first)
        page.get_by_text("Où en sont tes candidatures").first.wait_for(timeout=60_000)
        d.idle()
        d.snap("compte")
        cards = page.locator('[class*="st-key-espace_candidature_"]')
        for i in range(min(cards.count(), 3)):
            d.move_to(cards.nth(i), 0.3, 0.5)
            d.pause(a.pause_compte / 3)
        d.pause(1.0)
        if not a.sans_outro:  # 5. outro
            page.mouse.move(-50, -50)
            logo = LOGO_SVG.read_text(encoding="utf-8")
            logo = logo.replace('width="1022" height="216"', 'height="100%"')
            page.evaluate(OUTRO_JS.read_text(encoding="utf-8"), logo)
            for i, sec in enumerate((1.3, 1.4, 1.2, 1.2, 1.4, 1.6, 2.4)):  # ~10,5 s
                d.pause(sec)
                d.snap(f"outro_{i}")
        raw = None if a.essai else Path(page.video.path())
        ctx.close()
        browser.close()

    if a.essai:
        print(f"Captures → {shots}")
        return
    import imageio_ffmpeg

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    body = DEMO_DIR / "demo_complet_sans_intro.mp4"
    cmd = [ff, "-y", "-ss", f"{t0:.2f}", "-i", str(raw), "-c:v", "libx264", "-pix_fmt",
           "yuv420p", "-crf", "20", "-r", "30", "-an", str(body)]  # fmt: skip
    subprocess.run(cmd, check=True, capture_output=True)
    shutil.rmtree(raw_dir, ignore_errors=True)
    if a.intro.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "video_intro.py"), str(a.intro),
             "--demo", str(body), "--sortie", str(a.out), "--fondu", str(a.fondu)],
            check=True,
        )  # fmt: skip
    else:
        shutil.move(body, a.out)
        print(f"Vidéo → {a.out} (sans intro : {a.intro} absente)")


if __name__ == "__main__":
    main()
