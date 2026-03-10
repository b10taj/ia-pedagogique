# main.py
import os
import numpy as np
import matplotlib.pyplot as plt
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def detecter_type_probleme(question: str) -> str:
    """Détecte le type de problème électronique dans la question."""
    question_lower = question.lower()
    
    # Mots-clés pour inverseur bipolaire (priorité haute)
    keywords_inverseur = ["inverseur", "vout=f(vin)", "courbe vout", "pente", "zone linéaire", 
                         "bloqué", "saturé", "limite", "f(vin)"]
    
    # Mots-clés pour transistor bipolaire
    keywords_transistor = ["transistor", "bjt", "npn", "pnp", "collecteur", "base", "émetteur", 
                          "gain", "beta", "hfe", "ic", "ib", "vce"]
    
    # Mots-clés pour diviseur de tension
    keywords_diviseur = ["diviseur", "résistif", "r1", "r2"]
    
    # Ordre de priorité : inverseur > transistor > diviseur > general
    if any(kw in question_lower for kw in keywords_inverseur):
        return "inverseur"
    elif any(kw in question_lower for kw in keywords_transistor):
        return "transistor"
    elif any(kw in question_lower for kw in keywords_diviseur):
        return "diviseur"
    else:
        return "general"

def expliquer_diviseur_tension(question: str) -> str:
    prompt = f"""
Tu es un assistant expert en électronique.
Explique simplement comment résoudre cet exercice sur un diviseur de tension résistif :

{question}

Donne UNIQUEMENT :
- la formule clé,
- la démarche,
- l'application numérique avec le résultat final,
- et une brève explication intuitive.

Sois concis et direct. N'ajoute rien d'extra.
    """

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text.strip()

def expliquer_transistor_bipolaire(question: str) -> str:
    prompt = f"""
Tu es un assistant expert en électronique et en transistors bipolaires.
Explique simplement comment résoudre cet exercice sur un transistor bipolaire :

{question}

Donne UNIQUEMENT :
- les paramètres clés (Vbe, β/hfe, Ic, Ib, Vce),
- le régime de fonctionnement (saturation, linéaire, blocage),
- la démarche de résolution paso à paso,
- l'application numérique avec le résultat final,
- une brève explication intuitive.

Faire attention au fait qu'il pourrait y avoir un inverseur / un amplificateur et donc plusieurs circuits possibles.
Sois concis et direct. Ne divague pas. Termine après le résultat final et l'explication intuitive.
    """

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=600,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text.strip()

def expliquer_inverseur_bipolaire(question: str) -> str:
    prompt = f"""
Tu es un assistant expert en électronique et en transistors bipolaires.
Analyse cet inverseur bipolaire de manière COMPLÈTE et PRÉCISE.

{question}

INSTRUCTIONS STRICTES - NE SAUTE AUCUNE ÉTAPE :

1️⃣ RÉGIMES DE FONCTIONNEMENT
   a) Mode BLOQUÉ : VOUT = VCC
   b) Mode ACTIF/LINÉAIRE : VOUT = VCC - RC × IC, avec IC = β × (VIN - VBE) / RB
   c) Mode SATURÉ : VOUT ≈ VCE_sat

2️⃣ CALCULS NUMÉRIQUES - TOUS LES DÉTAILS

   ➤ Transition 1 (bloqué → actif) :
   VIN1 = VBE ≈ 0.7 V

   ➤ Transition 2 (actif → saturé) - CALCUL COMPLET OBLIGATOIRE :
   
   Étape A : IC_max = (VCC - VCE_sat) / RC = ... = [CHIFFRE] A
   
   Étape B : IB_sat = IC_max / β = ... = [CHIFFRE] A
   
   Étape C - FINIR LE CALCUL : 
   VIN2 = VBE + IB_sat × RB
       = 0,7 + [CHIFFRE] × [CHIFFRE]
       = 0,7 + [CHIFFRE]
       ≈ [RÉSULTAT FINAL] V
   
   ➤ Pente en zone active :
   Pente = -β × RC / RB = ... = [CHIFFRE] V/V

3️⃣ RÉSUMÉ DES TROIS ZONES (SYNTÈSE FINALE OBLIGATOIRE)
   
   Écrire EXPLICITEMENT :
   • Zone bloquée : VIN < [VIN1 numérique] V, VOUT ≈ [valeur] V
   • Zone active : [VIN1 numérique] < VIN < [VIN2 numérique] V, VOUT = [équation avec pente]
   • Zone saturée : VIN > [VIN2 numérique] V, VOUT ≈ [valeur] V

4️⃣ POINTS POUR TRACER
   Donner 5+ points (VIN, VOUT) couvrant les 3 zones

5️⃣ EXPLICATION INTUITIVE BRÈVE

⚠️ OBLIGATION ABSOLUE : Tu DOIS écrire explicitement VIN2 ≈ X,XX V et les trois zones synthétisées. 
Si tu termines avant ces deux éléments, ta réponse est INCOMPLÈTE.
    """

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text.strip()

def expliquer_probleme(question: str) -> str:
    """Fonction générale qui détecte le type et envoie au bon assistant."""
    type_probleme = detecter_type_probleme(question)
    
    if type_probleme == "inverseur":
        return expliquer_inverseur_bipolaire(question)
    elif type_probleme == "transistor":
        return expliquer_transistor_bipolaire(question)
    elif type_probleme == "diviseur":
        return expliquer_diviseur_tension(question)
    else:
        # Pour les autres problèmes généraux
        prompt = f"""
Tu es un assistant expert en électronique.
Explique simplement comment résoudre cet exercice :

{question}

Donne :
- les concepts clés,
- la démarche,
- un exemple numérique simple,
- et une explication intuitive.
    """
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text.strip()

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

if __name__ == "__main__":
    question = "Calculer la tension de sortie Vout d’un diviseur avec R1=1kΩ, R2=2kΩ et Vin=12V."
    reponse = expliquer_diviseur_tension(question)
    print(reponse)