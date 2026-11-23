"""Libellés fixes du HUD de conduite (banque couleur 0x0D8860 / mono 0x0CE000, redessin sur place).
Fond = couleur majoritaire de la grille d'origine, encre = 2e couleur (ou forcée)."""
from hud import Libelle, COULEUR, MONO
from gfx import texte, lignes_utiles, colle
from collections import Counter


def rect(im, x0, y0, x1, y1, c):
    for y in range(y0, y1):
        for x in range(x0, x1):
            im[y][x] = c


def pose(im, s, pol, x, haut, encre, align='g', w=None):
    bm, L, _ = texte(s, pol)
    top = lignes_utiles(texte('H', pol)[0])[0]
    if w is not None:
        if L > w:
            raise ValueError('%r : %d px > %d' % (s, L, w))
        x = x + (w - L) // 2 if align == 'c' else x
    colle(im, bm, x, haut - top, encre)
    return L


def simple(lab, s, pol, haut, banque, rom, encre=None, x=None):
    """Efface tout (fond) et écrit s centré (ou à x)."""
    im = lab.image(rom, banque)
    c = Counter(v for r in im for v in r).most_common()
    fond, ink = c[0][0], (encre if encre is not None else c[1][0])
    W = len(im[0])
    rect(im, 0, 0, W, len(im), fond)
    if x is None:
        pose(im, s, pol, 0, haut, ink, 'c', W)
    else:
        pose(im, s, pol, x, haut, ink)
    lab.ecrit(rom, banque, im)


def applique(rom):
    import hud, struct
    hud.MIROIR = bytes(rom)
    hud.FIXES = set(struct.unpack_from('<H', rom, 0x00A41E + 3 * i)[0] for i in range(380))
    hud.MANQUES = []
    import mono_hud, m_hudmsg
    directes = [(0x011AD8 + 36 * k, 2, 6) for k in range(8)]          # libellés « Passage à », « Arrêt à »...
    cartes = directes + m_hudmsg.connues(rom) + [(q, 2, 9) for q, a, b in m_hudmsg.G9] + [(q, 2, 8) for q, a, b in m_hudmsg.G8]
    hud.PAIRES = mono_hud.table_ids(rom, cartes)[0]
    hud.PAIRES.update({0x224: 0x382, 0x225: 0x383, 0x226: 0x384})       # 切 (relevé à l'écran en mono)
    _applique(rom)
    print('HUD mono : %d tuiles sans jumelle mono' % sum(hud.MANQUES))
    hud.MIROIR = None


