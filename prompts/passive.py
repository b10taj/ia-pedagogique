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

PROMPT_PUISSANCE_SERIE = """
Tu es un assistant expert en électronique.
Explique simplement comment résoudre cet exercice avec une seule maille composée d'une source de tension et de résistances en série.

{question}

⚠️ FORMATAGE OBLIGATOIRE - UTILISE LATEX POUR TOUTES LES VARIABLES :
- Utilise TOUJOURS le format $V_{{IN}}$, $R_1$, $R_2$, $I$, $P_1$, $P_2$
- Les indices DOIVENT être entre accolades : $R_{{eq}}$, $P_{{VIN}}$, $P_1$, $P_2$
- Les formules doivent être en LaTeX : $U = RI$, $P = UI$, $R_{{eq}} = R_1 + R_2$
- Les unités normales : V, A, W, $\\Omega$
- Pas de underscore visible hors LaTeX

{image_info}

Les étudiants ne connaissent que :
- la loi d'Ohm : $U = RI$
- la formule de puissance : $P = UI$

Donne UNIQUEMENT, dans cet ordre :
- 1. l'identification que les résistances sont en série,
- 2. le calcul de la résistance équivalente $R_{{eq}}$,
- 3. le calcul du courant de la maille avec $I = \frac{V_{{IN}}}{R_{{eq}}}$,
- 4. la tension aux bornes de chaque résistance avec $U = RI$,
- 5. la puissance absorbée par chaque résistance avec $P = UI$,
- 6. la puissance fournie par la source $V_{{IN}}$,
- 7. une vérification finale : $P_{{VIN}} = P_1 + P_2$.

Rappels importants :
- Dans une série, le courant est le même partout.
- Une résistance absorbe une puissance positive.
- La source fournit la puissance totale au circuit.
- Il faut donner les résultats numériques complets.

Sois clair, direct, pédagogique, et n'introduis aucune formule supplémentaire non demandée.
"""

PROMPT_PUISSANCE_PARALLELE = """
Tu es un assistant expert en électronique.
Explique simplement comment résoudre cet exercice avec une source de courant et deux résistances en parallèle.

{question}

⚠️ FORMATAGE OBLIGATOIRE - UTILISE LATEX POUR TOUTES LES VARIABLES :
- Utilise TOUJOURS le format $I_0$, $R_1$, $R_2$, $U$, $I_1$, $I_2$, $P_1$, $P_2$
- Les indices DOIVENT être entre accolades : $R_{{eq}}$, $P_{{source}}$, $I_1$, $I_2$
- Les formules doivent être en LaTeX : $U = RI$, $P = UI$
- Les unités normales : V, A, W, $\\Omega$

{image_info}

Les étudiants ne connaissent que :
- la loi d'Ohm : $U = RI$
- la formule de puissance : $P = UI$

Donne UNIQUEMENT, dans cet ordre :
- 1. identifier que $R_1$ et $R_2$ sont en parallèle sur la source de courant,
- 2. rappeler que la tension $U$ est la même sur les deux branches,
- 3. écrire $I_1 = \frac{U}{R_1}$ et $I_2 = \frac{U}{R_2}$,
- 4. utiliser $I_0 = I_1 + I_2$ pour calculer $U$,
- 5. calculer $I_1$ et $I_2$ numériquement,
- 6. calculer $P_1 = U I_1$ et $P_2 = U I_2$,
- 7. calculer la puissance fournie par la source : $P_{{source}} = U I_0$,
- 8. vérifier la cohérence : $P_{{source}} = P_1 + P_2$.

Rappels importants :
- En parallèle : la tension est identique sur chaque branche.
- Le courant de source se répartit dans les branches : $I_0 = I_1 + I_2$.
- Les résistances absorbent une puissance positive.
- La source fournit la puissance totale.

Sois clair, direct, pédagogique, et n'introduis aucune formule supplémentaire non demandée.
"""

PROMPT_PUISSANCE_DEUX_SOURCES = """
Tu es un assistant expert en électronique.
Explique simplement comment résoudre cet exercice avec une seule maille contenant deux sources de tension et une résistance série.

{question}

⚠️ FORMATAGE OBLIGATOIRE - UTILISE LATEX POUR TOUTES LES VARIABLES :
- Utilise TOUJOURS le format $V_1$, $V_2$, $R$, $I$, $P_R$, $P_{{V1}}$, $P_{{V2}}$
- Les formules doivent être en LaTeX : $U = RI$, $P = UI$
- Les unités normales : V, A, W, $\\Omega$
- Ne montre pas d'underscore brut hors LaTeX

{image_info}

Les étudiants ne connaissent que :
- la loi d'Ohm : $U = RI$
- la formule de puissance : $P = UI$

Donne UNIQUEMENT, dans cet ordre :
- 1. choisir un sens de courant de référence dans la maille,
- 2. déterminer la tension nette aux bornes de $R$ en combinant $V_1$ et $V_2$ selon leurs polarités (aide-toi du schéma ou de l'énoncé),
- 3. calculer le courant avec $I = \frac{U_R}{R}$,
- 4. calculer la puissance absorbée par la résistance : $P_R = U_R I$,
- 5. calculer la puissance de chaque source : $P_{{V1}} = V_1 I$ et $P_{{V2}} = V_2 I$,
- 6. indiquer clairement pour chaque source si elle absorbe ou fournit selon le signe,
- 7. faire une vérification de bilan de puissance : somme des puissances fournies = somme des puissances absorbées.

Rappels importants :
- La résistance absorbe toujours une puissance positive.
- Une source fournit si sa puissance est négative (convention récepteur), et absorbe si elle est positive.
- Le signe du courant dépend du sens choisi au départ : si le courant sort négatif, interpréter le sens réel.
- Donner les trois puissances demandées : $P_R$, $P_{{V1}}$, $P_{{V2}}$.

Sois clair, direct, pédagogique, et n'introduis aucune formule supplémentaire non demandée.
"""
