"""Messages du HUD (cartes id u16 + attr, banque couleur 0x0D8860 / mono 0x0CE000), redessinés SUR PLACE.
Registre global : un identifiant partagé entre deux messages doit recevoir le même contenu (sinon erreur).
Romanisation des gares : Hepburn sans macrons (usage courant en France : Tokyo, Omagari...)."""
import struct
from collections import Counter
from gfx import tuile_lit, tuile_octets, texte, lignes_utiles, colle
from hud import COULEUR, MONO

# --- messages par gare : (adresse carte couleur, D, E, ligne 1, ligne 2) ---
G9 = [(0x0163DE, 'ARRÊT À', 'SHIN-HANAMAKI'),      # stage bonus (parcours 0x12, Tohoku Shinkansen)
      (0x01644A, 'PASSAGE À', 'YOTSUGOYA'), (0x016480, 'PASSAGE À', 'WADA'), (0x0164B6, 'PASSAGE À', 'OBARINO'),
      (0x0164EC, 'PASSAGE À', 'UGO-SAKAI'), (0x016522, 'PASSAGE À', 'MINEKICHIKAWA'),
      (0x016558, 'PASSAGE À', 'KARIWANO'), (0x01658E, 'PASSAGE À', 'JINGUJI'), (0x0165C4, 'ARRÊT À', 'OMAGARI'),
      (0x016630, 'PASSAGE À', 'KUROI'), (0x016666, 'ARRÊT À', 'SAIGATA'), (0x0166D2, 'ARRÊT À', 'KUBIKI'),
      (0x01673E, 'PASSAGE À', 'OIKE-IKOI-NO-MORI'), (0x016774, 'ARRÊT À', 'URAGAWARA'),
      (0x0167E0, 'PASSAGE À', 'MUSHIGAWA-OSUGI'), (0x016816, 'ARRÊT À', 'HOKUHOKU-OSHIMA'),
      (0x016882, 'ARRÊT À', 'MATSUDAI'), (0x0168EE, 'ARRÊT À', 'TOKAMACHI'), (0x01695A, 'PASSAGE À', 'KUROI'),
      (0x016990, 'PASSAGE À', 'SAIGATA'), (0x0169C6, 'PASSAGE À', 'KUBIKI'),
      (0x0169FC, 'PASSAGE À', 'OIKE-IKOI-NO-MORI'), (0x016A32, 'PASSAGE À', 'URAGAWARA'),
      (0x016A68, 'PASSAGE À', 'MUSHIGAWA-OSUGI'), (0x016A9E, 'PASSAGE À', 'HOKUHOKU-OSHIMA'),
      (0x016AD4, 'PASSAGE À', 'MATSUDAI'), (0x016B0A, 'ARRÊT À', 'TOKAMACHI'), (0x016B76, 'PASSAGE À', 'SHINZA'),
      (0x016BAC, 'PASSAGE À', 'MISASHIMA'), (0x016BE2, 'PASSAGE À', 'UONUMA-KYURYO'),
      (0x016C18, 'ARRÊT À', 'MUIKAMACHI')]
G8 = [(0x016C7E, 'ARRÊT À', 'TAMACHI'), (0x016CDE, 'PASSAGE À', 'HAMAMATSUCHO'), (0x016D0E, 'PASSAGE À', 'SHIMBASHI'),
      (0x016D3E, 'PASSAGE À', 'YURAKUCHO'), (0x016D6E, 'ARRÊT À', 'TOKYO'), (0x016DCE, 'PASSAGE À', 'KANDA'),
      (0x016DFE, 'ARRÊT À', 'AKIHABARA'), (0x016E5E, 'PASSAGE À', 'OKACHIMACHI'), (0x016E8E, 'ARRÊT À', 'UENO')]
BANNIERES = [(0x00A89E, 'AKITA KOMACHI E3'), (0x00A8C2, 'TOHOKU YAMABIKO-KOMACHI'),
             (0x00A8E6, 'HOKUHOKU RAPIDE HK100'), (0x00A90A, 'KEIHIN-TOHOKU RAPIDE 209'),
             (0x00A92E, 'HOKUHOKU HAKUTAKA 681')]


def carte(rom, p, D, E):
    return [[(struct.unpack_from('<H', rom, p + 3 * (y * E + x))[0], rom[p + 3 * (y * E + x) + 2])
             for x in range(E)] for y in range(D)]


def _flip(px, a):
    if a & 0x80:
        px = [r[::-1] for r in px]
    if a & 0x40:
        px = px[::-1]
    return px


