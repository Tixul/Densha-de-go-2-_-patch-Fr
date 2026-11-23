"""Menu principal (アーケードモード...) : tuiles 0x04D06C (206, couleur) / 0x04E39A (mono), au-delà de 206 = tuiles
du titre restées en VRAM (0x0481A8 / 0x049638). Carte plan 2 20x25 (le menu défile) 0x04CA1E / 0x04DD4C ;
pièce 6x2 « 総走行距離 » 0x04D048 / 0x04E376 ; chiffres 0x04CFFA (non touchés). Fond 1, encre 3."""
from module import Module
from m_reglages import ecrire

ITEMS = [('Mode Arcade', 'Choisissez votre ligne'), ('Mode Original', 'Conditions au hasard'),
         ('Réglages', 'Options du jeu'), ('Classement', 'Meilleurs scores')]


def applique(rom, mono=False):
    if mono:
        M = Module(rom, 0x04E39A, 206, [(0x04DD4C, 20, 25), (0x04E376, 6, 2)], etrangeres=(0x049638, 0))
    else:
        M = Module(rom, 0x04D06C, 206, [(0x04CA1E, 20, 25), (0x04D048, 6, 2)], etrangeres=(0x0481A8, 0))
    im = M.image(0)
    for k, (g, p) in enumerate(ITEMS):
        y = 48 * k
        ecrire(M, 0, im, 40, y + 8, 116, 24, g, 'L', haut=y + 16)
        ecrire(M, 0, im, 40, y + 32, 116, 9, p, 'sm', haut=y + 32)
    im1 = M.image(1)
    ecrire(M, 1, im1, 0, 2, 48, 12, 'Kilométrage', 'sm', encre=2, align='d', haut=5)
    return M.applique()
