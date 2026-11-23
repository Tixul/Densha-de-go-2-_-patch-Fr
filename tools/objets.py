"""Remplacement d'objets sprites (moteur 0x0068C0 / tuiles 0x13ECF0, mode couleur).
Les nouvelles tuiles vont dans la zone libre 0x1F0000-0x1FBFFF (id = (adr - 0x13ECF0)/16, dédoublonnées), les
nouvelles listes dans 0x1FC000-0x1FFFFF ; le pointeur de l'objet est redirigé. L'ancienne liste reste (inutilisée).

    A = Allocateur(rom)
    remplace(rom, A, 0x12C, [Ligne('Dépassement !', 'sb', 2, 3, attr=1, y=-8)])"""
import struct
from collections import Counter
from gfx import texte, lignes_utiles, tuile_octets
import sprites
from sprites import liste


def tuile(rom, tid):
    return sprites.tuile(rom, tid, sprites.BASE)


def fichier(p):
    return p - 0x200000 if p < 0x800000 else p - 0x800000 + 0x200000


def mode(mono):
    """Couleur : table 0x0068C0, tuiles 0x13ECF0, trou 0x1EF2E0 ; mono : table 0x3BE000, tuiles 0x0D4800, pas de trou."""
    global ZT0, ZT1
    if mono:
        sprites.TABLE, sprites.BASE = 0x3BE000, 0x0D4800
        ZT0 = ZT1 = 0
    else:
        sprites.TABLE, sprites.BASE = 0x0068C0, 0x13ECF0
        ZT0, ZT1 = 0x1EF2E0, 0x1F0000


def debut(rom):
    """À appeler une fois par fabrication : les listes repartent au début de la zone libre."""
    global PROCHAIN
    PROCHAIN = ZL0

# ⛔ 0x1F0000-0x1FFFFF = SAUVEGARDE flash du jeu (classements, kilométrage) : NE JAMAIS Y ÉCRIRE.
ZT0, ZT1 = 0x1EF2E0, 0x1F0000        # seul trou vide à portée des identifiants (base 0x13ECF0)
ZL0, ZL1 = 0x3F6300, 0x400000        # listes : 2e puce (vide), adresse CPU = 0x800000 + (fichier - 0x200000)


PROCHAIN = None


def cpu(a):
    return 0x200000 + a if a < 0x200000 else 0x800000 + (a - 0x200000)


