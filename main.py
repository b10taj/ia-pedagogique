# main.py
import os
import re
import numpy as np
import matplotlib.pyplot as plt
from anthropic import Anthropic
from dotenv import load_dotenv

# Import des prompts depuis le module prompts
from prompts import (
    PROMPT_DIODE_SIMPLE,
    PROMPT_DIODE_BOITES,
    PROMPT_DIODE_ZENER_SIMPLE,
    PROMPT_TRANSISTOR_BIPOLAIRE,
    PROMPT_INVERSEUR_BIPOLAIRE,
    PROMPT_DIVISEUR_TENSION,
    PROMPT_PREMIER_ORDRE_PASSE_BAS,
    PROMPT_PREMIER_ORDRE_SIGNAL_CARRE,
    PROMPT_PREMIER_ORDRE_SIGNAL_CARRE_CRETE,
    PROMPT_THEVENIN_RC_SIGNAL_CARRE,
    PROMPT_PUISSANCE_SERIE,
    PROMPT_PUISSANCE_PARALLELE,
    PROMPT_PUISSANCE_DEUX_SOURCES,
    PROMPT_GENERAL
)

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def construire_message_avec_image(prompt: str, image_base64: str = None):
    """Construit un message avec texte et optionnellement une image."""
    content = [{"type": "text", "text": prompt}]
    
    if image_base64:
        # Extraire le type MIME et les données base64
        if "data:image/" in image_base64:
            media_type = image_base64.split("data:")[1].split(";")[0]
            data = image_base64.split(",")[1]
        else:
            media_type = "image/jpeg"
            data = image_base64
        
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": data
            }
        })
    
    return content

def nettoyer_reponse_sans_code(texte: str) -> str:
    """Retire les blocs de code si le modèle en génère malgré les consignes."""
    texte_sans_blocs = re.sub(r"```[\s\S]*?```", "", texte)
    texte_sans_imports = re.sub(r"(?im)^\s*(import\s+.+|from\s+.+\s+import\s+.+)\s*$", "", texte_sans_blocs)
    return re.sub(r"\n{3,}", "\n\n", texte_sans_imports).strip()

