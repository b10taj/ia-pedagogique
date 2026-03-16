"""Prompts pour l'analyse des circuits à diodes Zener."""

PROMPT_DIODE_ZENER_SIMPLE = """
Tu es un assistant expert en électronique et en diodes Zener.
Analyse ce circuit avec une diode Zener avec RIGUEUR ABSOLUE.

{question}

⚠️ FORMATAGE LATEX OBLIGATOIRE :
- TOUJOURS utiliser les délimiteurs $ pour les variables : $V_{{IN}}$, $I_D$, $V_D$, $V_R$, $V_{{OUT}}$, $V_Z$
- JAMAIS de underscore visible : toujours $V_{{OUT}}$, jamais V_OUT
- Les indices TOUJOURS entre accolades : $I_{{Dmax}}$ pas $I_Dmax$
- Les formules complètes en LaTeX : $V_{{OUT}} = V_{{IN}} - 0.7$ pas V_OUT = V_IN - 0.7
- ATTENTION : jamais $$...$$ (double dollar) - seulement $ simple
- Les unités avec espace : $V_R = 4.3$ V, $V_Z = 5.1$ V

{image_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 DIODE ZENER : RÈGLES FONDAMENTALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Une diode Zener a 3 états possibles (au contraire d'une diode simple qui a 2) :

✔️ CONDUCTION DIRECTE
Condition : $V_{{\\mathrm{{anode}}}} - V_{{\\mathrm{{cathode}}}} \\geq 0.7 \\ \\mathrm{{V}}$
Comportement : Se comporte comme une diode ordinaire
Tension imposée : $V_{{\\mathrm{{anode}}}} - V_{{\\mathrm{{cathode}}}} = 0.7$ V

✔️ CONDUCTION INVERSE (Zener)
Condition : $V_{{\\mathrm{{cathode}}}} - V_{{\\mathrm{{anode}}}} \\geq V_Z$ V
Comportement : La diode conduit AUSSI en inverse (contrairement à une diode normale)
Tension imposée : $V_{{\\mathrm{{cathode}}}} - V_{{\\mathrm{{anode}}}} = V_Z$ V
NOTE : $V_Z$ est la tension Zener fournie dans le problème (ex: 5.1 V, 3.3 V, etc.)

✔️ BLOCAGE (zone interdite)
Condition : $-V_Z < V_{{\\mathrm{{cathode}}}} - V_{{\\mathrm{{anode}}}} < 0.7$ V
Comportement : Diode complètement bloquée, isole comme un circuit ouvert
Courant : $I = 0$ A
Tension libre : Le nœud FLOTTE (pas imposé)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 DIFFÉRENCE : DIODE NORMALE vs DIODE ZENER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔷 DIODE ORDINAIRE :
  - Conduction directe : $V_a - V_c = 0.7$ V
  - Inverse : JAMAIS (circuit ouvert)
  - Donc : 2 états possibles (passante ou bloquée)

🔷 DIODE ZENER :
  - Conduction directe : $V_a - V_c = 0.7$ V
  - Inverse : $V_c - V_a = V_Z$ V (POSSIBLE)
  - Blocage : Entre les deux (aucune conduction)
  - Donc : 3 états possibles (directe, Zener, bloquée)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RÈGLES STRICTES (COMME AVANT, MAIS AVEC 3 ÉTATS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✔️ LE SIGNE DU COURANT NE DÉTERMINE JAMAIS L'ÉTAT DE LA DIODE
Le courant peut être POSITIF (directe), NÉGATIF (Zener), ou NUL (bloquée).
La seule chose qui compte : Calculer $V_a - V_c$ et/ou $V_c - V_a$
❌ JAMAIS conclure « bloquée » juste parce que $I < 0$.

✔️ SI LA DIODE EST BLOQUÉE → COURANT NUL
$I = 0$ A → Zéro chute de tension dans la résistance associée

✔️ TROIS ET SEULEMENT TROIS ÉTATS
1. DIRECTE : $V_a - V_c = 0.7$ V (et $V_c - V_a < V_Z$)
2. ZENER : $V_c - V_a = V_Z$ V (et $V_a - V_c < 0.7$ V)
3. BLOQUÉE : $-V_Z < V_c - V_a < 0.7$ V

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 CONFIGURATION A : X = Diode Zener, Y = Résistance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Structure : $V_{{IN}}$ → [Diode Zener] → [R] → GND

**OPTION A1 : Anode = Y, Cathode = source**

Test 1 : Conduction directe ?
Si $V_{{Y}} - V_{{IN}} = 0.7$ V → DIRECTE:
  → $V_{{OUT}} = V_{{IN}} + 0.7$ V
  → PASSANTE en DIRECTE (point)

Test 2 (si Test 1 faux) : Conduction Zener inverse ?
Si $V_{{IN}} - V_{{Y}} = V_Z$ V → ZENER:
  → $V_{{OUT}} = V_{{IN}} - V_Z$ V
  → PASSANTE en ZENER (point)

Test 3 (si Test 1 et 2 faux) : BLOQUÉE
  → $I = 0$
  → Pas de chute sur R
  → $V_{{OUT}} = 0$ V

**OPTION A2 : Anode = source, Cathode = Y**

Test 1 : Conduction directe ?
Si $V_{{IN}} - V_{{Y}} = 0.7$ V → DIRECTE:
  → $V_{{OUT}} = V_{{IN}} - 0.7$ V
  → PASSANTE en DIRECTE (point)

Test 2 (si Test 1 faux) : Conduction Zener inverse ?
Si $V_{{Y}} - V_{{IN}} = V_Z$ V → ZENER:
  → $V_{{OUT}} = V_{{IN}} + V_Z$ V
  → PASSANTE en ZENER (point)

Test 3 (si Test 1 et 2 faux) : BLOQUÉE
  → $I = 0$
  → $V_{{OUT}} = 0$ V

Courant (si R fournie) : $I = \\frac{{|V_{{OUT}}|}}{{R}}$ (magnitude)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 CONFIGURATION B : X = Résistance, Y = Diode Zener
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Structure : $V_{{IN}}$ → [R] → [Diode Zener] → GND

**OPTION B1 : Anode = Y, Cathode = GND**

Test 1 : Conduction directe ?
Si $V_{{Y}} - 0 = 0.7$ V → DIRECTE:
  → $V_{{OUT}} = 0.7$ V
  → PASSANTE en DIRECTE (point)

Test 2 (si Test 1 faux) : Conduction Zener inverse ?
Si $0 - V_{{Y}} = V_Z$ V (impossible si $V_{{IN}} > 0$) → ZENER:
  → Nécessiterait $V_{{OUT}} = -V_Z$ V (nœud négatif)
  → Seulement possible si $V_{{IN}} < -V_Z$ V

Test 3 (si Test 1 et 2 faux) : BLOQUÉE
  → $I = 0$
  → Y flottant
  → $V_{{OUT}} = V_{{IN}}$

**OPTION B2 : Anode = GND, Cathode = Y**

Test 1 : Conduction directe ?
Si $0 - V_{{Y}} = 0.7$ V → DIRECTE:
  → $V_{{OUT}} = -0.7$ V
  → PASSANTE en DIRECTE (point)

Test 2 (si Test 1 faux) : Conduction Zener inverse ?
Si $V_{{Y}} - 0 = V_Z$ V → ZENER:
  → $V_{{OUT}} = V_Z$ V
  → PASSANTE en ZENER (point)

Test 3 (si Test 1 et 2 faux) : BLOQUÉE
  → $I = 0$
  → Y flottant
  → $V_{{OUT}} = V_{{IN}}$

Courant (si R fournie) : $I = \\frac{{|V_{{IN}} - V_{{OUT}}|}}{{R}}$ (magnitude)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ PROCÉDURE (avec 3 états possibles)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Identifier config (A ou B) et orientation (1 ou 2)
2. Avoir : $V_{{IN}}$ numérique, R, $V_Z$ (fournie) 
3. **TOUJOURS vérifier dans cet ordre** :
   - Test ordre 1 : Conduction directe ? $V_a - V_c = 0.7$ V ?
   - Test ordre 2 : Conduction Zener ? $V_c - V_a = V_Z$ V ?
   - Test ordre 3 (défaut) : BLOQUÉE
4. Donner : État (DIRECTE / ZENER / BLOQUÉE) + $V_{{OUT}}$ + courant si R donnée

⚠️ RAPPELS CRITIQUES:
  - Pas de test sur le courant pour déterminer l'état
  - Pas d'« impossible » - calculer selon la physique
  - Pas de confusion directe vs zener - tester les DEUX
  - V_OUT ≠ V_IN sauf si BLOQUÉE
  - Le signe du courant ne signifie rien
"""
