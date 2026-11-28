"""T62 — Enregistre la vidéo de démo (1 minute) avec Playwright, sans écran : docs/DEMO.md.

Prérequis (une fois par pod) :
    uv run --with playwright playwright install chromium
    uv run --with playwright playwright install-deps chromium   # bibliothèques système (sudo)

L'appli doit tourner (uv run streamlit run app/streamlit_app.py, port 8501). Puis :
    uv run --with playwright --with imageio-ffmpeg python scripts/demo_video.py
    # → data/demo/demo.mp4 (hors Git) ; --essai : captures d'écran de chaque étape, sans vidéo

Scénario (docs/DEMO.md) : accueil déjà rempli (Rennes, stage, data, 20 km) → Rechercher → carte (pause)
→ Entreprises → « Hellowork », Rennes → fiche (pause). Les pauses sont calées sur le texte que
l'orateur lit par-dessus ; les régler avec --pause-carte et --pause-fiche.
"""

# ruff: noqa: E501 — JavaScript injecté, lignes longues assumées
from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
W, H = 1920, 1080

# Curseur visible (une vidéo Playwright ne montre pas la souris) + barre « Running… » masquée.
INIT_JS = """
(() => {
  const add = () => {
    if (!document.body || document.getElementById('demo-cursor')) return;
    const c = document.createElement('div');
    c.id = 'demo-cursor';
    c.style.cssText = 'position:fixed;z-index:2147483647;width:22px;height:22px;border-radius:50%;'
      + 'background:rgba(79,70,229,.35);border:2px solid #4f46e5;pointer-events:none;'
      + 'transform:translate(-50%,-50%);left:-100px;top:-100px;transition:width .1s,height .1s;';
    document.body.appendChild(c);
    document.addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
    document.addEventListener('mousedown', () => { c.style.width = c.style.height = '14px'; }, true);
    document.addEventListener('mouseup', () => { c.style.width = c.style.height = '22px'; }, true);
    const s = document.createElement('style');
    s.textContent = '[data-testid="stStatusWidget"],[data-testid="stToolbar"],'
      + '[data-testid="stDecoration"]{visibility:hidden!important}';
    document.head.appendChild(s);
  };
  document.addEventListener('DOMContentLoaded', add);
  new MutationObserver(add).observe(document, {childList: true, subtree: true});
})();
"""


class Demo:
    def __init__(self, page: Page, shots: Path | None):
        self.page, self.shots, self.n = page, shots, 0

    def snap(self, name: str) -> None:
        if self.shots:
            self.n += 1
            self.page.screenshot(path=self.shots / f"{self.n:02d}_{name}.png")

    def pause(self, seconds: float) -> None:
        self.page.wait_for_timeout(int(seconds * 1000))

    def move_to(self, loc: Locator, dx: float = 0.5, dy: float = 0.5) -> tuple[float, float]:
        loc.scroll_into_view_if_needed()
        box = loc.bounding_box()
        x, y = box["x"] + box["width"] * dx, box["y"] + box["height"] * dy
        self.page.mouse.move(x, y, steps=30)  # déplacement visible, pas de téléportation
        self.pause(0.3)
        return x, y

    def click(self, loc: Locator, **kw) -> None:
        self.move_to(loc, **kw)
        self.page.mouse.down()
        self.page.mouse.up()

    def type(self, text: str) -> None:
        self.page.keyboard.type(text, delay=70)

    def idle(self) -> None:
        """Attend que Streamlit ait fini de recalculer (plus d'indicateur « Running »)."""
        self.pause(0.5)
        self.page.wait_for_function(
            '() => !document.querySelector(\'[data-testid="stStatusWidget"] [data-testid="stStatusWidgetRunningIcon"]\')'
            " && !document.querySelector('.stSpinner')",
            timeout=120_000,
        )
        self.pause(0.5)


def fill(d: Demo, ville: str, contrat: str) -> None:
    """Remplit l'accueil (ville, contrat) ; hors vidéo par défaut (« accueil déjà rempli »)."""
    pg = d.page
    pg.get_by_role("button", name="Rechercher").wait_for(timeout=120_000)
    box = pg.locator('[data-testid="stSelectbox"]').filter(has_text="Où ?")
    d.click(box.locator("input"))
    d.type(ville)
    d.pause(0.6)
    d.click(pg.get_by_role("option").filter(has_text=f"{ville} (").first)
    d.idle()
    d.click(
        pg.get_by_role("radiogroup", name="Contrat").get_by_role("radio", name=contrat, exact=True)
    )
    d.idle()


