"""Objets sprites traduits (mode couleur). Voir objets.py. Couleurs : indices 1-3 de la palette de l'attribut."""
import struct
from objets import Allocateur, Ligne, remplace, attrs, recuperables, retouche, recompose


def specs(rom):
    class _A(dict):
        def __missing__(self, k):                     # bande absente (ex. mono) : attribut le plus courant
            from collections import Counter
            return Counter(self.values()).most_common(1)[0][0] if self else 0
    a = lambda n: _A(attrs(rom, n))
    S = {}
    # --- bilan d'arrêt en gare ---
    S[0x12B] = [Ligne('Arrêt', 'sb', 2, 3, a(0x12B)[-8], y=-6, x=-30, align='g')]
    S[0x12C] = [Ligne('Dépassé !', 'sb', 2, 3, a(0x12C)[-8], y=-6, x=-35, align='g')]
    S[0x131] = [Ligne('OK !', 'sb', 2, 3, a(0x131)[-8], y=-6)]
    S[0x132] = [Ligne('Bravo', 'sm', 2, 3, a(0x132)[-8], y=-6)]
    S[0x133] = [Ligne('s', 'sb', 2, 3, a(0x133)[-8], y=-6)]
    S[0x152] = [Ligne('s', 'sb', 2, 1, a(0x152)[-8], y=-6)]
    S[0x135] = [Ligne('Accél. en gare', 'sm', 2, 3, a(0x135)[-8], y=-6, x=-35, align='g')]
    S[0x136] = [Ligne('non', 'sb', 2, 3, a(0x136)[-8], y=-6)]
    S[0x137] = [Ligne('pén.', 'sb', 2, 3, a(0x137)[-8], y=-6)]
    # --- fins de partie ---
    S[0x116] = [Ligne('Service terminé', 'sm', 3, 1, a(0x116)[-16], y=-12),
                Ligne('FIN DE PARTIE', 'sb', 2, 1, a(0x116)[0], y=2)]
    S[0x129] = [Ligne('Service interrompu', 'sm', 3, 1, a(0x129)[-16], y=-12),
                Ligne('FIN DE PARTIE', 'sb', 3, 1, a(0x129)[0], y=2)]
    S[0x118] = [Ligne('APPUYEZ SUR A', 'sb', 3, 1, a(0x118)[-8], y=-4)]
    # --- mini-jeu bonus d'attelage ---
    S[0x14C] = [Ligne('JEU BONUS', 'L', 3, 1, a(0x14C)[-4], y=-8)]
    S[0x14D] = [Ligne('Attelez le train' + chr(10) + 'sans choc, à temps !', 'sm', 2, None, a(0x14D)[-8], y=-11,
                      boite=(-52, -16, 52, 16, 3))]
    S[0x14E] = [Ligne('Prêt ?', 'mb', 3, 1, a(0x14E)[-4], y=-6)]
    S[0x14F] = [Ligne('Allez !', 'sb', 3, 1, a(0x14F)[-4], y=-6)]
    S[0x150] = [Ligne('Attelage réussi', 'sb', 3, 1, a(0x150)[-16], y=-12),
                Ligne('BONUS !', 'L', 3, 1, a(0x150)[0], y=2)]
    S[0x151] = [Ligne('Attelage raté', 'sb', 3, 1, a(0x151)[-8], y=-4)]
    return S


TABLEAU = {0x119: 'SÉRIE 681', 0x11A: 'SÉRIE E3', 0x11B: 'HK100', 0x11C: 'SÉRIE 209', 0x11D: 'NAOETSU',
           0x11E: 'MUIKAMACHI', 0x11F: 'AKITA', 0x120: 'OMAGARI', 0x121: 'SHINAGAWA', 0x122: 'UENO',
           0x123: 'RAPIDE', 0x124: 'KOMACHI', 0x125: 'HAKUTAKA', 0x128: 'URAGAWARA'}