class Allocateur:
    def __init__(self, rom, recup=()):
        """recup = identifiants de tuiles récupérables (tuiles des objets remplacés, non partagées)."""
        self.rom = rom
        global PROCHAIN
        for a, b in ((PROCHAIN, ZL1),):
            if any(rom[x] != 0xFF for x in range(a, b)):
                raise RuntimeError('zone libre occupée en %06X-%06X' % (a, b))
        self.ids = list(recup) + (list(range((ZT0 - sprites.BASE) // 16, (ZT1 - sprites.BASE) // 16)) if ZT1 else [])
        self.l = PROCHAIN
        self.vus = {}

    def tuile(self, b):
        if b in self.vus:
            return self.vus[b]
        if not self.ids:
            raise RuntimeError('plus de tuiles sprites disponibles')
        t = self.ids.pop(0)
        a = sprites.BASE + 16 * t
        self.rom[a:a + 16] = b
        self.vus[b] = t
        return t

    def liste(self, ent):
        b = b''.join(struct.pack('<HbbB', i, dx, dy, a) for i, dx, dy, a in ent) + bytes(5)
        if self.l + len(b) > ZL1:
            raise RuntimeError('zone des listes pleine')
        global PROCHAIN
        a = self.l
        self.rom[a:a + len(b)] = b
        self.l += len(b)
        PROCHAIN = self.l
        return a


def recuperables(rom, remplaces):
    """Identifiants (base du mode courant) dont TOUS les utilisateurs, couleur ET mono confondus (adresses
    physiques), sont des objets remplacés du mode courant. Une tuile partagée couleur/mono n'est jamais recyclée."""
    from sprites import objets as _objs
    mode_mono = sprites.TABLE == 0x3BE000
    usage = {}
    for mono in (False, True):
        tab, base = (0x3BE000, 0x0D4800) if mono else (0x0068C0, 0x13ECF0)
        sv = sprites.TABLE
        sprites.TABLE = tab
        try:
            obs = _objs(rom)
        finally:
            sprites.TABLE = sv
        for n, p in obs:
            for e in liste(rom, p):
                usage.setdefault(base + 16 * e[0], set()).add((mono, n))
    rem = set((mode_mono, n) for n in remplaces)
    return sorted((a - sprites.BASE) // 16 for a, u in usage.items() if u <= rem and (a - sprites.BASE) % 16 == 0
                  and 0 <= (a - sprites.BASE) // 16 < 0x10000)


class Ligne:
    def __init__(self, s, pol='sb', encre=3, contour=2, attr=0, y=-8, x=None, align='c', fond=None, boite=None):
        """y = haut des capitales (px, relatif à l'ancre de l'objet) ; x = gauche (sinon centré sur 0) ;
        boite = (x0, y0, x1, y1, couleur) rectangle plein dessiné sous le texte (même attr)."""
        self.s, self.pol, self.encre, self.contour, self.attr = s, pol, encre, contour, attr
        self.y, self.x, self.align, self.boite = y, x, align, boite


def compose(l):
    """-> dict {(x, y): indice} des pixels de la ligne, en coordonnées objet."""
    px = {}
    if l.boite:
        x0, y0, x1, y1, c = l.boite
        for y in range(y0, y1):
            for x in range(x0, x1):
                px[(x, y)] = c
    lignes = l.s.split('\n')
    for k, s in enumerate(lignes):
        bm, L, _ = texte(s, l.pol)
        haut = lignes_utiles(texte('H', l.pol)[0])[0]
        a, b = lignes_utiles(bm)
        pas = (lignes_utiles(texte('H', l.pol)[0])[1] - haut) + 4
        x0 = (l.x if l.x is not None else -(L // 2)) if l.align == 'c' else l.x
        y0 = l.y - haut + k * pas
        if l.contour is not None:
            for y in range(len(bm)):
                for x in range(L):
                    if bm[y][x]:
                        for dy in (-1, 0, 1):
                            for dx in (-1, 0, 1):
                                px[(x0 + x + dx, y0 + y + dy)] = l.contour
        for y in range(len(bm)):
            for x in range(L):
                if bm[y][x]:
                    px[(x0 + x, y0 + y)] = l.encre
    return px


def remplace(rom, A, n, lignes, verbeux=True, marge=0):
    p0 = fichier(struct.unpack_from('<I', rom, sprites.TABLE + 4 * (n - 0x100))[0])
    orig = liste(rom, p0)
    ox0, ox1 = min(e[1] for e in orig), max(e[1] for e in orig) + 8
    oy0 = min(e[2] for e in orig)
    ent = []
    for l in lignes:
        px = compose(l)
        xs = [x for x, y in px]
        if min(xs) < ox0 - marge or max(xs) >= ox1 + marge:
            raise ValueError('objet %03X : %r déborde (%d..%d hors %d..%d)' % (n, l.s, min(xs), max(xs), ox0, ox1))
        cases = {}
        for (x, y), v in px.items():                   # grille calée sur le coin de l'objet d'origine
            cases.setdefault(((x - ox0) // 8, (y - oy0) // 8), {})[((x - ox0) % 8, (y - oy0) % 8)] = v
        for (cx, cy), d in sorted(cases.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            t = [[d.get((x, y), 0) for x in range(8)] for y in range(8)]
            ent.append((A.tuile(tuile_octets(t)), ox0 + 8 * cx, oy0 + 8 * cy, l.attr))
    a = A.liste(ent)
    struct.pack_into('<I', rom, sprites.TABLE + 4 * (n - 0x100), cpu(a))
    if verbeux:
        print('objet %03X : %d tuiles (origine %d)' % (n, len(ent), len(orig)))
    return len(ent)


def attrs(rom, n):
    """Attributs par bande (dy) de l'objet d'origine."""
    p = fichier(struct.unpack_from('<I', rom, sprites.TABLE + 4 * (n - 0x100))[0])
    c = {}
    for tid, dx, dy, a, _ in liste(rom, p):
        c.setdefault(dy, Counter())[a] += 1
    return {dy: v.most_common(1)[0][0] for dy, v in c.items()}


def recompose(rom, A, n, garde, extra, src, verbeux=True):
    """Objet n : garde les entrées d'origine pour lesquelles garde(dx, dy, attr) est vrai (dessin recopié) et
    ajoute extra = [(pixels 8x8, dx, dy, attr)]."""
    p0 = fichier(struct.unpack_from('<I', src, sprites.TABLE + 4 * (n - 0x100))[0])
    ent = []
    for tid, dx, dy, at, _ in liste(src, p0):
        if garde(dx, dy, at):
            ent.append((A.tuile(bytes(src[sprites.BASE + 16 * tid:sprites.BASE + 16 * tid + 16])), dx, dy, at & 0x3F))
    for t, dx, dy, at in extra:
        ent.append((A.tuile(tuile_octets(t)), dx, dy, at & 0x3F))
    struct.pack_into('<I', rom, sprites.TABLE + 4 * (n - 0x100), cpu(A.liste(ent)))
    if verbeux:
        print('objet %03X recomposé : %d sprites' % (n, len(ent)))
    return len(ent)


def retouche(rom, A, n, s, rect=(3, 2, 44, 14), encre=3, pol='mini', verbeux=True, ytexte=7, efface=None,
             src=None, recolore=(), extra=()):
    """src = ROM d'origine (lecture du dessin) : OBLIGATOIRE dès que des tuiles sont recyclées."""
    src = src if src is not None else rom
    """Garde le dessin de l'objet (cadre...), efface l'encre `encre` dans rect (chaque pixel reprend la couleur
    majoritaire de sa ligne dans rect) et écrit s centré ; mêmes cases et attributs que l'original."""
    from gfx import colle
    p0 = struct.unpack_from('<I', src, sprites.TABLE + 4 * (n - 0x100))[0]
    p0 = p0 - 0x200000 if p0 < 0x800000 else p0 - 0x800000 + 0x200000
    orig = liste(src, p0)
    x0, y0 = min(e[1] for e in orig), min(e[2] for e in orig)
    W, H = max(e[1] for e in orig) + 8 - x0, max(e[2] for e in orig) + 8 - y0
    im = [[0] * W for _ in range(H)]
    for tid, dx, dy, a, _ in orig:
        t = tuile(src, tid)
        if a & 0x80: t = [r[::-1] for r in t]
        if a & 0x40: t = t[::-1]
        for r in range(8):
            for x in range(8):
                im[dy - y0 + r][dx - x0 + x] = t[r][x]
    for (ra, rb, rc, rd), de, vers in recolore:      # ex. kanji 特急 effacé du bloc rouge (HAKUTAKA)
        for y in range(rb, rd):
            for x in range(ra, rc):
                if im[y][x] == de:
                    im[y][x] = vers
    a, b, c, d = rect
    for y in range(b, d):
        maj = Counter(v for v in im[y][a:c] if v != encre).most_common(1)
        for x in range(a, c):
            if im[y][x] in (efface or (encre,)):
                im[y][x] = 0 if efface else (maj[0][0] if maj else 0)
    bm, L, _ = texte(s, pol)
    if L > c - a:
        raise ValueError('objet %03X : %r %d px > %d' % (n, s, L, c - a))
    colle(im, bm, a + (c - a - L) // 2, ytexte, encre)        # capitales lignes 9-13, sous la séparation
    ent = []
    for tid, dx, dy, at, _ in orig:
        t = [im[dy - y0 + r][dx - x0:dx - x0 + 8] for r in range(8)]
        ent.append((A.tuile(tuile_octets(t)), dx, dy, at & 0x3F))
    for t, dx, dy, at in extra:                        # cases ajoutées (ex. DENSHA du titre)
        ent.append((A.tuile(tuile_octets(t)), dx, dy, at & 0x3F))
    struct.pack_into('<I', rom, sprites.TABLE + 4 * (n - 0x100), cpu(A.liste(ent)))
    if verbeux:
        print('objet %03X retouché : %r' % (n, s))