def detecter_type_probleme(question: str) -> str:
    """Détecte le type de problème électronique dans la question."""
    question_lower = question.lower()

    def contient_un_mot_cle(texte: str, mots_cles: list[str]) -> bool:
        """Évite les faux positifs en imposant des frontières de mot pour les mots-clés courts."""
        for mot in mots_cles:
            mot_lower = mot.lower()
            if len(mot_lower) <= 2:
                if re.search(rf"\b{re.escape(mot_lower)}\b", texte):
                    return True
            else:
                if mot_lower in texte:
                    return True
        return False

    def contient_parametres_rc(texte: str) -> bool:
        """Détecte explicitement la présence de R=... et C=... dans l'énoncé."""
        has_r = re.search(r"\br\s*=\s*\d+(?:[\.,]\d+)?", texte) is not None
        has_c = re.search(r"\bc\s*=\s*\d+(?:[\.,]\d+)?", texte) is not None
        has_r1 = re.search(r"\br1\s*=\s*\d+(?:[\.,]\d+)?", texte) is not None
        has_r2 = re.search(r"\br2\s*=\s*\d+(?:[\.,]\d+)?", texte) is not None
        has_r3 = re.search(r"\br3\s*=\s*\d+(?:[\.,]\d+)?", texte) is not None
        contient_parametres_rc.has_r3 = has_r3  # expose pour la détection Thévenin
        return (has_r and has_c) or (has_r1 and has_r2 and has_c)
    
    # D'ABORD : vérifier si c'est une Zener (avant de vérifier diode normale)
    # Être STRICT : seulement les vrais indicateurs Zener
    keywords_zener = ["zener", "vz", "tension zener", "mode inverse", "conduction inverse"]
    is_zener = contient_un_mot_cle(question_lower, keywords_zener)
    
    # Mots-clés pour circuit à diode (priorité très haute)
    keywords_diode = [
        "diode", "silicium", "anode", "cathode", "vd", "id", "redressement",
        # Aussi reconnaître les boîtes noires / indéterminée
        "boîte noire", "boite noire", "boîtes noires", "boites noires",
        "indéterminé", "indetermine", "inconnu", "inconnue",
        # Aussi reconnaître les configurations R-D ou D-R
        "r-d", "d-r", "configuration"
    ]
    keywords_diode_boites = [
        # Avec accents
        "boîte noire", "boîtes noires", 
        # Sans accents (variation courante)
        "boite noire", "boites noires",
        # Variantes avec X et Y
        "x et y", "x and y", "X et Y",
        # Indéterminé
        "indéterminé", "indetermine", "inconnue", "inconnu",
        # Black box en anglais
        "black box"
    ]
    keywords_diode_simple = ["r et d", "r puis d", "d puis r", "configuration", "r-d", "d-r"]
    
    # Mots-clés pour inverseur bipolaire
    keywords_inverseur = ["inverseur", "vout=f(vin)", "courbe vout", "pente", "zone linéaire", 
                         "bloqué", "saturé", "limite", "f(vin)"]
    
    # Mots-clés pour transistor bipolaire
    keywords_transistor = ["transistor", "bjt", "npn", "pnp", "collecteur", "base", "émetteur", 
                          "gain", "beta", "hfe", "ic", "ib", "vce"]
    
    # Mots-clés pour diviseur de tension
    keywords_diviseur = ["diviseur", "résistif", "r1", "r2"]

    # Mots-clés pour filtre passe-bas du premier ordre
    keywords_premier_ordre = [
        "passe-bas", "passe bas", "premier ordre", "1er ordre", "filtre rc",
        "condensateur", "constante de temps", "réponse indicielle", "saut",
        "echelon", "échelon", "transitoire", "rc"
    ]

    # Mots-clés pour RC soumis à un signal carré
    keywords_signal_carre = [
        "signal carré", "signal carre", "carré", "carre", "créneau", "creneau",
        "période", "periode", "demi-période", "demi periode", "niveau bas", "niveau haut"
    ]

    # Mots-clés pour le cas période courte / valeurs de crête
    keywords_signal_carre_crete = [
        "valeurs de crête", "valeurs de crete", "crête", "crete", "vmax", "vmin",
        "période très courte", "periode tres courte", "demi-période trop courte", "demi periode trop courte",
        "charge incomplète", "charge incomplete", "décharge incomplète", "decharge incomplete", "ondulation"
    ]
    
    # Mots-clés pour puissance dans une maille résistive série
    keywords_puissance_serie = [
        "puissance", "absorbée", "absorbee", "fournie", "fournie par vin",
        "une seule maille", "maille", "u=ri", "p=ui", "source de tension",
        "résistances en série", "resistances en serie"
    ]

    # Mots-clés pour puissance avec source de courant et résistances en parallèle
    keywords_puissance_parallele = [
        "source de courant", "i0", "i_0", "courant source",
        "parallèle", "parallel", "en parallèle", "resistances en parallele",
        "exercice_4.2", "exercice 4.2"
    ]

    # Mots-clés pour puissance avec deux sources de tension et une résistance
    keywords_puissance_deux_sources = [
        "deux sources", "v1", "v2", "source v1", "source v2",
        "trois puissances", "qui absorbe", "qui fournit",
        "sources de tension", "séparées par une résistance", "separees par une resistance"
    ]
    
    a_contexte_premier_ordre = contient_un_mot_cle(question_lower, keywords_premier_ordre)
    a_contexte_signal_carre = contient_un_mot_cle(question_lower, keywords_signal_carre)
    a_contexte_signal_carre_crete = contient_un_mot_cle(question_lower, keywords_signal_carre_crete)
    a_elements_rc = (
        (contient_un_mot_cle(question_lower, ["résistance", "resistance", "résistances", "resistances"]) and contient_un_mot_cle(question_lower, ["condensateur", "capacité", "capacite", "c="]))
        or contient_parametres_rc(question_lower)
    )
    est_premier_ordre = a_contexte_premier_ordre and a_elements_rc
    est_signal_carre_rc = a_contexte_signal_carre and a_elements_rc
    est_signal_carre_rc_crete = est_signal_carre_rc and a_contexte_signal_carre_crete

    # Détection Thévenin RC : "thévenin"/"r3" + signal carré + RC
    keywords_thevenin_rc = ["thévenin", "thevenin", "exercice_4"]
    a_r3 = getattr(contient_parametres_rc, "has_r3", False)
    est_thevenin_rc_signal_carre = est_signal_carre_rc and (
        contient_un_mot_cle(question_lower, keywords_thevenin_rc)
        or (
            a_r3
            and contient_un_mot_cle(question_lower, ["parallèle", "parallele", "r2 //", "r2//", "//c", "// c"])
        )
        or re.search(r"\br3\s*=\s*\d+", question_lower) is not None
    )

    # Ordre de priorité : diode > signal carré RC (crêtes) > signal carré RC > premier ordre > inverseur > puissance parallèle/série > transistor > diviseur > general
    if contient_un_mot_cle(question_lower, keywords_diode):
        if is_zener:
            # Zener : toujours en mode SIMPLE (boîtes noires trop compliqué)
            return "diode_zener_simple"
        # Sous-distinction pour diode ordinaire : boîtes noires vs simple
        if contient_un_mot_cle(question_lower, keywords_diode_boites):
            return "diode_boites"
        return "diode_simple"
    elif est_signal_carre_rc_crete:
        return "premier_ordre_signal_carre_crete"
    elif est_thevenin_rc_signal_carre:
        return "thevenin_rc_signal_carre"
    elif est_signal_carre_rc:
        return "premier_ordre_signal_carre"
    elif est_premier_ordre:
        return "premier_ordre_passe_bas"
    elif contient_un_mot_cle(question_lower, keywords_inverseur):
        return "inverseur"
    elif contient_un_mot_cle(question_lower, keywords_puissance_deux_sources):
        return "puissance_deux_sources"
    elif contient_un_mot_cle(question_lower, keywords_puissance_parallele):
        return "puissance_parallele"
    elif contient_un_mot_cle(question_lower, keywords_puissance_serie):
        return "puissance_serie"
    elif contient_un_mot_cle(question_lower, keywords_transistor):
        return "transistor"
    elif contient_un_mot_cle(question_lower, keywords_diviseur):
        return "diviseur"
    else:
        return "general"

