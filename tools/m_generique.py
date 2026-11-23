"""Générique (STAFF) : tuiles 0x06304E (469, couleur) / 0x065776 (mono) ; pages 20x6 0x0623A6 + 360k /
0x064ACE + 360k (k = 0..8). Seuls les intitulés de rôle (anglais) sont traduits ; les noms restent."""
from collections import Counter
from module import Module
from m_reglages import ecrire

ROLES = {0: 'Générique', 1: 'Producteur exécutif', 2: 'Producteurs', 3: 'Réalisation / conception',
         4: 'Programmation', 5: 'Graphismes', 7: 'Son', 8: 'Remerciements'}


def applique(rom, mono=False):
    base = 0x064ACE if mono else 0x0623A6
    M = Module(rom, 0x065776 if mono else 0x06304E, 469, [(base + 360 * k, 20, 6) for k in range(9)])
    for k, s in ROLES.items():
        im = M.image(k)
        if k == 0:                                     # « STAFF » centré au milieu de la page
            ys = [y for y in range(48) if len(set(im[y])) > 1]
            c = Counter(v for y in ys for v in im[y]).most_common()
            ecrire(M, k, im, 16, ys[0] - 1, 128, ys[-1] - ys[0] + 3, s, 'L', encre=c[1][0], fond=c[0][0],
                   align='c', haut=ys[0])
            continue
        c = Counter(v for y in range(0, 8) for v in im[y][:120]).most_common()
        ecrire(M, k, im, 0, 0, 160, 16, s, 'sb', encre=c[1][0], fond=c[0][0], haut=1)
    return M.applique()
