"""Ré-encodeur d'un « module » d'écrans fixes : UN jeu de tuiles (copié en VRAM tel quel) + des tilemaps
3 octets/case (lo, hi, d ; entrée = lo | (hi|d)<<8 : bits 0-8 tuile, 9-12 palette, 14 V, 15 H).

    mod = Module(rom, TUILES, NTUILES, [(adr_map, L, H), ...])
    img = mod.image(i)                  # indices 0-3 de la carte i (liste de lignes)
    mod.zone(i, x, y, l, h, pixels)     # nouveau contenu (8l x 8h indices) pour une zone de cases
    mod.applique()                      # alloue les tuiles, écrit tuiles + cartes dans rom (bytearray)

Règle d'allocation : une tuile dont TOUTES les utilisations (toutes cartes du module) sont dans des zones
redessinées est libérée ; chaque case redessinée prend une tuile existante identique (dédoublonnage) ou une
tuile libérée. Erreur explicite si les tuiles libres manquent (+ `reserve` = tuiles libres hors usage connues)."""
from gfx import tuile_lit, tuile_octets


class Module:
    def __init__(self, rom, tuiles, ntuiles, cartes, reserve=(), etrangeres=None, proteges=()):
        """etrangeres = (adresse, premier_id) : tuiles d'un autre module restées en VRAM au-delà de N
        (lues pour le rendu, jamais modifiées)."""
        self.rom, self.T, self.N = rom, tuiles, ntuiles
        self.etr = etrangeres
        self.proteges = set(proteges)
        self.cartes = list(cartes)
        self.reserve = list(reserve)
        self.zones = {}          # (carte, x, y) -> pixels 8x8
        self.pals = {}           # (carte, x, y) -> palette forcée (0-15)
        self.px = [tuile_lit(rom, tuiles + 16 * t) for t in range(ntuiles)]

    def case(self, i, x, y):
        a, L, H = self.cartes[i]
        o = a + 3 * (y * L + x)
        lo, hi, d = self.rom[o], self.rom[o + 1], self.rom[o + 2]
        return o, lo | (hi | d) << 8

    def tuile_case(self, i, x, y):
        _, e = self.case(i, x, y)
        n = e & 0x1FF
        if n < self.N:
            t = [r[:] for r in self.px[n]]
        elif self.etr:
            t = tuile_lit(self.rom, self.etr[0] + 16 * (n - self.etr[1]))
        else:
            t = [[0] * 8 for _ in range(8)]
        if e & 0x8000:
            t = [r[::-1] for r in t]
        if e & 0x4000:
            t = t[::-1]
        return t

    def image(self, i):
        a, L, H = self.cartes[i]
        im = [[0] * (8 * L) for _ in range(8 * H)]
        for y in range(H):
            for x in range(L):
                t = self.tuile_case(i, x, y)
                for r in range(8):
                    im[8 * y + r][8 * x:8 * x + 8] = t[r]
        return im

    def zone(self, i, x0, y0, l, h, pix, pal=None):
        for y in range(h):
            for x in range(l):
                self.zones[(i, x0 + x, y0 + y)] = [pix[8 * y + r][8 * x:8 * x + 8] for r in range(8)]
                if pal is not None:
                    self.pals[(i, x0 + x, y0 + y)] = pal

    def palette(self, i, x, y):
        return (self.case(i, x, y)[1] >> 9) & 0xF

    def applique(self, verbeux=True):
        usages = {}
        for i, (a, L, H) in enumerate(self.cartes):
            for y in range(H):
                for x in range(L):
                    _, e = self.case(i, x, y)
                    usages.setdefault(e & 0x1FF, set()).add((i, x, y))
        libres = sorted(t for t, u in usages.items() if t < self.N and t not in self.proteges
                        and all(k in self.zones for k in u))
        libres += [t for t in self.reserve if t not in usages]
        pris = set(t for t in usages if t not in libres)
        contenu = {}                       # octets -> tuile (parmi celles gardées)
        for t in sorted(pris):
            if t < self.N:
                contenu.setdefault(tuile_octets(self.px[t]), t)
        pool = list(libres)
        nouveaux, ecritures = {}, []
        for (i, x, y), p in sorted(self.zones.items()):        # 1) tout calculer (rien n'est écrit)
            b = tuile_octets(p)
            if b not in contenu:
                if not pool:
                    raise RuntimeError('tuiles libres épuisées (%d libérées)' % len(libres))
                t = pool.pop(0)
                contenu[b] = t
                nouveaux[t] = b
            t = contenu[b]
            o, e = self.case(i, x, y)
            hi = self.rom[o + 1] & 0x3E | (t >> 8) & 1       # palette gardée, retournements effacés
            d = self.rom[o + 2] & 0x3E & ~1
            if (i, x, y) in self.pals:
                hi = self.pals[(i, x, y)] << 1 | (t >> 8) & 1
                d = 0
            ecritures.append((o, t & 0xFF, hi, d))
        for o, lo, hi, d in ecritures:                         # 2) puis tout écrire
            self.rom[o], self.rom[o + 1], self.rom[o + 2] = lo, hi, d
        for t, b in nouveaux.items():
            self.rom[self.T + 16 * t:self.T + 16 * t + 16] = b
        if verbeux:
            print('module %06X : %d cases redessinées, %d tuiles libérées, %d utilisées, %d restent'
                  % (self.T, len(self.zones), len(libres), len(nouveaux), len(pool)))
        return len(pool)