def _applique(rom):
    for banque in (COULEUR, MONO):
        if banque == COULEUR:                          # hors carte fixe : ids mono différents (à faire)
            simple(Libelle([[0xF6 + i for i in range(7)]]), 'PASSAGE PRÉVU', 'mini', 2, banque, rom)
            simple(Libelle([[0xFD + i for i in range(7)]]), 'ARRIVÉE PRÉVUE', 'mini', 2, banque, rom)
        simple(Libelle([[0x17 + i for i in range(5)]]), 'HEURE', 'mini', 2, banque, rom, x=1)
        # TEMPS (持ち時間) : 2 rangées irrégulières ; texte dans la 2e rangée
        lab = Libelle([[0x0E, 0x0F, 0x0F, 0x10, None, None], [0x11 + i for i in range(6)]])
        im = lab.image(rom, banque)
        c = Counter(v for r in im[8:] for v in r).most_common()
        fond, ink = c[0][0], c[1][0]
        rect(im, 0, 0, 32, 8, fond)
        rect(im, 0, 8, 48, 16, fond)
        pose(im, 'TEMPS', 'sb', 0, 9, ink, 'c', 48)
        lab.ecrit(rom, banque, im)
        # « s » (秒) 2x2, aligné sur le bas des gros chiffres
        lab = Libelle([[0x1C, 0x1D], [0x1E, 0x1F]])
        im = lab.image(rom, banque)
        c = Counter(v for r in im for v in r).most_common()
        fond, ink = c[0][0], c[1][0]
        rect(im, 0, 0, 16, 16, fond)
        bm, L, _ = texte('s', 'L')
        a, b = lignes_utiles(bm)
        colle(im, bm[a:b + 1], (16 - L) // 2, 14 - (b - a), ink)
        lab.ecrit(rom, banque, im)
        if banque != COULEUR:                          # suite : hors carte fixe (mono à faire)
            continue
        # [Passage] à : cadre (couleur du cadre d'origine) + texte
        lab = Libelle([[0x3A + i for i in range(6)], [0x40 + i for i in range(6)]])
        im = lab.image(rom, banque)
        c = Counter(v for r in im for v in r).most_common()
        cadre = Counter(v for r in im[2:14] for v in r[2:20]).most_common()
        fond = Counter(v for r in im for v in r[36:]).most_common(1)[0][0]
        boite = cadre[0][0]
        ink_b = [k for k, _ in cadre if k != boite][0]
        ink = [k for k, _ in Counter(v for r in im for v in r[36:]).most_common() if k != fond][0]
        rect(im, 0, 0, 48, 16, fond)
        rect(im, 0, 1, 37, 15, boite)
        pose(im, 'Passage', 'sm', 0, 4, ink_b, 'c', 37)
        pose(im, 'à', 'sm', 40, 4, ink)
        lab.ecrit(rom, banque, im)
        # Arrêt à (停止位置あと)
        simple(Libelle([[0x46 + i for i in range(6)], [0x4C + i for i in range(6)]]), 'Arrêt à', 'sb', 5, banque,
               rom)
    signaux(rom)
    jauge(rom)
    coupe(rom)
    penalites(rom)
    repetiteur(rom)
    affluence(rom)


def lignes(lab, rom, banque, textes, pol='sm', fond=1, encre=3):
    """Efface la grille (fond) et écrit plusieurs lignes centrées ; textes = [(texte, haut_capitales)]."""
    im = lab.image(rom, banque)
    W, H = len(im[0]), len(im)
    rect(im, 0, 0, W, H, fond)
    for s, haut in textes:
        p = pol
        if texte(s, p)[1] > W:
            p = 'mini'
        pose(im, s, p, 0, haut if p != 'mini' else haut - 2, encre, 'c', W)
    lab.ecrit(rom, banque, im)


def signaux(rom):
    for banque in (COULEUR,):            # mono : ids différents (à faire)
        g = lambda a, n: Libelle([[a + 5 * r + i for i in range(5)] for r in range(n)])
        # 進行信号 / 停止信号 partagent « 信号 » (0x27D-0x27E / 0x282-0x283) : partie commune vide
        lignes(Libelle([[0x27D, 0x27E], [0x282, 0x283]]), rom, banque, [])
        lignes(Libelle([[0x27A, 0x27B, 0x27C], [0x27F, 0x280, 0x281]]), rom, banque,
               [('VOIE', 2), ('LIBRE', 10)], pol='mini')
        lignes(Libelle([[0x2AC, 0x2AD, 0x2AE], [0x2AF, 0x2B0, 0x2B1]]), rom, banque, [('ARRÊT', 6)], pol='mini')
        lignes(g(0x284, 2), rom, banque, [('VOIE LIBRE', 2), ('MAX', 10)], pol='mini')
        # 減速 / 注意 / 警戒 (0x28E..0x2AB, tuiles partagées) : redessinés par m_hudmsg.messages
        lignes(g(0x2C1, 2), rom, banque, [('Répétiteur', 5)])


def jauge(rom):
    """Jauge des crans (haut gauche) : 非常 -> URG., 解除 -> LIBRE (encre 3 effacée -> fond 1, barres gardées)."""
    for banque in (COULEUR,):            # mono : ids différents (à faire)
        for g, mot in (([[0x219, 0x21A, 0x21B], [0x21C, 0x21D, 0x21E]], 'URG.'),
                       ([[0x23B, 0x23C, 0x23D], [0x23E, 0x23F, 0x240]], 'LIBRE')):
            lab = Libelle(g)
            im = lab.image(rom, banque)
            for y in range(6, 16):
                for x in range(24):
                    if im[y][x] == 3:
                        im[y][x] = 1
            bm, L, _ = texte(mot, 'mini')
            colle(im, bm, (24 - L) // 2, 7, 3, contour=1)
            lab.ecrit(rom, banque, im)


def coupe(rom):
    """« 切 » (cran neutre, sous l'indicateur de cran) -> « N » : tuiles 0x225-0x226 + dernière ligne de 0x224."""
    for banque in (COULEUR,):            # mono : ids différents (à faire)
        lab = Libelle([[None, 0x224], [0x225, 0x226]])
        im = lab.image(rom, banque)
        for x in range(9, 16):
            im[7][x] = 1
        rect(im, 0, 8, 16, 16, 1)
        pose(im, 'N', 'sb', 0, 8, 3, 'c', 16)
        lab.ecrit(rom, banque, im)


def penalites(rom):
    """Lignes « 減点 N 秒 » (cartes 2x6 0x013FFE..) : morceaux partagés redessinés sur place -> « pén. N s »."""
    def morceau(g, mot, encre, contour, align='c'):
        for banque in (COULEUR,):            # mono : ids différents (à faire)
            lab = Libelle(g)
            im = lab.image(rom, banque)
            W = len(im[0])
            rect(im, 0, 0, W, 16, 0)
            bm, L, _ = texte(mot, 'sb')
            a, b = lignes_utiles(bm)
            x = (W - L) // 2 if align == 'c' else 1
            colle(im, bm[a:b + 1], x, 2, encre, contour=contour)
            lab.ecrit(rom, banque, im)
    for g in ([[0x50F, 0x510, 0x511], [0x515, 0x516, 0x517]], [[0x503, 0x504, 0x505], [0x509, 0x50A, 0x50B]]):
        morceau(g, 'pén.', 3, 2)
    morceau([[0x513, 0x514], [0x519, 0x51A]], 's', 2, 3, align='g')
    morceau([[0x508], [0x50E]], 's', 2, 3, align='g')
    # style C (減点20秒 / 減点50秒) : même dessin que A/B
    morceau([[0x522, 0x523, 0x524], [0x528, 0x529, 0x52A]], 'pén.', 3, 2)
    morceau([[0x527], [0x52D]], 's', 2, 3, align='g')
    for t in (0x526, 0x52C):
        for banque in (COULEUR,):            # mono : ids différents (à faire)
            fond = 0
            lab = Libelle([[t]])
            im = lab.image(rom, banque)
            for r in im:
                for x in range(2, 8):
                    r[x] = fond
            lab.ecrit(rom, banque, im)
    # deux chiffres : la 2e tuile de chiffres contient le début de 秒 (x >= 2) -> effacé
    import struct
    vus = set()
    for p in range(0x013FFE, 0x0143CA, 36):
        ids = [struct.unpack_from('<H', rom, p + 3 * i)[0] for i in range(12)]
        if ids[5] == 0x508 and ids[0] == 0x503:
            for t in (ids[4], ids[10]):
                if t in vus:
                    continue
                vus.add(t)
                for banque in (COULEUR,):            # mono : ids différents (à faire)
                    lab = Libelle([[t]])
                    im = lab.image(rom, banque)
                    for r in im:
                        for x in range(2, 8):
                            r[x] = 0
                    lab.ecrit(rom, banque, im)


def repetiteur(rom):
    """Dessin du signal répétiteur : étiquette « 進行 » (0x2BB-0x2C0, lignes 4-14) -> « LIBRE »."""
    for banque in (COULEUR,):            # mono : ids différents (à faire)
        lab = Libelle([[0x2BB, 0x2BC, 0x2BD], [0x2BE, 0x2BF, 0x2C0]])
        im = lab.image(rom, banque)
        rect(im, 2, 4, 24, 15, 1)
        bm, L, _ = texte('LIBRE', 'mini')
        colle(im, bm, 2 + (22 - L) // 2, 5, 3)
        lab.ecrit(rom, banque, im)


def affluence(rom):
    """Message de conduite du mode Original « 乗車率 N% » : libellé 2x6 -> « Affluence » (sur place).
    Couleur : tuiles 0x0414CC, carte 0x041460 ; mono : tuiles 0x041748, carte 0x0416DC."""
    import struct
    for base, carte_p in ((0x0414CC, 0x041460), (0x041748, 0x0416DC)):
        g = [[struct.unpack_from('<H', rom, carte_p + 3 * (6 * r + c))[0] for c in range(6)] for r in range(2)]
        lab = Libelle(g)
        im = lab.image(rom, base)
        rect(im, 0, 0, 48, 16, 1)
        pol = 'sb' if texte('Affluence', 'sb')[1] <= 47 else 'sm'
        pose(im, 'Affluence', pol, 0, 4, 3, 'c', 48)
        lab.ecrit(rom, base, im)
