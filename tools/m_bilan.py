"""Bilan d'arrêt en gare (surimpression pendant la conduite) : tuiles 0x0721F9 (131, couleur) / 0x0767F9 (mono).
Pièces 3 o/case (chacune possède ses tuiles) ; encre 3, contour 2, fond 0 (transparent).
Chiffres (tables 0x07A53B / 0x07A577) non touchés. « オーバーラン! », « 停止位置 », « 合格 » = ailleurs (sprites ?)."""
from module import Module
from m_reglages import ecrire

# (couleur, mono, L, H, texte)
PIECES = [(0x07A0E6, 0x07A0F2, 2, 2, 's'), (0x07A164, 0x07A176, 3, 2, 'pén.'), (0x07A1BB, 0x07A1CD, 3, 2, 'Total'),
          (0x07A212, 0x07A248, 9, 2, "Arrêt d'urgence"), (0x07A2B1, 0x07A2CF, 5, 2, 'moins'),
          (0x07A320, 0x07A332, 3, 2, 'non'), (0x07A377, 0x07A3AD, 9, 2, 'Réaccél. en gare'),
          (0x07A416, 0x07A440, 7, 2, 'Évaluation')]


def applique(rom, mono=False):
    M = Module(rom, 0x0767F9 if mono else 0x0721F9, 131, [(p[1] if mono else p[0], p[2], p[3]) for p in PIECES])
    for i, (c, m, L, H, t) in enumerate(PIECES):
        im = M.image(i)
        ecrire(M, i, im, 0, 0, 8 * L, 13, t, 'sm', encre=3, fond=0, align='g', haut=3, contour=2)
    return M.applique()