class Registre:
    """Ré-encodage d'un ensemble de cartes de messages : les tuiles utilisées UNIQUEMENT par les cartes
    redessinées (parmi toutes les cartes connues `connues`) sont libérées et réallouées (dédoublonnage)."""
    def __init__(self, rom, banque, connues=()):
        self.rom, self.b = rom, banque
        self.adr = (lambda q: q)
        if banque == MONO:
            import mono_hud
            self.adr = mono_hud.mono_adr
            connues = [(self.adr(q), D, E) for q, D, E in connues if self.adr(q) is not None]
        self.connues = list(connues)
        self.zones = {}                        # p -> (D, E, image)

    def image(self, grille):
        D, E = len(grille), len(grille[0])
        im = [[0] * (8 * E) for _ in range(8 * D)]
        for y, r in enumerate(grille):
            for x, (t, a) in enumerate(r):
                px = _flip(tuile_lit(self.rom, self.b + 16 * t), a)
                for k in range(8):
                    im[8 * y + k][8 * x:8 * x + 8] = px[k]
        return im

    def ecrit(self, p, D, E, im, nom):
        self.zones[p] = (D, E, im, nom)

    def applique(self):
        usage = {}
        for p, D, E in self.connues + [(p, z[0], z[1]) for p, z in self.zones.items()]:
            for y, r in enumerate(carte(self.rom, p, D, E)):
                for x, (t, a) in enumerate(r):
                    usage.setdefault(t, set()).add((p, x, y))
        redess = set((p, x, y) for p, (D, E, im, nom) in self.zones.items() for y in range(D) for x in range(E))
        # ids < 0x300 = libellés fixes du HUD (carte de conduite non répertoriée ici) : jamais libérés
        if self.b == MONO:
            import hud
            fixes = set(struct.unpack_from('<H', self.rom, 0x00A976 + 3 * i)[0] for i in range(380))
            prot = fixes | hud.ECRITS_MONO
            libres = sorted(t for t, u in usage.items() if u <= redess and t not in prot)
        else:
            libres = sorted(t for t, u in usage.items() if u <= redess and t >= 0x300)
        garde = {}
        for t, u in usage.items():
            if t not in libres:
                garde.setdefault(tuile_octets(tuile_lit(self.rom, self.b + 16 * t)), t)
        pool, nouveaux = list(libres), {}
        for p, (D, E, im, nom) in sorted(self.zones.items()):
            for y in range(D):
                for x in range(E):
                    b = tuile_octets([im[8 * y + k][8 * x:8 * x + 8] for k in range(8)])
                    if b not in garde:
                        if not pool:
                            raise RuntimeError('HUD : tuiles libres épuisées (%d libérées)' % len(libres))
                        t = pool.pop(0)
                        garde[b] = t
                        nouveaux[t] = b
                    t = garde[b]
                    o = p + 3 * (y * E + x)
                    self.rom[o], self.rom[o + 1] = t & 0xFF, t >> 8
                    self.rom[o + 2] &= 0x3F                       # retournements effacés, palette gardée
        for t, b in nouveaux.items():
            self.rom[self.b + 16 * t:self.b + 16 * t + 16] = b
        print('HUD %06X : %d cartes, %d tuiles libérées, %d utilisées' % (self.b, len(self.zones), len(libres),
                                                                       len(nouveaux)))


