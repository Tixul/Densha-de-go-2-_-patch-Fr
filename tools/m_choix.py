"""Choix du train (cartes) : tuiles 0x03110A (281, couleur) / 0x03346A (mono) ; cartes 40x19 3 o/case :
plan 1 0x02FF3A / 0x03229A (images des trains), plan 2 0x030822 / 0x032B82 (cartes : textes).
Une carte = 160 px de large (colonne gauche x0=0, droite x0=160), 48 px de haut (y0 = 0, 48, 96)."""
from collections import Counter
from module import Module
from gfx import texte, colle

CARTES = {  # (x0, y0) : (ligne, série, service, niveau, départ, arrivée)
    (0, 0): ('HOKUHOKU', 'HK100', 'RAPIDE', 'FACILE', 'NAOETSU', 'URAGAWARA'),
    (0, 48): ('AKITA', 'SÉRIE E3', 'KOMACHI', 'MOYEN', 'AKITA', 'OMAGARI'),
    (0, 96): ('KEIHIN', 'SÉRIE 209', 'RAPIDE', 'MOYEN', 'SHINAGAWA', 'UENO'),
    (160, 0): ('HOKUHOKU', 'HK100', 'RAPIDE', 'AVANCÉ', 'NAOETSU', 'MUIKAMACHI'),
    (160, 48): ('AKITA', 'SÉRIE E3', 'KOMACHI', 'EXPERT', 'AKITA', 'OMAGARI'),
    (160, 96): ('HOKUHOKU', 'SÉRIE 681', 'HAKUTAKA', 'EXPERT', 'NAOETSU', 'MUIKAMACHI'),
}
# rectangles intérieurs relatifs à la carte : (x0, y0, x1, y1) exclus
R_LIGNE, R_SERIE = (39, 7, 88, 17), (39, 17, 88, 27)
R_SERV, R_NIV = (89, 9, 121, 23), (123, 10, 150, 23)
R_DEP, R_ARR, R_DIFF = (49, 28, 80, 39), (89, 28, 121, 39), (120, 30, 153, 40)


def peint(M, i, im, x0, y0, r, s, cases):
    a, b, c, d = r[0] + x0, r[1] + y0, r[2] + x0, r[3] + y0
    cnt = Counter(im[y][x] for y in range(b, d) for x in range(a, c)).most_common()
    fond, ink = cnt[0][0], (cnt[1][0] if len(cnt) > 1 else 3)
    for y in range(b, d):
        for x in range(a, c):
            im[y][x] = fond
    bm, L, _ = texte(s, 'mini')
    if L > c - a:
        raise ValueError('choix : %r %d px > %d' % (s, L, c - a))
    yt = b + (d - b - 5) // 2 - 2                       # capitales centrées
    colle(im, bm, a + (c - a - L) // 2, yt, ink)
    for y in range(max(b, yt) // 8, (d - 1) // 8 + 1):
        for x in range(a // 8, (c - 1) // 8 + 1):
            cases.add((x, y))


def gares(M, im, x0, y0, dep, arr, cases, X0=47, X1=122, Y0=27, Y1=40):
    """Rangée départ - arrivée redessinée : cadres (haut + gauche, couleur du cadre d'origine) à la taille
    des noms, tiret entre les deux s'il reste >= 5 px."""
    a, b, c, d = X0 + x0, Y0 + y0, X1 + x0, Y1 + y0
    cadre = im[b][a + 2]                       # couleur de la bordure haute d'origine
    fond = Counter(im[y][x] for y in range(b + 1, d) for x in range(a, c)).most_common(1)[0][0]
    ink = [k for k, _ in Counter(im[y][x] for y in range(b + 1, d) for x in range(a, c)).most_common()
           if k not in (fond, cadre)] or [3]
    ink = ink[0]
    for y in range(b, d):
        for x in range(a, c):
            im[y][x] = fond
    (b1, l1, _), (b2, l2, _) = texte(dep, 'mini'), texte(arr, 'mini')
    w1, w2 = l1 + 3, l2 + 3
    gap = (c - a) - w1 - w2
    if gap < 1:
        raise ValueError('choix : %s - %s trop long (%d px)' % (dep, arr, w1 + w2))
    xs = [a, c - w2]
    for (bm, L), xb in zip(((b1, l1), (b2, l2)), xs):
        for x in range(xb, xb + L + 3):
            im[b][x] = cadre
        for y in range(b, d - 1):
            im[y][xb] = cadre
        colle(im, bm, xb + 2, b + 1, ink)
    if gap >= 5:
        xm = a + w1 + (gap - 3) // 2
        for x in range(xm, xm + 3):
            im[b + 7][x] = ink
    for y in range(b // 8, (d - 1) // 8 + 1):
        for x in range(a // 8, (c - 1) // 8 + 1):
            cases.add((x, y))


def applique(rom, mono=False):
    if mono:
        M = Module(rom, 0x03346A, 281, [(0x032B82, 40, 19), (0x03229A, 40, 19)])
    else:
        M = Module(rom, 0x03110A, 281, [(0x030822, 40, 19), (0x02FF3A, 40, 19)])
    im = M.image(0)
    cases = set()
    for (x0, y0), (lg, se, sv, nv, dp, ar) in CARTES.items():
        for r, s in ((R_LIGNE, lg), (R_SERIE, se), (R_SERV, sv), (R_NIV, nv), (R_DIFF, 'NIVEAU')):
            peint(M, 0, im, x0, y0, r, s, cases)
        gares(M, im, x0, y0, dp, ar, cases)
    for x, y in cases:
        M.zone(0, x, y, 1, 1, [row[8 * x:8 * x + 8] for row in im[8 * y:8 * y + 8]])
    return M.applique()
