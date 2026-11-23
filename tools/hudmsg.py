"""Messages du HUD : cartes (id u16, attr) x D x E dans des tables (couleur) ; rendu avec la banque 0x0D8860.
    python -I -B tools/hudmsg.py ROM SORTIE.png"""
import sys, struct
from PIL import Image, ImageDraw
sys.path.insert(0, __import__('os').path.dirname(__file__))
from gfx import tuile_lit

BANQUE = 0x0D8860
# (table couleur, D, E, nombre max)
TABLES = [(0x00057A, 2, 4, 3), (0x000CA0, 2, 8, 3), (0x000BEC, 3, 10, 3), (0x00AECE, 1, 12, 0),
          (0x00C622, 2, 6, 2), (0x00CBA4, 1, 3, 4), (0x00CBCE, 1, 6, 10), (0x00F23C, 3, 5, 1),
          (0x00F287, 3, 5, 1), (0x00F269, 2, 5, 1), (0x00F38C, 1, 6, 4), (0x00F32C, 2, 8, 2),
          (0x011AD8, 2, 6, 8), (0x011E98, 2, 2, 5), (0x011F10, 2, 10, 2), (0x012C38, 4, 5, 20),
          (0x013598, 4, 4, 3), (0x01392A, 5, 12, 2), (0x013CFE, 2, 8, 8), (0x013E1E, 2, 8, 8),
          (0x015EC9, 3, 8, 6), (0x016B40, 2, 9, 12), (0x016CAE, 2, 8, 12), (0x017795, 2, 9, 12),
          (0x017903, 2, 8, 12)]


def carte(rom, p, D, E):
    ids = []
    for k in range(D * E):
        t = struct.unpack_from('<H', rom, p + 3 * k)[0]
        ids.append((t, rom[p + 3 * k + 2]))
    return ids


def valide(ids):
    return all(t < 0xA000 for t, a in ids) and any(t for t, a in ids)


def rendu(rom, ids, D, E, banque=BANQUE):
    im = Image.new('L', (8 * E, 8 * D), 200)
    pal = [0, 90, 170, 255]
    for k, (t, a) in enumerate(ids):
        px = tuile_lit(rom, banque + 16 * t)
        if a & 0x80: px = [r[::-1] for r in px]
        if a & 0x40: px = px[::-1]
        for r in range(8):
            for x in range(8):
                im.putpixel(((k % E) * 8 + x, (k // E) * 8 + r), pal[px[r][x]])
    return im


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    ims = []
    for tab, D, E, n in TABLES:
        n = n or 1
        # table de pointeurs ? (4 o pointant en 0x2xxxxx)
        p0 = struct.unpack_from('<I', rom, tab)[0]
        ptrs = []
        if 0x200000 <= p0 < 0x240000:
            for k in range(n):
                p = struct.unpack_from('<I', rom, tab + 4 * k)[0]
                if 0x200000 <= p < 0x240000:
                    ptrs.append(p - 0x200000)
        else:
            ptrs = [tab + 3 * D * E * k for k in range(n)]
        for k, p in enumerate(ptrs):
            ids = carte(rom, p, D, E)
            if not valide(ids):
                break
            ims.append(('%06X+%d' % (tab, k), rendu(rom, ids, D, E)))
    W = 640
    f = Image.new('L', (W, 2000), 128)
    dr = ImageDraw.Draw(f)
    x = y = hl = 0
    for n, im in ims:
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        if x + im.width > W:
            x, y, hl = 0, y + hl + 2, 0
        dr.text((x, y), n, fill=255)
        f.paste(im, (x, y + 10))
        x += max(im.width, 70) + 4
        hl = max(hl, im.height + 10)
    f.crop((0, 0, W, y + hl + 2)).save(sys.argv[2])
    print(len(ims), 'cartes')
