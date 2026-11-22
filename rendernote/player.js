// Rendernote page: views, playback, mixer, click and loop, on plain Web Audio.
// Everything it needs is in the #rn-data block written by build.py:
//   midi.tracks [{name, program, notes: [[start, end, key, velocity]]}]  (in quarter notes)
//   midi.tempos [[beat, bpm]], midi.meter [numerator, denominator]
//   sounds {program: [{lo, hi, root, tune, rate, loop, format, audio}]}
//   files {filename: base64}, views [names], version

const D = JSON.parse(document.getElementById("rn-data").textContent);
const tracks = D.midi.tracks;
const [num, den] = D.midi.meter;
const BEAT = 4 / den;                 // quarter notes per beat
const BAR = num * BEAT;               // quarter notes per bar
const lastBeat = Math.max(...tracks.flatMap(t => t.notes.map(n => n[1])));
const $ = id => document.getElementById(id);

// ------------------------------------------------------------ settings
// Defaults, then this browser's last settings, then anything in the link.
const KEY = "rendernote:" + D.title;
const S = { view: "Score", tempo: 100, click: "off", clickVol: 70, countIn: 1, loop: false,
            loopFrom: 1, loopTo: Math.max(1, Math.ceil(lastBeat / BAR)),
            vol: {}, mute: {}, solo: {} };
