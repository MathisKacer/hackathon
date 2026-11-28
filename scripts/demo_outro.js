// T62 — Outro de la vidéo de démo (injectée par scripts/demo_video_complet.py, ~9 s).
// Le « O » boussole du logo en haut à gauche se détache, grossit en tournant, monte dans un
// bateau ; l'aiguille se fixe quand le bateau démarre, puis le bateau part vers la droite et le
// logo « Compass » s'affiche avec le slogan. Géométrie du « O » : app/static/logo-compass-clair.svg
// (viewBox 106 233 1022 216 ; groupe translate(262.1 240.8) scale(2.9333) sur une boîte 60×60).
(logoSvg) => {
  const NAVY = '#14213D', ORANGE = '#E4572E', INDIGO = '#3B5BDB';
  const link = document.querySelector('.st-key-entete_logo [data-testid="stPageLink"]');
  const r = link.getBoundingClientRect();
  // logo dessiné en « contain », calé à gauche et centré verticalement dans la boîte
  const lw = r.width, lh = Math.min(r.height, r.width * 216 / 1022);
  const top = r.top + (r.height - lh) / 2;
  const k = lh / 216;
  const O = { x: r.left + (262.1 - 106) * k, y: top + (240.8 - 233) * k, size: 60 * 2.9333 * k };
  const W = innerWidth, H = innerHeight;
  const bg = getComputedStyle(document.querySelector('.stApp') || document.body).backgroundColor;

  const el = (tag, css, html) => {
    const e = document.createElement(tag);
    e.style.cssText = css;
    if (html) e.innerHTML = html;
    document.body.appendChild(e);
    return e;
  };
  document.getElementById('demo-cursor')?.remove();

  // fond qui recouvre peu à peu la page
  const veil = el('div', `position:fixed;inset:0;z-index:2147483640;opacity:0;
    background:radial-gradient(circle at 50% 40%, #ffffff 0%, #eef2ff 60%, #dbe4ff 100%);`);
  // cache le « O » d'origine (le temps qu'il s'envole)
  el('div', `position:fixed;z-index:2147483641;left:${O.x - 2}px;top:${O.y - 2}px;
    width:${O.size + 4}px;height:${O.size + 4}px;border-radius:50%;background:${bg};`);

  // mer et bateau (cachés sous l'écran au début)
  const sea = el('div', `position:fixed;left:0;right:0;bottom:0;height:${H * 0.3}px;
    z-index:2147483642;transform:translateY(100%);`, `
    <svg width="200%" height="100%" viewBox="0 0 2400 300" preserveAspectRatio="none"
         style="position:absolute;left:0;top:0">
      <path d="M0 60 Q150 20 300 60 T600 60 T900 60 T1200 60 T1500 60 T1800 60 T2100 60 T2400 60
               V300 H0 Z" fill="${INDIGO}" opacity=".18"/>
      <path d="M0 100 Q150 60 300 100 T600 100 T900 100 T1200 100 T1500 100 T1800 100 T2100 100
               T2400 100 V300 H0 Z" fill="${INDIGO}" opacity=".35"/>
    </svg>`);
  const waves = sea.querySelector('svg');
  const BW = 420, BH = 360;
  // ligne de flottaison : ~1/4 de la hauteur de la mer ; la coque (y 258–330) s'y enfonce à y 300
  const BOAT = { left: W / 2 - BW / 2, top: H * 0.775 - BH * 300 / 360 };
  const boat = el('div', `position:fixed;z-index:2147483643;width:${BW}px;height:${BH}px;
    left:${BOAT.left}px;top:${BOAT.top}px;transform:translateY(${H}px);`, `
    <svg viewBox="0 0 420 360" width="${BW}" height="${BH}">
      <line x1="200" y1="30" x2="200" y2="262" stroke="${NAVY}" stroke-width="8"
            stroke-linecap="round"/>
      <path d="M208 40 L208 240 L360 240 Z" fill="#ffffff" stroke="${NAVY}" stroke-width="6"
            stroke-linejoin="round"/>
      <path d="M192 70 L192 240 L80 240 Z" fill="${ORANGE}" stroke="${NAVY}" stroke-width="6"
            stroke-linejoin="round"/>
      <path d="M200 30 L238 42 L200 54 Z" fill="${ORANGE}"/>
      <path d="M30 258 H390 L345 330 H75 Z" fill="${NAVY}"/>
    </svg>`);
  // emplacement de la boussole sur la coque (hublot) : centre (210, 294), diamètre 66
  const SEAT = { x: 210 / 420, y: 294 / 360, size: 66 };

  // la boussole (copie fidèle du « O »)
  const C = el('div', `position:fixed;z-index:2147483644;left:${O.x}px;top:${O.y}px;
    width:${O.size}px;height:${O.size}px;transform-origin:50% 50%;`, `
    <svg viewBox="0 0 60 60" width="100%" height="100%" style="overflow:visible">
      <circle cx="30" cy="30" r="28" fill="#ffffff"/>
      <circle cx="30" cy="30" r="24" fill="none" stroke="${NAVY}" stroke-width="7"/>
      <g class="needle" style="transform-box:view-box;transform-origin:30px 30px;
         transform:rotate(45deg)">
        <path d="M30 11 L36 30 L24 30 Z" fill="${ORANGE}"/>
        <path d="M30 49 L36 30 L24 30 Z" fill="${NAVY}"/>
      </g>
    </svg>`);
  const needle = C.querySelector('.needle');

  // fin : logo + slogan
  const brand = el('div', `position:fixed;z-index:2147483645;left:0;right:0;top:${H * 0.30}px;
    text-align:center;opacity:0;font-family:Inter,system-ui,sans-serif;`, `
    <div class="brand-logo" style="height:${H * 0.17}px;display:inline-block">${logoSvg}</div>
    <div style="margin-top:18px;font-size:${H * 0.036}px;font-style:italic;color:#4b5563">
      Oser l'audace, fini l'impasse</div>`);

  const ease = 'cubic-bezier(.45,0,.2,1)';
  const t = (ms, fn) => setTimeout(fn, ms);

  // 1) 0 → 2,6 s : le « O » grossit en tournant jusqu'au centre de l'écran
  // aiguille : accélère jusqu'à 2 tours/s, puis (stop) ralentit et se fixe sur 45° (cap du logo)
  let angle = 45, speed = 0, last = performance.now(), stop = null;
  const spin = now => {
    const dt = (now - last) / 1000; last = now;
    if (!stop) {
      speed = Math.min(speed + 900 * dt, 720);
      angle += speed * dt;
    } else {
      const p = Math.min((now - stop.t) / stop.ms, 1);
      angle = stop.a0 + (stop.target - stop.a0) * (1 - Math.pow(1 - p, 3));
      if (p === 1) { needle.style.transform = `rotate(${stop.target}deg)`; return; }
    }
    needle.style.transform = `rotate(${angle}deg)`;
    requestAnimationFrame(spin);
  };
  requestAnimationFrame(spin);

  const big = Math.min(W, H) * 0.42;
  veil.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 1400, delay: 500, fill: 'forwards' });
  C.animate([
    { left: `${O.x}px`, top: `${O.y}px`, width: `${O.size}px`, height: `${O.size}px` },
    { left: `${W / 2 - big / 2}px`, top: `${H * 0.40 - big / 2}px`, width: `${big}px`,
      height: `${big}px` },
  ], { duration: 2600, easing: ease, fill: 'forwards' });

  // 2) 2,6 → 4,4 s : la mer et le bateau arrivent, la boussole « monte à bord » (hublot)
  // place du hublot quand le bateau est arrivé (pas pendant sa montée)
  const seat = () => ({ x: BOAT.left + SEAT.x * BW - SEAT.size / 2,
                        y: BOAT.top + SEAT.y * BH - SEAT.size / 2 });
  t(2400, () => {
    sea.animate([{ transform: 'translateY(100%)' }, { transform: 'translateY(0)' }],
      { duration: 1200, easing: ease, fill: 'forwards' });
    waves.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-50%)' }],
      { duration: 6000, iterations: Infinity });
    boat.animate([{ transform: `translateY(${H}px)` }, { transform: 'translateY(0)' }],
      { duration: 1300, easing: ease, fill: 'forwards' });
  });
  t(3200, () => {
    const s = seat();
    const from = C.getBoundingClientRect();
    C.animate([
      { left: `${from.left}px`, top: `${from.top}px`, width: `${from.width}px`,
        height: `${from.height}px` },
      { left: `${s.x}px`, top: `${s.y}px`, width: `${SEAT.size}px`, height: `${SEAT.size}px` },
    ], { duration: 1200, easing: ease, fill: 'forwards' });
  });
  // le bateau tangue doucement pendant l'embarquement
  t(3700, () => {
    boat.animate([{ transform: 'translateY(0) rotate(0deg)' },
      { transform: 'translateY(-6px) rotate(-1.5deg)' },
      { transform: 'translateY(0) rotate(0deg)' }], { duration: 1400, iterations: 2 });
  });

  // 3) 4,6 s : l'aiguille se fixe (cap du logo) → 5,4 s : le bateau démarre vers la droite
  t(4600, () => {
    // au moins un tour de plus, en ralentissant, et arrêt pile sur 45°
    stop = { t: performance.now(), ms: 1000, a0: angle,
             target: Math.ceil((angle - 45) / 360 + 1) * 360 + 45 };
  });
  t(5600, () => {
    const s = seat();
    const go = W * 0.75;
    const opts = { duration: 2600, easing: 'cubic-bezier(.5,0,.75,0)', fill: 'forwards' };
    boat.animate([{ transform: 'translateX(0) rotate(0deg)' },
      { transform: `translateX(${go}px) rotate(-3deg)` }], opts);
    C.animate([{ left: `${s.x}px`, top: `${s.y}px` },
      { left: `${s.x + go}px`, top: `${s.y - 10}px` }], opts);
  });

  // 4) 7,4 s : logo et slogan
  t(7400, () => {
    brand.animate([{ opacity: 0, transform: 'translateY(16px)' },
      { opacity: 1, transform: 'translateY(0)' }], { duration: 900, easing: ease,
      fill: 'forwards' });
  });
}
