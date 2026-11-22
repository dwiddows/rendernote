"""Turn a LilyPond score into one self-contained HTML file.

LilyPond runs once per view: the full score and each part as SVG (every note
head tagged with its part and timing), each part as a PDF, the full score as
a PDF, and the MIDI with repeats played out. The page, its player, the notes
from the MIDI, the SVGs, the PDFs and the instrument samples all go into
<Title>.html next to the score.
"""
import base64, datetime, html, json, os, re, shutil, struct, subprocess, sys, tempfile, urllib.request

from .soundfont import SoundFont

HERE = os.path.dirname(os.path.abspath(__file__))
SOUNDFONT_URL = "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/"
SOUNDFONT = "MuseScore_General.sf3"
SOUNDFONT_LICENSE = "MuseScore_General_License.md"


# ---------------------------------------------------------------- LilyPond

def lilypond():
    exe = shutil.which("lilypond")
    if exe: return exe
    try:
        import lilypond as lp                  # the pip-installed LilyPond
        return str(lp.executable())
    except ImportError:
        sys.exit("Rendernote needs LilyPond: pip install lilypond")


def engrave(score, work, name, focus=None, mode="none", backend=None, narrow=False):
    """Run LilyPond on the score with rendernote.ily; returns the output base path."""
    wrapper = os.path.join(work, name + ".ly")
    with open(wrapper, "w") as f:
        f.write('#(define-public rendernote-focus %s)\n' % ("#f" if focus is None else json.dumps(focus)))
        f.write("#(define-public rendernote-mode '%s)\n" % mode)
        f.write("#(define-public rendernote-narrow %s)\n" % ("#t" if narrow else "#f"))
        f.write('\\include "%s"\n' % os.path.join(HERE, "rendernote.ily"))
        f.write('\\include "%s"\n' % os.path.abspath(score))
    cmd = [lilypond(), "-s", "-I", os.path.dirname(os.path.abspath(score)), "-o", os.path.join(work, name)]
    if backend: cmd.insert(1, "-dbackend=" + backend)
    r = subprocess.run(cmd + [wrapper], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    return os.path.join(work, name)


def clean_svg(svg):
    """The SVG as an inline element: no XML prolog, sized by the page."""
    svg = re.sub(r"<\?xml[^>]*>\s*", "", svg)
    return re.sub(r'<svg([^>]*?) width="[^"]*" height="[^"]*"', r'<svg\1', svg, count=1)


# ---------------------------------------------------------------- MIDI

def read_midi(path):
    """Notes per track, tempo changes, time signature and programs, in quarter notes."""
    data = open(path, "rb").read()
    ntracks, ppq = struct.unpack(">HH", data[10:14])
    pos, tracks, tempos, meter = 14, [], [], (4, 4)
    while pos < len(data):
        size = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        body, pos = data[pos + 8:pos + 8 + size], pos + 8 + size
        i, tick, status, on, notes, name, program = 0, 0, 0, {}, [], "", None
        while i < len(body):
            delta = 0
            while True:
                b = body[i]; i += 1
                delta = (delta << 7) | (b & 0x7F)
                if b < 0x80: break
            tick += delta
            if body[i] & 0x80: status = body[i]; i += 1
            kind = status & 0xF0
            if status == 0xFF:
                meta, length = body[i], body[i + 1]; i += 2   # LilyPond's meta events are short
                value = body[i:i + length]; i += length
                if meta == 0x51: tempos.append((tick / ppq, 60e6 / int.from_bytes(value, "big")))
                elif meta == 0x58: meter = (value[0], 2 ** value[1])
                elif meta == 0x03: name = value.decode("latin1")
            elif status in (0xF0, 0xF7):
                length = body[i]; i += 1 + length
            elif kind in (0x80, 0x90):
                key, vel = body[i], body[i + 1]; i += 2
                if kind == 0x90 and vel:
                    on.setdefault(key, []).append((tick, vel))
                elif on.get(key):
                    start, v = on[key].pop(0)
                    notes.append([round(start / ppq, 4), round(tick / ppq, 4), key, v])
            elif kind in (0xC0, 0xD0):
                if kind == 0xC0: program = body[i]
                i += 1
            else:
                i += 2
        if notes: tracks.append({"name": name, "program": program or 0, "notes": sorted(notes)})
    return {"tracks": tracks, "tempos": sorted(tempos) or [(0, 120)], "meter": meter}


# ---------------------------------------------------------------- sounds

def cache_dir():
    if sys.platform == "darwin": base = os.path.expanduser("~/Library/Caches")
    else: base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "rendernote")


def soundfont():
    """MuseScore General, fetched once into the cache. None if it can't be had."""
    d = cache_dir()
    path = os.path.join(d, SOUNDFONT)
    if not os.path.exists(path):
        os.makedirs(d, exist_ok=True)
        print(f"Fetching the MuseScore General sounds (40 MB, once) into {d}", flush=True)
        try:
            for name in (SOUNDFONT_LICENSE, SOUNDFONT):
                urllib.request.urlretrieve(SOUNDFONT_URL + name, os.path.join(d, name) + ".part")
                os.replace(os.path.join(d, name) + ".part", os.path.join(d, name))
        except OSError as e:
            print(f"Couldn't fetch the sounds ({e}); the page will use a plain synth sound.")
            return None
    return path