def launch(d: Demo) -> None:
    pg = d.page
    d.snap("accueil")
    d.click(pg.get_by_role("button", name="Rechercher"))
    pg.locator('iframe[title*="folium"]').first.wait_for(timeout=120_000)
    d.idle()
    d.pause(2.5)  # tuiles de la carte


def company(d: Demo, nom: str, ville: str, row: int) -> None:
    pg = d.page
    d.click(pg.get_by_role("link", name="Entreprises").first)
    d.idle()
    d.click(pg.get_by_label("Entreprise", exact=True))
    d.type(nom)
    d.click(pg.get_by_label("Ville ou code postal"))
    d.type(ville)
    pg.keyboard.press("Enter")
    d.idle()
    grid = pg.locator('[data-testid="stDataFrame"]').first
    grid.wait_for(timeout=60_000)
    d.pause(0.8)
    d.snap("entreprises")
    # Tableau dessiné sur un canvas : clic dans la 1re colonne (« Entreprise ») de la ligne voulue
    box = grid.bounding_box()
    y = 35 + 35 * (row + 0.5)  # en-tête ~35 px, lignes ~35 px
    d.click(grid, dx=min(120 / box["width"], 0.3), dy=min(y / box["height"], 0.95))
    pg.get_by_role("dialog").wait_for(timeout=60_000)
    d.idle()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", default="http://localhost:8501/")
    p.add_argument("--out", type=Path, default=ROOT / "data" / "demo" / "demo.mp4")
    p.add_argument("--ville", default="Rennes")
    p.add_argument("--contrat", default="Stage")
    p.add_argument("--entreprise", default="Hellowork")
    p.add_argument(
        "--ligne",
        type=int,
        default=1,
        help="ligne du tableau Entreprises (0 = toute l'entreprise, 1 = le site)",
    )
    p.add_argument("--pause-accueil", type=float, default=3, help="secondes sur l'accueil")
    p.add_argument("--pause-carte", type=float, default=15, help="secondes sur la carte")
    p.add_argument("--pause-fiche", type=float, default=20, help="secondes sur la fiche")
    p.add_argument("--taper-ville", action="store_true", help="filmer aussi la saisie de la ville")
    p.add_argument("--essai", action="store_true", help="captures d'écran seulement, pas de vidéo")
    a = p.parse_args()

    a.out.parent.mkdir(parents=True, exist_ok=True)
    shots = a.out.parent / "captures" if a.essai else None
    if shots:
        shutil.rmtree(shots, ignore_errors=True)
        shots.mkdir(parents=True)
    raw_dir = a.out.parent / "brut"
    shutil.rmtree(raw_dir, ignore_errors=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        # 1) Passage à blanc, non enregistré : remplit les caches de l'appli (démo fluide)
        warm = browser.new_page(viewport={"width": W, "height": H})
        warm.goto(a.url, wait_until="networkidle")
        fill(warm_demo := Demo(warm, None), a.ville, a.contrat)
        launch(warm_demo)
        warm.close()
        # 2) Passage enregistré
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=None if a.essai else str(raw_dir),
            record_video_size={"width": W, "height": H},
        )
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()
        t_page = time.monotonic()
        page.goto(a.url, wait_until="networkidle")
        page.get_by_role("button", name="Rechercher").wait_for(timeout=120_000)
        d = Demo(page, shots)
        d.idle()
        if not a.taper_ville:
            fill(d, a.ville, a.contrat)
            page.mouse.move(W / 2, H * 0.75)
        t0 = time.monotonic() - t_page  # début utile de la vidéo (page d'accueil affichée)
        if a.taper_ville:
            fill(d, a.ville, a.contrat)
        d.pause(a.pause_accueil)
        launch(d)
        d.snap("carte")
        map_box = page.locator('iframe[title*="folium"]').first
        d.move_to(map_box, 0.45, 0.45)  # le curseur se pose sur la carte pendant le texte
        d.pause(a.pause_carte)
        company(d, a.entreprise, a.ville, a.ligne)
        d.snap("fiche")
        d.pause(a.pause_fiche)
        raw = None if a.essai else Path(page.video.path())  # connu avant la fermeture
        ctx.close()
        browser.close()

    if a.essai:
        print(f"Captures → {shots}")
        return
    import imageio_ffmpeg

    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-ss", f"{t0:.2f}", "-i", str(raw),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-r", "30", "-an", str(a.out),
    ]  # fmt: skip
    subprocess.run(cmd, check=True, capture_output=True)
    shutil.rmtree(raw_dir, ignore_errors=True)
    dur = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(a.out)], capture_output=True, text=True
    ).stderr.split("Duration: ")[-1][:11]
    print(f"Vidéo → {a.out} (durée {dur})")


if __name__ == "__main__":
    main()
