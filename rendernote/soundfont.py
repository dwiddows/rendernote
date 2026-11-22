"""Read the instrument samples a score needs from a SoundFont (.sf2 or .sf3).

Only the parts Rendernote uses are read: for a General MIDI program, each
key range's sample (Ogg Vorbis in .sf3, raw PCM in .sf2), its root key and
tuning, and its loop points, so the page can hold a note as long as it lasts.
"""
import struct

GEN_KEY_RANGE, GEN_VEL_RANGE, GEN_INSTRUMENT, GEN_SAMPLE_ID = 43, 44, 41, 53
GEN_COARSE, GEN_FINE, GEN_MODES, GEN_ROOT = 51, 52, 54, 58


def _chunks(data, start, end):
    while start < end:
        cid, size = data[start:start + 4], struct.unpack("<I", data[start + 4:start + 8])[0]
        yield cid, start + 8, size
        start += 8 + size + (size & 1)


def _records(raw, fmt):
    n = struct.calcsize(fmt)
    return [struct.unpack(fmt, raw[i:i + n]) for i in range(0, len(raw) - n + 1, n)]


class SoundFont:
    def __init__(self, path):
        data = open(path, "rb").read()
        self.data, self.smpl, pdta = data, None, {}
        for cid, at, size in _chunks(data, 12, len(data)):
            if cid != b"LIST": continue
            kind = data[at:at + 4]
            for c2, a2, s2 in _chunks(data, at + 4, at + size):
                if kind == b"sdta" and c2 == b"smpl": self.smpl = (a2, s2)
                if kind == b"pdta": pdta[c2.decode()] = data[a2:a2 + s2]
        self.compressed = path.lower().endswith(".sf3")
        self.phdr = _records(pdta["phdr"], "<20sHHHIII")
        self.pbag = _records(pdta["pbag"], "<HH")
        self.pgen = _records(pdta["pgen"], "<HH")
        self.inst = _records(pdta["inst"], "<20sH")
        self.ibag = _records(pdta["ibag"], "<HH")
        self.igen = _records(pdta["igen"], "<HH")
        self.shdr = _records(pdta["shdr"], "<20sIIIIIbbHH")

    @staticmethod
    def _zones(bags, gens, first, last):
        """Generator dicts for bags[first:last]."""
        out = []
        for b in range(first, last):
            g = {}
            for op, amount in gens[bags[b][0]:bags[b + 1][0]]:
                g[op] = amount
            out.append(g)
        return out

    def program(self, program, bank=0):
        """Sample zones for a General MIDI program (0-127): a list of dicts with
        lo, hi, root, tune (cents), rate, loop (start, end in samples or None) and
        audio (Ogg bytes for .sf3, 16-bit PCM bytes for .sf2)."""
        idx = next((i for i, p in enumerate(self.phdr[:-1]) if p[1] == program and p[2] == bank), None)
        if idx is None: return []
        zones = []
        for pz in self._zones(self.pbag, self.pgen, self.phdr[idx][3], self.phdr[idx + 1][3]):
            if GEN_INSTRUMENT not in pz: continue
            ins = pz[GEN_INSTRUMENT]
            izones = self._zones(self.ibag, self.igen, self.inst[ins][1], self.inst[ins + 1][1])
            glob = izones[0] if izones and GEN_SAMPLE_ID not in izones[0] else {}
            for iz in izones:
                if GEN_SAMPLE_ID not in iz: continue
                g = {**glob, **iz}
                vel = g.get(GEN_VEL_RANGE, 127 << 8)
                if not (vel & 0xFF) <= 100 <= (vel >> 8): continue      # one velocity layer: mf
                name, start, end, ls, le, rate, opk, corr, _, _ = self.shdr[g[GEN_SAMPLE_ID]]
                kr = g.get(GEN_KEY_RANGE, 127 << 8)
                root = g.get(GEN_ROOT, 0xFFFF)
                coarse = struct.unpack("<h", struct.pack("<H", g.get(GEN_COARSE, 0)))[0]
                fine = struct.unpack("<h", struct.pack("<H", g.get(GEN_FINE, 0)))[0]
                a, n = self.smpl
                if self.compressed:                      # sf3: byte offsets of an Ogg file; loops relative to the sample
                    audio = self.data[a + start:a + end]
                    loop = (ls, le)
                else:
                    audio = self.data[a + 2 * start:a + 2 * end]
                    loop = (ls - start, le - start)
                zones.append({"lo": kr & 0xFF, "hi": kr >> 8,
                              "root": opk if root == 0xFFFF else root,
                              "tune": coarse * 100 + fine + corr, "rate": rate,
                              "loop": loop if g.get(GEN_MODES, 0) & 1 else None,
                              "audio": audio, "name": name.split(b"\0")[0].decode("latin1")})
        return zones
