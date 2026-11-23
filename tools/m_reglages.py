"""Module « Réglages » (ゲーム設定) : tuiles 0x081E66 (422, couleur), cartes plan 2 0x08B1DF (9 écrans 20x19),
plan 1 0x08B197 (écrans 1-4 : 0x08579A), pièces 8x2 0x08B344 (valeurs). Fond 1, encre 3.
    import m_reglages ; m_reglages.applique(rom)      (rom = bytearray)"""
import struct
from module import Module
from gfx import texte, colle, lignes_utiles

TUILES, NT = 0x081E66, 422


def cartes(rom, mono=False):
    """Couleur (flag 0x40E2 != 0) : écrans 0-8, pièces 0x08B2A8 ; mono : écrans 9-17, pièces 0x08B344."""
    k = 9 if mono else 0
    c = [(struct.unpack_from('<I', rom, 0x8B1DF + 4 * (i + k))[0] - 0x200000, 20, 19) for i in range(9)]
    c.append((struct.unpack_from('<I', rom, 0x8B197 + 4 * (1 + k))[0] - 0x200000, 20, 19))
    vus = []
    for i in range(26):
        p = struct.unpack_from('<I', rom, (0x8B344 if mono else 0x8B2A8) + 6 * i)[0] - 0x200000
        if p not in vus:
            vus.append(p)
    return c, vus