try { Object.assign(S, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) {}
const LINK = { view: "view", tempo: "tempo", click: "click", clickVol: "clickvol", countIn: "countin" };
for (const [k, v] of new URLSearchParams(location.hash.slice(1))) {
  const name = Object.keys(LINK).find(n => LINK[n] === k);
  if (name) S[name] = typeof S[name] === "number" ? Number(v) : v;
  if (k === "loop") { const [a, b] = v.split("-").map(Number); Object.assign(S, { loop: true, loopFrom: a, loopTo: b || a }); }
  if (k === "mute") v.split(",").forEach(p => S.mute[p] = true);
  if (k === "solo") v.split(",").forEach(p => S.solo[p] = true);
}
if (!D.views.includes(S.view)) S.view = "Score";

function save() {
  try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {}
  const p = new URLSearchParams();
  for (const [name, k] of Object.entries(LINK)) p.set(k, S[name]);
  if (S.loop) p.set("loop", `${S.loopFrom}-${S.loopTo}`);
  const muted = D.parts.filter(n => S.mute[n]), soloed = D.parts.filter(n => S.solo[n]);
  if (muted.length) p.set("mute", muted.join(","));
  if (soloed.length) p.set("solo", soloed.join(","));
  history.replaceState(null, "", "#" + p.toString());
}

// ------------------------------------------------------------ time
// Quarter-note beats <-> seconds through the score's tempo marks, at S.tempo percent.
const tempos = D.midi.tempos.length ? D.midi.tempos : [[0, 120]];
function secondsAt(beat) {
  let s = 0;
  for (let i = 0; i < tempos.length; i++) {
    const [b, bpm] = tempos[i], next = i + 1 < tempos.length ? tempos[i + 1][0] : Infinity;
    if (beat <= b) break;
    s += (Math.min(beat, next) - b) * 60 / bpm;
  }
  return s * 100 / S.tempo;
}
function beatAt(seconds) {
  const t = seconds * S.tempo / 100;
  let s = 0;
  for (let i = 0; i < tempos.length; i++) {
    const [b, bpm] = tempos[i], next = i + 1 < tempos.length ? tempos[i + 1][0] : Infinity;
    const span = (next - b) * 60 / bpm;
    if (t <= s + span) return b + (t - s) * bpm / 60;
    s += span;
  }
  return lastBeat;
}

// ------------------------------------------------------------ sound
let ctx, master, clickBus, buses = [], banks = {};

function decodeBase64(b64) {
  const bin = atob(b64), bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

async function startAudio() {
  if (ctx) { if (ctx.state !== "running") await ctx.resume(); return; }
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  master = ctx.createGain(); master.gain.value = 0.8; master.connect(ctx.destination);
  clickBus = ctx.createGain(); clickBus.connect(master);
  buses = tracks.map(() => { const g = ctx.createGain(); g.connect(master); return g; });
  mix();
  for (const [prog, zones] of Object.entries(D.sounds)) {
    try {
      banks[prog] = await Promise.all(zones.map(async z => {
        let buffer;
        if (z.format === "ogg") buffer = await ctx.decodeAudioData(decodeBase64(z.audio));
        else {
          const pcm = new Int16Array(decodeBase64(z.audio));
          buffer = ctx.createBuffer(1, pcm.length, z.rate);
          const ch = buffer.getChannelData(0);
          for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 32768;
        }
        return { ...z, buffer };
      }));
    } catch (e) { console.warn("Rendernote: using a plain synth for program", prog, e); }
  }
}

function mix() {
  if (!ctx) return;
  const soloing = D.parts.some(n => S.solo[n]);
  tracks.forEach((t, i) => {
    const on = soloing ? S.solo[t.name] : !S.mute[t.name];
    buses[i].gain.value = on ? (S.vol[t.name] ?? 80) / 100 : 0;
  });
  clickBus.gain.value = S.clickVol / 100;
}

let sounding = [];
function voice(track, key, velocity, start, end) {
  const amp = 0.25 + 0.6 * velocity / 127;
  const g = ctx.createGain();
  g.connect(buses[track]);
  g.gain.setValueAtTime(0, start);
  g.gain.linearRampToValueAtTime(amp, start + 0.012);
  g.gain.setValueAtTime(amp, end);
  g.gain.linearRampToValueAtTime(0, end + 0.08);
  const zone = (banks[tracks[track].program] || []).find(z => z.lo <= key && key <= z.hi);
  let src;
  if (zone) {
    src = ctx.createBufferSource();
    src.buffer = zone.buffer;
    src.playbackRate.value = 2 ** (((key - zone.root) * 100 + zone.tune) / 1200);
    if (zone.loop) {
      src.loop = true;
      src.loopStart = zone.loop[0] / zone.rate;
      src.loopEnd = zone.loop[1] / zone.rate;
    }
  } else {
    src = ctx.createOscillator();
    src.type = "triangle";
    src.frequency.value = 440 * 2 ** ((key - 69) / 12);
  }
  src.connect(g);
  src.start(start);
  src.stop(end + 0.1);
  sounding.push(src);
}

function tick(time, downbeat) {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.frequency.value = downbeat ? 1760 : 1320;
  g.gain.setValueAtTime(0, time);
  g.gain.linearRampToValueAtTime(downbeat ? 1 : 0.6, time + 0.002);
  g.gain.exponentialRampToValueAtTime(0.001, time + 0.05);
  o.connect(g); g.connect(clickBus);
  o.start(time); o.stop(time + 0.06);
  sounding.push(o);
}

// ------------------------------------------------------------ playback
// One pass from `from` to `to` (quarter-note beats), starting at audio time t0.
function schedule(from, to, t0, countIn) {
  const at = b => t0 + secondsAt(b) - secondsAt(from);
  if (countIn) {
    const beats = countIn * num;
    const lead = secondsAt(from) - secondsAt(Math.max(0, from - BEAT));   // count in at the tempo where we start
    const each = lead > 0 ? lead : 60 / tempos[0][1] * BEAT * 100 / S.tempo;
    for (let i = 0; i < beats; i++) tick(t0 - (beats - i) * each, i % num === 0);
  }
  if (S.click !== "off") {
    for (let b = Math.ceil(from / BEAT - 1e-6) * BEAT; b < to - 1e-6; b += BEAT) {
      const down = Math.abs(b / BAR - Math.round(b / BAR)) < 1e-6;
      if (S.click === "beat" || down) tick(at(b), down);
    }
  }
  tracks.forEach((t, i) => {
    for (const [s, e, key, vel] of t.notes) {
      if (s >= from - 1e-6 && s < to - 1e-6) voice(i, key, vel, at(s), at(Math.min(e, to + 0.5)));
    }
  });
}

let play = null;   // {t0, from, to} of the pass now sounding
let timer = null;

async function playFrom(beat) {
  stop();
  await startAudio();
  const loopA = (S.loopFrom - 1) * BAR, loopB = S.loopTo * BAR;
  const looping = S.loop && loopB > loopA;
  if (looping && (beat < loopA || beat >= loopB)) beat = loopA;
  const to = looping ? loopB : lastBeat;
  const countIn = Number(S.countIn);
  const lead = countIn ? countIn * num * (secondsAt(beat) - secondsAt(Math.max(0, beat - BEAT)) || 60 / tempos[0][1] * BEAT * 100 / S.tempo) : 0;
  const t0 = ctx.currentTime + 0.1 + lead;
  schedule(beat, to, t0, countIn);
  play = { t0, from: beat, to };
  $("play").textContent = "Stop";
  timer = setInterval(() => {
    const end = play.t0 + secondsAt(play.to) - secondsAt(play.from);
    if (looping && ctx.currentTime > end - 1) {          // queue the next time round
      schedule(loopA, loopB, end, 0);
      play = { t0: end, from: loopA, to: loopB };
    } else if (!looping && ctx.currentTime > end + 1) stop();
  }, 200);
}

function stop() {
  clearInterval(timer); timer = null;
  for (const s of sounding) { try { s.stop(); } catch (e) {} }
  sounding = [];
  play = null;
  $("play").textContent = "Play";
  document.querySelectorAll(".rn-note.on").forEach(n => n.classList.remove("on"));
  $("where").textContent = "Tap a note to play from it";
}

// ------------------------------------------------------------ the score on screen
// Each view is engraved twice: an A4-width page, and a 100 mm page for phones.
const NARROW = 700;   // px: below this the phone engraving is shown
const layout = () => innerWidth < NARROW ? "narrow" : "wide";
const views = {};
const current = () => views[S.view + "/" + layout()];
document.querySelectorAll(".view").forEach(v => {
  views[v.dataset.view + "/" + v.dataset.layout] = {
    el: v,
    notes: [...v.querySelectorAll(".rn-note")].map(el => ({ el, s: +el.dataset.start, e: +el.dataset.end })),
  };
});

function showView(name) {
  S.view = name;
  for (const [n, v] of Object.entries(views)) v.el.hidden = n !== name + "/" + layout();
  document.querySelectorAll("#tabs button").forEach(b => b.setAttribute("aria-pressed", b.dataset.view === name));
  save();
}

let lastScroll = 0;
function frame() {
  requestAnimationFrame(frame);
  if (!play || !ctx) return;
  const now = ctx.currentTime;
  if (now < play.t0) { $("where").textContent = "Count-in"; return; }
  const beat = beatAt(secondsAt(play.from) + now - play.t0);
  $("where").textContent = `Bar ${Math.floor(beat / BAR) + 1}`;
  let first = null;
  for (const n of current().notes) {
    const on = n.s <= beat && beat < n.e;
    if (on !== n.el.classList.contains("on")) n.el.classList.toggle("on", on);
    if (on && !first) first = n.el;
  }
  // keep the line that's playing just under the header
  if (first && performance.now() - lastScroll > 700) {
    const top = first.getBoundingClientRect().top;
    const head = document.querySelector("header").getBoundingClientRect().bottom;
    if (top < head + 10 || top > innerHeight * 0.75) {
      scrollBy({ top: top - head - 60, behavior: "smooth" });
      lastScroll = performance.now();
    }
  }
}

// ------------------------------------------------------------ controls
function setup() {
  for (const name of D.views) {
    const b = document.createElement("button");
    b.textContent = name === "Score" ? "Full score" : name;
    b.dataset.view = name;
    b.onclick = () => showView(name);
    $("tabs").append(b);
  }
  $("play").onclick = () => play ? stop() : playFrom(S.loop ? (S.loopFrom - 1) * BAR : 0);
  $("from-top").onclick = () => playFrom(0);
  document.querySelector("main").addEventListener("click", e => {
    const note = e.target.closest(".rn-note");
    if (note) playFrom(+note.dataset.start);
  });

  const restart = () => { if (play) playFrom(play.from); };
  const bpm = () => Math.round(tempos[0][1] * S.tempo / 100);
  $("tempo").value = S.tempo;
  $("tempo-out").textContent = `${S.tempo}% (♩ = ${bpm()})`;
  $("tempo").oninput = e => { S.tempo = +e.target.value; $("tempo-out").textContent = `${S.tempo}% (♩ = ${bpm()})`; save(); };
  $("tempo").onchange = restart;

  for (const t of tracks) {
    const name = document.createElement("span"); name.textContent = t.name;
    const vol = document.createElement("input");
    Object.assign(vol, { type: "range", min: 0, max: 100, step: 5, value: S.vol[t.name] ?? 80 });
    vol.oninput = () => { S.vol[t.name] = +vol.value; mix(); save(); };
    const toggle = (label, key) => {
      const b = document.createElement("button");
      b.textContent = label; b.title = key === "mute" ? "Mute" : "Solo";
      b.setAttribute("aria-pressed", !!S[key][t.name]);
      b.onclick = () => { S[key][t.name] = !S[key][t.name]; b.setAttribute("aria-pressed", S[key][t.name]); mix(); save(); };
      return b;
    };
    $("mixer").append(name, vol, toggle("M", "mute"), toggle("S", "solo"));
  }

  $("click").value = S.click;
  $("click").onchange = e => { S.click = e.target.value; save(); restart(); };
  $("click-vol").value = S.clickVol;
  $("click-vol").oninput = e => { S.clickVol = +e.target.value; mix(); save(); };
  $("count-in").value = S.countIn;
  $("count-in").onchange = e => { S.countIn = +e.target.value; save(); };
  $("loop-on").checked = S.loop;
  $("loop-from").value = S.loopFrom;
  $("loop-to").value = S.loopTo;
  $("loop-on").onchange = e => { S.loop = e.target.checked; save(); restart(); };
  $("loop-from").onchange = e => { S.loopFrom = Math.max(1, +e.target.value); save(); restart(); };
  $("loop-to").onchange = e => { S.loopTo = Math.max(S.loopFrom, +e.target.value); save(); restart(); };

  Object.keys(D.files).forEach((name, i) => {
    const a = document.createElement("a");
    a.textContent = name; a.href = "#"; a.download = name;
    a.onclick = e => {
      e.preventDefault();
      const type = name.endsWith(".pdf") ? "application/pdf" : "audio/midi";
      const url = URL.createObjectURL(new Blob([decodeBase64(D.files[name])], { type }));
      const link = document.createElement("a");
      link.href = url; link.download = name; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    };
    if (i) $("files").append(" · ");
    $("files").append(a);
  });
  $("version").textContent = D.version;
  showView(S.view);
  let wasLayout = layout();
  addEventListener("resize", () => { if (layout() !== wasLayout) { wasLayout = layout(); showView(S.view); } });
  requestAnimationFrame(frame);
}
setup();

// A different settings link pasted into the address bar: start again with it.
addEventListener("hashchange", () => location.reload());

// ------------------------------------------------------------ live reload
// When served by `rendernote serve`, reload (keeping the scroll position) after a rebuild.
if (location.protocol.startsWith("http")) {
  const y = sessionStorage.getItem(KEY + ":y");
  if (y) { scrollTo(0, +y); sessionStorage.removeItem(KEY + ":y"); }
  const poll = setInterval(async () => {
    try {
      const r = await fetch("__build", { cache: "no-store" });
      if (!r.ok) return clearInterval(poll);              // not `rendernote serve`: nothing to watch
      const v = await r.text();
      if (v && v !== D.build) { sessionStorage.setItem(KEY + ":y", scrollY); location.reload(); }
    } catch (e) { clearInterval(poll); }
  }, 1500);
}
