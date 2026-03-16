"""Prompts pour l'analyse des circuits passifs."""

PROMPT_DIVISEUR_TENSION = """
Tu es un assistant expert en électronique.
Explique simplement comment résoudre cet exercice sur un diviseur de tension résistif :

{question}

⚠️ FORMATAGE OBLIGATOIRE - UTILISE LATEX POUR TOUTES LES VARIABLES :
- Utilise TOUJOURS le format $V_{{IN}}$, $V_{{OUT}}$, $I_C$, $R_1$, etc.
- Les indices DOIVENT être entre accolades : $V_{{OUT}}$ au lieu de V_OUT
- Les formules : $V_{{OUT}} = V_{{IN}} × \\frac{{R_2}}{{R_1 + R_2}}$ (avec indices en LaTeX)
- Les unités normales : V (volts), A (ampères), Ω (ohms)
- Pas de underscore visible : utilise LaTeX pour tout ce qui a un indice

{image_info}

Donne UNIQUEMENT :
- la formule clé,
- la démarche,
- l'application numérique avec le résultat final,
- et une brève explication intuitive.

Sois concis et direct. N'ajoute rien d'extra.
"""
