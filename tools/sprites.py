"""Objets sprites du moteur (mode couleur) : table de pointeurs 0x0068C0 (index = objet - 0x100), chaque objet =
liste d'entrées 5 o (id tuile u16, dx s8, dy s8, attr) terminée par id 0 ; tuile = 0x13ECF0 + 16*id.
    python -I -B tools/sprites.py ROM SORTIE_PREFIXE [premier dernier]
-> planches PNG (étiquette = n° d'objet hex) + SORTIE_PREFIXE.tsv (objet, adresse liste, nb tuiles, ids)."""
import sys, struct
from PIL import Image, ImageDraw

TABLE, BASE = 0x0068C0, 0x13ECF0


def objets(rom):
    out = []
    for k in range(4096):
        p = struct.unpack_from('<I', rom, TABLE + 4 * k)[0]
        if 0x200000 <= p < 0x220000:
            out.append((0x100 + k, p - 0x200000))
        elif 0x800000 <= p < 0xA00000:                      # liste relogée en 2e puce
            out.append((0x100 + k, p - 0x800000 + 0x200000))
        else:
            break
    return out


def liste(rom, p):
    ent = []
    while True:
        tid = struct.unpack_from('<H', rom, p)[0]
        if tid == 0:
            return ent
        dx, dy = struct.unpack_from('<bb', rom, p + 2)
        ent.append((tid, dx, dy, rom[p + 4], p))
        p += 5
        if len(ent) > 200:
            return ent


def tuile(rom, tid, base=BASE):
    o = base + 16 * tid
    return [[(rom[o + 2 * r] | rom[o + 2 * r + 1] << 8) >> (14 - 2 * x) & 3 for x in range(8)] for r in range(8)]


def rendu(rom, ent, base=BASE):
    if not ent:
        return Image.new('L', (8, 8), 200), (0, 0)
    xs = [e[1] for e in ent]; ys = [e[2] for e in ent]
    x0, y0 = min(xs), min(ys)
    W, H = max(xs) - x0 + 8, max(ys) - y0 + 8
    im = Image.new('L', (W, H), 200)
    pal = [200, 120, 60, 0]
    for tid, dx, dy, a, _ in ent:
        t = tuile(rom, tid, base)
        if a & 0x80: t = [r[::-1] for r in t]
        if a & 0x40: t = t[::-1]
        for r in range(8):
            for x in range(8):
                if t[r][x]:
                    im.putpixel((dx - x0 + x, dy - y0 + r), pal[t[r][x]])
    return im, (x0, y0)


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    obs = objets(rom)
    a, b = (int(sys.argv[3], 16), int(sys.argv[4], 16)) if len(sys.argv) > 4 else (0, 0xFFFF)
    lignes, ims = [], []
    for n, p in obs:
        ent = liste(rom, p)
        lignes.append('%03X\t%06X\t%d\t%s' % (n, p, len(ent), ' '.join('%04X' % e[0] for e in ent)))
        if a <= n <= b and ent:
            ims.append((n, rendu(rom, ent)[0]))
    open(sys.argv[2] + '.tsv', 'w').write('\n'.join(lignes) + '\n')
    print(len(obs), 'objets')
    # planches : rangement en lignes de 640 px
    page, x, y, hl, num = Image.new('L', (640, 1000), 255), 0, 0, 0, 0
    dr = ImageDraw.Draw(page)
    def sauve():
        global num
        page.crop((0, 0, 640, y + hl + 12)).save('%s_%d.png' % (sys.argv[2], num)); num += 1
    for n, im in ims:
        w, h = max(im.width, 22), im.height + 10
        if x + w > 640:
            x, y, hl = 0, y + hl + 2, 0
        if y + h > 1000:
            sauve(); page = Image.new('L', (640, 1000), 255); dr = ImageDraw.Draw(page); x = y = hl = 0
        dr.text((x, y), '%X' % n, fill=0)
        page.paste(im, (x, y + 10))
        x += w + 3; hl = max(hl, h)
    sauve()
