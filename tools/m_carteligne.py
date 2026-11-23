"""Carte de ligne (avant chaque segment) : tuiles 0x039F1E (385, couleur), cartes 18x9 3 o/case (table 0x03D5FE).
Noms de gares en capitales `mini` TOURNÉES de 90° (lecture de haut en bas) dans les colonnes des noms japonais.
Couleur seulement. Les tuiles libérées sont celles des seules cases de noms (lignes >= 3)."""
import struct
from collections import Counter
from module import Module
import mini

T, NT = 0x039F1E, 385
NOMS = {
    0x03D9F6: ['AKITA', 'YOTSUGOYA', 'WADA', 'OBARINO', 'UGO-SAKAI', 'MINEKICHIKAWA', 'KARIWANO', 'JINGUJI',
               'OMAGARI'],
    0x03DBDC: ['NAOETSU', 'KUROI', 'SAIGATA', 'KUBIKI', 'OIKE-IKOI-NO-MORI', 'URAGAWARA', 'MUSHIGAWA-OSUGI',
               'HOKUHOKU-OSHIMA', 'MATSUDAI', 'TOKAMACHI'],
    0x03DDC2: ['TOKAMACHI', 'SHINZA', 'MISASHIMA', 'UONUMA-KYURYO', 'MUIKAMACHI'],
    0x03EB0C: ['SHINAGAWA', 'TAMACHI'],
    0x03ECF2: ['TAMACHI', 'HAMAMATSUCHO', 'SHIMBASHI', 'YURAKUCHO', 'TOKYO'],
    0x03EED8: ['TOKYO', 'KANDA', 'AKIHABARA'],
    0x03F0BE: ['AKIHABARA', 'OKACHIMACHI', 'UENO'],
    0x03DFA8: ['NAOETSU', 'KUROI', 'SAIGATA'],
    0x03E18E: ['SAIGATA', 'KUBIKI'],
    0x03E374: ['KUBIKI', 'OIKE-IKOI-NO-MORI', 'URAGAWARA'],
    0x03E55A: ['URAGAWARA', 'MUSHIGAWA-OSUGI', 'HOKUHOKU-OSHIMA'],
    0x03E740: ['HOKUHOKU-OSHIMA', 'MATSUDAI'],
    0x03E926: ['MATSUDAI', 'TOKAMACHI'],
}
ABREGE = {'OIKE-IKOI-NO-MORI': ['OIKE-IKOI', 'OIKE'], 'MUSHIGAWA-OSUGI': ['MUSHIGAWA'],
          'HOKUHOKU-OSHIMA': ['HK-OSHIMA', 'OSHIMA'], 'MINEKICHIKAWA': ['MINEKICHI.'],
          'UONUMA-KYURYO': ['UONUMA'], 'HAMAMATSUCHO': ['HAMAMATSU.'], 'SHIN-HANAMAKI': ['S-HANAMAKI']}


def tourne(s):
    """-> bitmap (hauteur = longueur, largeur 8) : lettres empilées, lecture de haut en bas (rotation 90° h)."""
    bm, L = mini.texte(s)
    return [[bm[7 - x][y] for x in range(8)] for y in range(L)]


def blocs(im, ligne0=17):
    """Colonnes de noms : groupes de colonnes de cases (8 px) ayant de l'encre sous la ligne ligne0."""
    W = len(im[0]) // 8
    fond = Counter(v for r in im[ligne0:] for v in r).most_common(1)[0][0]
    occ = [0 < c < W - 1 and any(im[y][x] != fond for y in range(ligne0, len(im) - 8) for x in range(8 * c, 8 * c + 8))
           for c in range(W)]
    out, c = [], 0
    while c < W:
        if occ[c]:
            d = c
            while d + 1 < W and occ[d + 1]:
                d += 1
            out.append((c, d))
            c = d + 1
        else:
            c += 1
    return out, fond


def pastilles(im, y=9):
    """Centres x des pastilles des gares (grappes de pixels != fond sur la ligne y)."""
    fond = Counter(im[4][8:-8]).most_common(1)[0][0]
    xs = [x for x in range(8, len(im[0]) - 8) if im[y][x] != fond]
    out, g = [], []
    for x in xs:
        if g and x != g[-1] + 1:
            out.append(sum(g) / len(g)); g = []
        g.append(x)
    if g:
        out.append(sum(g) / len(g))
    return out


