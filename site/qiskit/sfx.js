// Sonidos discretos sintetizados con WebAudio (sin archivos): acierto, error y fin de lección.
// oxlint-disable-next-line eslint/no-unused-vars -- Global que usa engine.js.
const SFX = (() => {
  let ctx = null,
    muted = false;
  try {
    muted = localStorage.getItem("qiskit:mute") === "1";
  } catch {}
  const ac = () =>
    ctx || (ctx = new (window.AudioContext || window.webkitAudioContext)());

  function tone(freq, dur, { type = "sine", vol = 0.08, at = 0 } = {}) {
    const c = ac(),
      t0 = c.currentTime + at,
      o = c.createOscillator(),
      g = c.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t0);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(vol, t0 + 0.015);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g).connect(c.destination);
    o.start(t0);
    o.stop(t0 + dur + 0.02);
  }
  const sounds = {
    tick: () => tone(880, 0.06, { vol: 0.03 }),
    ok: () => {
      tone(660, 0.18);
      tone(990, 0.28, { at: 0.09 });
    },
    no: () => tone(220, 0.22, { type: "triangle", vol: 0.06 }),
    done: () =>
      [523, 659, 784].forEach((f, i) =>
        tone(f, 0.35, { at: i * 0.12, vol: 0.07 }),
      ),
  };
  return {
    unlock() {
      try {
        ac().resume();
      } catch {}
    },
    play(n) {
      if (!muted && sounds[n])
        try {
          sounds[n]();
        } catch {}
    },
    get muted() {
      return muted;
    },
    toggle() {
      muted = !muted;
      try {
        localStorage.setItem("qiskit:mute", muted ? "1" : "0");
      } catch {}
      return muted;
    },
  };
})();