def expliquer_diviseur_tension(question: str, image_base64: str = None) -> str:
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_DIVISEUR_TENSION.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    return response.content[0].text.strip()

def expliquer_premier_ordre_passe_bas(question: str, image_base64: str = None) -> str:
    """Analyse d'un filtre passe-bas RC du premier ordre soumis à un saut."""
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_PREMIER_ORDRE_PASSE_BAS.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1600,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    texte = response.content[0].text.strip()
    return nettoyer_reponse_sans_code(texte)

def expliquer_premier_ordre_signal_carre(question: str, image_base64: str = None) -> str:
    """Analyse d'un RC du premier ordre soumis à un signal carré."""
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_PREMIER_ORDRE_SIGNAL_CARRE.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1600,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    texte = response.content[0].text.strip()
    return nettoyer_reponse_sans_code(texte)

def expliquer_thevenin_rc_signal_carre(question: str, image_base64: str = None) -> str:
    """Analyse Thévenin d'un RC à trois résistances soumis à un signal carré."""
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_THEVENIN_RC_SIGNAL_CARRE.format(question=question, image_info=image_info)
    content = construire_message_avec_image(prompt, image_base64)
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1800,
        messages=[{"role": "user", "content": content}]
    )
    texte = response.content[0].text.strip()
    return nettoyer_reponse_sans_code(texte)

def expliquer_premier_ordre_signal_carre_crete(question: str, image_base64: str = None) -> str:
    """Analyse d'un RC soumis à un signal carré avec période courte (calcul des crêtes)."""
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_PREMIER_ORDRE_SIGNAL_CARRE_CRETE.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1600,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    texte = response.content[0].text.strip()
    return nettoyer_reponse_sans_code(texte)

def expliquer_puissance_serie(question: str, image_base64: str = None) -> str:
    """Analyse d'une maille unique avec résistances en série et calculs de puissance."""
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_PUISSANCE_SERIE.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=700,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    return response.content[0].text.strip()

def expliquer_puissance_parallele(question: str, image_base64: str = None) -> str:
    """Analyse source de courant avec deux résistances en parallèle et calculs de puissance."""
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_PUISSANCE_PARALLELE.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=900,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    return response.content[0].text.strip()

def expliquer_puissance_deux_sources(question: str, image_base64: str = None) -> str:
    """Analyse d'une maille avec deux sources de tension et une résistance, avec bilan de puissance."""
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_PUISSANCE_DEUX_SOURCES.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=800,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    return response.content[0].text.strip()

def expliquer_transistor_bipolaire(question: str, image_base64: str = None) -> str:
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_TRANSISTOR_BIPOLAIRE.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=600,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    return response.content[0].text.strip()

def expliquer_inverseur_bipolaire(question: str, image_base64: str = None) -> str:
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_INVERSEUR_BIPOLAIRE.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    return response.content[0].text.strip()

def expliquer_probleme(question: str, image_base64: str = None) -> str:
    """Fonction générale qui détecte le type et envoie au bon assistant."""
    type_probleme = detecter_type_probleme(question)
    
    if type_probleme == "diode_zener_simple":
        reponse = expliquer_diode_zener_simple(question, image_base64)
    elif type_probleme == "diode_boites":
        reponse = expliquer_diode_boites(question, image_base64)
    elif type_probleme == "diode_simple":
        reponse = expliquer_diode_simple(question, image_base64)
    elif type_probleme == "premier_ordre_signal_carre_crete":
        reponse = expliquer_premier_ordre_signal_carre_crete(question, image_base64)
    elif type_probleme == "thevenin_rc_signal_carre":
        reponse = expliquer_thevenin_rc_signal_carre(question, image_base64)
    elif type_probleme == "premier_ordre_signal_carre":
        reponse = expliquer_premier_ordre_signal_carre(question, image_base64)
    elif type_probleme == "premier_ordre_passe_bas":
        reponse = expliquer_premier_ordre_passe_bas(question, image_base64)
    elif type_probleme == "inverseur":
        reponse = expliquer_inverseur_bipolaire(question, image_base64)
    elif type_probleme == "transistor":
        reponse = expliquer_transistor_bipolaire(question, image_base64)
    elif type_probleme == "puissance_deux_sources":
        reponse = expliquer_puissance_deux_sources(question, image_base64)
    elif type_probleme == "puissance_parallele":
        reponse = expliquer_puissance_parallele(question, image_base64)
    elif type_probleme == "puissance_serie":
        reponse = expliquer_puissance_serie(question, image_base64)
    elif type_probleme == "diviseur":
        reponse = expliquer_diviseur_tension(question, image_base64)
    else:
        # Pour les autres problèmes généraux
        image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
        prompt = PROMPT_GENERAL.format(question=question, image_info=image_info)
        content = construire_message_avec_image(prompt, image_base64)
        
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[
                {"role": "user", "content": content}
            ]
        )
        reponse = response.content[0].text.strip()
    
    return reponse

