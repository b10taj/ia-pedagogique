"""
ltspice_generator.py
Backend pour la génération automatique de fichiers LTSpice .asc depuis un énoncé textuel.
Ne dépend pas de Streamlit — retourne des données brutes exploitables par l'UI.

Circuits supportés :
  - diviseur_resistif_fixe       : Diviseur résistif avec résistances fixes (VIN, R1, R2)
  - diviseur_resistif_variable   : Diviseur avec résistance variable (sweep .step param)
  - rc_sinus_temporel            : RC + signal sinusoïdal, analyse temporelle (.tran)
  - rc_sinus_frequentiel         : RC + signal AC, diagramme de Bode (.ac)
  - zener_diviseur               : Diviseur résistif avec diode Zener (BZX84C10VL)
  - stabilisateur_tension_zener  : Stabilisateur 10V (diode + Zener + RL variable)
  - amplificateur_bipolaire      : Ampli NPN émetteur commun (2N2222, RL variable, .ac)
  - general                      : Circuit quelconque, généré par Claude IA
"""

import re
import os
import tempfile

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

TEMPLATE_MAP = {
    "diviseur_resistif_fixe":      "diviseur_resistif_fixe.asc",
    "diviseur_resistif_variable":  "diviseur_resistif_variable.asc",
    "rc_sinus_temporel":           "rc_sinus_temporel.asc",
    "rc_sinus_frequentiel":        "rc_sinus_frequentiel.asc",
    "zener_diviseur":              "zener_diviseur.asc",
    "stabilisateur_tension_zener": "stabbilisateur_tension_zener.asc",
    "amplificateur_bipolaire":     "amplificateur_bipolaire.asc",
    "general":                     "general.asc",
}

# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _formater_valeur(v: float) -> str:
    """Float → chaîne LTSpice. Ex: 4700 → '4.7k', 100e-9 → '100n'."""
    if v == 0:
        return "0"
    a = abs(v)
    if a >= 1e6:
        return f"{v / 1e6:.6g}Meg"
    if a >= 1e3:
        return f"{v / 1e3:.6g}k"
    if a >= 1:
        return f"{v:.6g}"
    if a >= 1e-3:
        return f"{v * 1e3:.6g}m"
    if a >= 1e-6:
        return f"{v * 1e6:.6g}u"
    if a >= 1e-9:
        return f"{v * 1e9:.6g}n"
    return f"{v * 1e12:.6g}p"


# ---------------------------------------------------------------------------
# 1. Modification du fichier .asc
# ---------------------------------------------------------------------------

def remplacer_valeur_composant(asc_content: str, inst_name: str, nouvelle_valeur: str) -> str:
    """
    Trouve SYMATTR InstName <inst_name> dans le contenu .asc et remplace
    la ligne SYMATTR Value suivante par <nouvelle_valeur>.
    Retourne le contenu modifié (ou inchangé si InstName introuvable).
    """
    lignes = asc_content.splitlines(keepends=True)
    resultat = []
    i = 0
    while i < len(lignes):
        ligne = lignes[i]
        if re.match(
            rf"^SYMATTR\s+InstName\s+{re.escape(inst_name)}\s*$",
            ligne.strip(),
            re.IGNORECASE,
        ):
            resultat.append(ligne)
            i += 1
            if i < len(lignes) and re.match(
                r"^SYMATTR\s+Value\b", lignes[i].strip(), re.IGNORECASE
            ):
                resultat.append(f"SYMATTR Value {nouvelle_valeur}\n")
                i += 1  # sauter l'ancienne ligne Value
            continue
        resultat.append(ligne)
        i += 1
    return "".join(resultat)


def _remplacer_commande_sim(asc_content: str, prefixe_cmd: str, nouvelle_cmd: str) -> str:
    """
    Remplace la commande SPICE (dans une ligne TEXT ... !<cmd>) dont le début
    correspond à <prefixe_cmd>, en préservant le '!' obligatoire.
    Ex: prefixe_cmd='.tran', nouvelle_cmd='.tran 5m'
    """
    pattern = rf"!{re.escape(prefixe_cmd)}\b[^\n]*"
    return re.sub(pattern, f"!{nouvelle_cmd}", asc_content, flags=re.IGNORECASE)