def ecrire(M, i, img, x, y, w, h, s, pol='m', encre=3, fond=1, align='g', haut=None, contour=None):
    """Efface le rectangle (pixels) puis écrit s ; haut = y (pixel) du HAUT DES CAPITALES (calage sur une rangée
    de tuiles pour économiser les tuiles) ; sinon centré verticalement. Enregistre les cases touchées."""
    from collections import Counter
    cpt = Counter()
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if img[yy][xx] == encre:
                cpt[M.palette(i, xx // 8, yy // 8)] += 1
            img[yy][xx] = fond
    pal = cpt.most_common(1)[0][0] if cpt else None
    bm, L, _ = texte(s, pol)
    marge = 1 if contour is not None else 0
    if L + 2 * marge > w:
        raise ValueError('%r : %d px > %d' % (s, L + 2 * marge, w))
    x0 = x + marge if align == 'g' else (x + (w - L) // 2 if align == 'c' else x + w - L - marge)
    if haut is not None:
        y0 = haut - lignes_utiles(texte('H', pol)[0])[0]
    else:
        a, b = lignes_utiles(bm)
        bm = bm[a:b + 1]
        y0 = y + (h - len(bm)) // 2
    a, b = lignes_utiles(bm)
    if y0 + b + marge >= len(img) or y0 + a - marge < 0:
        raise ValueError('%r déborde de la carte' % s)
    for yy in range(y0 + a, y0 + b + 1):                 # efface aussi sous les lignes d'encre débordantes
        for xx in range(x, x + w):
            img[yy][xx] = fond
    colle(img, bm, x0, y0, encre, contour=contour)
    y1 = max(y + h - 1, y0 + b + marge)
    y = min(y, y0 + a - marge)
    cx0, cy0, cx1, cy1 = x // 8, y // 8, (x + w - 1) // 8, y1 // 8
    M.zone(i, cx0, cy0, cx1 - cx0 + 1, cy1 - cy0 + 1,
           [r[8 * cx0:8 * cx1 + 8] for r in img[8 * cy0:8 * cy1 + 8]], pal)


TITRES = {0: 'Réglages', 1: 'Commandes', 2: 'Commandes', 3: 'Commandes', 4: 'Commandes', 5: 'Difficulté',
          6: 'Tachymètre', 7: 'Télémètre', 8: 'Réinitialiser'}
ITEMS = ['Commandes', 'Difficulté', 'Tachymètre', 'Télémètre', 'Réinitialiser']


def applique(rom, mono=False):
    c, pieces = cartes(rom, mono)
    base = len(c)
    for p in pieces:
        c.append((p, 8, 2))
    M = Module(rom, 0x0838C6 if mono else TUILES, NT, c)
    imgs = [M.image(i) for i in range(len(c))]
    for i in range(9):
        ecrire(M, i, imgs[i], 16 if i == 0 else 8, 9, 80, 13, TITRES[i], haut=12)                       # titre
        im = imgs[i]                                                          # barre d'aide
        ecrire(M, i, im, 30, 134, 29, 11, 'Choisir', 'sm')
        ecrire(M, i, im, 71, 134, 28, 11, 'Valider', 'sm')
        ecrire(M, i, im, 112, 134, 47, 11, 'Annuler', 'sm')
    for k, s in enumerate(ITEMS):                                             # liste principale
        ecrire(M, 0, imgs[0], 16, 33 + 16 * k, 70, 13, s, haut=40 + 16 * k)
    for k, s in enumerate(['Facile', 'Normal', 'Difficile', 'Extrême']):
        ecrire(M, 5, imgs[5], 16, 33 + 16 * k, 70, 13, s, haut=40 + 16 * k)
    for k, s in enumerate(['Caché', 'Affiché']):
        ecrire(M, 6, imgs[6], 16, 33 + 16 * k, 70, 13, s, haut=40 + 16 * k)
    for k, s in enumerate(['Caché', 'En cm', 'En m']):
        ecrire(M, 7, imgs[7], 16, 33 + 16 * k, 70, 13, s, haut=40 + 16 * k)
    ecrire(M, 8, imgs[8], 16, 33, 130, 13, 'Effacer les données ?', haut=40)
    for k, s in enumerate(['Non', 'Oui']):
        ecrire(M, 8, imgs[8], 16, 58 + 16 * k, 60, 13, s, haut=64 + 16 * k)
    noms = ['1 manette A', '1 manette B', '2 manettes A', '2 manettes B', 'Facile', 'Normal', 'Difficile', 'Extrême',
            'Caché', 'Affiché', 'En cm', 'En m']
    for k, s in enumerate(noms):
        i = base + k
        ecrire(M, i, imgs[i], 0, 1, 64, 13, s, haut=8)
    schemas(M, imgs, ecrire)
    return M.applique()


# Schémas de commandes (écrans 1-4) : (écran, x, y, l, h, texte) ; y = haut des capitales ; police 9 px.
SOUS_TITRES = {1: '1 manette A', 2: '1 manette B', 3: '2 manettes A', 4: '2 manettes B'}
ETIQ = []
for _e in (1, 2, 3, 4):
    ETIQ.append((_e, 8, 40, 62, 9, 'Manipulateur'))
for _e in (1, 2):
    ETIQ += [(_e, 11, 57, 27, 9, 'Urg.'), (_e, 11, 75, 27, 9, 'Neutre'), (_e, 11, 93, 27, 9, 'Tract.'),
             (_e, 130, 48, 26, 8, 'Mode'), (_e, 130, 56, 26, 8, 'PRO')]
for _e in (3, 4):
    ETIQ += [(_e, 11, 57, 27, 9, 'Neutre'), (_e, 11, 83, 27, 9, 'Tract.'),
             (_e, 123, 13, 27, 9, 'Urg.'), (_e, 123, 38, 27, 9, 'Libre'), (_e, 110, 53, 44, 9, 'Frein')]
ETIQ += [(1, 41, 110, 30, 8, 'Frein'), (1, 41, 119, 30, 8, 'urg.'), (1, 77, 110, 30, 9, 'Neutre'),
         (1, 103, 63, 28, 9, 'Klaxon'),
         (2, 41, 110, 30, 9, 'Klaxon'), (2, 77, 110, 30, 9, 'Neutre'),
         (2, 104, 51, 27, 9, 'Frein'), (2, 104, 61, 27, 9, 'urg.'),
         (3, 41, 110, 30, 9, 'Klaxon'), (3, 77, 110, 30, 8, 'Mode'), (3, 77, 119, 30, 8, 'PRO'),
         (4, 41, 110, 30, 9, 'Klaxon'), (4, 77, 110, 30, 9, 'Neutre')]


def schemas(M, imgs, ecr):
    for e, t in SOUS_TITRES.items():
        ecr(M, e, imgs[e], 16, 24, 90, 12, t, haut=24)
    for e, x, y, w, h, t in ETIQ:
        ecr(M, e, imgs[e], x, y, w, h, t, 'sm', align='c', haut=y)
