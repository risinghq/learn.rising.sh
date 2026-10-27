// Engine for animated, narrated lessons (Qiskit · IBM Quantum guides).
// A lesson is lessons/<id>/lesson.json: a list of "beats". Each beat has
//   say      narration (with [[name]] marks before the word that triggers something)
//   scene    blocks stacked on the stage (text, formulas, lists, boxes, figures)
//   actions  what happens and when: { at: "mark", t: extra seconds, do: "show", id: ... }
//   ask      optional question when the narration ends (choice, numeric, reveal)

// timings.json (from tools/tts.py) gives the duration of each clip, the second of each mark and the subtitles.
//
// Review mode: lesson.html?l=<id>&beat=N shows the final state of beat N without audio.
/* oxlint-disable unicorn/consistent-function-scoping --
   Classic script in a function: its helpers cannot move to the global scope. */
(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const NS = "http://www.w3.org/2000/svg";
  const qs = new URLSearchParams(location.search);
  const LID = qs.get("l");
  const REVIEW = qs.has("beat");
  const BASE = `lessons/${LID}/`;
  // The colors are CSS variables (they change with the light/dark theme).
  const NAMES = new Set([
    "fg",
    "muted",
    "blue",
    "gold",
    "teal",
    "red",
    "violet",
    "green",
    "grid",
    "axis",
  ]);
  const col = (c) => (NAMES.has(c) ? `var(--${c})` : c || "var(--fg)");
  const cssv = (n) =>
    getComputedStyle(document.documentElement)
      .getPropertyValue("--" + n)
      .trim();
  const MACROS = {};
  for (const k of NAMES) MACROS["\\" + k] = `\\htmlClass{c-${k}}{#1}`;

  const viewport = $("#viewport"),
    stage = $("#stage"),
    sceneEl = $("#scene"),
    askEl = $("#ask");
  const tagEl = $("#tag"),
    capEl = $("#caption"),
    steps = $("#steps"),
    playBtn = $("#play");
  const nar = new Audio();
  window.QGNarration = nar; // for automated tests
  let onNarrationEnd = null;
  nar.addEventListener("ended", () => onNarrationEnd?.());

  let L,
    T,
    beats,
    idx = -1,
    token = 0,
    objs = {},
    portrait = false,
    playing = true;
  let firstTry = 0,
    asked = 0;

  // ---------- utilidades ----------
  const el = (tag, cls, parent) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (parent) parent.appendChild(e);
    return e;
  };
  const svg = (tag, attrs = {}, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) {
      const v = attrs[k];
      // var(--x) is not valid in SVG presentation attributes: it goes in as a style.
      if (
        (k === "stroke" || k === "fill") &&
        typeof v === "string" &&
        v.startsWith("var(")
      )
        e.style.setProperty(k, v);
      else e.setAttribute(k, v);
    }
    if (parent) parent.appendChild(e);
    return e;
  };
  const tex = (node, src, display = false) =>
    katex.render(src, node, {
      throwOnError: false,
      displayMode: display,
      macros: MACROS,
      strict: false,
      trust: (ctx) => ctx.command === "\\htmlClass",
    });
  // Text with inline $math$ and **bold**.
  function rich(node, str) {
    node.textContent = "";
    String(str)
      .split(/(\$[^$]+\$)/)
      .forEach((part) => {
        if (!part) return;
        if (part[0] === "$" && part.length > 1) {
          const s = el("span", "", node);
          tex(s, part.slice(1, -1));
          return;
        }
        part
          .split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/)
          .forEach((p) => {
            if (p.startsWith("**"))
              el("b", "", node).textContent = p.slice(2, -2);
            else if (p.startsWith("`") && p.length > 1)
              el("code", "", node).textContent = p.slice(1, -1);
            else if (/^\[[^\]]+\]\(/.test(p)) {
              const a = el("a", "", node);
              a.textContent = p.slice(1, p.indexOf("]("));
              a.href = p.slice(p.indexOf("](") + 2, -1);
              a.target = "_blank";
              a.rel = "noopener";
            } else if (p) node.appendChild(document.createTextNode(p));
          });
      });
    return node;
  }
  const compile = (expr) =>
    new Function("x", "P", `with (Math) { with (P) { return (${expr}); } }`);
  const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
  // Interpolates something over time with requestAnimationFrame (or instantly in review mode).
  function tween(dur, step, instant) {
    if (instant || !dur) {
      step(1);
      return;
    }
    const t0 = performance.now(),
      my = token;
    const f = (now) => {
      if (my !== token) return;
      const q = Math.min(1, (now - t0) / (dur * 1000));
      step(ease(q));
      if (q < 1) requestAnimationFrame(f);
    };
    requestAnimationFrame(f);
  }

  // ---------- escenario escalable ----------
  const tall = matchMedia("(max-aspect-ratio: 1/1)");
  // A step with an exercise is not scaled. The editor needs real-size text and a scrollable column.
  let work = false;
  function setWork(on) {
    work = on;
    stage.classList.toggle("work", on);
    fit();
  }
  function fit() {
    const cw = viewport.clientWidth,
      ch = viewport.clientHeight;
    if (!cw || !ch) return;
    const p = tall.matches;
    if (work) {
      stage.style.width = cw + "px";
      stage.style.height = ch + "px";
      stage.style.transform = "none";
    } else {
      const LW = p ? 720 : 1280,
        LH = p ? 1080 : 720;
      const s = Math.min(cw / LW, ch / LH);
      stage.style.width = LW + "px";
      stage.style.height = LH + "px";
      stage.style.transform = `translate(${(cw - LW * s) / 2}px, ${(ch - LH * s) / 2}px) scale(${s})`;
    }
    if (p !== portrait) {
      portrait = p;
      stage.classList.toggle("portrait", p);
      Object.values(objs).forEach((o) => o.draw && o.draw());
      fitMath();
      autoZoom();
    }
  }
  // Formulas wider than the stage shrink until they fit (mostly in portrait).
  function fitMath() {
    const avail = (work ? stage.clientWidth : portrait ? 720 : 1280) - 2 * 48;
    sceneEl.querySelectorAll(".math").forEach((m) => {
      const base = +(
        m.dataset.size || parseFloat(getComputedStyle(m).fontSize)
      );
      m.dataset.size = base;
      m.style.fontSize = base + "px";
      const kx = m.querySelector(".katex"),
        k = kx ? kx.offsetWidth : 0;
      const lim =
        m.closest(".row") && !portrait
          ? avail / 2
          : m.closest(".box")
            ? avail - 60
            : avail;
      if (k > lim) m.style.fontSize = Math.max(16, (base * lim) / k) + "px";
    });
  }
  // If the blocks do not fit on the stage, the whole scene shrinks (zoom) until it does.
  function autoZoom() {
    sceneEl.style.zoom = "";
    if (work) return;
    const kids = [...sceneEl.children].filter((k) => k.offsetHeight);
    if (!kids.length) return;
    const cs = getComputedStyle(sceneEl),
      sr = sceneEl.getBoundingClientRect();
    const k = sr.height / sceneEl.offsetHeight; // scale of the stage on screen
    const rs = kids.map((c) => c.getBoundingClientRect());
    const needH =
      (Math.max(...rs.map((r) => r.bottom)) -
        Math.min(...rs.map((r) => r.top))) /
      k;
    const needW =
      (Math.max(...rs.map((r) => r.right)) -
        Math.min(...rs.map((r) => r.left))) /
      k;
    const availH =
      sceneEl.clientHeight -
      parseFloat(cs.paddingTop) -
      parseFloat(cs.paddingBottom);
    const availW =
      sceneEl.clientWidth -
      parseFloat(cs.paddingLeft) -
      parseFloat(cs.paddingRight);
    const z = Math.min(1, availH / needH, availW / needW);
    if (z < 0.995) sceneEl.style.zoom = Math.max(0.55, z);
  }
  new ResizeObserver(fit).observe(viewport);
  tall.addEventListener("change", fit);

  // ---------- figuras ----------
  function figSize(s) {
    if (!portrait) return [s.w, s.h];
    const w = s.pw || Math.min(s.w, 640);
    return [w, s.ph || Math.round((s.h * w) / s.w)];
  }
  function label(fig, x, y, str, color, size) {
    const d = el("div", "lab", fig);
    d.style.left = x + "px";
    d.style.top = y + "px";
    d.style.color = col(color);
    if (size) d.style.fontSize = size + "px";
    rich(d, str);
    return d;
  }

  // Function plot with animatable parameters.
  function makePlot(box, s) {
    const o = { spec: s, P: { ...s.params }, show: {} };
    (s.curves || []).forEach((c, i) => (o.show["c" + i] = !c.hidden));
    (s.areas || []).forEach((a, i) => (o.show["a" + i] = !a.hidden));
    (s.vlines || []).forEach((v, i) => (o.show["v" + i] = !v.hidden));
    (s.points || []).forEach((v, i) => (o.show["p" + i] = !v.hidden));
    const fns = (s.curves || []).map((c) => compile(c.expr));
    o.draw = () => {
      box.textContent = "";
      const [W, H] = figSize(s),
        [x0, x1] = s.xr,
        [y0, y1] = s.yr;
      const X = (x) => ((x - x0) / (x1 - x0)) * W,
        Y = (y) => H - ((y - y0) / (y1 - y0)) * H;
      box.style.width = W + "px";
      box.style.height = H + "px";
      box.style.marginBottom = (s.xticks ? 30 : 0) + "px";
      const g = svg(
        "svg",
        { width: W, height: H, viewBox: `0 0 ${W} ${H}` },
        box,
      );
      const id = "clip" + Math.random().toString(36).slice(2);
      svg(
        "rect",
        { x: 0, y: -40, width: W, height: H + 40 },
        svg("clipPath", { id }, svg("defs", {}, g)),
      );
      const ax = svg("g", { stroke: "var(--axis)", "stroke-width": 2 }, g);
      const yAxisAt = y0 <= 0 && y1 >= 0 ? Y(0) : H;
      svg("line", { x1: 0, x2: W, y1: yAxisAt, y2: yAxisAt }, ax);
      if (x0 <= 0 && x1 >= 0 && s.yaxis !== false)
        svg("line", { x1: X(0), x2: X(0), y1: 0, y2: H }, ax);
      (s.xticks || []).forEach((t) => {
        const [v, lab] = Array.isArray(t) ? t : [t, String(t)];
        svg(
          "line",
          { x1: X(v), x2: X(v), y1: yAxisAt - 6, y2: yAxisAt + 6 },
          ax,
        );
        label(box, X(v), yAxisAt + 24, lab, "muted", 22);
      });
      (s.yticks || []).forEach((t) => {
        const [v, lab] = Array.isArray(t) ? t : [t, String(t)];
        svg("line", { x1: X(0) - 6, x2: X(0) + 6, y1: Y(v), y2: Y(v) }, ax);
        label(box, X(0) - 26, Y(v), lab, "muted", 22);
      });
      const layer = svg("g", { "clip-path": `url(#${id})` }, g);
      const sample = (f, a, b, n = 300) => {
        const pts = [];
        for (let i = 0; i <= n; i++) {
          const x = a + ((b - a) * i) / n;
          let y = f(x, o.P);
          if (!isFinite(y)) y = y > 0 ? y1 * 3 : y0 * 3;
          pts.push([x, y]);
        }
        return pts;
      };
      (s.areas || []).forEach((a, i) => {
        if (!o.show["a" + i]) return;
        const A = typeof a.a === "string" ? o.P[a.a] : a.a,
          B = typeof a.b === "string" ? o.P[a.b] : a.b;
        const pts = sample(fns[a.curve || 0], A, B, 200);
        const d =
          `M${X(A)} ${Y(0)}` +
          pts
            .map(
              (p) =>
                `L${X(p[0])} ${Y(Math.max(y0 - 1, Math.min(y1 + 1, p[1])))}`,
            )
            .join("") +
          `L${X(B)} ${Y(0)}Z`;
        svg(
          "path",
          { d, fill: col(a.color || "gold"), opacity: a.opacity || 0.28 },
          layer,
        );
      });
      o.paths = [];
      (s.curves || []).forEach((c, i) => {
        const pts = sample(fns[i], c.from ?? x0, c.to ?? x1);
        const d = pts
          .map(
            (p, k) =>
              `${k ? "L" : "M"}${X(p[0]).toFixed(1)} ${Y(Math.max(y0 - (y1 - y0), Math.min(y1 + (y1 - y0), p[1]))).toFixed(1)}`,
          )
          .join("");
        const path = svg(
          "path",
          {
            d,
            fill: "none",
            stroke: col(c.color || "blue"),
            "stroke-width": c.width || 4,
            "stroke-linejoin": "round",
            "stroke-linecap": "round",
            "stroke-dasharray": c.dash || "",
          },
          layer,
        );
        if (!o.show["c" + i]) path.style.opacity = 0;
        o.paths.push(path);
        if (c.label && o.show["c" + i])
          label(
            box,
            X(c.lx ?? x1 * 0.8),
            Y(c.ly ?? y1 * 0.9),
            c.label,
            c.color || "blue",
            c.lsize,
          );
      });
      (s.vlines || []).forEach((v, i) => {
        if (!o.show["v" + i]) return;
        const xv = typeof v.x === "string" ? o.P[v.x] : v.x;
        svg(
          "line",
          {
            x1: X(xv),
            x2: X(xv),
            y1: 0,
            y2: H,
            stroke: col(v.color || "muted"),
            "stroke-width": 2.5,
            "stroke-dasharray": v.dash ?? "8 7",
          },
          g,
        );
        if (v.label)
          label(
            box,
            X(xv),
            v.ly != null ? Y(v.ly) : -18,
            v.label,
            v.color || "muted",
            24,
          );
      });
      (s.points || []).forEach((p, i) => {
        if (!o.show["p" + i]) return;
        const px = typeof p.x === "string" ? o.P[p.x] : p.x;
        const py = p.y != null ? p.y : fns[p.curve || 0](px, o.P);
        svg(
          "circle",
          { cx: X(px), cy: Y(py), r: 8, fill: col(p.color || "gold") },
          g,
        );
        if (p.label)
          label(
            box,
            X(px) + (p.dx || 0),
            Y(py) + (p.dy ?? -30),
            p.label,
            p.color || "gold",
            24,
          );
      });
      if (s.xlabel) label(box, W + 18, yAxisAt, s.xlabel, "muted", 26);
      if (s.ylabel)
        label(box, x0 <= 0 && x1 >= 0 ? X(0) : 0, -22, s.ylabel, "muted", 26);
      (s.labels || []).forEach((l) =>
        label(box, X(l.x), Y(l.y), l.text, l.color || "fg", l.size),
      );
    };
    o.draw();
    return o;
  }

  // Places the vector labels near their tip without overlapping each other or the arrows:
  // tries 16 positions around the tip (at two distances) and picks the one with the lowest penalty.
  function placeLabels(box, labs, obst, W, H) {
    const placed = [];
    const overlap = (r, q) =>
      Math.max(0, Math.min(r[2], q[2]) - Math.max(r[0], q[0])) *
      Math.max(0, Math.min(r[3], q[3]) - Math.max(r[1], q[1]));
    const hits = (r) => {
      let n = 0;
      for (const [a, b, wgt] of obst)
        for (let k = 0; k <= 24; k++) {
          const x = a[0] + ((b[0] - a[0]) * k) / 24,
            y = a[1] + ((b[1] - a[1]) * k) / 24;
          if (x > r[0] - 3 && x < r[2] + 3 && y > r[1] - 3 && y < r[3] + 3)
            n += wgt;
        }
      return n;
    };
    // Longer arrows' labels first (they usually have more free room).
    labs.sort(
      (p, q) =>
        Math.hypot(q.b[0] - q.a[0], q.b[1] - q.a[1]) -
        Math.hypot(p.b[0] - p.a[0], p.b[1] - p.a[1]),
    );
    for (const v of labs) {
      const d = label(box, 0, 0, v.lab, v.color, 27);
      d.classList.add("vlab");
      const w = d.offsetWidth,
        h = d.offsetHeight;
      const dx = v.b[0] - v.a[0],
        dy = v.b[1] - v.a[1],
        n = Math.hypot(dx, dy) || 1;
      let best = null;
      for (const far of [1, 1.9])
        for (let k = 0; k < 16; k++) {
          const ang = (k * Math.PI) / 8,
            ux = Math.cos(ang),
            uy = Math.sin(ang);
          const rad = far * (8 + 0.5 * (Math.abs(ux) * w + Math.abs(uy) * h));
          const cx = v.b[0] + ux * rad,
            cy = v.b[1] + uy * rad;
          const r = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2];
          let score =
            40 * hits(r) + (far - 1) * 6 + 3 * (1 - (ux * dx + uy * dy) / n);
          for (const q of placed) score += (200 * overlap(r, q)) / (w * h);
          if (r[0] < 2 || r[1] < 2 || r[2] > W - 2 || r[3] > H - 2)
            score += 300;
          if (!best || score < best.score) best = { score, cx, cy, r };
        }
      d.style.left = best.cx + "px";
      d.style.top = best.cy + "px";
      placed.push(best.r);
    }
  }

  // 2D plane with a grid that deforms under a matrix (linear algebra).
  function makePlane(box, s) {
    const R = s.range || 4;
    const o = {
      spec: s,
      M: [
        [1, 0],
        [0, 1],
      ],
      vecs: {},
      segs: {},
      lines: {},
    };
    (s.vectors || []).forEach(
      (v) => (o.vecs[v.name] = { ...v, show: !v.hidden }),
    );
    (s.segments || []).forEach(
      (v) => (o.segs[v.name] = { ...v, show: !v.hidden }),
    );
    (s.lines || []).forEach(
      (v) => (o.lines[v.name] = { ...v, show: !v.hidden }),
    );
    const mul = (M, v) => [
      M[0][0] * v[0] + M[0][1] * v[1],
      M[1][0] * v[0] + M[1][1] * v[1],
    ];
    o.draw = () => {
      box.textContent = "";
      const [W, H] = figSize({ w: s.w || 560, h: s.h || 560, pw: s.pw || 600 });
      const u = Math.min(W, H) / (2 * R),
        cx = W / 2,
        cy = H / 2;
      const P = (v) => [cx + v[0] * u, cy - v[1] * u];
      box.style.width = W + "px";
      box.style.height = H + "px";
      const g = svg("svg", { width: W, height: H }, box);
      const id = "pc" + Math.random().toString(36).slice(2);
      svg(
        "rect",
        { x: 0, y: 0, width: W, height: H, rx: 14 },
        svg("clipPath", { id }, svg("defs", {}, g)),
      );
      const defs = svg("defs", {}, g);
      const marker = (c) => {
        const mid = "m" + c.replace(/[^a-z0-9]/gi, "") + id;
        if (!g.querySelector("#" + mid)) {
          const m = svg(
            "marker",
            {
              id: mid,
              viewBox: "0 0 10 10",
              refX: 8,
              refY: 5,
              markerWidth: 5,
              markerHeight: 5,
              orient: "auto-start-reverse",
            },
            defs,
          );
          svg("path", { d: "M0 0L10 5L0 10z", fill: c }, m);
        }
        return `url(#${mid})`;
      };
      const clip = svg("g", { "clip-path": `url(#${id})` }, g);
      svg(
        "rect",
        { x: 0, y: 0, width: W, height: H, fill: "var(--fig-bg)", rx: 14 },
        clip,
      );
      const N = Math.ceil(R * 2);
      if (s.ghost !== false) {
        const gh = svg(
          "g",
          { stroke: "var(--grid-ghost)", "stroke-width": 1.5 },
          clip,
        );
        for (let i = -N; i <= N; i++) {
          let a = P([i, -N]),
            b = P([i, N]);
          svg("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, gh);
          a = P([-N, i]);
          b = P([N, i]);
          svg("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, gh);
        }
      }
      if (s.grid !== false) {
        const gr = svg(
          "g",
          { stroke: "var(--grid)", "stroke-width": 1.6, opacity: 0.9 },
          clip,
        );
        for (let i = -3 * N; i <= 3 * N; i++) {
          let a = P(mul(o.M, [i, -3 * N])),
            b = P(mul(o.M, [i, 3 * N]));
          svg("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, gr);
          a = P(mul(o.M, [-3 * N, i]));
          b = P(mul(o.M, [3 * N, i]));
          svg("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, gr);
        }
        const axes = svg(
          "g",
          { stroke: "var(--axis-strong)", "stroke-width": 2.5 },
          clip,
        );
        let a = P(mul(o.M, [-3 * N, 0])),
          b = P(mul(o.M, [3 * N, 0]));
        svg("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, axes);
        a = P(mul(o.M, [0, -3 * N]));
        b = P(mul(o.M, [0, 3 * N]));
        svg("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, axes);
      }
      const obst = [],
        labs = []; // obstacles (segments in pixels) and labels left to place
      for (const ln of Object.values(o.lines)) {
        if (!ln.show) continue;
        const d = ln.fixed ? ln.dir : mul(o.M, ln.dir),
          k = (3 * N) / Math.hypot(d[0], d[1]);
        const a = P([-d[0] * k, -d[1] * k]),
          b = P([d[0] * k, d[1] * k]);
        obst.push([a, b, 0.5]);
        svg(
          "line",
          {
            x1: a[0],
            y1: a[1],
            x2: b[0],
            y2: b[1],
            stroke: col(ln.color || "gold"),
            "stroke-width": 3,
            "stroke-dasharray": "10 8",
            opacity: 0.85,
          },
          clip,
        );
      }
      for (const sg of Object.values(o.segs)) {
        if (!sg.show) continue;
        const a = P(sg.fixed ? sg.a : mul(o.M, sg.a)),
          b = P(sg.fixed ? sg.b : mul(o.M, sg.b));
        obst.push([a, b, 0.5]);
        svg(
          "line",
          {
            x1: a[0],
            y1: a[1],
            x2: b[0],
            y2: b[1],
            stroke: col(sg.color || "muted"),
            "stroke-width": 2.5,
            "stroke-dasharray": sg.dash ?? "7 6",
          },
          clip,
        );
      }
      const arrow = (from, to, color, lab) => {
        const a = P(from),
          b = P(to);
        svg(
          "line",
          {
            x1: a[0],
            y1: a[1],
            x2: b[0],
            y2: b[1],
            stroke: col(color),
            "stroke-width": 5,
            "marker-end": marker(col(color)),
            "stroke-linecap": "round",
          },
          g,
        );
        obst.push([a, b, 1]);
        if (lab) labs.push({ a, b, lab, color });
      };
      if (s.basis) {
        arrow(
          [0, 0],
          mul(o.M, [1, 0]),
          "green",
          s.basisLabels ? s.basisLabels[0] : "$\\hat\\imath$",
        );
        arrow(
          [0, 0],
          mul(o.M, [0, 1]),
          "red",
          s.basisLabels ? s.basisLabels[1] : "$\\hat\\jmath$",
        );
      }
      for (const v of Object.values(o.vecs)) {
        if (!v.show) continue;
        const from = v.from ? (v.fixed ? v.from : mul(o.M, v.from)) : [0, 0];
        const to = v.fixed ? v.v : mul(o.M, v.v);
        arrow(
          from,
          v.from
            ? [
                from[0] + (v.fixed ? v.v[0] : to[0]),
                from[1] + (v.fixed ? v.v[1] : to[1]),
              ]
            : to,
          v.color || "gold",
          v.label,
        );
      }
      placeLabels(box, labs, obst, W, H);
    };
    o.transform = (M2, dur, instant) => {
      const M1 = o.M.map((r) => r.slice());
      tween(
        dur,
        (q) => {
          o.M = M1.map((r, i) => r.map((v, j) => v + (M2[i][j] - v) * q));
          o.draw();
        },
        instant,
      );
    };
    o.vecTo = (name, v2, dur, instant) => {
      const vec = o.vecs[name],
        v1 = vec.v.slice();
      tween(
        dur,
        (q) => {
          vec.v = [v1[0] + (v2[0] - v1[0]) * q, v1[1] + (v2[1] - v1[1]) * q];
          o.draw();
        },
        instant,
      );
    };
    o.draw();
    return o;
  }

  // Histogram of a discrete distribution with mean and standard deviation.
  function makeBars(box, s) {
    const o = { spec: s, show: { mean: false, sigma: false } };
    o.draw = () => {
      box.textContent = "";
      const [W, H] = figSize(s);
      const xs = s.data.map((d) => d[0]),
        x0 = (s.xr || [Math.min(...xs) - 1, Math.max(...xs) + 1])[0],
        x1 = (s.xr || [0, Math.max(...xs) + 1])[1];
      const ymax = s.ymax || Math.max(...s.data.map((d) => d[1])) * 1.15;
      const X = (x) => ((x - x0) / (x1 - x0)) * W,
        Y = (y) => H - (y / ymax) * H;
      box.style.width = W + "px";
      box.style.height = H + "px";
      box.style.marginBottom = "30px";
      const g = svg("svg", { width: W, height: H }, box);
      if (o.show.sigma)
        svg(
          "rect",
          {
            x: X(s.mean - s.sigma),
            y: 0,
            width: X(s.mean + s.sigma) - X(s.mean - s.sigma),
            height: H,
            fill: col("teal"),
            opacity: 0.14,
          },
          g,
        );
      const bw = (X(1) - X(0)) * 0.78;
      s.data.forEach(([x, n]) => {
        if (!n) return;
        svg(
          "rect",
          {
            x: X(x) - bw / 2,
            y: Y(n),
            width: bw,
            height: H - Y(n),
            rx: 3,
            fill: col(s.color || "blue"),
            opacity: 0.85,
          },
          g,
        );
      });
      svg(
        "line",
        {
          x1: 0,
          x2: W,
          y1: H,
          y2: H,
          stroke: "var(--axis)",
          "stroke-width": 2,
        },
        g,
      );
      (s.xticks || []).forEach((v) =>
        label(box, X(v), H + 24, String(v), "muted", 22),
      );
      if (o.show.mean) {
        svg(
          "line",
          {
            x1: X(s.mean),
            x2: X(s.mean),
            y1: 0,
            y2: H,
            stroke: col("gold"),
            "stroke-width": 3,
          },
          g,
        );
        label(
          box,
          X(s.mean),
          -20,
          s.meanLabel || "$\\langle j\\rangle$",
          "gold",
          26,
        );
      }
      if (o.show.sigma)
        label(box, X(s.mean + s.sigma) + 34, 30, "$\\pm\\sigma$", "teal", 26);
      if (s.xlabel) label(box, W + 20, H, s.xlabel, "muted", 24);
    };
    o.draw();
    return o;
  }

  // Detection screen: particles that arrive one at a time (double slit).
  function makeDots(box, s) {
    const o = { spec: s, n: 0, pts: [] };
    const I = (x) =>
      Math.pow(Math.cos((s.k || 4.2) * x), 2) *
      Math.exp((-x * x) / (s.env || 1.6));
    const sampleX = () => {
      for (;;) {
        const x = (Math.random() * 2 - 1) * 3;
        if (Math.random() < I(x)) return x;
      }
    };
    o.draw = () => {
      box.textContent = "";
      const [W, H] = figSize(s);
      box.style.width = W + "px";
      box.style.height = H + "px";
      const c = el("canvas", "", box);
      c.width = W * 2;
      c.height = H * 2;
      c.style.width = W + "px";
      c.style.height = H + "px";
      o.ctx = c.getContext("2d");
      o.W = W;
      o.H = H;
      o.ctx.fillStyle = cssv("fig-bg");
      o.ctx.fillRect(0, 0, W * 2, H * 2);
      o.pts.forEach((p) => o.dot(p));
    };
    o.dot = (p) => {
      o.ctx.fillStyle = cssv("dot");
      o.ctx.beginPath();
      o.ctx.arc((p[0] / 6 + 0.5) * o.W * 2, p[1] * o.H * 2, 2.4, 0, 7);
      o.ctx.fill();
    };
    o.emit = (n, dur, instant) => {
      const start = o.pts.length;
      const add = (k) => {
        while (o.pts.length < start + k) {
          const p = [sampleX(), 0.05 + 0.9 * Math.random()];
          o.pts.push(p);
          o.dot(p);
        }
      };
      if (instant || !dur) return add(n);
      tween(dur, (q) => add(Math.round(n * q)));
    };
    o.draw();
    return o;
  }

  // Utilities the blocks defined in blocks.js receive.
  const afterBuild = []; // functions the blocks ask to run once the scene is mounted
  const API = {
    el,
    svg,
    tex,
    rich,
    col,
    cssv,
    tween,
    label,
    isPortrait: () => portrait,
    isReview: () => REVIEW,
    after: (f) => afterBuild.push(f),
  };

  // ---------- building the scene ----------
  function build(s, parent) {
    let e;
    switch (s.type) {
      case "math":
        e = el("div", "blk math");
        if (s.size) e.style.fontSize = s.size + "px";
        tex(e, s.tex, true);
        break;
      case "text":
        e = el("div", "blk text " + (s.style || "body"));
        if (s.size) e.style.fontSize = s.size + "px";
        rich(e, s.text);
        break;
      case "list":
        e = el("ul", "blk list");
        if (s.size) e.style.fontSize = s.size + "px";
        s.items.forEach((it) => {
          rich(el("li", s.stagger ? "hid" : "", e), it);
        });
        break;
      case "row":
        e = el("div", "blk row");
        if (s.gap) e.style.gap = s.gap + "px";
        s.items.forEach((it) => build(it, e));
        break;
      case "box":
        e = el("div", "blk box " + (s.kind || "thm"));
        if (s.title) rich(el("div", "box-title", e), s.title);
        (s.body || []).forEach((it) => build(it, e));
        break;
      case "plot":
        e = el("div", "blk fig");
        break;
      case "plane":
        e = el("div", "blk fig");
        break;
      case "bars":
        e = el("div", "blk fig");
        break;
      case "dots":
        e = el("div", "blk fig");
        break;
      case "spacer":
        e = el("div", "blk");
        e.style.height = (s.h || 20) + "px";
        break;
      default:
        if (!window.BLOCKS || !BLOCKS[s.type])
          throw new Error("tipo desconocido: " + s.type);
        e = el("div", "blk fig " + s.type);
    }
    if (s.color) e.style.color = col(s.color);
    if (s.hidden) e.classList.add("hid");
    if (s.maxw) e.style.maxWidth = s.maxw + "px";
    parent.appendChild(e);
    let o = { spec: s, el: e };
    if (s.type === "plot") o = Object.assign(makePlot(e, s), { el: e });
    if (s.type === "plane") o = Object.assign(makePlane(e, s), { el: e });
    if (s.type === "bars") o = Object.assign(makeBars(e, s), { el: e });
    if (s.type === "dots") o = Object.assign(makeDots(e, s), { el: e });
    if (window.BLOCKS && BLOCKS[s.type])
      o = Object.assign(BLOCKS[s.type](e, s, API), { el: e });
    if (s.id) objs[s.id] = o;
    return e;
  }

  function buildScene(beat) {
    sceneEl.textContent = "";
    sceneEl.className = "scene" + (beat.align === "top" ? " top" : "");
    objs = {};
    (beat.scene || []).forEach((s) => build(s, sceneEl));
    setWork(!!sceneEl.querySelector(".xpanel"));
    if (work) {
      stage.scrollTop = 0;
      const go = el("button", "abtn primary xnext", sceneEl);
      go.textContent = "Continuar";
      go.addEventListener("click", () => {
        setPlaying(true);
        goto(idx + 1);
      });
    }
    afterBuild.splice(0).forEach((f) => f());
    fitMath();
    autoZoom();
    const my = token;
    document.fonts.ready.then(() => {
      if (my === token) {
        fitMath();
        autoZoom();
      }
    });
    tagEl.innerHTML = "";
    if (beat.tag) {
      el("b", "", tagEl).textContent = beat.tag[0];
      tagEl.appendChild(document.createTextNode(beat.tag[1] || ""));
    }
  }

  // ---------- acciones ----------
  function exec(a, instant) {
    if (a.sfx && !instant) SFX.play(a.sfx);
    const o = objs[a.id];
    if (a.id && !o) {
      console.error("objeto inexistente", a.id);
      return;
    }
    switch (a.do) {
      case "show":
        o.el.classList.remove("hid", "dim");
        break;
      case "hide":
        o.el.classList.add("hid");
        break;
      case "dim":
        o.el.classList.add("dim");
        break;
      case "undim":
        o.el.classList.remove("dim");
        break;
      case "item":
        (o.items || o.el.children)[a.i].classList.remove("hid");
        break;
      case "emph":
        o.el.classList.add("emph");
        break;
      case "unemph":
        o.el.classList.remove("emph");
        break;
      case "tex":
        tex(o.el, a.tex, true);
        fitMath();
        break;
      case "text":
        rich(o.el, a.text);
        break;
      case "curve":
        o.show["c" + a.i] = true;
        o.draw();
        if (!instant) {
          const p = o.paths[a.i],
            Lp = p.getTotalLength();
          p.style.strokeDasharray = Lp;
          p.style.strokeDashoffset = Lp;
          p.animate([{ strokeDashoffset: Lp }, { strokeDashoffset: 0 }], {
            duration: (a.dur || 1.2) * 1000,
            easing: "ease-in-out",
            fill: "forwards",
          });
        }
        break;
      case "uncurve":
        o.show["c" + a.i] = false;
        o.draw();
        break;
      case "area":
        o.show["a" + a.i] = true;
        o.draw();
        break;
      case "unarea":
        o.show["a" + a.i] = false;
        o.draw();
        break;
      case "vline":
        o.show["v" + a.i] = true;
        o.draw();
        break;
      case "point":
        o.show["p" + a.i] = true;
        o.draw();
        break;
      case "param": {
        const v0 = o.P[a.p],
          v1 = a.to;
        tween(
          a.dur ?? 1.5,
          (q) => {
            o.P[a.p] = v0 + (v1 - v0) * q;
            if (o.spec.type !== "exp") o.draw();
          },
          instant,
        );
        break;
      }
      case "transform":
        o.transform(a.m, a.dur ?? 1.6, instant);
        break;
      case "vec":
        o.vecs[a.name] = { ...o.vecs[a.name], ...a.vec, show: true };
        o.draw();
        break;
      case "vecTo":
        o.vecTo(a.name, a.v, a.dur ?? 1.2, instant);
        break;
      case "unvec":
        o.vecs[a.name].show = false;
        o.draw();
        break;
      case "seg":
        o.segs[a.name] = { ...o.segs[a.name], ...a.seg, show: true };
        o.draw();
        break;
      case "unseg":
        o.segs[a.name].show = false;
        o.draw();
        break;
      case "line":
        o.lines[a.name] = { ...o.lines[a.name], ...a.line, show: true };
        o.draw();
        break;
      case "mean":
        o.show.mean = true;
        o.draw();
        break;
      case "sigma":
        o.show.sigma = true;
        o.draw();
        break;
      case "emit":
        o.emit(a.n, a.dur ?? 3, instant);
        break;
      case "sfx":
        break;
      default:
        if (!(o && o.act && o.act(a, instant)))
          console.error("acción desconocida", a.do);
    }
  }
  const atTime = (a, marks) => {
    if (a.at && marks[a.at] == null) console.error("marca inexistente", a.at);
    return (a.at ? (marks[a.at] ?? 0) : 0) + (a.t || 0);
  };

  // ---------- playback ----------
  // Progress saved per lesson: steps already heard and the last step visited.
  const store = {
    get(k, d) {
      try {
        const v = localStorage.getItem(`qiskit:${k}:${LID}`);
        return v == null ? d : JSON.parse(v);
      } catch {
        return d;
      }
    },
    set(k, v) {
      try {
        localStorage.setItem(`qiskit:${k}:${LID}`, JSON.stringify(v));
      } catch {}
      QGAccount.changed(`qiskit:${k}:${LID}`);
    },
  };
  function paintSteps() {
    const k = Math.max(idx, 0);
    steps.value = k;
    steps.style.setProperty(
      "--p",
      `${(k / Math.max(beats.length - 1, 1)) * 100}%`,
    );
    $("#stepno").textContent =
      `Paso ${k + 1} de ${beats.length}${beats[k].ask ? ", con pregunta" : ""}`;
  }

  // Go to step i; if t0 > 0, start at that second of the narration with the scene already in its state.
  function goto(i, t0 = 0) {
    if (i < 0) i = 0;
    if (i >= beats.length) return finish();
    const my = ++token;
    idx = i;
    if (!REVIEW) store.set("pos", i);
    nar.pause();
    askEl.className = "";
    askEl.textContent = "";
    const beat = beats[i],
      tm = T[beat.id];
    buildScene(beat);
    paintSteps();
    capEl.textContent = "";
    const pending = (beat.actions || [])
      .map((a) => Object.assign({}, a, { time: atTime(a, tm.marks) }))
      .toSorted((a, b) => a.time - b.time);
    t0 = Math.max(0, Math.min(t0, tm.dur - 0.05));
    if (t0 > 0) {
      const later = pending.findIndex((a) => a.time > t0);
      pending
        .splice(0, later < 0 ? pending.length : later)
        .forEach((a) => exec(a, true));
    }
    if (REVIEW) {
      pending.forEach((a) => exec(a, true));
      capEl.textContent = beat.say
        .replace(/\[\[\w+\]\]/g, "")
        .replace(/`/g, "");
      if (beat.ask) showAsk(beat);
      return;
    }
    let cue = -1;
    const tick = () => {
      if (my !== token) return;
      const now = nar.currentTime;
      while (pending.length && pending[0].time <= now + 0.03)
        exec(pending.shift());
      let c = -1;
      tm.cues.forEach((q, k) => {
        if (q[0] <= now + 0.05) c = k;
      });
      if (c !== cue && c >= 0) {
        cue = c;
        capEl.textContent = tm.cues[c][1];
      }
      if (!nar.ended) requestAnimationFrame(tick);
    };
    onNarrationEnd = () => {
      if (my !== token) return;
      pending.splice(0).forEach((a) => exec(a));
      if (beat.ask) return showAsk(beat);
      if (work) return; // The exercise advances with «Continuar».
      setTimeout(
        () => {
          if (my === token && playing) goto(idx + 1);
        },
        (beat.hold ?? 0.9) * 1000,
      );
    };
    const start = () => {
      if (my !== token) return;
      if (t0 > 0) nar.currentTime = t0;
      nar.playbackRate = +$("#speed").value;
      if (playing) nar.play().catch(() => setPlaying(false));
      else {
        const c = tm.cues.findLast((q) => q[0] <= t0 + 0.05);
        if (c) capEl.textContent = c[1];
      }
    };
    // The clip loads whole into memory (blob): that lets it seek with any server,
    // even `python -m http.server`, which does not support range requests.
    clip(beat.id).then((url) => {
      if (my !== token) return;
      nar.src = url;
      nar.addEventListener("loadedmetadata", start, { once: true });
      if (beats[i + 1]) clip(beats[i + 1].id); // preload the next one
    });
    requestAnimationFrame(tick);
  }
  const clips = new Map();
  const clip = (id) => {
    if (!clips.has(id))
      clips.set(
        id,
        fetch(`${BASE}audio/${id}.mp3`)
          .then((r) => r.blob())
          .then((b) => URL.createObjectURL(b)),
      );
    return clips.get(id);
  };

  // Skip seconds within the current step (going back rebuilds the scene).
  function seekRel(d) {
    if (REVIEW || idx < 0 || askEl.classList.contains("on")) return;
    const dur = T[beats[idx].id].dur,
      t = nar.currentTime + d;
    if (t >= dur) return goto(idx + 1);
    if (t < 0) return goto(Math.max(0, idx - (nar.currentTime < 1 ? 1 : 0)), 0);
    if (d > 0) nar.currentTime = t;
    else goto(idx, t);
  }

  function setPlaying(p) {
    playing = p;
    playBtn.textContent = p ? "Pausa" : "Reproducir";
  }
  function togglePlay() {
    if (REVIEW) return;
    if (askEl.classList.contains("on")) return;
    if (nar.ended) {
      setPlaying(true);
      return goto(idx + 1);
    }
    if (nar.paused) {
      setPlaying(true);
      nar.play();
    } else {
      setPlaying(false);
      nar.pause();
    }
  }

  // ---------- preguntas ----------
  function showAsk(beat) {
    const a = beat.ask;
    let tries = 0,
      solved = false;
    asked++;
    askEl.textContent = "";
    askEl.className = "on";
    el("div", "qlabel", askEl).textContent = a.label || "Pregunta";
    rich(el("div", "prompt", askEl), a.prompt);
    const fb = el("div", "fb", askEl);
    const nextRow = el("div", "next-row", askEl);
    const say = (cls, content) => {
      fb.className = "fb on " + cls;
      fb.textContent = "";
      (Array.isArray(content) ? content : [content]).forEach((c) => {
        if (typeof c === "string" && c.startsWith("$$")) {
          const m = el("div", "math", fb);
          tex(m, c.slice(2, -2), true);
        } else rich(el("div", "", fb), c);
      });
    };
    const done = (ok) => {
      if (solved) return;
      solved = true;
      if (ok && tries === 0) firstTry++;
      const b = el("button", "abtn primary", nextRow);
      b.textContent = "Continuar";
      b.addEventListener("click", () => {
        setPlaying(true);
        goto(idx + 1);
      });
      b.focus({ preventScroll: true });
    };
    const fail = (msg) => {
      tries++;
      SFX.play("no");
      say(
        "no",
        msg ||
          a.hint ||
          "No es correcto. Revisa el razonamiento e inténtalo otra vez.",
      );
      if (tries >= 2 && a.solution && !nextRow.querySelector(".sol")) {
        const s = el("button", "abtn sol", nextRow);
        s.textContent = "Ver solución";
        s.addEventListener("click", () => {
          say("sol", a.solution);
          s.remove();
          done(false);
        });
      }
    };
    if (a.kind === "choice") {
      const box = el("div", "opts", askEl);
      askEl.insertBefore(box, fb);
      a.options.forEach((opt, k) => {
        const b = el("button", "opt", box);
        el("span", "k", b).textContent = String.fromCharCode(97 + k) + ")";
        rich(el("span", "", b), opt);
        b.addEventListener("click", () => {
          if (solved) return;
          if (k === a.right) {
            b.classList.add("right");
            SFX.play("ok");
            say("ok", a.why);
            done(true);
          } else {
            b.classList.add("wrong");
            fail(a.wrong && a.wrong[k]);
          }
        });
      });
    } else if (a.kind === "numeric") {
      const row = el("div", "numrow", askEl);
      askEl.insertBefore(row, fb);
      const inp = el("input", "", row);
      inp.inputMode = "decimal";
      inp.placeholder = a.placeholder || "Tu respuesta";
      if (a.unit) rich(el("span", "", row), a.unit);
      const b = el("button", "abtn primary", row);
      b.textContent = "Comprobar";
      const parse = (str) => {
        str = str.trim().replace(",", ".").replace(/\s/g, "");
        if (/^-?\d*\.?\d+\/-?\d*\.?\d+$/.test(str)) {
          const [p, q] = str.split("/");
          return +p / +q;
        }
        return str === "" ? NaN : Number(str);
      };
      const check = () => {
        if (solved) return;
        const v = parse(inp.value);
        if (!isFinite(v))
          return say(
            "no",
            "Escribe un número (se aceptan decimales y fracciones como 3/4).",
          );
        const tol = a.tol ?? 0.01;
        if (Math.abs(v - a.answer) <= tol * Math.max(1, Math.abs(a.answer))) {
          SFX.play("ok");
          say("ok", a.why);
          done(true);
        } else fail(a.hint);
      };
      b.addEventListener("click", check);
      inp.addEventListener("keydown", (e) => {
        if (e.key === "Enter") check();
        e.stopPropagation();
      });
      if (!REVIEW) setTimeout(() => inp.focus({ preventScroll: true }), 50);
    } else if (a.kind === "reveal") {
      const row = el("div", "numrow", askEl);
      askEl.insertBefore(row, fb);
      const b = el("button", "abtn primary", row);
      b.textContent = a.button || "Mostrar la respuesta";
      b.addEventListener("click", () => {
        say("sol", a.solution);
        b.remove();
        done(false);
        asked--;
      });
    } else if (a.kind === "predict") {
      // Bet: there is no correct answer yet; the next step reveals the result.
      asked--;
      askEl.querySelector(".qlabel").textContent = a.label || "Tu predicción";
      const key = `qiskit:predict:${LID}:${beat.id}`;
      const box = el("div", "opts", askEl);
      askEl.insertBefore(box, fb);
      a.options.forEach((opt, k) => {
        const b = el("button", "opt", box);
        el("span", "k", b).textContent = String.fromCharCode(97 + k) + ")";
        rich(el("span", "", b), opt);
        b.addEventListener("click", () => {
          if (solved) return;
          b.classList.add("picked");
          try {
            localStorage.setItem(key, String(k));
          } catch {}
          QGAccount.changed(key);
          SFX.play("ok");
          say("sol", a.after);
          done(false);
        });
      });
    } else if (a.kind === "reflect") {
      // Open questions: saved in the browser and restored on return.
      asked--;
      askEl.querySelector(".qlabel").textContent = a.label || "Reflexiona";
      askEl.querySelector(".prompt").remove();
      const key = `qiskit:reflect:${LID}:${beat.id}`;
      let saved = [];
      try {
        saved = JSON.parse(localStorage.getItem(key) || "[]");
      } catch {}
      const areas = a.prompts.map((p, k) => {
        rich(el("div", "prompt rprompt", askEl), p);
        const ta = el("textarea", "reflect", askEl);
        ta.rows = 2;
        ta.placeholder = "Escribe con tus palabras…";
        ta.value = saved[k] || "";
        ta.addEventListener("keydown", (e) => e.stopPropagation());
        askEl.insertBefore(ta, fb);
        return ta;
      });
      askEl
        .querySelectorAll(".rprompt")
        .forEach((p, k) => askEl.insertBefore(p, areas[k]));
      const row = el("div", "numrow", askEl);
      askEl.insertBefore(row, fb);
      const b = el("button", "abtn primary", row);
      b.textContent = "Guardar";
      const skip = el("button", "abtn", row);
      skip.textContent = "Ahora no";
      b.addEventListener("click", () => {
        try {
          localStorage.setItem(
            key,
            JSON.stringify(areas.map((t) => t.value.trim())),
          );
        } catch {}
        say("ok", "Guardado. Lo verás aquí cuando vuelvas a esta lección.");
        row.remove();
        done(false);
      });
      skip.addEventListener("click", () => {
        row.remove();
        done(false);
      });
      if (!REVIEW)
        setTimeout(() => areas[0].focus({ preventScroll: true }), 50);
    }
  }

  // ---------- fin ----------
  function finish() {
    token++;
    nar.pause();
    try {
      const done = new Set(
        JSON.parse(localStorage.getItem("qiskit:done") || "[]"),
      );
      done.add(LID);
      localStorage.setItem("qiskit:done", JSON.stringify([...done]));
    } catch {}
    QGAccount.changed("qiskit:done");
    $("#end-title").textContent = L.title;
    $("#end-score").textContent = asked
      ? `Preguntas acertadas al primer intento: ${firstTry} de ${asked}.`
      : "";
    const ul = $("#end-practice");
    ul.textContent = "";
    (L.practice || []).forEach((p) => rich(el("li", "", ul), p));
    $("#end-practice-wrap").style.display = (L.practice || []).length
      ? ""
      : "none";
    const nx = $("#end-next");
    if (L.next) {
      nx.href = "lesson.html?l=" + L.next;
      nx.style.display = "";
    } else nx.style.display = "none";
    $("#end").classList.remove("hide");
    SFX.play("done");
  }

  // ---------- arranque ----------
  async function init() {
    if (!LID) {
      location.href = "index.html";
      return;
    }
    await QGAccount.ready;
    L = await (await fetch(BASE + "lesson.json")).json();
    T = await (await fetch(BASE + "timings.json")).json();
    beats = L.beats;
    document.title = `${L.section} · ${L.title}`;
    $("#crumb-part").textContent = L.part;
    $("#crumb-title").textContent = `${L.section} ${L.title}`;
    $("#start-eyebrow").textContent = `${L.part}, lección ${L.section}`;
    $("#start-title").textContent = L.title;
    const mins = Math.round(
      beats.reduce((s, b) => s + (T[b.id]?.dur || 0), 0) / 60,
    );
    $("#start-meta").textContent =
      `Unos ${mins + 1} min y ${beats.filter((b) => b.ask).length} preguntas.`;
    const ul = $("#start-goals");
    (L.goals || []).forEach((g) => rich(el("li", "", ul), g));

    steps.max = beats.length - 1;
    steps.addEventListener("change", () => {
      setPlaying(true);
      goto(+steps.value);
    });
    fit();

    const pos = store.get("pos", 0);
    paintSteps();
    $("#go").addEventListener("click", () => {
      SFX.unlock();
      $("#start").classList.add("hide");
      setPlaying(true);
      goto(0);
    });
    if (pos > 0 && pos < beats.length) {
      const c = $("#resume");
      c.style.display = "";
      c.textContent = `Continuar en el paso ${pos + 1} de ${beats.length}`;
      c.addEventListener("click", () => {
        SFX.unlock();
        $("#start").classList.add("hide");
        setPlaying(true);
        goto(pos);
      });
    }
    $("#back5").addEventListener("click", () => seekRel(-5));
    $("#fwd5").addEventListener("click", () => seekRel(5));
    $("#again").addEventListener("click", () => {
      $("#end").classList.add("hide");
      firstTry = 0;
      asked = 0;
      setPlaying(true);
      goto(0);
    });
    addEventListener("themechange", () =>
      Object.values(objs).forEach((o) => o.draw && o.draw()),
    );
    $("#next").addEventListener("click", () => {
      setPlaying(true);
      goto(idx + 1);
    });
    $("#prev").addEventListener("click", () => {
      setPlaying(true);
      goto(idx - 1);
    });
    $("#replay").addEventListener("click", () => {
      setPlaying(true);
      goto(idx);
    });
    playBtn.addEventListener("click", togglePlay);
    $("#speed").addEventListener("change", (e) => {
      nar.playbackRate = +e.target.value;
      try {
        localStorage.setItem("qiskit:speed", e.target.value);
      } catch {}
    });
    try {
      const sp = localStorage.getItem("qiskit:speed");
      if (sp) $("#speed").value = sp;
    } catch {}
    $("#cc").addEventListener("click", () => {
      capEl.classList.toggle("off");
      $("#cc").setAttribute(
        "aria-pressed",
        String(!capEl.classList.contains("off")),
      );
    });
    const muteLabel = () => {
      $("#mute").setAttribute("aria-pressed", String(!SFX.muted));
    };
    $("#mute").addEventListener("click", () => {
      SFX.toggle();
      muteLabel();
    });
    muteLabel();
    addEventListener("keydown", (e) => {
      if (e.target.closest("input, textarea, select, [contenteditable]"))
        return;
      if (e.code === "Space") {
        if (e.target.closest("button, a")) return;
        e.preventDefault();
        togglePlay();
      } else if (e.code === "ArrowRight" && e.shiftKey) seekRel(5);
      else if (e.code === "ArrowLeft" && e.shiftKey) seekRel(-5);
      else if (e.code === "ArrowRight") $("#next").click();
      else if (e.code === "ArrowLeft") $("#prev").click();
      else if (e.key === "c") $("#cc").click();
      else if (askEl.classList.contains("on") && /^[a-f]$/.test(e.key)) {
        const b = askEl.querySelectorAll(".opt")[e.key.charCodeAt(0) - 97];
        if (b) b.click();
      } else if (e.key === "Enter") {
        const b = askEl.querySelector(".next-row .primary");
        if (b) b.click();
      }
    });

    if (REVIEW) {
      $("#start").classList.add("hide");
      playing = false;
      goto(+qs.get("beat"));
    }
  }
  init();
})();
