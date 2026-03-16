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

def detecter_type_probleme(question: str) -> str:
    """Détecte le type de problème électronique dans la question."""
    question_lower = question.lower()
    
    # D'ABORD : vérifier si c'est une Zener (avant de vérifier diode normale)
    # Être STRICT : seulement les vrais indicateurs Zener
    keywords_zener = ["zener", "vz", "tension zener", "mode inverse", "conduction inverse"]
    is_zener = any(kw in question_lower for kw in keywords_zener)
    
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
    
    # Ordre de priorité : diode (avec distinction zener) > inverseur > transistor > diviseur > general
    if any(kw in question_lower for kw in keywords_diode):
        if is_zener:
            # Zener : toujours en mode SIMPLE (boîtes noires trop compliqué)
            return "diode_zener_simple"
        else:
            # Sous-distinction pour diode ordinaire : boîtes noires vs simple
            if any(kw in question_lower for kw in keywords_diode_boites):
                return "diode_boites"
            else:
                return "diode_simple"
    elif any(kw in question_lower for kw in keywords_inverseur):
        return "inverseur"
    elif any(kw in question_lower for kw in keywords_transistor):
        return "transistor"
    elif any(kw in question_lower for kw in keywords_diviseur):
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
    elif type_probleme == "inverseur":
        reponse = expliquer_inverseur_bipolaire(question, image_base64)
    elif type_probleme == "transistor":
        reponse = expliquer_transistor_bipolaire(question, image_base64)
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