# ---------------------------------------------------------------------------
# 2. Application des paramètres par type de circuit
# ---------------------------------------------------------------------------

def _appliquer_diviseur_fixe(asc_content: str, params: dict) -> str:
    if "VIN" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "VIN", _formater_valeur(params["VIN"])
        )
    if "R1" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R1", _formater_valeur(params["R1"])
        )
    if "R2" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R2", _formater_valeur(params["R2"])
        )
    return asc_content


def _appliquer_diviseur_variable(asc_content: str, params: dict) -> str:
    # R2 reste {Rvar} — on ne touche que VIN et R1 (fixe)
    if "VIN" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "VIN", _formater_valeur(params["VIN"])
        )
    if "R1" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R1", _formater_valeur(params["R1"])
        )
    return asc_content


def _appliquer_rc_temporel(asc_content: str, params: dict) -> str:
    if "R1" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R1", _formater_valeur(params["R1"])
        )
    if "C1" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "C1", _formater_valeur(params["C1"])
        )

    # Construire la valeur SINE
    vamp = params.get("Vamp", 1.0)
    freq = params.get("freq", 1000.0)
    freq_str = _formater_valeur(freq)
    vamp_str = _formater_valeur(vamp)
    sine_val = f"SINE(0 {vamp_str} {freq_str})"
    asc_content = remplacer_valeur_composant(asc_content, "V1", sine_val)

    # Durée de simulation : 10 périodes
    duree = 10.0 / freq
    asc_content = _remplacer_commande_sim(
        asc_content, ".tran", f".tran {_formater_valeur(duree)}"
    )
    return asc_content


def _appliquer_rc_frequentiel(asc_content: str, params: dict) -> str:
    if "R1" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R1", _formater_valeur(params["R1"])
        )
    if "C1" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "C1", _formater_valeur(params["C1"])
        )
    # V1 garde SYMATTR Value "" / SpiceLine AC 1 — pas de modification

    # Mise à jour de la commande .ac si une plage est donnée
    f_start = params.get("f_start", None)
    f_stop  = params.get("f_stop",  None)
    if f_start or f_stop:
        fs  = _formater_valeur(f_start) if f_start else "1"
        fe  = _formater_valeur(f_stop)  if f_stop  else "10Meg"
        asc_content = _remplacer_commande_sim(
            asc_content, ".ac", f".ac dec 100 {fs} {fe}"
        )
    return asc_content


def _appliquer_zener_diviseur(asc_content: str, params: dict) -> str:
    if "R1" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R1", _formater_valeur(params["R1"])
        )
    if "R2" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R2", _formater_valeur(params["R2"])
        )
    vamp = params.get("VIN", 12.0)
    freq = params.get("freq", 1000.0)
    sine_val = f"SINE(0 {_formater_valeur(vamp)} {_formater_valeur(freq)} 0 0 0 2)"
    asc_content = remplacer_valeur_composant(asc_content, "VIN", sine_val)
    duree = 5.0 / freq
    asc_content = _remplacer_commande_sim(
        asc_content, ".tran", f".tran 0 {_formater_valeur(duree)} 0"
    )
    return asc_content


def _appliquer_stabilisateur_zener(asc_content: str, params: dict) -> str:
    if "R1" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R1", _formater_valeur(params["R1"])
        )
    vamp = params.get("Vamp", 20.0)
    freq = params.get("freq", 50.0)
    sine_val = f"SINE(0 {_formater_valeur(vamp)} {_formater_valeur(freq)} 0 0 0 3)"
    asc_content = remplacer_valeur_composant(asc_content, "V1", sine_val)
    return asc_content


