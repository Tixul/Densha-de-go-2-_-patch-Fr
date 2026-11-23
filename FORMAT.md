# Densha de Go! 2 on Neo Geo Pocket — notes techniques

Tout a été mesuré sur la ROM japonaise **Beta** (4 Mio, MD5 `13f0584aeab81fdbcdb09bc89367bd89`). Les
adresses sont des adresses **fichier**. La cartouche a deux puces : la puce 1 (fichier 0-0x1FFFFF) est vue
en CPU 0x200000, la puce 2 (fichier 0x200000-0x3FFFFF) en CPU 0x800000.

⚠️ La notice japonaise décrit une démo d'ouverture et un menu « ランキングを見る » qui n'existent pas dans
cette ROM. La Beta diffère donc de la version commerciale. Un dump commercial aurait d'autres adresses.

## Principe
- Aucun texte encodé (ni Shift-JIS, ni table de caractères) : tout est en **tuiles 2 bpp en clair**, sans
  compression. Traduire, c'est redessiner.
- Chaque donnée graphique existe en deux exemplaires, **couleur** et **mono** (Neo Geo Pocket noir et blanc ;
  drapeau RAM 0x40E2). Les jeux de tuiles et les cartes mono ont souvent leur propre disposition. Certaines
  tuiles sont partagées entre les deux.
- Encre mono des sprites : 1 noir, 2 gris, 3 blanc. Sur le plan B mono du titre, le noir est 3.
- ⛔ **0x1F0000-0x1FFFFF** (rempli de FF) = **sauvegarde flash** (classements, kilométrage), pas de la place
  libre. Y écrire casse le classement.

## Écrans fixes (`tools/module.py`)
- Module des menus, code 0x28B1xx-0x28B45x. Les tilemaps font 20 x 19 cases, avec **3 octets par case** :
  lo, hi, puis un octet combiné par OU dans hi.
- Tables de pointeurs : plan 2 en 0x28B1DF, plan 1 en 0x28B197. Elles sont indexées par écran, et l'écran
  +9 est la version mono.
- Pièces 8 x 2 placées en (H, L) : tables 0x28B2A8 (couleur) et 0x28B344 (mono), 6 octets par entrée
  (pointeur 4 octets, colonne, ligne).
- Jeux de tuiles copiés vers la VRAM 0xA000, adresses couleur / mono, nombre de tuiles entre parenthèses :
  - titre + logos SNK/TAITO : 0x0481A8 / 0x049638 (329) ;
  - menu : 0x04D06C / 0x04E39A (206). Le menu voit aussi les tuiles 206 et suivantes du titre, qui sont
    donc **protégées** ;
  - illustrations du choix du train : 0x04F40A (457) ;
  - générique : 0x06304E / 0x065776 (469) ;
  - classement : 0x068028 / 0x069D6E (323) ;
  - registre 乗務記録 : 0x06BE2B / 0x06C19B (56) ;
  - tableau 発車案内 : 0x071615 / 0x071A75 (140) ;
  - bilan d'arrêt : 0x0721F9 / 0x0767F9 (131) ;
  - évaluation 運転評価 : 0x080761 / 0x080F31 (125) ;
  - réglages : 0x081E66 / 0x0838C6 (422).
- Choix du train : module 0x03110A, cartes de 40 x 19.
- Annonce du mode Original :
  - écran 20 x 19 en 0x0373CF, chiffres 0x037843 (3 x 2) ;
  - mot météo : table 0x037909 (6 x 3 cases, indice (0x59F2) x 54 ; code 0x237116) ;
  - en mono : tuiles 0x038B73, écran 0x038561, chiffres 0x0389D5, météo 0x038A9B.
- `Module` **ré-encode** un écran :
  1. il redessine les zones demandées ;
  2. il libère les tuiles que plus aucune case n'utilise ;
  3. il réutilise ces tuiles, en forçant la palette case par case si besoin.

  L'opération est transactionnelle : si les tuiles manquent, la ROM n'est pas touchée. Caler le haut des
  capitales sur une rangée de tuiles (paramètre `haut`) divise le besoin en tuiles.

## Écran titre (`tools/m_titre.py`)
- Logo 電車 : carte de remplissage 0x046FD8 et carte de contour 0x0478C0.
- Le titre n'utilise que 38 sprites sur 64. DENSHA est donc coupé en deux :
  - x < 40 : en **sprites**, ajoutés à l'objet 0x117 (ancre écran (79, 76)) ;
  - x ≥ 40 : dans les **deux plans** (A = remplissage avec palette 1 forcée, B = contour).
