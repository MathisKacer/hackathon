"""T62 — Colle une vidéo d'intro devant la vidéo de démo (data/demo/demo.mp4) : docs/DEMO.md.

    uv run --with imageio-ffmpeg python scripts/video_intro.py data/demo/intro.mp4
    # → data/demo/demo_avec_intro.mp4
    uv run --with imageio-ffmpeg python scripts/video_intro.py intro.mov --fondu 0.5 \
        --sortie final.mp4

L'intro peut avoir n'importe quel format (MP4, MOV, WebM…), taille ou cadence : elle est mise au
format de la démo (1920×1080, 30 i/s, bandes noires si les proportions diffèrent). Son son est
gardé ; la démo, muette, reçoit un silence. Fondu enchaîné facultatif entre les deux.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1920, 1080, 30


def probe(path: Path) -> tuple[float, bool]:
    """(durée en secondes, a une piste audio) d'après la sortie de ffmpeg -i."""
    err = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if not m:
        raise SystemExit(f"Vidéo illisible : {path}")
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s), " Audio:" in err


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("intro", type=Path, help="vidéo d'intro")
    p.add_argument("--demo", type=Path, default=ROOT / "data" / "demo" / "demo.mp4")
    p.add_argument("--sortie", type=Path, default=ROOT / "data" / "demo" / "demo_avec_intro.mp4")
    p.add_argument(
        "--fondu", type=float, default=0.0, help="fondu enchaîné en secondes (0 = coupe)"
    )
    a = p.parse_args()

    d_intro, intro_audio = probe(a.intro)
    d_demo, _ = probe(a.demo)
    fit = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
        f"setsar=1,fps={FPS},format=yuv420p"
    )
    # audio : celui de l'intro (ou un silence), puis un silence de la durée de la démo
    a_intro = "[0:a]aresample=48000,aformat=channel_layouts=stereo[ai]" if intro_audio else ""
    silence_intro = "" if intro_audio else f"[2:a]atrim=0:{d_intro:.3f}[ai]"
    filters = [f"[0:v]{fit}[vi]", f"[1:v]{fit}[vd]", a_intro or silence_intro,
               f"[3:a]atrim=0:{d_demo:.3f}[ad]"]  # fmt: skip
    if a.fondu > 0:
        off = max(d_intro - a.fondu, 0)
        filters += [
            f"[vi][vd]xfade=transition=fade:duration={a.fondu}:offset={off:.3f}[v]",
            f"[ai][ad]acrossfade=d={a.fondu}[a]",
        ]
    else:
        filters.append("[vi][ai][vd][ad]concat=n=2:v=1:a=1[v][a]")
    silent = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    cmd = [FFMPEG, "-y", "-i", str(a.intro), "-i", str(a.demo), *silent, *silent,
           "-filter_complex", ";".join(f for f in filters if f), "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
           "-movflags", "+faststart", str(a.sortie)]  # fmt: skip
    a.sortie.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-1500:])
    total, _ = probe(a.sortie)
    print(f"Vidéo → {a.sortie} ({d_intro:.1f} s d'intro + {d_demo:.1f} s de démo = {total:.1f} s)")


if __name__ == "__main__":
    main()
