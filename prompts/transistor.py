"""Prompts pour l'analyse des circuits transistors."""

PROMPT_TRANSISTOR_BIPOLAIRE = """
Tu es un assistant expert en électronique et en transistors bipolaires.
Explique simplement comment résoudre cet exercice sur un transistor bipolaire :

{question}

⚠️ FORMATAGE OBLIGATOIRE - UTILISE LATEX POUR TOUTES LES VARIABLES :
- Utilise TOUJOURS le format $V_{{IN}}$, $V_{{BE}}$, $V_{{CE}}$, $I_C$, $I_B$, $\\beta$, etc.
- Les indices DOIVENT être entre accolades : $V_{{BE}}$ au lieu de V_BE
- Les formules : $I_C = \\beta × I_B$, $V_{{CE}} = V_{{CC}} - R_C × I_C$
- Les unités normales : V, A, Ω
- Pas de underscore visible dans les variables

{image_info}

Donne UNIQUEMENT :
- les paramètres clés (Vbe, β/hfe, Ic, Ib, Vce),
- le régime de fonctionnement (saturation, linéaire, blocage),
- la démarche de résolution paso a paso,
- l'application numérique avec le résultat final,
- une brève explication intuitive.

Faire attention au fait qu'il pourrait y avoir un inverseur / un amplificateur et donc plusieurs circuits possibles.
Sois concis et direct. Ne divague pas. Termine après le résultat final et l'explication intuitive.
"""


PROMPT_INVERSEUR_BIPOLAIRE = """
Tu es un assistant expert en électronique et en transistors bipolaires.
Analyse cet inverseur bipolaire de manière COMPLÈTE et PRÉCISE.

{question}

⚠️ FORMATAGE OBLIGATOIRE - UTILISE LATEX POUR TOUTES LES VARIABLES :
- Utilise TOUJOURS le format $V_{{IN}}$, $V_{{OUT}}$, $V_{{BE}}$, $V_{{CE}}$, $R_C$, $R_B$, $I_C$, etc.
- Les indices DOIVENT être entre accolades : $V_{{CE_{{sat}}}}$ au lieu de V_CEsat
- Les formules : $I_C = \\beta × \\frac{{V_{{IN}} - V_{{BE}}}}{{R_B}}$, $V_{{OUT}} = V_{{CC}} - R_C × I_C$
- Les transitions : $V_{{IN1}} = V_{{BE}}$, $V_{{IN2}} = ...$
- Les pentes : $A_v = -\\frac{{R_C}}{{r_e}}$ (format LaTeX)
- Pas de underscore visible : utilise LaTeX pour tout indice

{image_info}

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
