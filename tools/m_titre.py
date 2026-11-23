"""Écran titre : tuiles 0x0481A8 (329, couleur) / 0x049638 (mono) ; carte A 0x046FD8 / 0x04744C (remplissages
colorés du logo), carte B 0x0478C0 / 0x047D34 (contours noirs, bandeau ON ネオジオポケット, copyright).
Le menu (carte 0x04CA1E 20x25) utilise les tuiles >= 206 de ce jeu : ajouté aux usages (prudence).
« 電車で » -> « DENSHA DE » (capitales grasses étirées x2 en hauteur, rouge + contour noir)."""
import os
from module import Module
from gfx import texte, lignes_utiles
import gfx


def etire(bm, fy):
    return [r[:] for r in bm for _ in range(fy)]


SANS_BANDEAU_MONO = False   # True : pas de bandeau en mono (inutile : le logo mono tient avec)
MONO_UN_CALQUE = True       # mono : DENSHA dessiné sur la seule carte B
MONO_REMPLI = 2             # indice de remplissage de DENSHA en mono (carte B)


# DENSHA = SPRITES (partie gauche) + PLANS DE TUILES (partie droite), à la place du bloc 電車 ; « DE » en sprites
# bleus contourés à la place du で. Titre : 38 sprites sur 64 à l'origine (dont 5 pour le で).
LOGO_POLICE = ('impact.ttf', 16)
LOGO_H = 38                      # hauteur du texte (sans contour) -> DENSHA contouré 50 x 40
LOGO_PENCHE = 0                  # italique ESSAYÉ (6 px) : marches d'escalier sur lettres étirées -> non
LOGO_REFLET = False              # liseré rose ESSAYÉ : délave le rouge -> non
LOGO_X, LOGO_Y = 0, 8            # coin haut-gauche (écran) du DENSHA contouré (x 0-49, y 8-47)
COUPE = 40                       # x < COUPE : sprites (5 x 5 = 25) ; x >= COUPE : plans (cases 5-6)
DE_POLICE, DE_H = ('impact.ttf', 13), 14
DE_X, DE_Y = 50, 24              # « DE » contouré 13 x 16 (4 sprites), entre DENSHA et GO
PAL_SPRITE_7 = 0x0019E4 + 7 * 8  # palette de sprites n° 7 du jeu chargé au titre (inutilisée : 777 partout)
ANCRE = (79, 76)                 # position écran de l'ancre de l'objet 0x117


