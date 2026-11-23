"""HUD du jeu bonus d'attelage (après Tokamachi / Tokyo sans continuer, voir notice p.15).
Jeu de tuiles 0x05D329 (couleur) / 0x05EE87 (mono), copié en VRAM dès la tuile 0x55 : tuile VRAM v <- base_v + 16*v
avec base_v = base - 0x55*16. Mêmes identifiants en couleur et en mono. Redessin SUR PLACE (tuiles propres au bonus).
Panneau (plan 2, rangées 13-14) : 衝撃メーター / 合格範囲 / 危険 ; 持ち時間 (carte 0x061018, v = id + 0x159) ;
bannière 信越本線EF63 (carte 0x061071, v = id + 0x159)."""
import struct
from collections import Counter
from hud import Libelle
from gfx import texte, lignes_utiles, colle

BASES = (0x05D329 - 0x55 * 16, 0x05EE87 - 0x55 * 16)


def efface(im, y0, y1, x0, x1, garde=()):
    for y in range(y0, y1):
        for x in range(x0, x1):
            if im[y][x] not in garde:
                im[y][x] = 0


def carte(rom, p, L, H, off=0x159):
    return [[struct.unpack_from('<H', rom, p + 3 * (L * r + c))[0] + off for c in range(L)] for r in range(H)]


