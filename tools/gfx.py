"""Dessin de texte français en pixels nets + tuiles 2 bpp NGPC.
Polices : TTF Windows rendues sans lissage (fontmode '1') ; 'p5' = police maison 3x5 (majuscules + chiffres).
Bitmap = liste de lignes de 0/1."""
import os
from PIL import Image, ImageDraw, ImageFont

# dossier des polices TrueType (Tahoma, Verdana, Microsoft Sans Serif, Impact, Arial) ; variable POLICES pour un autre
FW = os.path.join(os.environ.get('POLICES') or os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts'), '')
POLICES = {
    'm': ('tahoma.ttf', 11),      # texte de menu (~8 px de capitale)
    'mb': ('tahomabd.ttf', 11),   # menu gras
    's': ('tahoma.ttf', 9),       # petit
    'sm': ('micross.ttf', 9),     # petit, autre dessin
    'sb': ('verdanab.ttf', 9),    # petit gras
    'L': ('tahomabd.ttf', 16),    # grand gras
}
_cache = {}


def police(nom):
    if nom not in _cache:
        f, t = POLICES[nom]
        _cache[nom] = ImageFont.truetype(FW + f, t)
    return _cache[nom]


def texte(s, nom='m', espace=0):
    """-> (bitmap, largeur, (haut_ligne, ascent)). Hauteur = ascent+descent de la police (stable)."""
    if nom == 'p5':
        return p5(s)
    if nom == 'mini':
        import mini
        bm, L = mini.texte(s)
        return bm, L, (8, 7)
    f = police(nom)
    asc, desc = f.getmetrics()
    H = asc + desc
    W = int(f.getlength(s)) + 8 + espace * len(s)
    im = Image.new('1', (W, H), 0)
    dr = ImageDraw.Draw(im)
    dr.fontmode = '1'
    if espace:
        x = 3
        for ch in s:
            dr.text((x, 0), ch, font=f, fill=1)
            x += f.getlength(ch) + espace
    else:
        dr.text((3, 0), s, font=f, fill=1)
    px = [[im.getpixel((x, y)) for x in range(W)] for y in range(H)]
    cols = [x for x in range(W) if any(px[y][x] for y in range(H))]
    if not cols:
        return [[0] for _ in range(H)], 0, (H, asc)
    x0, x1 = cols[0], cols[-1]
    return [r[x0:x1 + 1] for r in px], x1 - x0 + 1, (H, asc)


def lignes_utiles(bm):
    ys = [y for y, r in enumerate(bm) if any(r)]
    return (ys[0], ys[-1]) if ys else (0, 0)


# Police 3x5 maison (HUD minuscule)
_P5 = {
    'A': '.#.#.##.####.#.#.#', 'B': '##.#.###.#.###.', 'C': '.###..#..#...##', 'D': '##.#.##.##.###.',
    'E': '####..###..####', 'F': '####..###..#...', 'G': '.###..#.##.#.##', 'H': '#.##.####.##.##.#'[:15],
    'I': '###.#..#..#.###', 'J': '..#..#..##.#.#.', 'K': '#.##.###.#.##.#', 'L': '#..#..#..#..###',
    'M': '#.####.##.##.#', 'N': '##.#.##.##.##.#', 'O': '.#.#.##.##.#.#.', 'P': '##.#.###.#..#..',
    'Q': '.#.#.##.##.#.##', 'R': '##.#.###.#.##.#', 'S': '.###...#...###.', 'T': '###.#..#..#..#.',
    'U': '#.##.##.##.#.#.'[:15], 'V': '#.##.##.##.#.#.', 'W': '#.##.##.#####.#', 'X': '#.##.#.#.#.##.#',
    'Y': '#.##.#.#..#..#.', 'Z': '###..#.#.#..###', '0': '.#.#.##.##.#.#.', '1': '.#.##..#..#.###',
    '2': '##...#.#.#..###', '3': '##...#.#...###.', '4': '#.##.####..#..#', '5': '####..##...###.',
    '6': '.###..##.#.#.#.'[:15], '7': '###..#.#..#..#.', '8': '.#.#.#.#.#.#.#.', '9': '.#.#.#.##..###.',
    ' ': '.' * 15, '.': '.' * 12 + '.#.', '-': '......###......', ':': '....#.....#....',
    '/': '..#..#.#..#.#..', "'": '.#..#..........', '!': '.#..#..#.....#.', '?': '##...#.#.....#.',
}
_P5['U'] = '#.##.##.##.####'
_P5['V'] = '#.##.##.##.#.#.'
_P5['O'] = '####.##.##.####'
_P5['0'] = '####.##.##.####'
_P5['6'] = '####..####.####'
_P5['8'] = '####.#####.####'
_P5['9'] = '####.####..####'
_P5['H'] = '#.##.#####.##.#'
_P5['A'] = '.#.#.######.##.#'[:15]
_P5['M'] = '#.####.##.##.#'
_P5['M'] = '#.####.##.##.#.'[:15]


def p5(s):
    bm = [[] for _ in range(5)]
    for i, ch in enumerate(s.upper()):
        g = _P5.get(ch, _P5['?'])
        if i:
            for r in bm:
                r.append(0)
        for y in range(5):
            bm[y] += [1 if c == '#' else 0 for c in g[3 * y:3 * y + 3]]
    return bm, len(bm[0]), (5, 5)


# --- tuiles 2 bpp ---
def tuile_lit(rom, o):
    return [[(rom[o + 2 * r] | rom[o + 2 * r + 1] << 8) >> (14 - 2 * x) & 3 for x in range(8)] for r in range(8)]


def tuile_octets(px):
    out = bytearray()
    for r in range(8):
        w = 0
        for x in range(8):
            w |= (px[r][x] & 3) << (14 - 2 * x)
        out += bytes([w & 0xFF, w >> 8])
    return bytes(out)


def colle(dst, bm, x0, y0, encre, fond=None, contour=None):
    """Pose un bitmap 0/1 dans une image d'indices (liste de listes) ; fond=None -> transparent."""
    H, W = len(dst), len(dst[0])
    if contour is not None:
        for y in range(len(bm)):
            for x in range(len(bm[0])):
                if bm[y][x]:
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y0 + y + dy, x0 + x + dx
                            if 0 <= yy < H and 0 <= xx < W:
                                dst[yy][xx] = contour
    for y in range(len(bm)):
        for x in range(len(bm[0])):
            yy, xx = y0 + y, x0 + x
            if 0 <= yy < H and 0 <= xx < W:
                if bm[y][x]:
                    dst[yy][xx] = encre
                elif fond is not None and contour is None:
                    dst[yy][xx] = fond
