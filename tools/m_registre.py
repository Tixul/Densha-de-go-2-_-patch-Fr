"""Écran 乗務記録 (registre de service) : tuiles 0x06BE2B (56, couleur) / 0x06C19B (mono) ;
titre 7x2 0x06BA8F / 0x06BAB9 ; carte de ligne 20x7 0x06BAE3 / 0x06BC87 (« 選択: ◀▶ 決定: ● »)."""
from module import Module
from m_reglages import ecrire


def applique(rom, mono=False):
    if mono:
        M = Module(rom, 0x06C19B, 56, [(0x06BAB9, 7, 2), (0x06BC87, 20, 7)])
    else:
        M = Module(rom, 0x06BE2B, 56, [(0x06BA8F, 7, 2), (0x06BAE3, 20, 7)])
    im = M.image(0)
    ecrire(M, 0, im, 4, 3, 48, 10, 'Registre', 'sb', encre=3, fond=2, align='c', haut=4)
    im = M.image(1)
    ecrire(M, 1, im, 20, 40, 31, 10, 'Choix :', 'sm', encre=3, fond=0, align='d', haut=42)
    ecrire(M, 1, im, 92, 40, 31, 10, 'OK :', 'sm', encre=3, fond=0, align='d', haut=42)
    return M.applique()
