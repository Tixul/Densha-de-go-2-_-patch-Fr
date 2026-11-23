"""Tableau de départ (発車案内) : tuiles 0x071615 (140, couleur) / 0x071A75 (mono) ; carte 20x8 0x071255 / 0x071435.
Les noms (train, service, gares) sont les objets sprites 0x119-0x128 (m_objets)."""
from module import Module
from m_reglages import ecrire


def applique(rom, mono=False):
    M = Module(rom, 0x071A75 if mono else 0x071615, 140, [(0x071435 if mono else 0x071255, 20, 8)])
    im = M.image(0)
    ecrire(M, 0, im, 33, 1, 93, 13, 'Départs', 'mb', encre=3, fond=1, align='c', haut=4)
    return M.applique()
