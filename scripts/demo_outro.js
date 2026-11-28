// T62 — Outro de la vidéo de démo (injectée par scripts/demo_video_complet.py, ~5,5 s).
// Le « O » boussole du logo (en haut à gauche) se détache et devient un petit personnage : il
// grossit en tournant l'aiguille, des yeux, des bras et des jambes lui poussent ; un bateau arrive,
// il saute à bord et se tient sur le pont ; son aiguille se fixe et il montre le cap quand le
// bateau démarre ; puis logo « Compass » et slogan. Géométrie du « O » :
// app/static/logo-compass-clair.svg (viewBox 106 233 1022 216 ; groupe translate(262.1 240.8)
// scale(2.9333) sur une boîte 60×60).
(logoSvg) => {
  const NAVY = '#14213D', ORANGE = '#E4572E', INDIGO = '#3B5BDB';
  const link = document.querySelector('.st-key-entete_logo [data-testid="stPageLink"]');
  const r = link.getBoundingClientRect();
  const lh = Math.min(r.height, r.width * 216 / 1022);  // logo en « contain », calé à gauche
  const k = lh / 216, top0 = r.top + (r.height - lh) / 2;
  const O = { size: 60 * 2.9333 * k };
  O.cx = r.left + (262.1 - 106) * k + O.size / 2;
  O.cy = top0 + (240.8 - 233) * k + O.size / 2;
  const W = innerWidth, H = innerHeight;
  const bg = getComputedStyle(document.querySelector('.stApp') || document.body).backgroundColor;
  const ease = 'cubic-bezier(.45,0,.2,1)';
  const later = (ms, fn) => setTimeout(fn, ms);

  const el = (tag, css, html) => {
    const e = document.createElement(tag);
    e.style.cssText = css;
    if (html) e.innerHTML = html;
    document.body.appendChild(e);
    return e;
  };
  document.getElementById('demo-cursor')?.remove();

  // fond qui recouvre la page ; disque qui cache le « O » d'origine
  const veil = el('div', `position:fixed;inset:0;z-index:2147483640;opacity:0;
    background:radial-gradient(circle at 50% 40%, #ffffff 0%, #eef2ff 60%, #dbe4ff 100%);`);
  el('div', `position:fixed;z-index:2147483641;left:${O.cx - O.size / 2 - 2}px;
    top:${O.cy - O.size / 2 - 2}px;width:${O.size + 4}px;height:${O.size + 4}px;
    border-radius:50%;background:${bg};`);

  // mer
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

  // bateau : pont à y = 258 (repère 420×360), coque enfoncée dans l'eau
  const BW = 420, BH = 360;
  const BOAT = { left: W / 2 - BW / 2 - W * 0.05, top: H * 0.775 - BH * 300 / 360 };
  const boat = el('div', `position:fixed;z-index:2147483643;width:${BW}px;height:${BH}px;
    left:${BOAT.left}px;top:${BOAT.top}px;transform:translateY(${H}px);`, `
    <svg viewBox="0 0 420 360" width="${BW}" height="${BH}">
      <line x1="170" y1="30" x2="170" y2="262" stroke="${NAVY}" stroke-width="8"
            stroke-linecap="round"/>
      <path d="M178 40 L178 240 L300 240 Z" fill="#ffffff" stroke="${NAVY}" stroke-width="6"
            stroke-linejoin="round"/>
      <path d="M162 70 L162 240 L60 240 Z" fill="${ORANGE}" stroke="${NAVY}" stroke-width="6"
            stroke-linejoin="round"/>
      <path d="M170 30 L208 42 L170 54 Z" fill="${ORANGE}"/>
      <path d="M30 258 H390 L345 330 H75 Z" fill="${NAVY}"/>
    </svg>`);

  // le personnage : le « O » (anneau + aiguille) avec yeux, bras et jambes (cachés au début).
  // Repère : anneau dans la boîte 0..60 ; le dessin complet va de x -30..90 et y -22..100.
  const VB = { x: -30, y: -22, w: 120, h: 122 };
  const C = el('div', 'position:fixed;z-index:2147483644;', `
    <svg viewBox="${VB.x} ${VB.y} ${VB.w} ${VB.h}" width="100%" height="100%"
         style="overflow:visible">
      <g class="limbs" style="opacity:0">
        <g class="leg-l" style="transform-box:view-box;transform-origin:24px 52px">
          <path d="M24 52 L19 80" stroke="${NAVY}" stroke-width="6" stroke-linecap="round"/>
          <ellipse cx="15" cy="82" rx="8" ry="4.5" fill="${NAVY}"/></g>
        <g class="leg-r" style="transform-box:view-box;transform-origin:36px 52px">
          <path d="M36 52 L41 80" stroke="${NAVY}" stroke-width="6" stroke-linecap="round"/>
          <ellipse cx="45" cy="82" rx="8" ry="4.5" fill="${NAVY}"/></g>
        <g class="arm-l" style="transform-box:view-box;transform-origin:6px 34px">
          <path d="M6 34 L-12 46" stroke="${NAVY}" stroke-width="6" stroke-linecap="round"/>
          <circle cx="-13" cy="47" r="4.5" fill="${NAVY}"/></g>
        <g class="arm-r" style="transform-box:view-box;transform-origin:54px 34px">
          <path d="M54 34 L72 46" stroke="${NAVY}" stroke-width="6" stroke-linecap="round"/>
          <circle cx="73" cy="47" r="4.5" fill="${NAVY}"/></g>
      </g>
      <circle cx="30" cy="30" r="27" fill="#ffffff"/>
      <circle cx="30" cy="30" r="24" fill="none" stroke="${NAVY}" stroke-width="7"/>
      <g class="needle" style="transform-box:view-box;transform-origin:30px 30px;
         transform:rotate(45deg)">
        <path d="M30 11 L36 30 L24 30 Z" fill="${ORANGE}"/>
        <path d="M30 49 L36 30 L24 30 Z" fill="${NAVY}"/>
      </g>
      <g class="eyes" style="opacity:0;transform-box:view-box;transform-origin:30px 2px">
        <circle cx="21" cy="2" r="7.5" fill="#ffffff" stroke="${NAVY}" stroke-width="3"/>
        <circle cx="39" cy="2" r="7.5" fill="#ffffff" stroke="${NAVY}" stroke-width="3"/>
        <circle class="pupil" cx="23" cy="3" r="3.4" fill="${NAVY}"/>
        <circle class="pupil" cx="41" cy="3" r="3.4" fill="${NAVY}"/>
      </g>
    </svg>`);
  const part = s => C.querySelector(s);
  // position du personnage d'après le centre de l'anneau et sa taille
  const at = (cx, cy, ring) => {
    const u = ring / 60;
    return { left: `${cx - (30 - VB.x) * u}px`, top: `${cy - (30 - VB.y) * u}px`,
             width: `${VB.w * u}px`, height: `${VB.h * u}px` };
  };
  Object.assign(C.style, at(O.cx, O.cy, O.size));

  // aiguille : accélère jusqu'à 2 tours/s ; puis ralentit et se fixe sur 45° (cap du logo)
  const needle = part('.needle');
  let angle = 45, speed = 0, last = performance.now(), stop = null;
  const spin = now => {
    const dt = (now - last) / 1000; last = now;
    if (!stop) { speed = Math.min(speed + 1500 * dt, 720); angle += speed * dt; }
    else {
      const p = Math.min((now - stop.t) / stop.ms, 1);
      angle = stop.a0 + (stop.target - stop.a0) * (1 - Math.pow(1 - p, 3));
      if (p === 1) { needle.style.transform = `rotate(${stop.target}deg)`; return; }
    }
    needle.style.transform = `rotate(${angle}deg)`;
    requestAnimationFrame(spin);
  };
  requestAnimationFrame(spin);

  const swing = (sel, a, ms) => part(sel).animate(
    [{ transform: `rotate(${-a}deg)` }, { transform: `rotate(${a}deg)` }],
    { duration: ms, iterations: Infinity, direction: 'alternate', easing: 'ease-in-out' });

  // 1) 0 → 1,4 s : il grossit jusqu'au centre ; à 0,6 s, yeux, bras et jambes apparaissent
  const big = Math.min(W, H) * 0.30;
  veil.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 900, delay: 200, fill: 'forwards' });
  C.animate([at(O.cx, O.cy, O.size), at(W / 2, H * 0.36, big)],
    { duration: 1400, easing: ease, fill: 'forwards' });
  let moves = [];
  later(600, () => {
    for (const s of ['.limbs', '.eyes']) {
      part(s).animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300, fill: 'forwards' });
    }
    // il fait coucou et piétine d'impatience
    moves = [swing('.arm-r', 35, 260), swing('.leg-l', 8, 300), swing('.leg-r', -8, 300)];
  });
  later(1100, () => part('.eyes').animate(  // clignement des yeux
    [{ transform: 'scaleY(1)' }, { transform: 'scaleY(.1)' }, { transform: 'scaleY(1)' }],
    { duration: 220 }));

  // 2) 1,0 → 1,9 s : la mer et le bateau arrivent ; il regarde le bateau
  later(1000, () => {
    sea.animate([{ transform: 'translateY(100%)' }, { transform: 'translateY(0)' }],
      { duration: 900, easing: ease, fill: 'forwards' });
    waves.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-50%)' }],
      { duration: 6000, iterations: Infinity });
    boat.animate([{ transform: `translateY(${H}px)` }, { transform: 'translateY(0)' }],
      { duration: 900, easing: ease, fill: 'forwards' });
    C.querySelectorAll('.pupil').forEach(p => p.animate(
      [{ transform: 'translate(0,0)' }, { transform: 'translate(1px,3px)' }],
      { duration: 400, fill: 'forwards' }));
  });

  // 3) 1,8 → 2,6 s : il saute à bord et se pose sur le pont, à droite du mât
  const RING = 84;  // taille de l'anneau une fois à bord ; pieds à y = 86 dans son repère
  const deck = { cx: BOAT.left + 255 / 420 * BW,
                 cy: BOAT.top + 258 / 360 * BH - (86 - 30) * RING / 60 };
  const jump = (sel, a) => part(sel).animate(
    [{ transform: 'rotate(0)' }, { transform: `rotate(${a}deg)` }, { transform: 'rotate(0)' }],
    { duration: 800 });
  later(1800, () => {
    moves.forEach(m => m.cancel());
    jump('.leg-l', 25); jump('.leg-r', -25); jump('.arm-l', 60); jump('.arm-r', -60);
    const from = C.getBoundingClientRect();
    const mid = at((W / 2 + deck.cx) / 2, Math.min(H * 0.22, deck.cy - 160), (big + RING) / 2);
    C.animate([
      { left: `${from.left}px`, top: `${from.top}px`, width: `${from.width}px`,
        height: `${from.height}px` },
      { ...mid, offset: 0.45, easing: 'ease-in' },
      at(deck.cx, deck.cy, RING),
    ], { duration: 800, easing: 'ease-out', fill: 'forwards' });
  });
  later(2600, () => {  // il atterrit : le bateau s'enfonce un peu et tangue
    boat.animate([{ transform: 'translateY(0) rotate(0)' },
      { transform: 'translateY(8px) rotate(1.5deg)' }, { transform: 'translateY(0) rotate(0)' }],
      { duration: 500, easing: 'ease-out' });
  });

  // 4) 2,7 s : l'aiguille se fixe, il montre le cap → 3,2 s : le bateau démarre vers la droite
  later(2700, () => {
    stop = { t: performance.now(), ms: 700, a0: angle,
             target: Math.ceil((angle - 45) / 360 + 1) * 360 + 45 };
    part('.arm-r').animate([{ transform: 'rotate(0)' }, { transform: 'rotate(-55deg)' }],
      { duration: 400, easing: ease, fill: 'forwards' });
  });
  later(3200, () => {
    const go = W * 0.8;
    const opts = { duration: 1800, easing: 'cubic-bezier(.5,0,.75,0)', fill: 'forwards' };
    boat.animate([{ transform: 'translateX(0) rotate(0)' },
      { transform: `translateX(${go}px) rotate(-3deg)` }], opts);
    const s = at(deck.cx, deck.cy, RING);
    C.animate([s, { ...s, left: `${parseFloat(s.left) + go}px`,
      top: `${parseFloat(s.top) - 10}px` }], opts);
  });

  // 5) 4,4 s : logo et slogan
  const brand = el('div', `position:fixed;z-index:2147483645;left:0;right:0;top:${H * 0.28}px;
    text-align:center;opacity:0;font-family:Inter,system-ui,sans-serif;`, `
    <div style="height:${H * 0.17}px;display:inline-block">${logoSvg}</div>
    <div style="margin-top:18px;font-size:${H * 0.036}px;font-style:italic;color:#4b5563">
      Oser l'audace, fini l'impasse</div>`);
  later(4400, () => brand.animate([{ opacity: 0, transform: 'translateY(16px)' },
    { opacity: 1, transform: 'translateY(0)' }], { duration: 700, easing: ease, fill: 'forwards' }));
}
