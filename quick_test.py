#!/usr/bin/env python
import re

def formatter_variables_latex(texte: str) -> str:
    """
    Convertit les variables non-formatées en LaTeX.
    """
    pattern = r'\b([A-Z][A-Za-z]*?)_([A-Za-z0-9_]+)\b'
    
    def replace_var(match):
        var_name = match.group(1)
        indice = match.group(2)
        return f"${var_name}_{{{indice}}}$"
    
    result = re.sub(pattern, replace_var, texte)
    return result

# Tests rapides
tests = [
    "V_OUT = V_IN - V_D",
    "I_D = (V_IN - 0.7) / R",
    "V_BE est la tension base-emetteur",
    "V_CE_sat est petit",
]

print("Tests de formatage LaTeX:\n")
for test in tests:
    result = formatter_variables_latex(test)
    print(f"Input:  {test}")
    print(f"Output: {result}")
    print()