def _appliquer_amplificateur_bipolaire(asc_content: str, params: dict) -> str:
    if "VCC" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "VCC", _formater_valeur(params["VCC"])
        )
    if "RC" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "RC", _formater_valeur(params["RC"])
        )
    if "RE" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "RE", _formater_valeur(params["RE"])
        )
    if "R1" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R1", _formater_valeur(params["R1"])
        )
    if "R2" in params:
        asc_content = remplacer_valeur_composant(
            asc_content, "R2", _formater_valeur(params["R2"])
        )
    vamp = params.get("Vamp", 0.01)
    freq = params.get("freq", 1000.0)
    sine_val = f"SINE(0 {_formater_valeur(vamp)} {_formater_valeur(freq)} 0 0 0 2)"
    asc_content = remplacer_valeur_composant(asc_content, "VIN", sine_val)
    return asc_content


_APPLIQUER = {
    "diviseur_resistif_fixe":      _appliquer_diviseur_fixe,
    "diviseur_resistif_variable":  _appliquer_diviseur_variable,
    "rc_sinus_temporel":           _appliquer_rc_temporel,
    "rc_sinus_frequentiel":        _appliquer_rc_frequentiel,
    "zener_diviseur":              _appliquer_zener_diviseur,
    "stabilisateur_tension_zener": _appliquer_stabilisateur_zener,
    "amplificateur_bipolaire":     _appliquer_amplificateur_bipolaire,
    # "general" est géré séparément (génération IA)
}


# ---------------------------------------------------------------------------
# 3. Génération IA pour les circuits hors-template
# ---------------------------------------------------------------------------

_PROMPT_GENERATION_ASC = """\
Tu es un expert LTSpice XVII. Génère un fichier schématique LTSpice .asc VALIDE et COMPLET \
pour le circuit décrit par l'utilisateur.

RÈGLE ABSOLUE : réponds UNIQUEMENT avec le contenu brut du fichier .asc.
Pas de markdown, pas de ``` , pas de texte avant ni après. \
La première ligne doit être exactement "Version 4".

COORDONNÉES : multiples de 16 pixels.

CONNEXIONS :
  WIRE x1 y1 x2 y2   — segment de fil
  FLAG x y 0          — masse (GND) à ce point exact
  FLAG x y NOM        — étiquette de nœud

POSITIONS DES PINS (offsets VÉRIFIÉS depuis l'ancre du symbole Xs Ys) :
  SYMBOL voltage Xs Ys R0  →  +pin à (Xs,    Ys+16)  /  −pin à (Xs,    Ys+96)
  SYMBOL res     Xs Ys R0  →  pin1 à (Xs+16, Ys+16)  /  pin2 à (Xs+16, Ys+96)
  SYMBOL cap     Xs Ys R0  →  pin1 à (Xs+16, Ys+16)  /  pin2 à (Xs+16, Ys+96)
  SYMBOL ind     Xs Ys R0  →  pin1 à (Xs+16, Ys+16)  /  pin2 à (Xs+16, Ys+96)

RÈGLE DE CHAÎNAGE VERTICAL (série) :
  Pour chaîner deux composants passifs en série dans la même colonne :
  → placer le 2ème à Ys2 = Ys1 + 80 (même Xs)
  → leurs pins se rejoignent automatiquement : (Xs+16, Ys1+96) == (Xs+16, Ys2+16)
  Exemple : Xs=240, Ys1=80 → Ys2=160 → Ys3=240

RAIL SUPÉRIEUR :  y_top = Ys + 16  (pour le premier composant de la colonne)
MASSE source   :  FLAG Xs_vs (Ys_vs+96) 0
MASSE passifs  :  FLAG (Xs_pas+16) (Ys_dernier+96) 0

COMMANDES DE SIMULATION :
  TEXT 48 400 Left 2 !.op
  TEXT 48 400 Left 2 !.tran 10m
  TEXT 48 400 Left 2 !.ac dec 100 1 10Meg

── EXEMPLE 1 : Diviseur résistif VIN=10V R1=10k R2=10k ──
Version 4
SHEET 1 880 680
WIRE 80 96 256 96
WIRE 256 176 352 176
FLAG 80 176 0
FLAG 256 256 0
FLAG 352 176 VOUT
SYMBOL voltage 80 80 R0
WINDOW 123 0 0 Left 0
WINDOW 39 0 0 Left 0
SYMATTR InstName VIN
SYMATTR Value 10
SYMBOL res 240 80 R0
SYMATTR InstName R1
SYMATTR Value 10k
SYMBOL res 240 160 R0
SYMATTR InstName R2
SYMATTR Value 10k
TEXT 48 320 Left 2 !.op

── EXEMPLE 2 : Filtre RC passe-bas R=1k C=100n sinus 1kHz ──
Version 4
SHEET 1 880 680
WIRE 80 96 256 96
WIRE 256 176 352 176
FLAG 80 176 0
FLAG 256 256 0
FLAG 352 176 VOUT
SYMBOL voltage 80 80 R0
WINDOW 123 0 0 Left 0
WINDOW 39 0 0 Left 0
SYMATTR InstName V1
SYMATTR Value SINE(0 1 1k)
SYMBOL res 240 80 R0
SYMATTR InstName R1
SYMATTR Value 1k
SYMBOL cap 240 160 R0
SYMATTR InstName C1
SYMATTR Value 100n
TEXT 48 320 Left 2 !.tran 10m

── EXEMPLE 3 : RLC série R=100 L=10mH C=1µF sinus 1kHz, VOUT sur C1 ──
Version 4
SHEET 1 880 680
WIRE 80 96 256 96
WIRE 256 256 352 256
FLAG 80 176 0
FLAG 256 336 0
FLAG 352 256 VOUT
SYMBOL voltage 80 80 R0
WINDOW 123 0 0 Left 0
WINDOW 39 0 0 Left 0
SYMATTR InstName V1
SYMATTR Value SINE(0 1 1k)
SYMBOL res 240 80 R0
SYMATTR InstName R1
SYMATTR Value 100
SYMBOL ind 240 160 R0
SYMATTR InstName L1
SYMATTR Value 10m
SYMBOL cap 240 240 R0
SYMATTR InstName C1
SYMATTR Value 1u
TEXT 48 400 Left 2 !.tran 20m
"""


