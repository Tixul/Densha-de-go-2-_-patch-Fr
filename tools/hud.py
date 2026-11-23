"""Libellés du HUD de conduite : tuiles de la banque adressée par identifiant (couleur 0x0D8860, mono 0x0CE000),
redessinées SUR PLACE (mêmes identifiants). Une grille = lignes d'identifiants (None = case non touchée).
    lab = Libelle([[0xF6, 0xF7, ...]])
    img = lab.image(rom, banque)       # indices 0-3
    lab.ecrit(rom, banque, img)        # vérifie qu'un identifiant répété reçoit le même contenu"""
from gfx import tuile_lit, tuile_octets
from collections import Counter

COULEUR, MONO = 0x0D8860, 0x0CE000
MIROIR = None        # ROM d'origine : si défini, toute écriture couleur est recopiée en mono (hors carte fixe)
FIXES = set()
MANQUES = []
PAIRES = {}             # id couleur -> id mono (paires de cartes, mono_hud.table_ids)
ECRITS_MONO = set()      # ids mono redessinés sur place par vers_mono (à protéger ensuite)


class Libelle:
    def __init__(self, grille):
        self.g = grille

    def image(self, rom, banque):
        H, W = len(self.g), max(len(r) for r in self.g)
        im = [[0] * (8 * W) for _ in range(8 * H)]
        for y, r in enumerate(self.g):
            for x, t in enumerate(r):
                if t is None:
                    continue
                px = tuile_lit(rom, banque + 16 * t)
                for k in range(8):
                    im[8 * y + k][8 * x:8 * x + 8] = px[k]
        return im

    def couleurs(self, rom, banque):
        c = Counter(v for r in self.image(rom, banque) for v in r)
        tri = [k for k, _ in c.most_common()]
        return tri[0], (tri[1] if len(tri) > 1 else 3)

    def ecrit(self, rom, banque, im):
        vu = {}
        for y, r in enumerate(self.g):
            for x, t in enumerate(r):
                if t is None:
                    continue
                b = tuile_octets([im[8 * y + k][8 * x:8 * x + 8] for k in range(8)])
                if t in vu and vu[t] != b:
                    raise ValueError('identifiant %04X répété avec deux contenus' % t)
                vu[t] = b
        for t, b in vu.items():
            rom[banque + 16 * t:banque + 16 * t + 16] = b
        if banque == COULEUR and MIROIR is not None:
            g = [[t if (t is not None and t not in FIXES) else None for t in r] for r in self.g]
            vers_mono(MIROIR, rom, g, im, MANQUES)


def _tuile(rom, a):
    return [[(rom[a + 2 * r] | rom[a + 2 * r + 1] << 8) >> (14 - 2 * x) & 3 for x in range(8)] for r in range(8)]


def jumelle_mono(src, t):
    if t in PAIRES:                                       # paire de cartes connue : sûr
        m = PAIRES[t]
        pc, pm = _tuile(src, COULEUR + 16 * t), _tuile(src, MONO + 16 * m)
        perm = {}
        for y in range(8):
            for x in range(8):
                perm.setdefault(pc[y][x], pm[y][x])
        return m, perm
    return _jumelle_contenu(src, t)


def _jumelle_contenu(src, t):
    """Identifiant mono de la tuile couleur t (ROM d'origine src) : contenu identique, sinon même forme
    (pixels non nuls) ; None si absent ou ambigu. Renvoie (id_mono, permutation couleur->mono)."""
    c = bytes(src[COULEUR + 16 * t:COULEUR + 16 * t + 16])
    if len(set(c)) <= 1:
        return None
    hits, i = [], src.find(c, MONO)
    while 0 <= i < COULEUR:
        if (i - MONO) % 16 == 0:
            hits.append((i - MONO) // 16)
        i = src.find(c, i + 1)
    if len(hits) == 1:
        return hits[0], {0: 0, 1: 1, 2: 2, 3: 3}
    if hits:
        return None
    pc = _tuile(src, COULEUR + 16 * t)
    forme = [[v != 0 for v in r] for r in pc]
    cands = []
    for m in range((COULEUR - MONO) // 16):
        pm = _tuile(src, MONO + 16 * m)
        if all((pm[y][x] != 0) == forme[y][x] for y in range(8) for x in range(8)):
            cands.append((m, pm))
            if len(cands) > 1:
                return None
    if len(cands) != 1:
        return None
    m, pm = cands[0]
    perm = {}
    for y in range(8):
        for x in range(8):
            if perm.setdefault(pc[y][x], pm[y][x]) != pm[y][x]:
                return None
    return m, perm


def vers_mono(src, rom, grille, im, journal=None):
    """Recopie en banque mono les pixels redessinés (im) d'une grille couleur, via jumelle_mono."""
    manq = 0
    for y, r in enumerate(grille):
        for x, t in enumerate(r):
            if t is None:
                continue
            j = jumelle_mono(src, t)
            if j is None:
                manq += 1
                continue
            m, perm = j
            px = [[perm.get(v, v) for v in im[8 * y + k][8 * x:8 * x + 8]] for k in range(8)]
            rom[MONO + 16 * m:MONO + 16 * m + 16] = tuile_octets(px)
            ECRITS_MONO.add(m)
    if journal is not None:
        journal.append(manq)
    return manq
