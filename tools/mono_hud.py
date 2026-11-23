"""Correspondance des cartes de messages HUD couleur -> mono (décalages relevés dans les paires de pointeurs du code)
et des identifiants de tuiles couleur -> mono (comparaison case à case des paires de cartes).
    mono_adr(p) -> adresse de la carte mono correspondant à la carte couleur p (ou None)
    table_ids(rom) -> {id_couleur: id_mono}"""
import struct

# (début couleur, fin couleur, décalage vers la carte mono)
ZONES = [(0x00057A, 0x000592, 0x18), (0x000BEC, 0x000C46, 0x5A), (0x000CA0, 0x000CD0, 0x30),
         (0x00A89E, 0x00A952, 0x54C), (0x00C622, 0x00C646, 0x24), (0x00CBA4, 0x00CC94, 0xF0),
         (0x00F23C, 0x00F2B4, 0x78), (0x00F32C, 0x00F35C, 0x30), (0x00F38C, 0x00F3C2, 0x36),
         (0x010999, 0x010B01, -0x438), (0x011AD8, 0x011B68, 0x90), (0x011E98, 0x011ED4, 0x3C), (0x011F10, 0x011F4C, 0x3C),
         (0x012C38, 0x0130E8, 0x4B0), (0x013598, 0x0135C8, 0x30), (0x01392A, 0x0139DE, 0xB4),
         (0x013CFE, 0x013E7E, 0x180), (0x013E7E, 0x013F9E, 0x180), (0x015EC9, 0x015F71, 0xA8),
         (0x0163DE, 0x016F00, 0xC55)]


def mono_adr(p):
    for a, b, d in ZONES:
        if a <= p < b:
            return p + d
    return None


def table_ids(rom, cartes):
    """cartes = [(p_couleur, D, E)] ; renvoie {id couleur: id mono} (premier vu ; conflits signalés)."""
    t, conflits = {}, 0
    for p, D, E in cartes:
        q = mono_adr(p)
        if q is None:
            continue
        for k in range(D * E):
            a = struct.unpack_from('<H', rom, p + 3 * k)[0]
            b = struct.unpack_from('<H', rom, q + 3 * k)[0]
            if a in t and t[a] != b:
                conflits += 1
                continue
            t[a] = b
    return t, conflits
