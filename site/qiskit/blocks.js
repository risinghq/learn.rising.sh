// Blocks specific to the Qiskit course, plugged into the engine (engine.js) through window.BLOCKS.
//
// Each constructor receives (container, spec, API) and returns an object with:
//   draw()            paints again (orientation or theme change)
//   act(a, instant)   runs an action of its own; returns true if it recognised it
//   items             (optional) elements the generic 'item' action reveals

//   code    highlighted code: reveal lines ('lines'), highlight ('hl', 'unhl')
//   circuit circuit diagram: gates that appear ('gate'), highlight ('hlop'), column cursor ('cursor')
//   hist    histogram of counts or probabilities with text labels: 'grow', 'data'
//   table   table whose rows appear with 'item'; 'hlrow' highlights a row
//   flow    steps chained with arrows; 'item' reveals, 'step' highlights one
//   graph   coupling graph (physical qubits): 'hlnode', 'hledge', 'nodelabel', 'clearhl'

// The 'exercise' block lives in exercise.js, which loads after this file.
/* oxlint-disable unicorn/consistent-function-scoping --
   Classic script in a function: its helpers cannot move to the global scope. */
(() => {
  "use strict";
  const B = (window.BLOCKS = {});
  const availW = (A, s, pad = 0, box = null) => {
    let w = A.isPortrait() ? 624 : s.maxw || 1160;
    // Inside a horizontal row, each block gets a share of the width.
    const row = box && !A.isPortrait() && box.closest(".row");
    if (row && !s.maxw)
      w = Math.min(w, 1160 / Math.max(2, row.children.length) - 40);
    return w - pad;
  };

  // ---------------------------------------------------------------- code
  const PY_KW = new Set(
    "False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield".split(
      " ",
    ),
  );
  const PY_BI = new Set(
    "print range len list dict set tuple enumerate zip abs sum min max int float str round sorted isinstance type open super".split(
      " ",
    ),
  );
  const QASM_KW = new Set(
    "OPENQASM include qubit qreg bit creg gate measure reset barrier if else for while def let input output const in return box delay stretch duration float int uint bool angle complex extern defcal defcalgrammar ctrl inv pow end break continue".split(
      " ",
    ),
  );

  function highlight(line, lang) {
    const out = [];
    const push = (cls, t) =>
      out.push(cls ? `<span class="t-${cls}">${esc(t)}</span>` : esc(t));
    if (lang === "out" || lang === "text") return esc(line) || " ";
    if (lang === "sh") {
      const m = line.match(/^(\s*)(\$ |> |PS> )?(.*)$/);
      if (m[2]) push("com", m[2]);
      m[3]
        .split(/(\s+)/)
        .forEach((w, k) =>
          push(
            k === 0 && m[2]
              ? "fn"
              : w.startsWith("-")
                ? "cls"
                : w.startsWith("#")
                  ? "com"
                  : "",
            w,
          ),
        );
      return (m[1] ? esc(m[1]) : "") + out.join("") || " ";
    }
    const qasm = lang === "qasm";
    const re = qasm
      ? /(\/\/.*$)|("(?:\\.|[^"])*")|(\b\d+(?:\.\d+)?(?:e-?\d+)?(?:ns|us|ms|dt|s|im)?\b)|([A-Za-z_]\w*)|(\s+)|(.)/g
      : /(#.*$)|([rbfuRBFU]{0,2}(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'))|(\b\d+(?:\.\d+)?(?:e-?\d+)?j?\b)|([A-Za-z_]\w*)|(\s+)|(.)/g;
    let m,
      prevDot = false;
    while ((m = re.exec(line))) {
      const [t, com, str, num, id, ws] = m;
      if (com) push("com", t);
      else if (str) push("str", t);
      else if (num) push("num", t);
      else if (id) {
        const rest = line.slice(re.lastIndex);
        if (qasm)
          push(
            QASM_KW.has(id)
              ? "kw"
              : /^\s*\(/.test(rest) || (/^\s*[a-z]/.test(rest) && false)
                ? "fn"
                : "",
            t,
          );
        else if (PY_KW.has(id)) push("kw", t);
        else if (!prevDot && PY_BI.has(id)) push("bi", t);
        else if (/^\s*\(/.test(rest)) push(/^[A-Z]/.test(id) ? "cls" : "fn", t);
        else if (/^[A-Z][a-z]/.test(id)) push("cls", t);
        else push(prevDot ? "attr" : "", t);
      } else push(ws ? "" : /[=+\-*/<>%@]/.test(t) ? "op" : "p", t);
      if (!ws) prevDot = t === ".";
    }
    return out.join("") || " ";
  }
  function esc(t) {
    return t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  B.code = (box, s, A) => {
    const lang = s.lang || "python";
    const lines = s.src.replace(/^\n+|\s+$/g, "").split("\n");
    const o = { spec: s, shown: s.reveal ? 0 : lines.length };
    box.classList.add("lang-" + lang);
    if (s.title) A.el("div", "code-title", box).textContent = s.title;
    const pre = A.el("div", "code-body", box);
    const rows = lines.map((ln, k) => {
      const r = A.el("div", "cl" + (k >= o.shown ? " hid" : ""), pre);
      if (s.numbers) A.el("span", "ln", r).textContent = k + 1;
      A.el("span", "cc", r).innerHTML = highlight(ln, lang);
      return r;
    });
    o.draw = () => {
      const L =
        Math.max(...lines.map((l) => l.length), 8) + (s.numbers ? 4 : 0);
      const base = s.size || (A.isPortrait() ? 22 : 25);
      const maxH = s.maxh || (A.isPortrait() ? 860 : 540);
      const win = Math.min(
        lines.length,
        s.window || (A.isPortrait() ? 22 : 16),
      );
      const fs = Math.max(
        A.isPortrait() ? 18 : 12,
        Math.min(base, availW(A, s, 60, box) / (0.61 * L), maxH / (1.5 * win)),
      );
      // Long code: a window of `win` lines that scrolls to the highlighted part.
      pre.classList.toggle("win", win < lines.length);
      pre.style.height = win < lines.length ? win * 1.5 * fs + "px" : "";
      o.fs = fs;
      pre.classList.toggle("wrap", fs * 0.61 * L > availW(A, s, 60, box) + 1);
      pre.style.fontSize = fs + "px";
    };
    // Scrolls the window so line k (1-based) sits near the top edge.
    o.scrollTo = (k, instant) => {
      if (!pre.classList.contains("win")) return;
      const r = rows[Math.max(0, k - 1)];
      const top = Math.max(0, r.offsetTop - pre.offsetTop - 2 * 1.5 * o.fs);
      pre.scrollTo({ top, behavior: instant ? "auto" : "smooth" });
    };
    const parse = (a) =>
      a.lines
        ? a.lines
        : a.range
          ? (([x, y]) => Array.from({ length: y - x + 1 }, (_, k) => x + k))(
              a.range.split("-").map(Number),
            )
          : [];
    o.act = (a, instant) => {
      if (a.do === "lines") {
        const to = a.to ?? lines.length;
        rows.forEach((r, k) => {
          if (k < to && r.classList.contains("hid")) {
            if (instant) r.classList.remove("hid");
            else
              setTimeout(
                () => r.classList.remove("hid"),
                (k - o.shown) * (a.gap ?? 70),
              );
          }
        });
        o.shown = Math.max(o.shown, to);
        o.scrollTo(
          Math.max(1, to - Math.floor((s.window || 16) * 0.7)),
          instant,
        );
        return true;
      }
      if (a.do === "hl") {
        const set = new Set(parse(a));
        rows.forEach((r, k) => {
          r.classList.toggle("hl", set.has(k + 1));
          r.classList.toggle("lo", !!a.dim && !set.has(k + 1));
        });
        if (set.size) o.scrollTo(Math.min(...set), instant);
        return true;
      }
      if (a.do === "unhl") {
        rows.forEach((r) => r.classList.remove("hl", "lo"));
        return true;
      }
      return false;
    };
    o.draw();
    A.after(o.draw); // again, now inside its row (the available width changes)
    return o;
  };

  // ---------------------------------------------------------------- circuits
  // ops:{g:'h', q:[0]} · {g:'cx', q:[c, t]} · {g:'cz'|'swap'|'cp'|'crz'…} · {g:'ccx', q:[c1, c2, t]}
  //      {g:'c', ctrl:[…], q:[t], label:'H'} generic control · {g:'box', q:[…], label:'QFT'}
  //      {g:'measure', q:[i], c:j} · {g:'barrier', q?:[…]} · {g:'reset', q:[i]} · {g:'if', q:[…], label:'if c==1'}
  //      p: parameter shown under the name · hidden: appears with the 'gate' action
  const GCOL = {
    h: "red",
    x: "blue",
    y: "blue",
    z: "blue",
    s: "violet",
    sdg: "violet",
    t: "violet",
    tdg: "violet",
    p: "violet",
    sx: "blue",
    sxdg: "blue",
    rx: "teal",
    ry: "teal",
    rz: "teal",
    u: "teal",
    r: "teal",
    rzz: "teal",
    rxx: "teal",
    ryy: "teal",
    measure: "muted",
    reset: "muted",
    delay: "muted",
    box: "gold",
    id: "muted",
    if: "green",
  };
  const GNAME = {
    sdg: "S†",
    tdg: "T†",
    sxdg: "√X†",
    sx: "√X",
    id: "I",
    u: "U",
    reset: "|0⟩",
  };
  const CTRL2 = {
    cx: "x",
    cy: "y",
    cz: "z",
    ch: "h",
    cp: "p",
    crx: "rx",
    cry: "ry",
    crz: "rz",
    cs: "s",
    csx: "sx",
  };

  B.circuit = (box, s, A) => {
    const n = s.qubits,
      nc = s.clbits || 0;
    const ops = s.ops.map((op) => ({ ...op, show: !op.hidden }));
    const o = { spec: s, hl: new Set(), cursor: null };
    // layers: each operation takes the first free column in the vertical range it crosses
    const level = Array.from({ length: n }, () => 0);
    ops.forEach((op) => {
      const qs = op.ctrl
        ? [...op.ctrl, ...op.q]
        : op.g === "barrier" && !(op.q && op.q.length)
          ? [...Array(n).keys()]
          : op.q;
      op.qs = qs;
      let lo = Math.min(...qs),
        hi = Math.max(...qs);
      if (op.g === "measure") hi = n - 1;
      if (op.g === "if") {
        lo = 0;
        hi = n - 1;
      }
      const c = op.col ?? Math.max(...level.slice(lo, hi + 1));
      op.colIdx = c;
      for (let k = lo; k <= hi; k++) level[k] = c + 1;
    });
    const ncol = Math.max(0, ...level);
    const colW = [],
      allBarrier = [];
    for (let c = 0; c < ncol; c++) {
      const here = ops.filter((op) => op.colIdx === c);
      const wide = Math.max(0, ...here.map((op) => gateWidth(op)));
      colW.push(
        here.length && here.every((op) => op.g === "barrier")
          ? 30
          : Math.max(64, wide + 18),
      );
      allBarrier.push(here.every((op) => op.g === "barrier"));
    }
    const qlab = s.qlabels || [...Array(n).keys()].map((i) => `q${sub(i)}`);
    const clab =
      s.clabels ||
      (nc ? [...Array(nc).keys()].map((i) => `${s.creg || "c"}${sub(i)}`) : []);
    const RY = 64,
      X0 =
        70 +
        8 *
          Math.max(
            ...qlab.map((l) => l.length),
            ...clab.map((l) => l.length),
            2,
          ) -
        16;
    const colX = [];
    let acc = X0 + 14;
    colW.forEach((w) => {
      colX.push(acc + w / 2);
      acc += w;
    });
    const W = acc + 26,
      H = (n + nc) * RY + 10;
    const Y = (i) => 38 + i * RY;
    function gateWidth(op) {
      if (
        ["cx", "ccx", "cz", "swap", "barrier", "measure", "ccz"].includes(op.g)
      )
        return 46;
      const name =
        op.label ||
        GNAME[CTRL2[op.g] || op.g] ||
        (CTRL2[op.g] || op.g).toUpperCase();
      return Math.max(
        46,
        13 * Math.max(name.length, (op.p || "").length * 0.8) + 16,
      );
    }
    function sub(i) {
      return String(i)
        .split("")
        .map((d) => "₀₁₂₃₄₅₆₇₈₉"[d])
        .join("");
    }

    o.draw = () => {
      box.textContent = "";
      const sc = Math.min(
        availW(A, s, 0, box) / W,
        s.scale || (A.isPortrait() ? 1 : 1.3),
      );
      const g = A.svg(
        "svg",
        {
          width: W * sc,
          height: H * sc,
          viewBox: `0 0 ${W} ${H}`,
          class: "circ",
        },
        box,
      );
      box.style.width = W * sc + "px";
      const wires = A.svg("g", {}, g);
      for (let i = 0; i < n; i++) {
        A.svg(
          "line",
          {
            x1: X0,
            x2: W - 14,
            y1: Y(i),
            y2: Y(i),
            stroke: "var(--wire)",
            "stroke-width": 2,
          },
          wires,
        );
        const t = A.svg(
          "text",
          { x: X0 - 12, y: Y(i) + 8, "text-anchor": "end", class: "wl" },
          wires,
        );
        t.textContent = qlab[i];
      }
      for (let j = 0; j < nc; j++) {
        const y = Y(n + j);
        A.svg(
          "line",
          {
            x1: X0,
            x2: W - 14,
            y1: y - 2.5,
            y2: y - 2.5,
            stroke: "var(--wire)",
            "stroke-width": 1.6,
          },
          wires,
        );
        A.svg(
          "line",
          {
            x1: X0,
            x2: W - 14,
            y1: y + 2.5,
            y2: y + 2.5,
            stroke: "var(--wire)",
            "stroke-width": 1.6,
          },
          wires,
        );
        const t = A.svg(
          "text",
          { x: X0 - 12, y: y + 8, "text-anchor": "end", class: "wl" },
          wires,
        );
        t.textContent = clab[j];
      }
      if (o.cursor != null && o.cursor < ncol) {
        const cx = colX[o.cursor],
          w = colW[o.cursor];
        A.svg(
          "rect",
          {
            x: cx - w / 2,
            y: 6,
            width: w,
            height: n * RY + 4,
            rx: 10,
            fill: "var(--cursor)",
          },
          g,
        );
      }
      o.groups = ops.map((op, k) => {
        const gg = A.svg(
          "g",
          {
            class:
              "gate" + (op.show ? "" : " off") + (o.hl.has(k) ? " hlop" : ""),
          },
          g,
        );
        drawOp(gg, op, colX[op.colIdx]);
        return gg;
      });
    };
    function boxGate(gg, x, y, name, color, p, h = 46, w) {
      w =
        w ||
        Math.max(46, 13 * Math.max(name.length, (p || "").length * 0.8) + 16);
      A.svg(
        "rect",
        {
          x: x - w / 2,
          y: y - h / 2,
          width: w,
          height: h,
          rx: 6,
          fill: A.col(color),
          class: "gbox",
        },
        gg,
      );
      const t = A.svg(
        "text",
        { x, y: y + (p ? -2 : 8), "text-anchor": "middle", class: "gn" },
        gg,
      );
      t.textContent = name;
      if (p) {
        const tp = A.svg(
          "text",
          { x, y: y + 15, "text-anchor": "middle", class: "gp" },
          gg,
        );
        tp.textContent = p;
      }
    }
    function dot(gg, x, y, color) {
      A.svg("circle", { cx: x, cy: y, r: 7.5, fill: A.col(color) }, gg);
    }
    function vline(gg, x, y1, y2, color) {
      A.svg(
        "line",
        { x1: x, x2: x, y1, y2, stroke: A.col(color), "stroke-width": 3 },
        gg,
      );
    }
    function drawOp(gg, op, x) {
      const g0 = op.g,
        color = op.color || GCOL[CTRL2[g0] || g0] || "gold";
      if (g0 === "barrier") {
        const qs = op.qs,
          y1 = Y(Math.min(...qs)) - 26,
          y2 = Y(Math.max(...qs)) + 26;
        A.svg(
          "rect",
          {
            x: x - 9,
            y: y1,
            width: 18,
            height: y2 - y1,
            fill: "var(--barrier)",
          },
          gg,
        );
        A.svg(
          "line",
          {
            x1: x,
            x2: x,
            y1,
            y2,
            stroke: "var(--muted)",
            "stroke-width": 2,
            "stroke-dasharray": "6 5",
          },
          gg,
        );
        return;
      }
      if (g0 === "measure") {
        const y = Y(op.q[0]),
          yc = Y(n + (op.c ?? 0));
        A.svg(
          "line",
          {
            x1: x - 2.5,
            x2: x - 2.5,
            y1: y,
            y2: yc - 12,
            stroke: "var(--muted)",
            "stroke-width": 1.6,
          },
          gg,
        );
        A.svg(
          "line",
          {
            x1: x + 2.5,
            x2: x + 2.5,
            y1: y,
            y2: yc - 12,
            stroke: "var(--muted)",
            "stroke-width": 1.6,
          },
          gg,
        );
        A.svg(
          "path",
          {
            d: `M${x - 8} ${yc - 14}L${x + 8} ${yc - 14}L${x} ${yc - 3}Z`,
            fill: "var(--muted)",
          },
          gg,
        );
        A.svg(
          "rect",
          {
            x: x - 23,
            y: y - 23,
            width: 46,
            height: 46,
            rx: 6,
            fill: A.col(op.color || "muted"),
            class: "gbox",
          },
          gg,
        );
        A.svg(
          "path",
          {
            d: `M${x - 14} ${y + 8}A14 14 0 0 1 ${x + 14} ${y + 8}`,
            fill: "none",
            stroke: "var(--stage)",
            "stroke-width": 2.5,
          },
          gg,
        );
        A.svg(
          "line",
          {
            x1: x,
            y1: y + 8,
            x2: x + 10,
            y2: y - 10,
            stroke: "var(--stage)",
            "stroke-width": 2.5,
          },
          gg,
        );
        if (nc > 1 || s.cidx) {
          const t = A.svg(
            "text",
            { x: x + 14, y: yc + 22, class: "gp", fill: "var(--muted)" },
            gg,
          );
          t.textContent = op.c ?? 0;
        }
        return;
      }
      if (g0 === "if") {
        const y1 = 10,
          y2 = Y(n - 1) + 30;
        A.svg(
          "rect",
          {
            x: x - 30,
            y: y1,
            width: 60,
            height: y2 - y1,
            rx: 8,
            fill: "none",
            stroke: A.col(color),
            "stroke-width": 2.5,
            "stroke-dasharray": "7 5",
          },
          gg,
        );
        const t = A.svg(
          "text",
          {
            x,
            y: y2 + 20,
            "text-anchor": "middle",
            class: "gp",
            fill: A.col(color),
          },
          gg,
        );
        t.textContent = op.label || "if";
        (op.q || []).forEach((q) =>
          boxGate(gg, x, Y(q), op.inner || "X", op.innerColor || "blue"),
        );
        return;
      }
      if (op.ctrl && op.q.length > 1) {
        const lo = Math.min(...op.q),
          hi = Math.max(...op.q),
          all = [...op.ctrl, lo, hi];
        vline(gg, x, Y(Math.min(...all)), Y(Math.max(...all)), "blue");
        op.ctrl.forEach((q) => dot(gg, x, Y(q), "blue"));
        const name = op.label || "U",
          w = Math.max(56, 13 * name.length + 22);
        A.svg(
          "rect",
          {
            x: x - w / 2,
            y: Y(lo) - 23,
            width: w,
            height: Y(hi) - Y(lo) + 46,
            rx: 6,
            fill: A.col(op.color || "gold"),
            class: "gbox",
          },
          gg,
        );
        const t = A.svg(
          "text",
          {
            x,
            y: (Y(lo) + Y(hi)) / 2 + 8,
            "text-anchor": "middle",
            class: "gn",
          },
          gg,
        );
        t.textContent = name;
        return;
      }
      if (
        g0 === "box" ||
        (op.q.length > 1 &&
          !CTRL2[g0] &&
          !["ccx", "swap", "ccz", "cx"].includes(g0) &&
          !op.ctrl)
      ) {
        const lo = Math.min(...op.q),
          hi = Math.max(...op.q),
          name = op.label || g0.toUpperCase();
        const w = Math.max(
          56,
          13 * Math.max(name.length, (op.p || "").length * 0.8) + 22,
        );
        A.svg(
          "rect",
          {
            x: x - w / 2,
            y: Y(lo) - 23,
            width: w,
            height: Y(hi) - Y(lo) + 46,
            rx: 6,
            fill: A.col(color),
            class: "gbox",
          },
          gg,
        );
        const ym = (Y(lo) + Y(hi)) / 2;
        const t = A.svg(
          "text",
          { x, y: ym + (op.p ? -2 : 8), "text-anchor": "middle", class: "gn" },
          gg,
        );
        t.textContent = name;
        if (op.p) {
          const tp = A.svg(
            "text",
            { x, y: ym + 15, "text-anchor": "middle", class: "gp" },
            gg,
          );
          tp.textContent = op.p;
        }
        return;
      }
      if (g0 === "swap") {
        const [a, b] = op.q;
        vline(gg, x, Y(a), Y(b), "blue");
        [a, b].forEach((q) => {
          const y = Y(q);
          A.svg(
            "path",
            {
              d: `M${x - 9} ${y - 9}L${x + 9} ${y + 9}M${x + 9} ${y - 9}L${x - 9} ${y + 9}`,
              stroke: A.col("blue"),
              "stroke-width": 3.5,
            },
            gg,
          );
        });
        return;
      }
      const ctrls =
        op.ctrl ||
        (g0 === "ccx" || g0 === "ccz"
          ? op.q.slice(0, 2)
          : CTRL2[g0]
            ? op.q.slice(0, 1)
            : []);
      const tgt = op.ctrl ? op.q[0] : op.q[op.q.length - 1];
      const base = op.ctrl
        ? op.base || "box"
        : g0 === "ccx"
          ? "x"
          : g0 === "ccz"
            ? "z"
            : CTRL2[g0] || g0;
      const ccol =
        op.color ||
        (ctrls.length
          ? GCOL[base] === "blue" || base === "box"
            ? "blue"
            : GCOL[base] || "blue"
          : color);
      if (ctrls.length) {
        const all = [...ctrls, tgt];
        vline(gg, x, Y(Math.min(...all)), Y(Math.max(...all)), ccol);
        ctrls.forEach((q) => dot(gg, x, Y(q), ccol));
      }
      const yt = Y(tgt);
      if (ctrls.length && base === "x") {
        A.svg("circle", { cx: x, cy: yt, r: 17, fill: A.col(ccol) }, gg);
        A.svg(
          "path",
          {
            d: `M${x - 10} ${yt}L${x + 10} ${yt}M${x} ${yt - 10}L${x} ${yt + 10}`,
            stroke: "var(--stage)",
            "stroke-width": 3,
          },
          gg,
        );
      } else if (ctrls.length && (base === "z" || base === "p") && !op.label) {
        dot(gg, x, yt, ccol);
        if (op.p) {
          const t = A.svg(
            "text",
            {
              x: x + 12,
              y: (Y(ctrls[0]) + yt) / 2 + 6,
              class: "gp",
              fill: A.col(ccol),
            },
            gg,
          );
          t.textContent = base === "p" ? "P(" + op.p + ")" : "";
        }
      } else {
        const name = op.label || GNAME[base] || base.toUpperCase();
        boxGate(
          gg,
          x,
          yt,
          name,
          ctrls.length ? op.color || GCOL[base] || "gold" : color,
          op.p,
        );
      }
    }
    o.act = (a, instant) => {
      const idx = a.i == null ? [] : [].concat(a.i);
      if (a.do === "gate") {
        idx.forEach((k) => {
          ops[k].show = true;
          const gg = o.groups[k];
          gg.classList.remove("off");
          if (!instant) gg.classList.add("pop");
        });
        return true;
      }
      if (a.do === "ungate") {
        idx.forEach((k) => {
          ops[k].show = false;
          o.groups[k].classList.add("off");
        });
        return true;
      }
      if (a.do === "hlop") {
        o.hl = new Set(idx);
        o.groups.forEach((gg, k) => gg.classList.toggle("hlop", o.hl.has(k)));
        return true;
      }
      if (a.do === "cursor") {
        o.cursor = a.col ?? null;
        o.draw();
        return true;
      }
      return false;
    };
    o.draw();
    A.after(o.draw);
    return o;
  };

  // ---------------------------------------------------------------- histogram of counts
  B.hist = (box, s, A) => {
    const o = {
      spec: s,
      data: s.data.map((d) => d.slice()),
      f: s.grow ? 0 : 1,
    };
    o.draw = () => {
      box.textContent = "";
      const W0 = A.isPortrait() ? Math.min(s.w || 620, 620) : s.w || 640,
        H = (A.isPortrait() ? s.ph : null) || s.h || 300;
      const n = o.data.length,
        W = Math.min(W0, Math.max(240, n * 120));
      const ymax =
        s.ymax || Math.max(0, ...o.data.map((d) => d[1])) * 1.15 || 1;
      const ymin = s.ymin ?? Math.min(0, ...o.data.map((d) => d[1])) * 1.15;
      const Y = (v) => (H * (ymax - v)) / (ymax - ymin),
        Y0 = Y(0);
      const g = A.svg(
        "svg",
        { width: W, height: H + 64, viewBox: `0 -30 ${W} ${H + 64}` },
        box,
      );
      box.style.width = W + "px";
      const slot = W / n,
        bw = Math.min(90, slot * 0.7);
      A.svg(
        "line",
        {
          x1: 0,
          x2: W,
          y1: Y0,
          y2: Y0,
          stroke: "var(--axis)",
          "stroke-width": 2,
        },
        g,
      );
      o.data.forEach(([lab, v, c], k) => {
        const yv = Y0 + (Y(v) - Y0) * o.f,
          x = slot * k + slot / 2,
          top = Math.min(yv, Y0);
        A.svg(
          "rect",
          {
            x: x - bw / 2,
            y: top,
            width: bw,
            height: Math.abs(yv - Y0),
            rx: 4,
            fill: A.col(c || s.color || "blue"),
            opacity: 0.9,
          },
          g,
        );
        const t = A.svg(
          "text",
          { x, y: H + 30, "text-anchor": "middle", class: "hl-x" },
          g,
        );
        t.textContent = lab;
        if (s.values !== false && o.f > 0.98) {
          const tv = A.svg(
            "text",
            {
              x,
              y: v < 0 ? yv + 24 : yv - 10,
              "text-anchor": "middle",
              class: "hl-v",
            },
            g,
          );
          tv.textContent = s.prob
            ? (v * 100).toFixed(s.digits ?? 1) + " %"
            : s.digits != null
              ? v.toFixed(s.digits)
              : v;
        }
      });
      if (s.ylabel) {
        const t = A.svg("text", { x: 0, y: -12, class: "hl-x" }, g);
        t.textContent = s.ylabel;
      }
    };
    o.act = (a, instant) => {
      if (a.do === "grow") {
        A.tween(
          a.dur ?? 1.2,
          (q) => {
            o.f = q;
            o.draw();
          },
          instant,
        );
        return true;
      }
      if (a.do === "data") {
        const from = o.data.map((d) => d[1]),
          to = a.data;
        A.tween(
          a.dur ?? 1.2,
          (q) => {
            o.data.forEach(
              (d, k) => (d[1] = from[k] + (to[k][1] - from[k]) * q),
            );
            o.draw();
          },
          instant,
        );
        return true;
      }
      return false;
    };
    o.draw();
    return o;
  };

  // ---------------------------------------------------------------- table
  B.table = (box, s, A) => {
    const o = { spec: s };
    box.classList.remove("fig");
    const t = A.el("table", "tbl", box);
    if (s.size) t.style.fontSize = s.size + "px";
    if (s.head) {
      const tr = A.el("tr", "", A.el("thead", "", t));
      s.head.forEach((h) => A.rich(A.el("th", "", tr), h));
    }
    const tb = A.el("tbody", "", t);
    o.items = s.rows.map((r) => {
      const tr = A.el("tr", s.stagger ? "hid" : "", tb);
      r.forEach((c) => A.rich(A.el("td", "", tr), c));
      return tr;
    });
    o.act = (a) => {
      if (a.do === "hlrow") {
        o.items.forEach((tr, k) =>
          tr.classList.toggle("on", [].concat(a.i).includes(k)),
        );
        return true;
      }
      return false;
    };
    return o;
  };

  // ---------------------------------------------------------------- "Tu turno" mission
  // notebook: path of the marimo notebook · tasks: [{level: 1|2|3, text}]
  const LV = { 1: "Reproduce", 2: "Modifica", 3: "Crea" };

  B.mission = (box, s, A) => {
    const o = { spec: s };
    box.classList.remove("fig");
    const card = A.el("div", "mcard", box);
    A.el("div", "mtitle", card).textContent = s.title || "Tu turno";
    o.items = s.tasks.map((t) => {
      const r = A.el("div", "mtask" + (s.stagger ? " hid" : ""), card);
      A.el("span", "mlv", r).textContent = LV[t.level] || LV[1];
      A.rich(A.el("span", "mtx", r), t.text);
      return r;
    });
    const cmd = `uv run marimo edit ${s.notebook}`;
    const row = A.el("div", "mcmd", card);
    A.el("code", "", row).textContent = cmd;
    const b = A.el("button", "abtn", row);
    b.textContent = "Copiar";
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      navigator.clipboard?.writeText(cmd).then(() => {
        b.textContent = "Copiado";
      });
    });
    window.notebookHelp(row);
    return o;
  };
  B.mission.levels = LV;

  // ---------------------------------------------------------------- flow of steps
  B.flow = (box, s, A) => {
    const o = { spec: s, items: [] };
    box.classList.remove("fig");
    const wrap = A.el("div", "flow" + (s.vertical ? " vert" : ""), box);
    s.steps.forEach((st, k) => {
      if (k)
        A.el("div", "farrow" + (s.stagger ? " hid" : ""), wrap).textContent =
          s.vertical ? "↓" : "→";
      const d = A.el("div", "fstep" + (s.stagger ? " hid" : ""), wrap);
      if (st.n != null || s.numbered)
        A.el("div", "fn", d).textContent = st.n ?? k + 1;
      A.rich(A.el("div", "ft", d), st.t);
      if (st.s) A.rich(A.el("div", "fs", d), st.s);
      if (st.color) d.style.setProperty("--fc", A.col(st.color));
      o.items.push(d);
    });
    // 'item' reveals step k and the arrow before it
    o.items = o.items.map((d) => ({
      classList: {
        remove: (c) => {
          d.classList.remove(c);
          const p = d.previousElementSibling;
          if (p) p.classList.remove(c);
        },
      },
    }));
    o.act = (a) => {
      if (a.do === "step") {
        [...wrap.querySelectorAll(".fstep")].forEach((d, k) =>
          d.classList.toggle("on", [].concat(a.i).includes(k)),
        );
        return true;
      }
      return false;
    };
    return o;
  };

  // ---------------------------------------------------------------- coupling graph
  // nodes: [[x, y], …] (coordinates on a grid), edges: [[a, b], …]
  B.graph = (box, s, A) => {
    const o = { spec: s, hn: {}, he: {}, lab: { ...s.nodeLabels } };
    o.draw = () => {
      box.textContent = "";
      const xs = s.nodes.map((p) => p[0]),
        ys = s.nodes.map((p) => p[1]);
      const [x0, x1, y0, y1] = [
        Math.min(...xs),
        Math.max(...xs),
        Math.min(...ys),
        Math.max(...ys),
      ];
      const u = s.unit || 70,
        pad = 34;
      let W = (x1 - x0) * u + 2 * pad,
        H = (y1 - y0) * u + 2 * pad;
      const sc = Math.min(1, availW(A, s) / W);
      const g = A.svg(
        "svg",
        { width: W * sc, height: H * sc, viewBox: `0 0 ${W} ${H}` },
        box,
      );
      box.style.width = W * sc + "px";
      const P = (k) => [
        pad + (s.nodes[k][0] - x0) * u,
        pad + (s.nodes[k][1] - y0) * u,
      ];
      s.edges.forEach(([a, b]) => {
        const key = a < b ? a + "-" + b : b + "-" + a,
          [xa, ya] = P(a),
          [xb, yb] = P(b);
        A.svg(
          "line",
          {
            x1: xa,
            y1: ya,
            x2: xb,
            y2: yb,
            stroke: o.he[key] ? A.col(o.he[key]) : "var(--wire)",
            "stroke-width": o.he[key] ? 7 : 4,
            "stroke-linecap": "round",
          },
          g,
        );
      });
      s.nodes.forEach((_, k) => {
        const [x, y] = P(k),
          c = o.hn[k];
        A.svg(
          "circle",
          {
            cx: x,
            cy: y,
            r: s.r || 18,
            fill: c ? A.col(c) : "var(--node)",
            stroke: c ? "none" : "var(--wire)",
            "stroke-width": 2,
          },
          g,
        );
        const t = A.svg(
          "text",
          {
            x,
            y: y + 6,
            "text-anchor": "middle",
            class: "nd" + (c ? " on" : ""),
          },
          g,
        );
        t.textContent = o.lab[k] ?? (s.numbers === false ? "" : k);
      });
    };
    o.act = (a) => {
      if (a.do === "hlnode") {
        [].concat(a.i).forEach((k) => (o.hn[k] = a.color || "gold"));
        o.draw();
        return true;
      }
      if (a.do === "hledge") {
        (a.edges || [a.i]).forEach(
          ([x, y]) =>
            (o.he[x < y ? x + "-" + y : y + "-" + x] = a.color || "gold"),
        );
        o.draw();
        return true;
      }
      if (a.do === "nodelabel") {
        Object.assign(o.lab, a.labels);
        o.draw();
        return true;
      }
      if (a.do === "clearhl") {
        o.hn = {};
        o.he = {};
        o.draw();
        return true;
      }
      return false;
    };
    o.draw();
    return o;
  };
})();
