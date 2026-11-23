"""Classement (ランキング) : tuiles 0x068028 (323, couleur) / 0x069D6E (mono).
Cartes : en-têtes 4 x (20x3) 0x067512 / 0x069258 ; tableau 18x14 0x0677E2 / 0x069528 ; rangs 2x14 0x067C92 /
0x0699D8 ; 2x2 0x067C1A / 0x069960 ; 3x2 0x067FE0 / 0x069D26 ; barre 20x2 0x067D0A / 0x069A50 ;
glyphes (chiffres) 121 cases 0x067E72 / 0x069BB8."""
from module import Module
from m_reglages import ecrire
from gfx import texte

TETES = ['Akita Shinkansen - E3', 'Keihin-Tohoku - 209', 'Hokuhoku - HK100', 'Hokuhoku - 681']


# Noms par défaut des classements (codes de l'alphabet de saisie : 0-9 = chiffres, 0x0B = espace, 0x0C.. =
# lettres, 0x2F = « HK », 0x0A = « 00 », 0x37 = 系, 0x38 = 形) : 32 enregistrements de 8 o dès 0x06740E
# (4 lignes x 8 : nom 4 o + 00 00 + distance) et 4 noms en 0x07121C. 系/形 -> espace : 209, HK100, E3, 681.
# N'agit que sur une sauvegarde NEUVE (le jeu y recopie ces valeurs).
NOMS_DEFAUT = {bytes.fromhex('02000937'): bytes.fromhex('0200090b'), bytes.fromhex('2f010a38'): bytes.fromhex('2f010a0b'),
               bytes.fromhex('1003370b'): bytes.fromhex('10030b0b'), bytes.fromhex('06080137'): bytes.fromhex('0608010b')}


def noms_defaut(rom):
    for a in [0x06740E + 8 * k for k in range(32)] + [0x07121C + 4 * k for k in range(4)]:
        v = bytes(rom[a:a + 4])
        if v in NOMS_DEFAUT:
            rom[a:a + 4] = NOMS_DEFAUT[v]
        elif v not in NOMS_DEFAUT.values():
            raise RuntimeError('classement : nom par défaut inattendu en %06X : %s' % (a, v.hex()))


def applique(rom, mono=False):
    noms_defaut(rom)
    if mono:
        T, h, tab, rg, a, b, barre, gl = 0x069D6E, 0x069258, 0x069528, 0x0699D8, 0x069960, 0x069D26, 0x069A50, 0x069BB8
    else:
        T, h, tab, rg, a, b, barre, gl = 0x068028, 0x067512, 0x0677E2, 0x067C92, 0x067C1A, 0x067FE0, 0x067D0A, 0x067E72
    cartes = [(h + 180 * k, 20, 3) for k in range(4)] + [(tab, 18, 14), (rg, 2, 14), (a, 2, 2), (b, 3, 2),
                                                          (barre, 20, 2), (gl, 121, 1)]
    M = Module(rom, T, 323, cartes)
    for k, s in enumerate(TETES):
        im = M.image(k)
        pol = 'sb' if texte(s, 'sb')[1] <= 108 else 'sm'
        ecrire(M, k, im, 24, 8, 118, 14, s, pol, encre=3, fond=2, align='c', haut=9)
    im = M.image(8)
    ecrire(M, 8, im, 39, 2, 38, 10, 'Suivant', 'sm', encre=3, fond=2, haut=4)
    ecrire(M, 8, im, 90, 2, 68, 10, 'Retour au menu', 'sm', encre=3, fond=2, haut=4)
    return M.applique()
