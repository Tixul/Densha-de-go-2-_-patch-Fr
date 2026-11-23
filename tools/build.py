"""Fabrique la ROM française depuis la ROM japonaise d'origine (Beta, 4 Mio) :

    python tools/build.py ROM_JP.ngc SORTIE.ngc [--ips SORTIE.ips]

Applique tous les modules graphiques traduits (couleur ET noir et blanc). La ROM d'origine est vérifiée
(empreinte MD5) : tout autre fichier est refusé. Avec --ips, écrit aussi le patch, revérifié.
Variable SAUTE=nom1,nom2 : étapes à omettre (diagnostic)."""
import hashlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import m_reglages, m_menu, m_eval, m_bilan, m_objets, m_hud, m_hudmsg, m_choix, m_tableau, m_classement
import m_registre, m_generique, m_original, m_titre, m_carteligne
import objets
import m_bonus
import ips

MD5_JP = '13f0584aeab81fdbcdb09bc89367bd89'


def objets_tous(rom):
    objets.debut(rom)
    m_objets.applique(rom)
    m_objets.applique(rom, mono=True)
    objets.mode(False)


def titre(rom):
    m_titre.applique(rom)
    try:
        m_titre.applique(rom, mono=True)
    except RuntimeError as e:
        print('ATTENTION titre mono non traduit :', e)


def deux(mod):
    return lambda rom: (mod.applique(rom), mod.applique(rom, mono=True))


ETAPES = [('m_reglages', deux(m_reglages)), ('m_menu', deux(m_menu)), ('m_eval', deux(m_eval)),
          ('m_bilan', deux(m_bilan)), ('m_objets', objets_tous), ('m_hud', m_hud.applique),
          ('m_hudmsg', m_hudmsg.applique), ('m_choix', deux(m_choix)), ('m_tableau', deux(m_tableau)),
          ('m_classement', deux(m_classement)), ('m_registre', deux(m_registre)),
          ('m_generique', deux(m_generique)), ('m_original', deux(m_original)),
          ('m_carteligne', deux(m_carteligne)), ('m_titre', titre), ('m_bonus', m_bonus.applique)]


def ecrit(chemin, data):
    tmp = Path(str(chemin) + '.tmp')
    tmp.write_bytes(data)
    tmp.replace(chemin)


def main():
    args = sys.argv[1:]
    sortie_ips = None
    if '--ips' in args:
        k = args.index('--ips')
        sortie_ips = args[k + 1]
        del args[k:k + 2]
    if len(args) != 2:
        raise SystemExit(__doc__)
    src, dst = args
    jp = Path(src).read_bytes()
    if hashlib.md5(jp).hexdigest() != MD5_JP:
        raise SystemExit('ERREUR : %s n\'est pas la ROM attendue (Densha de Go! 2 on Neo Geo Pocket (Japan) '
                         '(Beta), MD5 %s)' % (src, MD5_JP))
    saute = set(x for x in os.environ.get('SAUTE', '').split(',') if x)
    rom = bytearray(jp)
    for nom, f in ETAPES:
        if nom not in saute:
            f(rom)
    ecrit(dst, rom)
    print('ok', dst)
    if sortie_ips:
        p = ips.fabrique(jp, bytes(rom))
        if ips.applique(jp, p) != bytes(rom):
            raise SystemExit('ERREUR : le patch ne redonne pas la ROM FR')
        ecrit(sortie_ips, p)
        print('ok %s (%d octets, vérifié)' % (sortie_ips, len(p)))


if __name__ == '__main__':
    main()