def samples(programs):
    """{program: [zone...]} with each zone's audio as base64, for the page's sampler."""
    path = soundfont()
    if not path: return {}, ""
    sf, out = SoundFont(path), {}
    for prog in sorted(set(programs)):
        zones = sf.program(prog)
        out[prog] = [{"lo": z["lo"], "hi": z["hi"], "root": z["root"], "tune": z["tune"], "rate": z["rate"],
                      "loop": z["loop"], "format": "ogg" if sf.compressed else "pcm16",
                      "audio": base64.b64encode(z["audio"]).decode()} for z in zones]
    lic = os.path.join(cache_dir(), SOUNDFONT_LICENSE)
    return out, open(lic).read() if os.path.exists(lic) else ""


# ---------------------------------------------------------------- the page

def title_of(score):
    m = re.search(r'\btitle\s*=\s*"([^"]*)"', open(score).read())
    return m.group(1) if m else os.path.splitext(os.path.basename(score))[0]


def file_name(text):
    """A title as a file name with no spaces: "Jingle Bells" -> "Jingle-Bells"."""
    return re.sub(r"[^\w.]+", "-", text).strip("-")


def version_line(score):
    stamp = datetime.datetime.now().strftime("%-d %b %Y, %H:%M")
    try:
        commit = subprocess.run(["git", "log", "-1", "--format=%h", "--", os.path.basename(score)],
                                cwd=os.path.dirname(os.path.abspath(score)), capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", os.path.basename(score)],
                               cwd=os.path.dirname(os.path.abspath(score)), capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = dirty = ""
    return f"Built {stamp}" + (f" from commit {commit}" + (" with changes" if dirty else "") if commit else "")


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def build(score, out=None, files=False):
    score = os.path.abspath(score)
    title = title_of(score)
    base = file_name(title)
    out = out or os.path.join(os.path.dirname(score), base + ".html")
    with tempfile.TemporaryDirectory() as work:
        full = engrave(score, work, "score", backend="svg")
        svg = open(full + ".svg").read()
        parts = list(dict.fromkeys(re.findall(r'data-part="([^"]*)"', svg)))
        views = {("Score", "wide"): clean_svg(svg),
                 ("Score", "narrow"): clean_svg(open(engrave(score, work, "score-narrow", backend="svg", narrow=True) + ".svg").read())}
        pdfs = {f"{base}.pdf": b64(engrave(score, work, "print") + ".pdf")}
        for i, part in enumerate(parts):
            for layout in ("wide", "narrow"):
                views[(part, layout)] = clean_svg(open(engrave(score, work, f"view{i}-{layout}", part, "shrink", "svg",
                                                               narrow=layout == "narrow") + ".svg").read())
            pdfs[f"{base}-{file_name(part)}.pdf"] = b64(engrave(score, work, f"part{i}", part, "remove") + ".pdf")
        midi_path = engrave(score, work, "midi", mode="midi") + ".midi"
        midi = read_midi(midi_path)
        # tracks come in staff order; name them after the parts
        for i, t in enumerate(midi["tracks"]):
            t["name"] = parts[i] if i < len(parts) else t["name"] or f"Part {i + 1}"
        sounds, sound_licence = samples([t["program"] for t in midi["tracks"]])
        data = {"title": title, "parts": [t["name"] for t in midi["tracks"]], "views": list(dict.fromkeys(v for v, _ in views)),
                "midi": midi, "sounds": {str(k): v for k, v in sounds.items()},
                "files": {name: data for name, data in pdfs.items()} | {f"{base}.mid": b64(midi_path)},
                "version": version_line(score), "build": datetime.datetime.now().isoformat(timespec="seconds")}
        if files:
            for name, content in data["files"].items():
                open(os.path.join(os.path.dirname(out), name), "wb").write(base64.b64decode(content))
    page = open(os.path.join(HERE, "page.html")).read()
    svgs = "\n".join(f'<div class="view" data-view="{html.escape(name)}" data-layout="{layout}" hidden>{s}</div>'
                     for (name, layout), s in views.items())
    licences = sound_licence + "\n\n" if sounds else ""
    page = (page.replace("{{TITLE}}", html.escape(title))
                .replace("{{VIEWS}}", svgs)
                .replace("{{LICENCES}}", html.escape(licences + open(os.path.join(HERE, "..", "LICENSE")).read()
                                                      if os.path.exists(os.path.join(HERE, "..", "LICENSE")) else licences))
                .replace("{{PLAYER}}", open(os.path.join(HERE, "player.js")).read())
                .replace("{{DATA}}", json.dumps(data, separators=(",", ":")).replace("</", "<\\/")))
    open(out, "w").write(page)
    return out