def _nettoyer_sortie_ia(texte: str) -> str:
    """Retire le markdown éventuel et coupe avant la première ligne 'Version'."""
    texte = re.sub(r"```[^\n]*\n?", "", texte)
    texte = texte.strip()
    m = re.search(r"^Version\s+\d", texte, re.MULTILINE)
    if m and m.start() > 0:
        texte = texte[m.start():]
    return texte


def _generer_asc_ia(enonce: str, client=None) -> str:
    """
    Appelle Claude (Haiku) pour générer un fichier .asc LTSpice complet.
    En cas d'échec retourne le contenu du template de secours general.asc.
    """
    try:
        if client is None:
            from anthropic import Anthropic
            from dotenv import load_dotenv
            load_dotenv()
            client = Anthropic()

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2000,
            system=_PROMPT_GENERATION_ASC,
            messages=[{
                "role": "user",
                "content": f"Génère le fichier .asc LTSpice pour ce circuit : {enonce}",
            }],
        )
        asc = _nettoyer_sortie_ia(response.content[0].text)
        if "Version 4" in asc and "SHEET" in asc:
            return asc
    except Exception:
        pass

    # Fallback : template vide
    chemin = os.path.join(TEMPLATES_DIR, "general.asc")
    with open(chemin, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 4. Point d'entrée public
# ---------------------------------------------------------------------------

_PROMPT_ANALYSE_CIRCUIT = """\
Tu es un expert en circuits électroniques et LTSpice. Analyse la description de circuit
fournie et retourne un JSON structuré identifiant le template LTSpice le plus adapté.

Templates disponibles (paramètres en unités SI de base) :
  "diviseur_resistif_fixe"     : VIN (V), R1 (Ω), R2 (Ω)
  "diviseur_resistif_variable" : VIN (V), R1 (Ω)
  "rc_sinus_temporel"          : R1 (Ω), C1 (F), Vamp (V), freq (Hz)
  "rc_sinus_frequentiel"       : R1 (Ω), C1 (F), f_start (Hz), f_stop (Hz)
  "zener_diviseur"             : VIN (V, amplitude), R1 (Ω, résistance série), R2 (Ω, charge en parallèle avec la Zener), freq (Hz)
  "stabilisateur_tension_zener": Vamp (V), freq (Hz), R1 (Ω, résistance série)
  "amplificateur_bipolaire"    : VCC (V), Vamp (V), freq (Hz), RC (Ω), RE (Ω), R1 (Ω), R2 (Ω)
  "general"                    : tout autre circuit non couvert par les templates ci-dessus

Réponds UNIQUEMENT avec un JSON valide (pas de markdown, pas de texte avant/après) :
{
  "type_circuit": "<type>",
  "parametres": { "<nom>": <valeur_float_SI>, ... },
  "explication": "<une courte phrase justifiant le choix du template>"
}

Règles :
- Convertis les préfixes SI : k→×1000, n→×1e-9, µ/u→×1e-6, p→×1e-12, meg→×1e6
- N'inclus QUE les paramètres effectivement mentionnés dans la description
- Utilise un template connu dès que la topologie correspond, même si les noms diffèrent
- Pour "zener_diviseur" : R1 = résistance série (limiteuse de courant), R2 = charge parallèle à la Zener
- Pour "amplificateur_bipolaire" : R1/R2 = pont diviseur de polarisation de base
"""


def analyser_enonce_ia(enonce: str, client=None) -> dict:
    """
    Utilise Claude Haiku pour analyser un énoncé libre et identifier le meilleur template.
    Retourne {"type_circuit": str, "parametres": {str: float}, "explication": str}.
    """
    import json as _json

    if client is None:
        from anthropic import Anthropic
        from dotenv import load_dotenv
        load_dotenv()
        client = Anthropic()

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=_PROMPT_ANALYSE_CIRCUIT,
        messages=[{"role": "user", "content": enonce}],
    )
    texte = re.sub(r"```[^\n]*\n?", "", response.content[0].text).strip()
    try:
        data = _json.loads(texte)
        return {
            "type_circuit": data.get("type_circuit", "general"),
            "parametres":   {k: float(v) for k, v in data.get("parametres", {}).items()},
            "explication":  data.get("explication", ""),
        }
    except (ValueError, KeyError):
        return {"type_circuit": "general", "parametres": {}, "explication": ""}