def extraire_parametres_passe_bas_premier_ordre(question: str) -> dict | None:
    """Extrait les paramètres usuels d'un exercice RC du premier ordre."""
    texte = question.lower().replace(",", ".")

    def convertir_prefixe(valeur: float, prefixe: str | None) -> float:
        multiplicateurs = {
            "": 1.0,
            "micro": 1e-6,
            "nano": 1e-9,
            "k": 1e3,
            "m": 1e-3,
            "u": 1e-6,
            "µ": 1e-6,
            "n": 1e-9,
            "p": 1e-12,
            "meg": 1e6,
        }
        return valeur * multiplicateurs.get(prefixe or "", 1.0)

    resistance_match = re.search(
        r"\br\s*=\s*(\d+(?:\.\d+)?)\s*(meg|k|m|u|µ|n|p)?\s*(?:ohms?|Ω)?",
        texte,
    )
    capacite_match = re.search(
        r"\bc\s*=\s*(\d+(?:\.\d+)?)\s*(micro|nano|meg|k|m|u|µ|n|p)?\s*(?:f|farad|farads)?",
        texte,
    )

    if not resistance_match or not capacite_match:
        return None

    resistance = convertir_prefixe(float(resistance_match.group(1)), resistance_match.group(2))
    capacite = convertir_prefixe(float(capacite_match.group(1)), capacite_match.group(2))

    vin_initial = 0.0
    vin_final = None
    vin_final_2 = None
    temps_second_saut = None

    initial_match = re.search(r"v(?:in)?\s*\(t\)?[^.\n]*?vaut\s*(\-?\d+(?:\.\d+)?)\s*v\s*avant le saut", texte)
    if initial_match:
        vin_initial = float(initial_match.group(1))

    initial_match_alt = re.search(r"v(?:in)?\s*\(t\)?[^.\n]*?val(?:ant|oir)\s*(\-?\d+(?:\.\d+)?)\s*v\s*avant le saut", texte)
    if initial_match_alt:
        vin_initial = float(initial_match_alt.group(1))

    transition_match = re.search(
        r"passe\s+de\s*(\-?\d+(?:\.\d+)?)\s*v\s+à\s*(\-?\d+(?:\.\d+)?)\s*v",
        texte,
    )
    if transition_match:
        vin_initial = float(transition_match.group(1))
        vin_final = float(transition_match.group(2))

    saut_match = re.search(r"saut\s+de\s*(\-?\d+(?:\.\d+)?)\s*v", texte)
    if vin_final is None and saut_match:
        vin_final = vin_initial + float(saut_match.group(1))

    sauts = [float(val) for val in re.findall(r"saut(?:\s+[a-zàâäéèêëîïôöùûüç]+){0,3}\s+de\s*([+\-]?\d+(?:\.\d+)?)\s*v", texte)]
    if sauts and vin_final is None:
        vin_final = vin_initial + sauts[0]

    if len(sauts) >= 2:
        vin_final_2 = (vin_initial + sauts[0]) + sauts[1]

    second_saut_temps_match = re.search(
        r"(?:au bout de|apres|après|à\s*t\s*=|a\s*t\s*=)\s*(\d+(?:\.\d+)?)\s*(ms|s)",
        texte,
    )
    if second_saut_temps_match:
        valeur = float(second_saut_temps_match.group(1))
        unite = second_saut_temps_match.group(2)
        temps_second_saut = valeur / 1000.0 if unite == "ms" else valeur

    # Cas fréquent: "puis ... saut ..." sans précision explicite de vin_final_2
    if vin_final_2 is None and len(sauts) >= 2 and vin_final is not None:
        vin_final_2 = vin_final + sauts[1]

    if vin_final is None:
        final_match = re.search(r"(?:après le saut|valeur finale)\s*(?:vaut|=)?\s*(\-?\d+(?:\.\d+)?)\s*v", texte)
        if final_match:
            vin_final = float(final_match.group(1))

    if vin_final is None:
        return None

    return {
        "resistance": resistance,
        "capacite": capacite,
        "vin_initial": vin_initial,
        "vin_final": vin_final,
        "temps_second_saut": temps_second_saut,
        "vin_final_2": vin_final_2,
    }

