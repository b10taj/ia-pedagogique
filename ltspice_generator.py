"""
ltspice_generator.py
Backend pour la génération automatique de fichiers LTSpice .asc depuis un énoncé textuel.
Ne dépend pas de Streamlit — retourne des données brutes exploitables par l'UI.

Circuits supportés :
  - diviseur_resistif_fixe     : Diviseur résistif avec résistances fixes (VIN, R1, R2)
  - diviseur_resistif_variable : Diviseur avec résistance variable (sweep .step param)
  - rc_sinus_temporel          : RC + signal sinusoïdal, analyse temporelle (.tran)
  - rc_sinus_frequentiel       : RC + signal AC, diagramme de Bode (.ac)
  - general                    : Circuit quelconque, généré par Claude IA
"""

import re
import os
import tempfile
import unicodedata

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

TEMPLATE_MAP = {
    "diviseur_resistif_fixe":    "diviseur_resistif_fixe.asc",
    "diviseur_resistif_variable": "diviseur_resistif_variable.asc",
    "rc_sinus_temporel":         "rc_sinus_temporel.asc",
    "rc_sinus_frequentiel":      "rc_sinus_frequentiel.asc",
    "general":                   "general.asc",
}

# ---------------------------------------------------------------------------
# Utilitaires texte
# ---------------------------------------------------------------------------

def _normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFKC", texte)
    texte = texte.lower()
    texte = re.sub(r"\s+", " ", texte)
    return texte


def _parse_valeur(s: str) -> float | None:
    """
    Convertit une chaîne LTSpice/texte en float SI.
    Ex: '4.7k' → 4700.0, '100n' → 1e-7, '2.2meg' → 2.2e6.
    """
    if not s:
        return None
    s = s.strip().lower().replace(",", ".")
    prefixes = [
        ("meg", 1e6), ("k", 1e3),
        ("m",   1e-3), ("u", 1e-6), ("µ", 1e-6), ("micro", 1e-6),
        ("n",   1e-9), ("nano", 1e-9),
        ("p",   1e-12),
    ]
    for suffix, factor in prefixes:
        if s.endswith(suffix):
            num = s[: -len(suffix)]
            try:
                return float(num) * factor
            except ValueError:
                return None
    # Strip trailing unit labels that don't affect magnitude
    s_clean = re.sub(r"[a-zΩω°]+$", "", s)
    try:
        return float(s_clean) if s_clean else None
    except ValueError:
        return None


def _parse_freq(s: str) -> float | None:
    """
    Convertit une chaîne de fréquence en Hz.
    Ex: '10kHz' → 10000.0, '1MHz' → 1e6, '50' → 50.0.
    """
    if not s:
        return None
    s = s.strip().lower().replace(",", ".")
    if s.endswith("mhz"):
        try:
            return float(s[:-3]) * 1e6
        except ValueError:
            return None
    if s.endswith("khz"):
        try:
            return float(s[:-3]) * 1e3
        except ValueError:
            return None
    if s.endswith("hz"):
        try:
            return float(s[:-2])
        except ValueError:
            return None
    # Fallback: treat as plain LTSpice value
    return _parse_valeur(s)


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


def _extraire_groupe(pattern: str, texte: str) -> str | None:
    """Cherche le pattern dans texte et retourne le premier groupe capturé non-None."""
    m = re.search(pattern, texte, re.IGNORECASE)
    if not m:
        return None
    for g in m.groups():
        if g is not None:
            return g.strip()
    return None


# ---------------------------------------------------------------------------
# 1. Détection du type de circuit
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 1. Détection du type de circuit
# ---------------------------------------------------------------------------