# Parcours 0x12 (stage bonus Morioka -> Shin-Hanamaki, « ATC » / « BONUS ROUND ») : autre branche du code
# (0x239CBA couleur / 0x239D70 mono) : 54 tuiles propres, en-tête et carte fixes.
BONUS = {False: (0x03B72E, 0x03D696, 0x03F2A4), True: (0x03D29E, 0x03D76E, 0x040D38)}
NOMS_BONUS = ['MORIOKA', 'SHIN-HANAMAKI']


def applique(rom, mono=False):
    noms = NOMS
    tuiles, tete = T, 0x03D846
    if mono:                                           # tables parallèles : couleur 0x03D5FE, mono 0x03D64A
        corr = {}
        for k in range(22):
            c = struct.unpack_from('<I', rom, 0x03D5FE + 4 * k)[0] - 0x200000
            m = struct.unpack_from('<I', rom, 0x03D64A + 4 * k)[0] - 0x200000
            corr.setdefault(c, m)
        noms = {corr[p]: v for p, v in NOMS.items() if p in corr}
        tuiles, tete = 0x03BA8E, 0x03D91E
    r = carte(rom, tuiles, NT, noms, tete)
    t, e, c = BONUS[mono]
    carte(rom, t, 54, {c: NOMS_BONUS}, e, local=True)
    return r


def carte(rom, tuiles, nt, noms, tete, local=False):
    """local=True : n'efface que les colonnes des noms (le reste de la carte porte du texte latin à garder)."""
    M = Module(rom, tuiles, nt, [(p, 18, 9) for p in noms] + [(tete, 18, 4)])
    ie = M.image(len(noms))                            # en-tête : 発 / 着 -> DÉP. / ARR.
    for (xa, xb, s) in ((9, 24, 'DÉP.'), (120, 136, 'ARR.')):
        for y in range(11, 23):
            for x in range(xa, xb):
                ie[y][x] = 1
        bm, L = mini.texte(s)
        for y in range(8):
            for x in range(L):
                if bm[y][x]:
                    ie[12 + y][xa + (xb - xa - L) // 2 + x] = 3
        for cy in (1, 2):
            for cx in range(xa // 8, (xb - 1) // 8 + 1):
                M.zone(len(noms), cx, cy, 1, 1, [r[8 * cx:8 * cx + 8] for r in ie[8 * cy:8 * cy + 8]])
    for i, (p, liste_noms) in enumerate(noms.items()):
        im = M.image(i)
        cx = pastilles(im)
        if len(cx) != len(liste_noms):
            print('ATTENTION carte de ligne %06X : %d pastilles pour %d noms -> ignorée' % (p, len(cx), len(liste_noms)))
            continue
        y0, y1, xa, xb = 17, 64, 8, 136
        fond = Counter(im[y1 - 1][xa:xb]).most_common(1)[0][0]
        coul = []
        for c in cx:                                   # couleur d'origine du nom sous chaque pastille
            cnt = Counter(im[y][x] for y in range(y0, y1) for x in range(int(c) - 3, int(c) + 4)
                          if im[y][x] != fond).most_common(1)
            coul.append(cnt[0][0] if cnt else 1)
        for y in range(y0, y1):
            for x in range(xa, xb):
                if not local or y < 47 and any(abs(x - c) <= 6 for c in cx):   # « BONUS ROUND » en y 49-55
                    im[y][x] = fond
        for c, nom, e in zip(cx, liste_noms, coul):
            cands = [nom] + ABREGE.get(nom, [])
            bm = next((tourne(s) for s in cands if len(tourne(s)) <= y1 - y0 - 1), None)
            if bm is None:
                raise ValueError('carte de ligne : %s trop long' % nom)
            x0 = int(round(c)) - 4 if not local else 8 * int((c + 1) // 8) - 1   # local : encre dans UNE colonne de cases (tuiles comptées)
            for y, r in enumerate(bm):
                for x, v in enumerate(r):
                    if v:
                        im[y0 + 1 + y][x0 + x] = e
        for cy in range(2, 8):
            for cxx in range(1, 17):
                M.zone(i, cxx, cy, 1, 1, [r[8 * cxx:8 * cxx + 8] for r in im[8 * cy:8 * cy + 8]])
    return M.applique()
