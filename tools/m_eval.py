"""Écran 運転評価 (évaluation de fin de partie) : tuiles 0x080761 (125, couleur) / 0x080F31 (mono) ;
plan 2 0x07FA05 (texte, fond 3, encre 1) / mono 0x0802ED ; plan 1 0x07F591 (cadre) / 0x07FE79.
Tampons de notation 2x2 : table 0x07F501 (couleur) / 0x07F549 (mono) - PAS ENCORE traités (sens à établir).
⚠ le code lit aussi des « cartes » 14x2 et 2x3 depuis 0x280761 (= début du jeu de tuiles) : tuiles 0-6 intouchées
(jamais libérées car utilisées partout)."""
from module import Module
from m_reglages import ecrire

LIGNES = ['Ponctualité', 'Freinage', 'Arrêt', 'Signaux', 'Sécurité']


TAMPONS = ['I', 'P', 'B', 'TB', '!']      # 0 insuffisant, 1 可 passable, 2 良 bien, 3 優 très bien, 4 infraction


def tampon(s, rond):
    """Cachet 16x16 : fond 3, trait 2 (cercle ou rectangle) + appréciation."""
    from gfx import texte, lignes_utiles
    im = [[3] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            if rond:
                d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
                if 6.3 <= d <= 7.6:
                    im[y][x] = 2
            elif x in (1, 14) and 1 <= y <= 14 or y in (1, 14) and 1 <= x <= 14:
                im[y][x] = 2
    pol = 'sb' if len(s) == 1 else 'mini'
    bm, L, _ = texte(s, pol)
    a, b = lignes_utiles(bm)
    bm = bm[a:b + 1]
    x0, y0 = (16 - L) // 2, (16 - len(bm)) // 2
    for y, r in enumerate(bm):
        for x, v in enumerate(r):
            if v:
                im[y0 + y][x0 + x] = 2
    return im


def applique(rom, mono=False):
    st = 0x07F549 if mono else 0x07F501
    if mono:
        M = Module(rom, 0x080F31, 125, [(0x0802ED, 20, 19), (0x07FE79, 20, 19)] + [(st + 12 * k, 2, 2) for k in range(6)])
    else:
        M = Module(rom, 0x080761, 125, [(0x07FA05, 20, 19), (0x07F591, 20, 19)] + [(st + 12 * k, 2, 2) for k in range(6)])
    for k, t in enumerate(TAMPONS):
        M.zone(2 + k, 0, 0, 2, 2, tampon(t, k < 4))
    im = M.image(0)
    ecrire(M, 0, im, 44, 12, 72, 15, 'Évaluation', 'm', encre=1, fond=3, align='c', haut=16)
    for k, s in enumerate(LIGNES):
        ecrire(M, 0, im, 6, 35 + 16 * k, 47, 11, s, 'sm', encre=1, fond=3, align='c', haut=37 + 16 * k)
    ecrire(M, 0, im, 30, 121, 66, 15, 'Note finale', 'm', encre=1, fond=3, align='d', haut=124)
    ecrire(M, 0, im, 136, 121, 22, 15, 'pts', 'm', encre=1, fond=3, haut=124)
    return M.applique()
