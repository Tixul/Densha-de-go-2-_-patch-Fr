"""Annonce du mode Original (heure, 乗車率, 天候) : glyphes 24 px en « lignes images » ; tuile VRAM t <- ROM
0x0379E1 + 16*t (jeu 0x037A01 copié en VRAM 0x002). Mots météo : blocs 6x3 dès 0x038B83 (+288 par mot).
Couleur seulement (mono non localisé). Redessin SUR PLACE (identifiants propres à ces lignes ; 0x033 partagé
entre 乗車率 et 天候 -> laissé vide des deux côtés)."""
from collections import Counter
from hud import Libelle
from gfx import texte, lignes_utiles, colle

B = 0x0379E1


def _fond_encre(im):
    W, H = len(im[0]), len(im)
    bord = Counter([im[0][x] for x in range(W)] + [im[H - 1][x] for x in range(W)]
                   + [im[y][0] for y in range(H)] + [im[y][W - 1] for y in range(H)]).most_common(1)[0][0]
    autres = [k for k, _ in Counter(v for r in im for v in r).most_common() if k != bord]
    return bord, (autres[0] if autres else 3)


def ecrit(rom, banque, grille, s, pol='L', x=None, vide=()):
    lab = Libelle(grille)
    im = lab.image(rom, banque)
    fond, ink = _fond_encre(im)
    W, H = len(im[0]), len(im)
    for r in im:
        for i in range(W):
            r[i] = fond
    if s:
        bm, L, _ = texte(s, pol)
        a, b = lignes_utiles(bm)
        bm = bm[a:b + 1]
        x0 = (W - L) // 2 if x is None else x
        colle(im, bm, x0, (H - len(bm)) // 2, ink)
    for (vx, vy) in vide:                      # cases à laisser vides (tuile partagée)
        for yy in range(8 * vy, 8 * vy + 8):
            for xx in range(8 * vx, 8 * vx + 8):
                im[yy][xx] = fond
    lab.ecrit(rom, banque, im)


def _trad_mono(rom):
    """id couleur -> id mono, par comparaison case à case des écrans (0x0373CF / 0x038561, 20x19)."""
    import struct
    t = {}
    for i in range(380):
        a = struct.unpack_from('<H', rom, 0x0373CF + 3 * i)[0]
        b = struct.unpack_from('<H', rom, 0x038561 + 3 * i)[0]
        t.setdefault(a, b)
    return t


def applique(rom, mono=False):
    global B, METEO
    if mono:
        tr = _trad_mono(rom)
        _ec = ecrit
        Bm = 0x038B73

        import struct as _st
        chiffres = set(_st.unpack_from('<H', rom, 0x0389D5 + 3 * i)[0] for i in range(11 * 6))  # chiffres 0-9 + vide

        def ecrit_m(rom_, banque, grille, s_, **k):
            g = [[(tr.get(x) if x is not None and tr.get(x) not in chiffres else None) for x in r] for r in grille]
            _ec(rom_, Bm, g, s_, **k)
        globals()['ecrit'] = ecrit_m
        try:
            _applique_ecran(rom)
        finally:
            globals()['ecrit'] = _ec
        B, METEO = 0x038B73, 0x038A9B
        try:
            meteo(rom, partage={0x025} | chiffres)        # 0x02D : morceau de 雨 ET du chiffre 1
        finally:
            B, METEO = 0x0379E1, 0x037909
        return
    _applique_ecran(rom)
    meteo(rom)


def _applique_ecran(rom):
    ecrit(rom, B, [[0x002, 0x003, 0x004], [0x008, 0x009, 0x00A], [0x00F, 0x010, 0x011]], 'h')
    ecrit(rom, B, [[0x005, 0x006, 0x007, None], [0x00B, 0x00C, 0x00D, 0x00E], [0x012, 0x013, 0x014, None]], '')
    ecrit(rom, B, [list(range(0x015, 0x01E)), list(range(0x021, 0x02A)), list(range(0x02D, 0x036))],
          'Affluence', x=0, vide=[(6, 2)])
    ecrit(rom, B, [list(range(0x039, 0x03F)), [0x033] + list(range(0x03F, 0x044)), list(range(0x044, 0x04A))],
          'Météo', pol='mb', x=9, vide=[(0, 1)])


METEO = 0x037909          # cartes 6x3 (id u16 + attr), indice (0x59F2) x 54
MOTS = ['Beau', 'Nuageux', 'Pluie', 'Neige']


def meteo(rom, partage=None):
    """Mots météo : cases partagées (0x001 vide, 0x008 de 時, 0x033, 0x053 du chiffre 1) redirigées vers 0x001,
    puis les tuiles propres au mot sont redessinées sur place (texte confiné aux cases propres)."""
    import struct
    from gfx import texte, lignes_utiles, colle
    partage = partage or {0x001, 0x008, 0x033, 0x053}
    for k, mot in enumerate(MOTS):
        p = METEO + 54 * k
        g = []
        for r in range(3):
            ligne = []
            for c in range(6):
                o = p + 3 * (6 * r + c)
                t = struct.unpack_from('<H', rom, o)[0]
                if t in partage:
                    rom[o], rom[o + 1] = 0x01, 0x00
                    ligne.append(None)
                else:
                    ligne.append(t)
            g.append(ligne)
        lab = Libelle(g)
        im = lab.image(rom, B)
        libres = [(c, r) for r in range(3) for c in range(6) if g[r][c] is not None]
        from collections import Counter as _C
        cnt = _C(im[y][x] for (c, r) in libres for y in range(8 * r, 8 * r + 8) for x in range(8 * c, 8 * c + 8))
        tri = [v for v, _ in cnt.most_common()]
        fond = 1 if 1 in tri else tri[0]               # fond de l'écran (tuile 0x001)
        ink = [v for v in tri if v != fond][0]
        for (c, r) in libres:
            for y in range(8 * r, 8 * r + 8):
                for x in range(8 * c, 8 * c + 8):
                    im[y][x] = fond
        cols = [c for c in range(6) if all(g[r][c] is not None for r in range(3))]
        xa, xb = 8 * cols[0], 8 * cols[-1] + 8
        for pol in ('mb', 'sb', 'sm'):
            bm, L, _ = texte(mot, pol)
            if L <= xb - xa:
                break
        a, b = lignes_utiles(bm)
        bm = bm[a:b + 1]
        colle(im, bm, xa + (xb - xa - L) // 2, (24 - len(bm)) // 2, ink)
        lab.ecrit(rom, B, im)