def extraire_parametres_signal_carre_rc(question: str) -> dict | None:
    """Extrait les paramètres d'un exercice RC soumis à un signal carré."""
    texte = question.lower().replace(",", ".")

    def extraire_valeur(prefixes: list[str], unites: list[str]) -> float | None:
        pattern_prefixes = "|".join(re.escape(p) for p in prefixes)
        pattern_unites = "|".join(re.escape(u) for u in unites)
        m = re.search(rf"(?:{pattern_prefixes})\s*=\s*(\d+(?:\.\d+)?)\s*(micro|meg|k|m|u|µ|n|p)?\s*(?:{pattern_unites})?", texte)
        if not m:
            return None
        val = float(m.group(1))
        prefixe = m.group(2) or ""
        scale = {
            "": 1.0,
            "micro": 1e-6,
            "nano": 1e-9,
            "k": 1e3,
            "m": 1e-3,
            "u": 1e-6,
            "µ": 1e-6,
            "n": 1e-9,
            "p": 1e-12,
            "meg": 1e6,
        }
        return val * scale.get(prefixe, 1.0)

    r1 = extraire_valeur(["r1"], ["ohm", "ohms", "ω"])
    r2 = extraire_valeur(["r2"], ["ohm", "ohms", "ω"])
    c = extraire_valeur(["c"], ["f", "farad", "farads"])
    t = extraire_valeur(["période", "periode", "t"], ["s", "ms", "us", "µs"])

    # Si l'extraction de T via l'unité est ambiguë, on récupère explicitement "période vaut ..."
    periode_match = re.search(r"période(?:\s+du\s+signal\s+carré|\s+du\s+signal\s+carre)?\s*(?:vaut|=)?\s*(\d+(?:\.\d+)?)\s*(ms|s|us|µs)", texte)
    if periode_match:
        val = float(periode_match.group(1))
        u = periode_match.group(2)
        if u == "ms":
            t = val / 1000.0
        elif u in ("us", "µs"):
            t = val / 1e6
        else:
            t = val

    bas_match = re.search(r"niveau\s+bas\s+(?:de|=)\s*(\-?\d+(?:\.\d+)?)\s*v", texte)
    haut_match = re.search(r"niveau\s+haut\s+(?:de|=)\s*(\-?\d+(?:\.\d+)?)\s*v", texte)
    v_bas = float(bas_match.group(1)) if bas_match else None
    v_haut = float(haut_match.group(1)) if haut_match else None

    if r1 is None or r2 is None or c is None or t is None or v_bas is None or v_haut is None:
        return None

    return {
        "r1": r1,
        "r2": r2,
        "capacite": c,
        "periode": t,
        "v_bas": v_bas,
        "v_haut": v_haut,
    }

def extraire_parametres_thevenin_rc_signal_carre(question: str) -> dict | None:
    """Extrait R1, R2, R3, C, T et les niveaux du signal pour l'exercice Thévenin RC."""
    texte = question.lower().replace(",", ".")

    def extraire_valeur(prefixes: list[str], unites: list[str]) -> float | None:
        pattern_prefixes = "|".join(re.escape(p) for p in prefixes)
        pattern_unites = "|".join(re.escape(u) for u in unites)
        m = re.search(
            rf"(?:{pattern_prefixes})\s*=\s*(\d+(?:\.\d+)?)\s*(micro|meg|k|m|u|µ|n|p)?\s*(?:{pattern_unites})?",
            texte,
        )
        if not m:
            return None
        val = float(m.group(1))
        prefixe = m.group(2) or ""
        scale = {
            "": 1.0, "micro": 1e-6, "nano": 1e-9, "k": 1e3, "m": 1e-3,
            "u": 1e-6, "µ": 1e-6, "n": 1e-9, "p": 1e-12, "meg": 1e6,
        }
        return val * scale.get(prefixe, 1.0)

    r1 = extraire_valeur(["r1"], ["ohm", "ohms", "ω"])
    r2 = extraire_valeur(["r2"], ["ohm", "ohms", "ω"])
    r3 = extraire_valeur(["r3"], ["ohm", "ohms", "ω"])
    c  = extraire_valeur(["c"],  ["f", "farad", "farads"])

    t = None
    periode_match = re.search(
        r"p\u00e9riode(?:\s+du\s+signal\s+carr\u00e9|\s+du\s+signal\s+carre)?\s*(?:vaut|=)?\s*(\d+(?:\.\d+)?)\s*(ms|s|us|\u00b5s)",
        texte,
    )
    if periode_match:
        val = float(periode_match.group(1))
        u = periode_match.group(2)
        t = val / 1000.0 if u == "ms" else (val / 1e6 if u in ("us", "µs") else val)
    else:
        t = extraire_valeur(["t"], ["s", "ms", "us", "µs"])

    # Niveaux du signal carré
    v_bas, v_haut = None, None
    variant_match = re.search(
        r"variant\s+de\s+(\-?\d+(?:\.\d+)?)\s*v?\s+[a\u00e0]\s+(\-?\d+(?:\.\d+)?)\s*v", texte
    )
    if variant_match:
        v_bas  = float(variant_match.group(1))
        v_haut = float(variant_match.group(2))
    else:
        entre_match = re.search(
            r"entre\s+(\-?\d+(?:\.\d+)?)\s*v?\s+et\s+(\-?\d+(?:\.\d+)?)\s*v", texte
        )
        if entre_match:
            v_bas  = float(entre_match.group(1))
            v_haut = float(entre_match.group(2))
        else:
            bas_match  = re.search(r"niveau\s+bas\s+(?:de|=)\s*(\-?\d+(?:\.\d+)?)\s*v", texte)
            haut_match = re.search(r"niveau\s+haut\s+(?:de|=)\s*(\-?\d+(?:\.\d+)?)\s*v", texte)
            if bas_match:  v_bas  = float(bas_match.group(1))
            if haut_match: v_haut = float(haut_match.group(1))

    if None in (r1, r2, r3, c, t, v_bas, v_haut):
        return None

    return {"r1": r1, "r2": r2, "r3": r3, "capacite": c, "periode": t, "v_bas": v_bas, "v_haut": v_haut}


