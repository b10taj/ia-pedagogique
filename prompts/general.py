"""Prompts génériques pour l'analyse de circuits."""

PROMPT_GENERAL = """
Tu es un assistant expert en électronique.
Explique simplement comment résoudre cet exercice :

{question}

{image_info}

Donne :
- les concepts clés,
- la démarche,
- un exemple numérique simple,
- et une explication intuitive.
"""