def generer_asc_depuis_params(
    type_circuit: str,
    params: dict,
    enonce_ia: str = None,
    client=None,
) -> dict:
    """
    Génère le fichier .asc depuis des paramètres explicites (formulaire ou analyse IA).
    Pour type "general", enonce_ia est utilisé comme prompt de génération.
    params : {str: float} — valeurs en unités SI de base.
    """
    ia_generated = False

    if type_circuit == "general":
        asc_content  = _generer_asc_ia(enonce_ia or "circuit général", client)
        fichier      = "general.asc"
        ia_generated = True
    else:
        fichier = TEMPLATE_MAP[type_circuit]
        chemin  = os.path.join(TEMPLATES_DIR, fichier)
        with open(chemin, "r", encoding="utf-8") as f:
            asc_content = f.read()
        asc_content = _APPLIQUER[type_circuit](asc_content, params)

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=f"_{type_circuit}.asc",
        delete=False,
        encoding="utf-8",
    )
    tmp.write(asc_content)
    tmp.close()

    return {
        "asc_path":         tmp.name,
        "asc_content":      asc_content,
        "parametres":       params,
        "parametres_bruts": {k: str(v) for k, v in params.items()},
        "type_circuit":     type_circuit,
        "template_fichier": fichier,
        "ia_generated":     ia_generated,
    }