# Alphabet de saisie du nom (registre) : un objet 8x16 par code (objet = 0x154 + code). Les glyphes japonais
# (0x184-0x18C dont 系 0x18B / 形 0x18C, et 終 0x18E = fin de saisie) -> É È Ê À Ç Ô ! ' + et ✓ (fin).
# Lettre = lignes 3-12, x 1-6, encre 3 (ligne 7 : encre 2, effet de bande) ; lignes 1-2 / 13-14 libres (accents).
ACC_AIGU, ACC_GRAVE, ACC_CIRC = ['....##', '...##.'], ['##....', '.##...'], ['..##..', '.#..#.']
CEDILLE = ['...##.', '..##..']
GLYPHES_SAISIE = {0x184: (0x164, ACC_AIGU, None), 0x185: (0x164, ACC_GRAVE, None),
                  0x186: (0x164, ACC_CIRC, None), 0x187: (0x160, ACC_GRAVE, None),
                  0x188: (0x162, None, CEDILLE), 0x189: (0x16E, ACC_CIRC, None),
                  0x18A: (['..##..'] * 7 + ['......', '..##..', '..##..'], None, None),           # !
                  0x18B: (['..##..', '..##..', '..#...', '......', '......', '......', '......', '......',
                           '......', '......'], None, None),                                        # '
                  0x18C: (['......', '......', '..##..', '..##..', '######', '######', '..##..', '..##..',
                           '......', '......'], None, None),                                        # +
                  0x18E: (['......', '.....#', '.....#', '....##', '....#.', '#..##.', '##.#..', '.###..',
                           '..##..', '..#...'], None, None)}                                        # ✓ (fin)


def glyphe(src, n):
    """Image 16 x 8 de l'objet n (deux tuiles empilées)."""
    import objets, sprites
    p0 = objets.fichier(struct.unpack_from('<I', src, sprites.TABLE + 4 * (n - 0x100))[0])
    im = [[0] * 8 for _ in range(16)]
    for tid, dx, dy, at, _ in objets.liste(src, p0):
        t = objets.tuile(src, tid)
        for r in range(8):
            im[dy + 8 + r] = t[r][:]
    return im


def alphabet_saisie(rom, A, src):
    import objets
    cadre = glyphe(src, 0x164)
    for y in range(1, 15):                             # cadre vide : fond 1, bordure gauche (colonne 0) gardée
        for x in range(1, 7):
            cadre[y][x] = 1
    for n, (base, haut, bas) in GLYPHES_SAISIE.items():
        if isinstance(base, int):
            im = glyphe(src, base)
        else:
            im = [r[:] for r in cadre]
            for y, ligne in enumerate(base):
                for x, c in enumerate(ligne):
                    if c == '#':
                        im[3 + y][1 + x] = 2 if 3 + y == 7 else 3
        for (rangs, y0) in ((haut, 1), (bas, 13)):
            if rangs:
                for y, ligne in enumerate(rangs):
                    for x, c in enumerate(ligne):
                        if c == '#':
                            im[y0 + y][1 + x] = 3
        at = attrs(src, n)
        recompose(rom, A, n, lambda dx, dy, a: False,
                  [(im[0:8], -4, -8, at.get(-8, 0)), (im[8:16], -4, 0, at.get(0, 0))], src, verbeux=False)


def applique(rom, mono=False):
    import objets
    objets.mode(mono)
    src = bytes(rom)                    # dessins d'origine (les tuiles recyclées seront réécrites)
    S = specs(rom)
    A = Allocateur(rom, recuperables(rom, list(S.keys()) + list(TABLEAU.keys()) + [0x117] + list(GLYPHES_SAISIE)))
    for n, l in S.items():
        remplace(rom, A, n, l)
    for n, s in TABLEAU.items():
        if n == 0x125:          # 特急 はくたか : bloc rouge 特急 (x 2-9) vidé, kana à l'encre 0 sur champ blanc 3
            retouche(rom, A, n, s, rect=(11, 3, 45, 13), encre=0, ytexte=4, src=src, recolore=[((2, 2, 10, 14), 3, 2)])
        else:
            retouche(rom, A, n, s, src=src)
    import m_titre                     # « で » du logo -> « DE » + le grand DENSHA en sprites (titre)
    # objet 0x117 du titre : « で » (entrées x < 0 sauf le point en (-24, -20)) retiré ; ® et morceaux du « 2 »
    # gardés ; + DENSHA (partie sprites) + « DE »
    recompose(rom, A, 0x117, lambda dx, dy, at: dx >= 0,
              m_titre.densha_sprites(mono) + m_titre.de_sprites(mono), src)
    alphabet_saisie(rom, A, src)
    return A