def rendu(s, police, h=None, penche=0):
    """Texte sans lissage, recadré ; h = hauteur imposée (étirement) ; penche = décalage italique (px)."""
    from PIL import Image, ImageDraw, ImageFont
    F = ImageFont.truetype(gfx.FW + police[0], police[1])
    im = Image.new('1', (300, 60))
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.text((5, 5), s, font=F, fill=1)
    im = im.crop(im.getbbox())
    if h:
        im = im.resize((im.width, h), Image.NEAREST)
    bm = [[im.getpixel((x, y)) for x in range(im.width)] for y in range(im.height)]
    if penche:
        H = len(bm)
        bm = [[0] * (penche * (H - 1 - y) // (H - 1)) + r + [0] * (penche - penche * (H - 1 - y) // (H - 1))
              for y, r in enumerate(bm)]
    return bm


def espace(s, police, gap=1, blanc=3):
    """Texte composé lettre par lettre (espacement constant : pas de crénage irrégulier aux petites tailles)."""
    lettres = [rendu(c, police) if c != ' ' else None for c in s]
    H = max(len(l) for l in lettres if l)
    out = [[] for _ in range(H)]
    for k, l in enumerate(lettres):
        if l is None:
            for r in out:
                r.extend([0] * blanc)
            continue
        off = H - len(l)                               # lettres alignées en bas
        for y in range(H):
            out[y].extend(l[y - off] if y >= off else [0] * len(l[0]))
            if k < len(lettres) - 1:
                out[y].extend([0] * gap)
    return out


def contoure(bm, reflet=False):
    """Bitmap -> image contourée d'1 px : 2 = remplissage, 1 = contour, 0 = vide ; reflet : 3 sur le bord
    haut/gauche du remplissage (liseré clair comme le 電車 d'origine)."""
    W, H = len(bm[0]) + 2, len(bm) + 2
    im = [[0] * W for _ in range(H)]
    for y in range(len(bm)):
        for x in range(len(bm[0])):
            if bm[y][x]:
                for dy in (0, 1, 2):
                    for dx in (0, 1, 2):
                        if im[y + dy][x + dx] == 0:
                            im[y + dy][x + dx] = 1
    for y in range(len(bm)):
        for x in range(len(bm[0])):
            if bm[y][x]:
                im[y + 1][x + 1] = 2
    if reflet:
        for y in range(len(bm)):
            for x in range(len(bm[0])):
                if bm[y][x] and (y == 0 or x == 0 or not bm[y - 1][x] or not bm[y][x - 1]):
                    im[y + 1][x + 1] = 3
    return im


def densha_image():
    return contoure(rendu('DENSHA', LOGO_POLICE, LOGO_H, penche=LOGO_PENCHE), reflet=LOGO_REFLET)


def cases(im, x0, y0, attr, xmax=None):
    W, H = len(im[0]), len(im)
    out = []
    for cy in range(0, H, 8):
        for cx in range(0, min(W, xmax) if xmax else W, 8):
            t = [[im[y][x] if y < H and x < W else 0 for x in range(cx, cx + 8)] for y in range(cy, cy + 8)]
            if any(any(r) for r in t):
                out.append((t, x0 + cx - ANCRE[0], y0 + cy - ANCRE[1], attr))
    return out


def densha_sprites(mono):
    """Partie SPRITES (x < COUPE) du DENSHA : couleur palette 7 (2 rouge, 1 noir) ; mono attribut 0x20."""
    im = densha_image()
    if mono:                                           # mono : pas de liseré (la partie plans ne peut pas l'avoir)
        im = [[2 if v == 3 else v for v in r] for r in im]
    return cases(im, LOGO_X, LOGO_Y, 0x20 if mono else 0x07, COUPE - LOGO_X)


def de_sprites(mono):
    """« DE » : couleur palette 3 comme le で d'origine (2 bleu, 1 noir) ; mono attribut 0x20 (2 gris, 1 noir)."""
    return cases(contoure(rendu('DE', DE_POLICE, DE_H)), DE_X, DE_Y, 0x20 if mono else 0x03)


def palette_logo(rom):
    """Palette de sprites 7 (titre) : blanc, noir, rouge, rose (format 0BGR)."""
    for k, c in enumerate((0x0FFF, 0x0000, 0x000F, 0x088F)):
        rom[PAL_SPRITE_7 + 2 * k:PAL_SPRITE_7 + 2 * k + 2] = c.to_bytes(2, 'little')


def applique(rom, mono=False):
    if not mono:
        palette_logo(rom)
    if mono:
        A, B, menu, T = 0x04744C, 0x047D34, 0x04DD4C, 0x049638
        logos = [0x0619B6, 0x061E2A]
    else:
        A, B, menu, T = 0x046FD8, 0x0478C0, 0x04CA1E, 0x0481A8
        logos = [0x0610CE, 0x061542]                    # logos SNK / TAITO : même jeu de tuiles
    prot = set()
    for k in range(20 * 25):                           # tuiles du titre (>= 206) vues par le menu
        e = rom[menu + 3 * k] | (rom[menu + 3 * k + 1] | rom[menu + 3 * k + 2]) << 8
        if (e & 0x1FF) >= 206:
            prot.add(e & 0x1FF)
    vus = set(prot)
    for c in [A, B] + logos:
        for k in range(20 * 19):
            e = rom[c + 3 * k] | (rom[c + 3 * k + 1] | rom[c + 3 * k + 2]) << 8
            vus.add(e & 0x1FF)
    # ⛔ PAS de réserve « ids jamais affichés » : ils servent après le titre (sprites / écrans suivants) -> casse
    reserve = []
    M = Module(rom, T, 329, [(A, 20, 19), (B, 20, 19)] + [(l, 20, 19) for l in logos], proteges=prot,
               reserve=reserve)
    ia, ib = M.image(0), M.image(1)
    x0, y0, x1, y1 = 0, 8, 62, 47                      # zone de « 電車 » (« で » = objet sprite 0x117)
    zones = [(x0, y0, x1, y1)]
    for (a0, b0, a1, b1) in zones:
        for y in range(b0, b1):
            for x in range(a0, a1):
                ia[y][x] = 0
                ib[y][x] = 0
    # « DENSHA » n'est plus dans les plans de tuiles : SPRITES (objet 0x117, voir m_objets / densha_sprites) ;
    # la zone de 電車 reste vide ici (et libère ses tuiles).
    noir = 3 if mono else 1                            # carte B : encre noire = 1 en couleur, 3 en mono (relevé)
    # partie PLANS du DENSHA (x >= COUPE) : couleur = A remplissage 2 (palette 1 rouge forcée) + B contour 1 ;
    # mono = B seule (2 gris, 3 noir)
    dimg = densha_image()
    for y in range(len(dimg)):
        for x in range(COUPE - LOGO_X, len(dimg[0])):
            v = dimg[y][x]
            X, Y = LOGO_X + x, LOGO_Y + y
            if v in (2, 3):
                if mono:
                    ib[Y][X] = 2
                else:
                    ia[Y][X] = v
            elif v == 1:
                ib[Y][X] = noir
    cases_densha = [(cx, cy) for cy in range(LOGO_Y // 8, (LOGO_Y + len(dimg) - 1) // 8 + 1)
                    for cx in range(COUPE // 8, (LOGO_X + len(dimg[0]) - 1) // 8 + 1)]
    if not (mono and SANS_BANDEAU_MONO):
        # bandeau « ON ネオジオポケット » (vitre noire du train, lettres en creux colorées par la carte A) ->
        # bande noire nette x 38-135, y 55-62 (ligne 54 = carrosserie), « SUR » rouge + « NEO GEO POCKET » jaune,
        # Arial gras 8 (capitales 6 px, nettes) en lignes 56-61.
        bx0, bx1 = 38, 136
        for y in range(54, 63):
            for x in range(bx0, bx1):
                ia[y][x] = 0
                ib[y][x] = noir if y >= 55 else 0
        x = 40
        for mot, coul, fin in (('SUR', 2, 54), ('NEO GEO POCKET', 3, None)):
            bmm = espace(mot, ('arialbd.ttf', 8))
            Lm = len(bmm[0])
            if fin:
                x = fin - Lm + 1
            for yy, r in enumerate(bmm):
                for xx, v in enumerate(r):
                    if v:
                        if not mono:                   # mono : lettres = trous de la bande (couleur du fond)
                            ia[56 + yy][x + xx] = coul
                        ib[56 + yy][x + xx] = 0
            x += Lm + 3
        if x - 3 > bx1:
            raise ValueError('bandeau trop long : %d' % x)
        for i, im in ((0, ia), (1, ib)):
            for cy in (6, 7):
                for cx in range(bx0 // 8, (bx1 - 1) // 8 + 1):
                    pal = (1 if cx < 7 else 4) if (i == 0 and not mono) else None   # SUR rouge, reste jaune
                    M.zone(i, cx, cy, 1, 1, [r[8 * cx:8 * cx + 8] for r in im[8 * cy:8 * cy + 8]], pal=pal)
    if True:
        # copyright : « Licensed by » -> « Sous licence » (carte B, lignes 120-127, encre 1)
        for y in range(120, 128):
            for x in range(12, 80):
                ib[y][x] = 0
        bmc, Lc, _ = texte('Sous licence', 'sm')
        a, b = lignes_utiles(bmc)
        for yy in range(a, b + 1):
            for xx in range(Lc):
                if bmc[yy][xx]:
                    ib[120 + yy - a][78 - Lc + xx] = noir
        for cy in (15,):
            for cx in range(1, 10):
                M.zone(1, cx, cy, 1, 1, [r[8 * cx:8 * cx + 8] for r in ib[8 * cy:8 * cy + 8]])
    for i, im in ((0, ia), (1, ib)):
        for cy in range(y0 // 8, (y1 - 1) // 8 + 1):
            for cx in range(x0 // 8, (x1 - 1) // 8 + 1):
                M.zone(i, cx, cy, 1, 1, [r[8 * cx:8 * cx + 8] for r in im[8 * cy:8 * cy + 8]],
                       pal=1 if (i == 0 and not mono and (cx, cy) in cases_densha) else None)
    return M.applique()