def _detecter_type(texte: str) -> str:
    """Retourne le type de circuit depuis le texte normalisé."""

    # Priorité 0 – demande explicite de circuit général / personnalisé
    if re.search(
        r"g[eé]n[eé]ral|personnalis[eé]|custom|libre|quelconque|"
        r"autre.*circuit|circuit.*autre|de.*z[eé]ro|from.*scratch",
        texte,
    ):
        return "general"

    # Priorité 1 – circuits hors-template connus (trigger IA)
    if re.search(
        r"ampli.?op\b|op.?amp\b|\baop\b|opamp|"
        r"\brlc\b|\blc\b|inductance|bobine|"
        r"passe.haut|passe.bande|rejecteur|"
        r"oscillateur|trigger|schmitt|"
        r"transistor|bjt|mosfet|\bfet\b|"
        r"diode|zener|rectif|"
        r"\b555\b|ne555|timer|"
        r"pont.*wheatstone|wheatstone|"
        r"pont.*de.*wien|wien",
        texte,
    ):
        return "general"

    # Priorité 2 – résistance variable / potentiomètre
    if re.search(
        r"variable|potentio|pot\b|rh[eé]ostat|r_?var|rvar|"
        r"diviseur.*vari|vari.*diviseur",
        texte,
    ):
        return "diviseur_resistif_variable"

    # Priorité 3 – Bode / analyse fréquentielle
    if re.search(
        r"bode|fr[eé]quentiel|diagramme.*gain|gain.*phase|"
        r"analyse.*fr[eé]q|\.ac\b|balayage.*fr[eé]q",
        texte,
    ):
        return "rc_sinus_frequentiel"

    # Priorité 4 – RC + signal sinusoïdal temporel
    if re.search(
        r"sinus|sinuso[iï]dal|temporel|\.tran\b|"
        r"r[eé]ponse.*temps|signal.*sin|analyse.*temp",
        texte,
    ):
        return "rc_sinus_temporel"

    # Priorité 5 – diviseur résistif fixe (explicite ou R1+R2+VIN)
    if re.search(
        r"diviseur|pont.*r[eé]sist|voltage.*divid|"
        r"r1.*r2|r_?1.*r_?2",
        texte,
    ):
        return "diviseur_resistif_fixe"

    # Priorité 6 – circuit RC sans autre précision → temporel
    if re.search(r"\brc\b|r[eé]sistance.*capa|capa.*r[eé]sist", texte):
        return "rc_sinus_temporel"

    # Fallback – rien de reconnu → IA
    return "general"


# ---------------------------------------------------------------------------
# 2. Extraction des paramètres selon le type
# ---------------------------------------------------------------------------

def _extraire_parametres(texte: str, type_circuit: str) -> tuple[dict, dict]:
    """
    Retourne (params_bruts: {str→str}, params_float: {str→float}).
    """
    bruts: dict[str, str] = {}
    floats: dict[str, float] = {}

    def _cap(cle: str, pattern: str, parser=_parse_valeur):
        val = _extraire_groupe(pattern, texte)
        if val:
            bruts[cle] = val
            parsed = parser(val)
            if parsed is not None:
                floats[cle] = parsed

    # ── Paramètres communs à tous les circuits ──────────────────────────
    # Résistance(s)
    _cap("R1",
         r"r1\s*[=:]\s*([\d.,]+\s*(?:meg|k|m|u|µ|n|p)?)"
         r"|r[_\s]?1\s*[=:]\s*([\d.,]+\s*(?:meg|k|m|u|µ|n|p)?)")

    if not bruts.get("R1"):
        # Résistance générique : R = ...  ou  r = ...
        _cap("R1",
             r"\br\s*[=:]\s*([\d.,]+\s*(?:meg|k|m|u|µ|n|p)?)")

    # ── Paramètres spécifiques ──────────────────────────────────────────
    if type_circuit in ("diviseur_resistif_fixe", "diviseur_resistif_variable"):
        # Tension d'alimentation
        _cap("VIN",
             r"v(?:in|s|cc|alim|source|dd)?\s*[=:]\s*([\d.,]+\s*(?:meg|k|m|u|µ|n|p|v)?)")
        # R2 (seulement pour le diviseur fixe)
        if type_circuit == "diviseur_resistif_fixe":
            _cap("R2",
                 r"r2\s*[=:]\s*([\d.,]+\s*(?:meg|k|m|u|µ|n|p)?)"
                 r"|r[_\s]?2\s*[=:]\s*([\d.,]+\s*(?:meg|k|m|u|µ|n|p)?)")

    if type_circuit in ("rc_sinus_temporel", "rc_sinus_frequentiel"):
        # Capacité
        _cap("C1",
             r"c1\s*[=:]\s*([\d.,]+\s*(?:meg|k|m|u|µ|n|p)?)"
             r"|c\s*[=:]\s*([\d.,]+\s*(?:meg|k|m|u|µ|n|p)?)")

    if type_circuit == "rc_sinus_temporel":
        # Amplitude
        _cap("Vamp",
             r"v(?:amp|p(?:eak)?|cr[eê]te|max)\s*[=:]\s*([\d.,]+)"
             r"|amplitude\s*(?:de\s*)?([\d.,]+)")
        # Fréquence
        _cap("freq",
             r"f(?:r[eé]q(?:uence)?)?\s*[=:]\s*([\d.,]+\s*(?:meg|k|mhz|khz|hz)?)"
             r"|([\d.,]+)\s*(?:k?hz|mhz|khz)",
             parser=_parse_freq)

    if type_circuit == "rc_sinus_frequentiel":
        # Plage de fréquence pour .ac : "de X à Y"
        m_range = re.search(
            r"de\s+([\d.,]+\s*(?:meg|k|mhz|khz|hz)?)\s*[àa]\s*([\d.,]+\s*(?:meg|k|mhz|khz|hz)?)",
            texte,
            re.IGNORECASE,
        )
        if m_range:
            fstart = _parse_freq(m_range.group(1))
            fstop = _parse_freq(m_range.group(2))
            if fstart:
                bruts["f_start"] = m_range.group(1)
                floats["f_start"] = fstart
            if fstop:
                bruts["f_stop"] = m_range.group(2)
                floats["f_stop"] = fstop

    return bruts, floats