- « DE » est en sprites (palette 3).
- La palette de sprites 7 (inutilisée) du bloc de palettes 0x0019E4, chargé au titre, est redéfinie.
- Les logos SNK/TAITO (cartes 0x0610CE / 0x061542) utilisent le jeu de tuiles du titre.

## Sprites (objets, `tools/objets.py`, `tools/sprites.py`)
- Table des objets 0x0068C0 : 4 octets par objet, objet = 0x100 + k.
- Liste d'un objet : entrées de 5 octets (id u16, dx, dy, attr), terminée par id 0.
- Tuile = 0x13ECF0 + 16 x id (couleur). En mono : tuiles 0x0D4800, table 0x3BE000.
- Place libre :
  - tuiles 0x1EF2E0-0x1EFFFF (210 tuiles), seul trou à portée de la base ;
  - tuiles des objets remplacés, quand elles ne sont pas partagées ;
  - listes d'objets en puce 2, à partir de 0x3F6300.
- Objets texte :
  - 0x116 / 0x129 : fin de partie ;
  - 0x118 : PRESS A BUTTON ;
  - 0x119-0x128 : tableau de départ ;
  - 0x12B, 0x12C, 0x132-0x137 : bilan d'arrêt ;
  - 0x14C-0x151 : mini-jeu d'attelage ;
  - 0x15F-0x18E : alphabet de saisie.
- Alphabet de saisie : objet = 0x154 + code. Codes :
  - 0-9 : chiffres ;
  - 0x0B : espace ;
  - 0x0C et suivants : A-Z ;
  - 0x26 et suivants : ponctuation ;
  - 0x184-0x18C : kanji et kana remplacés par les accents ;
  - 0x18D : ← ;
  - 0x18E : 終, la fin de saisie.

## HUD de conduite (`tools/hud.py`, `tools/m_hud.py`, `tools/m_hudmsg.py`, `tools/mono_hud.py`)
- Banque de tuiles : couleur 0x0D8860, mono 0x0CE000. Tuile = base + 16 x id.
- Libellés fixes (ids 0x01-0x39 et 0xF6-0x103) : copiés une seule fois en début de parcours, donc
  redessinés sur place.
- Messages = cartes D x E d'entrées (id u16, attr), dessinées par la routine 0x20E512. Exemples :
  - messages de gare 2 x 9 (0x016414…) et 2 x 8 (0x016C4E…) ;
  - bannières 1 x 12 (0x00A89E…) ;
  - panneaux de signal 3 x 5 (0x010999 / 0x010A11 / 0x010A89).

  Beaucoup de morceaux sont **partagés** entre messages (駅通過, 信号, « km/h »…). Les messages sont
  donc ré-encodés avec des tuiles neuves, jamais modifiés sur place. Les ids inférieurs à 0x300 ne sont
  jamais libérés.
- Mono : les cartes de messages mono ont des **ids différents** de la couleur. Seule la carte fixe du HUD
  (0x00A41E / 0x00A976) est identique. Correspondance par paires de cartes : gares +0xC55, incidents
  +0x180, panneaux +0x4B0, bannières +0x54C, panneaux de signal −0x438, etc. (`mono_hud.py`).
- Carte de ligne (avant chaque segment), routine 0x239C43 :
  - tuiles 0x039F1E (385 tuiles) ;
  - en-tête 18 x 4 en 0x03D846 (発/着 → DÉP./ARR.) ;
  - carte 18 x 9 via la table 0x03D5FE[(0x40E0)] (22 parcours) ;
  - branche du stage bonus (parcours 0x12) : couleur 0x239CBA, mono 0x239D70.
- Jeu bonus d'attelage (`m_bonus.py`) :
  - jeu de tuiles 0x05D329 (couleur) / 0x05EE87 (mono), chargé à partir de la tuile VRAM 0x55 ;
  - cartes 0x061018 (consignes) et 0x061071 (bannière) ;
  - le panneau mono a sa propre disposition.
- Noms par défaut du classement : 0x06740E (32 x 8 octets) et 0x07121C.

## RAM utile (conduite)
- Cran 0x4AEC : 0 = urgence, 1-8 = B8..B1, 9 = N, 10-14 = P1..P5.
- Position 0x4ADC (cm, 32 bits), mètres parcourus 0x4AE0, distance restante 0x4B10 (cm).
- Temps restant 0x591C (affiché : 0x5912). Parcours choisi 0x40E0 (0x12 = stage bonus). Drapeau mono 0x40E2.