def tracer_thevenin_rc_signal_carre(
    r1=1000, r2=2000, r3=1000, capacite=20e-9, periode=1e-3, v_bas=0, v_haut=5, nb_periodes=4
):
    """Trace la réponse Vout(t) du circuit R1-(R2//C)-R3 après réduction Thévenin."""
    rth = r2 * (r1 + r3) / (r1 + r2 + r3)
    k   = r2 / (r1 + r2 + r3)          # coefficient diviseur de tension
    vth_high = v_haut * k
    vth_low  = v_bas  * k
    tau = rth * capacite
    demi_periode = periode / 2.0

    t_start = -0.25 * periode
    t_end   = nb_periodes * periode
    temps   = np.linspace(t_start, t_end, 2400)

    # Signal VIN carré (niveaux originaux pour affichage)
    vin = np.where(
        temps < 0, v_bas,
        np.where(np.floor(2 * temps / periode).astype(int) % 2 == 0, v_haut, v_bas)
    )

    # VTH(t) (signal Thévenin)
    vth_signal = k * vin

    # Calcul de VOUT via intégration analytique par morceaux
    transitions = []
    n = int(np.floor(t_end / demi_periode)) + 1
    for i in range(n + 1):
        t_trans = i * demi_periode
        if t_start < t_trans <= t_end:
            transitions.append(t_trans)

    vout = np.zeros_like(temps)
    # Avant t=0 : régime permanent au niveau bas
    masque_neg = temps < 0
    vout[masque_neg] = vth_low

    # Premier segment (0 → première transition)
    t_prec = 0.0
    v_depart = vth_low
    for idx_tr, t_tr in enumerate(transitions):
        cible = vth_high if idx_tr % 2 == 0 else vth_low
        masque = (temps >= t_prec) & (temps < t_tr)
        vout[masque] = cible + (v_depart - cible) * np.exp(-(temps[masque] - t_prec) / tau)
        v_depart = cible + (v_depart - cible) * np.exp(-(t_tr - t_prec) / tau)
        t_prec = t_tr

    # Dernier segment
    cible_finale = vth_high if len(transitions) % 2 == 0 else vth_low
    masque_fin = temps >= (transitions[-1] if transitions else 0.0)
    vout[masque_fin] = cible_finale + (v_depart - cible_finale) * np.exp(
        -(temps[masque_fin] - (transitions[-1] if transitions else 0.0)) / tau
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(temps * 1e3, vin,        linestyle="--", color="gray",     linewidth=2,   label="VIN(t)")
    ax.plot(temps * 1e3, vth_signal, linestyle=":",  color="tab:green", linewidth=1.8, label=f"Vth(t) = {k:.2f}·VIN")
    ax.plot(temps * 1e3, vout,       color="tab:blue", linewidth=2.5,   label="VOUT(t)")

    ax.axvline(tau * 1e3, color="tab:red",    linestyle="--", alpha=0.6,
               label=f"τ = Rth·C = {tau * 1e6:.1f} µs")
    ax.axvline(demi_periode * 1e3, color="tab:purple", linestyle="--", alpha=0.6,
               label=f"T/2 = {demi_periode * 1e6:.0f} µs")

    ratio = demi_periode / tau if tau > 0 else np.inf
    regime = "charge/décharge complète" if ratio >= 5 else "charge/décharge partielle"

    ax.set_title(
        f"Circuit R1-(R2//C)-R3 — Réduction Thévenin ({regime})\n"
        f"R1={r1/1e3:.3g}kΩ, R2={r2/1e3:.3g}kΩ, R3={r3/1e3:.3g}kΩ, "
        f"C={capacite*1e9:.3g}nF  →  Rth={rth/1e3:.3g}kΩ, k={k:.2f}",
        fontsize=12,
    )
    ax.set_xlabel("Temps (ms)", fontsize=12)
    ax.set_ylabel("Tension (V)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    return fig


def tracer_signal_carre_rc(r1=1000, r2=4000, capacite=20e-9, periode=2e-3, v_bas=1, v_haut=6, nb_periodes=4):
    """Trace la réponse d'un RC du premier ordre soumis à un signal carré."""
    req = r1 + r2
    tau = req * capacite
    demi_periode = periode / 2.0

    t_start = -0.25 * periode
    t_end = nb_periodes * periode
    temps = np.linspace(t_start, t_end, 2400)

    # Signal carré: bas avant t=0, puis première demi-période au niveau haut.
    vin = np.full_like(temps, v_bas, dtype=float)
    masque_t_pos = temps >= 0
    phase = np.floor((temps[masque_t_pos]) / demi_periode).astype(int)
    vin[masque_t_pos] = np.where(phase % 2 == 0, v_haut, v_bas)

    vout = np.full_like(temps, v_bas, dtype=float)
    transitions = [0.0]
    t_cursor = 0.0
    while t_cursor <= t_end + demi_periode:
        transitions.append(t_cursor + demi_periode)
        t_cursor += demi_periode

    v_depart = v_bas
    for i in range(len(transitions) - 1):
        t0 = transitions[i]
        t1 = transitions[i + 1]
        cible = v_haut if i % 2 == 0 else v_bas
        segment = (temps >= t0) & (temps < t1)
        vout[segment] = cible + (v_depart - cible) * np.exp(-(temps[segment] - t0) / tau)
        v_depart = cible + (v_depart - cible) * np.exp(-(t1 - t0) / tau)

    segment_fin = temps >= transitions[-1]
    if np.any(segment_fin):
        cible = v_haut if (len(transitions) - 1) % 2 == 0 else v_bas
        vout[segment_fin] = cible + (v_depart - cible) * np.exp(-(temps[segment_fin] - transitions[-1]) / tau)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(temps * 1e3, vin, linestyle="--", color="gray", linewidth=2, label="VIN(t)")
    ax.plot(temps * 1e3, vout, color="tab:blue", linewidth=2.5, label="VOUT(t)")

    ax.axvline(0, color="black", linestyle=":", alpha=0.7)
    ax.axvline(demi_periode * 1e3, color="tab:purple", linestyle="--", alpha=0.6, label=f"T/2 = {demi_periode * 1e3:.2f} ms")
    ax.axvline(tau * 1e3, color="tab:red", linestyle="--", alpha=0.6, label=f"τ = {tau * 1e3:.2f} ms")

    ax.axhline(v_bas, color="tab:green", linestyle=":", alpha=0.5)
    ax.axhline(v_haut, color="tab:orange", linestyle=":", alpha=0.5)

    ratio = demi_periode / tau if tau > 0 else np.inf
    regime = "charge/decharge complete" if ratio >= 5 else "charge/decharge partielle"
    ax.set_title(
        f"RC avec signal carré ({regime})\nR1={r1/1000:.3g}kΩ, R2={r2/1000:.3g}kΩ, C={capacite*1e9:.3g}nF, T={periode*1e3:.3g}ms",
        fontsize=14,
    )
    ax.set_xlabel("Temps (ms)", fontsize=12)
    ax.set_ylabel("Tension (V)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    return fig

def tracer_passe_bas_premier_ordre(
    resistance=1000,
    capacite=1e-6,
    vin_initial=0,
    vin_final=5,
    temps_second_saut=None,
    vin_final_2=None,
):
    """Trace la réponse temporelle d'un filtre RC passe-bas du premier ordre."""
    tau = resistance * capacite
    if temps_second_saut is not None and vin_final_2 is not None:
        tmax = max(temps_second_saut + 5 * tau, 6 * tau)
        temps = np.linspace(-0.5 * tau, tmax, 900)
    else:
        temps = np.linspace(-0.5 * tau, 5 * tau, 600)

    vin = np.where(temps < 0, vin_initial, vin_final)
    if temps_second_saut is not None and vin_final_2 is not None:
        vin = np.where(temps >= temps_second_saut, vin_final_2, vin)

    vout = np.where(
        temps < 0,
        vin_initial,
        vin_final + (vin_initial - vin_final) * np.exp(-temps / tau),
    )

    if temps_second_saut is not None and vin_final_2 is not None:
        vout_t2 = vin_final + (vin_initial - vin_final) * np.exp(-temps_second_saut / tau)
        masque_apres_t2 = temps >= temps_second_saut
        vout[masque_apres_t2] = vin_final_2 + (vout_t2 - vin_final_2) * np.exp(-(temps[masque_apres_t2] - temps_second_saut) / tau)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(temps * 1e3, vin, linestyle="--", color="gray", linewidth=2, label="VIN(t)")
    ax.plot(temps * 1e3, vout, color="tab:blue", linewidth=2.5, label="VOUT(t)")

    ax.axvline(0, color="black", linestyle=":", alpha=0.7)
    ax.axvline(tau * 1e3, color="tab:red", linestyle="--", alpha=0.6, label=f"τ = {tau * 1e3:.2f} ms")
    if temps_second_saut is not None and vin_final_2 is not None:
        ax.axvline(temps_second_saut * 1e3, color="tab:purple", linestyle="--", alpha=0.6, label=f"2e saut: t = {temps_second_saut * 1e3:.2f} ms")

    ax.axhline(vin_initial, color="tab:green", linestyle=":", alpha=0.5)
    ax.axhline(vin_final, color="tab:orange", linestyle=":", alpha=0.5)
    if vin_final_2 is not None:
        ax.axhline(vin_final_2, color="tab:brown", linestyle=":", alpha=0.5)

    points_t = [0, tau * 1e3]
    points_v = [vin_initial, vin_final + (vin_initial - vin_final) * np.exp(-1)]
    if temps_second_saut is not None and vin_final_2 is not None:
        points_t.extend([temps_second_saut * 1e3, (temps_second_saut + tau) * 1e3])
        vout_t2 = vin_final + (vin_initial - vin_final) * np.exp(-temps_second_saut / tau)
        points_v.extend([
            vout_t2,
            vin_final_2 + (vout_t2 - vin_final_2) * np.exp(-1),
        ])
    ax.scatter(points_t, points_v, color="tab:blue", zorder=3)

    titre = "Réponse indicielle RC passe-bas"
    if temps_second_saut is not None and vin_final_2 is not None:
        titre = "Réponse RC à deux sauts successifs"
    ax.set_title(
        f"{titre}\nR = {resistance / 1000:.3g} kΩ, C = {capacite * 1e6:.3g} µF",
        fontsize=14,
    )
    ax.set_xlabel("Temps (ms)", fontsize=12)
    ax.set_ylabel("Tension (V)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    return fig

def tracer_inverseur(vcc=5, rc=2000, rb=10000, beta=200, vbe=0.7, vce_sat=0.2):
    """Trace la courbe VOUT = f(VIN) pour un inverseur bipolaire."""
    # Générer une plage de VIN de 0 à VCC
    vin = np.linspace(0, vcc, 500)
    vout = np.zeros_like(vin)
    
    # Calcul de VIN2 (transition actif → saturé)
    vin2 = vbe + (vcc - vce_sat) * rb / (beta * rc)
    
    for i, v in enumerate(vin):
        if v < vbe:
            # Mode bloqué
            vout[i] = vcc
        elif v < vin2:
            # Mode actif/linéaire
            ib = (v - vbe) / rb
            ic = beta * ib
            vout[i] = vcc - rc * ic
        else:
            # Mode saturé
            vout[i] = vce_sat
    
    # Créer le graphique
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(vin, vout, 'b-', linewidth=2, label='VOUT = f(VIN)')
    
    # Marquer les transitions
    ax.axvline(vbe, color='r', linestyle='--', alpha=0.5, label=f'VIN1 (bloqué→actif) = {vbe:.2f}V')
    ax.axvline(vin2, color='g', linestyle='--', alpha=0.5, label=f'VIN2 (actif→saturé) = {vin2:.2f}V')
    
    # Zones colorées
    ax.axvspan(0, vbe, alpha=0.1, color='red', label='Zone bloquée')
    ax.axvspan(vbe, vin2, alpha=0.1, color='yellow', label='Zone linéaire')
    ax.axvspan(vin2, vcc, alpha=0.1, color='green', label='Zone saturée')
    
    # Labels et titre
    ax.set_xlabel('VIN (V)', fontsize=12)
    ax.set_ylabel('VOUT (V)', fontsize=12)
    ax.set_title(f'Courbe de transfert - Inverseur Bipolaire\nβ={beta}, VCC={vcc}V, RC={rc/1000}kΩ, RB={rb/1000}kΩ', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    ax.set_xlim(0, vcc)
    ax.set_ylim(-0.5, vcc + 0.5)
    
    return fig


def expliquer_diode_simple(question: str, image_base64: str = None) -> str:
    """Analyse d'un circuit simple avec R et D explicites (4 configurations)."""
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_DIODE_SIMPLE.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    return response.content[0].text.strip()

def expliquer_diode_boites(question: str, image_base64: str = None) -> str:
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_DIODE_BOITES.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=3500,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    return response.content[0].text.strip()

def expliquer_diode_zener_simple(question: str, image_base64: str = None) -> str:
    """Analyse d'un circuit simple avec une diode Zener et une résistance."""
    image_info = "Si une image du circuit a été fournie, utilise-la pour valider ton analyse." if image_base64 else ""
    prompt = PROMPT_DIODE_ZENER_SIMPLE.format(question=question, image_info=image_info)

    content = construire_message_avec_image(prompt, image_base64)
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=3500,
        messages=[
            {"role": "user", "content": content}
        ]
    )

    return response.content[0].text.strip()

if __name__ == "__main__":
    question = "Calculer la tension de sortie Vout d’un diviseur avec R1=1kΩ, R2=2kΩ et Vin=12V."
    reponse = expliquer_diviseur_tension(question)
    print(reponse)