def deux_lignes(R, p, D, E, l1, l2, nom, fond=0, encre=3, contour=1):
    p = R.adr(p)
    g = carte(R.rom, p, D, E)
    im = R.image(g)
    W = 8 * E
    for r in im:
        for x in range(W):
            r[x] = fond
    for k, s in enumerate((l1, l2)):
        bm, L, _ = texte(s, 'mini')
        if L + 2 > W:
            raise ValueError('%s : %r %d px > %d' % (nom, s, L + 2, W))
        colle(im, bm, (W - L) // 2, 8 * k, encre, contour=contour)
    R.ecrit(p, D, E, im, nom)


def une_ligne(R, p, D, E, s, nom, pol='mini', haut=2):
    p = R.adr(p)
    g = carte(R.rom, p, D, E)
    im = R.image(g)
    c = Counter(v for r in im for v in r).most_common()
    fond, ink = c[0][0], c[1][0]
    W = 8 * E
    for r in im:
        for x in range(W):
            r[x] = fond
    bm, L, _ = texte(s, pol)
    if L > W:
        raise ValueError('%s : %r %d px > %d' % (nom, s, L, W))
    colle(im, bm, (W - L) // 2, haut - lignes_utiles(texte('H', pol)[0])[0], ink)
    R.ecrit(p, D, E, im, nom)


def connues(rom):
    """Toutes les cartes de messages repérées (tables de hudmsg.py), pour le calcul des tuiles libres."""
    import hudmsg
    out = []
    for tab, D, E, n in hudmsg.TABLES:
        p0 = struct.unpack_from('<I', rom, tab)[0]
        if 0x200000 <= p0 < 0x240000:
            ptrs = [struct.unpack_from('<I', rom, tab + 4 * k)[0] - 0x200000 for k in range(n or 1)]
            ptrs = [q for q in ptrs if 0 <= q < 0x40000]
        else:
            ptrs = [tab + 3 * D * E * k for k in range(n or 1)]
        for q in ptrs:
            ids = hudmsg.carte(rom, q, D, E)
            if not hudmsg.valide(ids):
                break
            out.append((q, D, E))
    return out


def applique(rom):
    for banque in (COULEUR, MONO):       # mono : cartes via mono_hud.mono_adr
        import hudmsg
        R = Registre(rom, banque, connues(rom))
        for p, l1, l2 in G9:
            deux_lignes(R, p, 2, 9, l1, l2, 'gare %06X' % p)
        for p, l1, l2 in G8:
            deux_lignes(R, p, 2, 8, l1, l2, 'gare %06X' % p)
        for p, s in BANNIERES:
            une_ligne(R, p, 1, 12, s, 'bannière %06X' % p)
        messages(R)
        R.applique()


def choisit(cands, pols, W):
    for c in cands:
        for pol in pols:
            bm, L, _ = texte(c, pol)
            if L <= W:
                return c, pol, bm, L
    raise ValueError('rien ne tient en %d px : %r' % (W, cands))


def pilule(R, p, D, E, cands, nom, pols=('sm', 'mini'), marge=2):
    """Message dans un cadre : corps = couleur majoritaire (non 0) du bord ; texte = les autres couleurs de
    l'intérieur (2 couleurs : la plus fréquente = contour, l'autre = encre ; 1 couleur : encre seule)."""
    p = R.adr(p)
    g = carte(R.rom, p, D, E)
    im = R.image(g)
    W, H = 8 * E, 8 * D
    bord = Counter(v for y, r in enumerate(im) for x, v in enumerate(r)
                   if (y < 3 or y >= H - 3 or x < 3 or x >= W - 3) and v)
    corps = bord.most_common(1)[0][0] if bord else 0
    inter = [k for k, _ in Counter(v for r in im[marge:H - marge] for v in r[marge:W - marge]
                                   if v != corps).most_common()]
    contour = inter[0] if len(inter) > 1 else None
    ink = inter[1] if len(inter) > 1 else (inter[0] if inter else 3)
    m = 2 if contour is not None else 0
    s, pol, bm, L = choisit(cands, pols, W - 2 * marge - 2 - m)
    for y in range(marge, H - marge):
        for x in range(marge, W - marge):
            if im[y][x] != corps or True:
                im[y][x] = corps
    a, b = lignes_utiles(bm)
    colle(im, bm[a:b + 1], (W - L) // 2, (H - (b - a + 1)) // 2, ink, contour=contour)
    R.ecrit(p, D, E, im, nom)


def panneau(R, p, D, E, s, nom, ligne=None):
    """Panneau : seule la rangée du bas (libellé) est réécrite en petites capitales."""
    p = R.adr(p)
    g = carte(R.rom, p, D, E)
    im = R.image(g)
    W = 8 * E
    y0 = 8 * (D - 1) if ligne is None else 8 * ligne
    c = Counter(v for r in im[y0:y0 + 8] for v in r).most_common()
    fond, ink = c[0][0], c[1][0]
    for y in range(y0, y0 + 8):
        for x in range(W):
            im[y][x] = fond
    bm, L, _ = texte(s, 'mini')
    if L > W:
        raise ValueError('%s : %r trop large' % (nom, s))
    colle(im, bm, (W - L) // 2, y0, ink)
    R.ecrit(p, D, E, im, nom)


INCIDENTS = [['ATS activé'], ['Frein brutal'], ['Panneau ignoré'], ['Arrêt manqué'],
             ['Survitesse'], ['Voyant ignoré'], ['Avancez le train', 'Avancez !'], ['Choc heurtoir', 'Heurtoir !']]
PANNEAUX = {1: 'LIMITE', 2: 'LIMITE', 3: 'LIMITE', 4: 'LIMITE', 5: 'LIMITE', 6: 'REPRISE', 7: 'PALIER',
            8: 'RAMPE', 9: 'PENTE', 10: 'LIMITE', 11: 'LIMITE', 12: 'LIMITE', 13: 'LIMITE', 14: 'LIMITE',
            15: 'LIMITE', 16: 'LIMITE', 17: 'LIMITE', 18: 'LIMITE', 19: 'SIFFLER'}


def zone(R, p, D, E, rect, lignes, fond, encre, contour=None):
    """Repeint rect (fond) et écrit des lignes [(texte, police, haut_capitales)] centrées dans rect."""
    p = R.adr(p)
    g = carte(R.rom, p, D, E)
    im = R.image(g)
    a, b, c, d = rect
    for y in range(b, d):
        for x in range(a, c):
            im[y][x] = fond
    for s, pol, haut in lignes:
        bm, L, _ = texte(s, pol)
        m = 2 if contour is not None else 0
        if L + m > c - a:
            raise ValueError('%06X : %r %d px > %d' % (p, s, L + m, c - a))
        top = lignes_utiles(texte('H', pol)[0])[0]
        colle(im, bm, a + (c - a - L) // 2, haut - top, encre, contour=contour)
    R.ecrit(p, D, E, im, '%06X' % p)


def messages(R):
    # Panneaux de signal 減速 / 注意 / 警戒信号 (cartes 3x5 0x010999 / 0x010A11 / 0x010A89, mono -0x438) : en JP,
    # 信号 et des morceaux de « 速度..km/h » sont des tuiles PARTAGÉES -> chaque panneau redessiné en entier
    # (nouvelles tuiles), pas sur place.
    for p, nom, v in ((0x010999, 'Ralentir', '70'), (0x010A11, 'Attention', '45'), (0x010A89, 'Vigilance', '25')):
        zone(R, p, 3, 5, (0, 0, 40, 24), [(nom, 'sm', 2), (v + ' km/h', 'sm', 13)], 1, 3)
    zone(R, 0x01392A, 5, 12, (3, 5, 93, 34), [('Ligne terminée', 'mb', 9), ('FÉLICITATIONS', 'sb', 24)], 1, 3, 2)
    zone(R, 0x015EC9, 3, 8, (14, 3, 58, 18), [('TEMPS FINI', 'mini', 9)], 1, 3)
    zone(R, 0x013598, 4, 4, (2, 1, 30, 11), [('SIGNAL', 'mini', 4)], 3, 1)
    for k, c in enumerate(INCIDENTS):
        pilule(R, 0x013CFE + 48 * k, 2, 8, c, 'incident %d' % k)
    pilule(R, 0x013E1E, 2, 8, INCIDENTS[6], 'avancez bis')
    pilule(R, 0x013E1E + 48, 2, 8, INCIDENTS[7], 'heurtoir bis')
    for k, s in PANNEAUX.items():
        panneau(R, 0x012C38 + 60 * k, 4, 5, s, 'panneau %d' % k)
    pilule(R, 0x011AD8 + 36 * 2, 2, 6, ['Zone OK'], 'zone ok', marge=1)
    pilule(R, 0x011AD8 + 36 * 3, 2, 6, ['Dépassé'], 'dépassé', marge=1)
    pilule(R, 0x000CA0, 2, 8, ['Reprise'], 'reprise', pols=('sb', 'sm', 'mini'), marge=1)
    pilule(R, 0x000BEC, 3, 10, ['Continuer ?'], 'continuer', pols=('L', 'mb', 'sb', 'sm'), marge=1)
    pilule(R, 0x00C622, 2, 6, ['Mode PRO', 'PRO'], 'pro', pols=('sb', 'sm', 'mini'), marge=1)
    pilule(R, 0x00F23C, 3, 5, ['Bien !', 'Bien'], 'good', pols=('mb', 'sb', 'sm', 'mini'), marge=1)
    pilule(R, 0x00F287, 3, 5, ["À l'heure"], 'teitsu', pols=('sb', 'sm', 'mini'), marge=1)
    pilule(R, 0x00F269, 2, 5, ['Bonus'], 'bonus', pols=('sb', 'sm', 'mini'), marge=1)
    pilule(R, 0x011F10, 2, 10, ['Section neutre'], 'section', pols=('sb', 'sm', 'mini'), marge=1)