def applique(rom):
    # grand « 秒 » du compteur TEMPS (jeu 0x0607AC) = copie des tuiles HUD 0x1C-0x1F, déjà traduites (« s »)
    for k, a in enumerate((0x0608CC, 0x0608DC, 0x060A1C, 0x060A2C)):
        o = 0x0D8860 + 16 * (0x1C + k)
        rom[a:a + 16] = rom[o:o + 16]
    # « 切 » (cran neutre) : le jeu bonus charge des COPIES des tuiles HUD 0x224-0x226 (jeu 0x0D61E0 en VRAM 0x1C3..,
    # et 0x1CD530..) -> recopie des tuiles déjà traduites en « N » (couleur 0x0D8860, mono 0x0CE000 ids 0x382..)
    for k in range(3):
        rom[0x0D7E10 + 16 * k:0x0D7E20 + 16 * k] = rom[0x0D8860 + 16 * (0x224 + k):0x0D8870 + 16 * (0x224 + k)]
        rom[0x1CD530 + 16 * k:0x1CD540 + 16 * k] = rom[0x0CE000 + 16 * (0x382 + k):0x0CE010 + 16 * (0x382 + k)]
    B = BASES[0]                           # COULEUR
    if True:
        # « 衝撃メーター » : haut en rangée 13 (cases propres), corps en rangée 14
        g = [[0x0E8, 0x0E9, 0x0EA, 0x0EB, 0x0EC, None, 0x0ED, None, None], [0x0F8 + i for i in range(9)]]
        lab = Libelle(g)
        im = lab.image(rom, B)
        efface(im, 0, 16, 0, 72)
        bm, L, _ = texte('CHOC', 'sb')
        a, b = lignes_utiles(bm)
        colle(im, bm[a:b + 1], 4, 8, 2, contour=1)
        for (c, r) in ((5, 0), (7, 0), (8, 0)):            # cases vides partagées : rien dessus
            for y in range(8):
                for x in range(8):
                    im[8 * r + y][8 * c + x] = 0
        lab.ecrit(rom, B, im)
        # bas des kanji de 衝撃メーター en rangée 15 (lignes 0-3) ; la plaque EF63 commence plus bas
        lab = Libelle([[0x10A, 0x10B, 0x10C, 0x10D, 0x10E, None, 0x10F, 0x110]])
        im = lab.image(rom, B)
        efface(im, 0, 4, 0, 64)
        lab.ecrit(rom, B, im)
        # haut des kanji de 合格範囲 / 危険 en rangée 13 : vidé
        lab = Libelle([[0x0EE + i for i in range(6)] + [None] + [0x0F4 + i for i in range(4)]])
        im = lab.image(rom, B)
        efface(im, 0, 8, 0, 88)
        lab.ecrit(rom, B, im)
        # « 合格範囲 » -> ZONE OK (lignes 0-4 ; accolade des lignes 6-7 gardée)
        lab = Libelle([[0x101 + i for i in range(5)]])
        im = lab.image(rom, B)
        efface(im, 0, 5, 0, 40)
        bm, L, _ = texte('ZONE OK', 'mini')
        colle(im, bm[2:7], (40 - L) // 2, 0, 3)
        lab.ecrit(rom, B, im)
        # « 危険 » -> DANGER
        lab = Libelle([[0x106 + i for i in range(4)]])
        im = lab.image(rom, B)
        efface(im, 0, 6, 0, 32)
        bm, L, _ = texte('DANGER', 'mini')
        colle(im, bm[2:7], (32 - L) // 2, 0, 2)
        lab.ecrit(rom, B, im)
    # MONO : autre disposition (rangées 13-14 = E8..FB / FC..10E, panneau d'une pièce, fond 3)
    B = BASES[1]
    lab = Libelle([[0x0E8 + i for i in range(20)], [0x0FC + i for i in range(15)] + [0x105, 0x10B, 0x10C, 0x10D, 0x10E],
                   [0x10F + i for i in range(9)] + [None] * 11])
    im = lab.image(rom, B)
    for y in range(2, 19):                 # 衝撃メーター (rangées 13-15, x 1-67)
        for x in range(1, 68):
            im[y][x] = 3
    for y in (11, 12, 13):                 # bout du trait « ー » qui dépasse en x 68-69
        for x in (68, 69):
            im[y][x] = 3
    bm, L, _ = texte('CHOC', 'sb')
    a, b = lignes_utiles(bm)
    colle(im, bm[a:b + 1], (68 - L) // 2, 6, 2, contour=1)
    for y in range(3, 13):                 # 合格範囲 (encre 0 : invisible en mono comme dans l'original)
        for x in range(79, 120):           # (case 15 = tuile 0x105 répétée : intouchée)
            if im[y][x] == 0:
                im[y][x] = 3
    bm, L, _ = texte('ZONE OK', 'mini')
    colle(im, bm[2:7], 79 + (40 - L) // 2, 6, 0)
    for y in range(4, 13):
        for x in range(128, 157):          # 危険 (encre 2) ; bord « 121 » en x 157-159 gardé
            im[y][x] = 3
    bm, L, _ = texte('DANGER', 'mini')
    colle(im, bm[2:7], 128 + (29 - L) // 2, 6, 2)
    lab.ecrit(rom, B, im)
    for B in BASES:
        # « 持ち時間 » -> TEMPS (carte 6x2 : 1re rangée en partie partagée)
        g = carte(rom, 0x061018, 6, 2)
        lab = Libelle(g)
        im = lab.image(rom, B)
        c = Counter(v for r in im[8:] for v in r).most_common()
        fond, ink = c[0][0], c[1][0]
        for r in im:
            for x in range(48):
                r[x] = fond
        bm, L, _ = texte('TEMPS', 'sb')
        a, b = lignes_utiles(bm)
        colle(im, bm[a:b + 1], (48 - L) // 2, 9, ink)
        lab.ecrit(rom, B, im)
        # bannière « 信越本線EF63 »
        g = carte(rom, 0x061071, 12, 1)
        lab = Libelle(g)
        im = lab.image(rom, B)
        c = Counter(v for r in im for v in r).most_common()
        fond, ink = c[0][0], c[1][0]
        for r in im:
            for x in range(96):
                r[x] = fond
        bm, L, _ = texte('LIGNE SHINETSU EF63', 'mini')
        colle(im, bm, (96 - L) // 2, 0, ink)
        lab.ecrit(rom, B, im)