# ---------------------------------------------------------------------------
# 3. Modification du fichier .asc
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
    correspond à <prefixe_cmd>.
    Ex: prefixe_cmd='.tran', nouvelle_cmd='.tran 5m'
    """
    def _rempl(m):
        return m.group(0).replace(m.group(1), nouvelle_cmd)

    pattern = rf"(!({re.escape(prefixe_cmd)}\b[^\n]*))"
    return re.sub(pattern, _rempl, asc_content, flags=re.IGNORECASE)


# ---------------------------------------------------------------------------
# 4. Application des paramètres par type de circuit
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


_APPLIQUER = {
    "diviseur_resistif_fixe":    _appliquer_diviseur_fixe,
    "diviseur_resistif_variable": _appliquer_diviseur_variable,
    "rc_sinus_temporel":         _appliquer_rc_temporel,
    "rc_sinus_frequentiel":      _appliquer_rc_frequentiel,
    # "general" est géré séparément (génération IA)
}


# ---------------------------------------------------------------------------
# 5. Génération IA pour les circuits hors-template
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
# 6. Point d'entrée public
# ---------------------------------------------------------------------------

def analyser_enonce(enonce: str) -> dict:
    """
    Analyse l'énoncé et retourne le type détecté + les paramètres extraits.
    {
        "type_circuit": str,
        "parametres": {nom: float},
        "parametres_bruts": {nom: str}
    }
    """
    texte = _normaliser(enonce)
    type_circuit = _detecter_type(texte)
    bruts, floats = _extraire_parametres(texte, type_circuit)
    return {
        "type_circuit": type_circuit,
        "parametres": floats,
        "parametres_bruts": bruts,
    }


def generer_asc_depuis_enonce(enonce: str, client=None) -> dict:
    """
    Analyse l'énoncé, génère le fichier .asc (template ou IA) et retourne :
    {
        "asc_path": str,          # chemin du fichier temporaire
        "asc_content": str,       # contenu (pour st.download_button)
        "parametres": dict,       # valeurs float détectées
        "parametres_bruts": dict, # valeurs texte telles que dans l'énoncé
        "type_circuit": str,
        "template_fichier": str,
        "ia_generated": bool,     # True si le fichier a été généré par IA
    }
    """
    analyse = analyser_enonce(enonce)
    type_circuit = analyse["type_circuit"]
    parametres   = analyse["parametres"]
    ia_generated = False

    if type_circuit == "general":
        # Génération complète par Claude
        asc_content  = _generer_asc_ia(enonce, client)
        fichier      = "general.asc"
        ia_generated = True
    else:
        # Template fixe + remplacement des valeurs
        fichier = TEMPLATE_MAP[type_circuit]
        chemin  = os.path.join(TEMPLATES_DIR, fichier)
        with open(chemin, "r", encoding="utf-8") as f:
            asc_content = f.read()
        asc_content = _APPLIQUER[type_circuit](asc_content, parametres)

    # Écriture dans un fichier temporaire
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
        "parametres":       parametres,
        "parametres_bruts": analyse["parametres_bruts"],
        "type_circuit":     type_circuit,
        "template_fichier": fichier,
        "ia_generated":     ia_generated,
    }
