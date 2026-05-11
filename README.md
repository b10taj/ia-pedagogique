# Assistant Electronique

Application Streamlit qui assiste la résolution d'exercices d'électronique (analyse guidée + tracés automatiques) et la génération de fichiers LTSpice XVII (`.asc`) depuis un formulaire ou une description libre.

## Fonctionnalités

### UI à deux modes

Sélection via cartes cliquables (clic direct sur la carte, sans bouton séparé) :

- **Mode Résolution d'exercice** : détection automatique du type d'énoncé, explication pas à pas, tracés matplotlib si applicable
- **Mode Simulation LTspice** : formulaire structuré par type de circuit + mode IA général

### Génération LTSpice — 7 templates + mode Général

| Type | Paramètres formulaire | Analyse simulée |
|---|---|---|
| Diviseur résistif (résistances fixes) | VIN, R1, R2 | `.op` |
| Diviseur résistif (résistance variable) | VIN, R1 fixe | `.step param` R2 |
| Circuit RC — temporel (sinus) | R, C, amplitude, fréquence | `.tran` (10 périodes) |
| Circuit RC — fréquentiel (Bode) | R, C, f_min, f_max | `.ac dec 100` |
| Diviseur avec diode Zener | VIN amplitude, R série, R charge, fréquence | `.tran` (5 périodes) |
| Stabilisateur de tension Zener | Amplitude, fréquence, R série | `.tran` + `.step param` RL |
| Amplificateur bipolaire NPN | VCC, VIN, fréq, RC, RE, R1, R2 | `.ac` + `.step param` RL |
| **Général (IA)** | Description libre | Généré entièrement par Claude Haiku |

En mode **Général**, Claude Haiku analyse l'énoncé, identifie le meilleur template (ou génère le `.asc` de zéro si aucun ne correspond), et affiche les paramètres extraits.

### Détection automatique des exercices

- Diode silicium simple / boîtes noires / Zener
- Inverseur bipolaire, transistor bipolaire
- Diviseur de tension
- Exercices de puissance (série, parallèle, deux sources)
- RC premier ordre passe-bas (saut simple ou double)
- RC premier ordre sous signal carré
- RC signal carré en régime de crêtes
- RC avec réduction de Thévenin : R1-(R2 // C)-R3
- Fallback problème général

### Tracés automatiques (matplotlib)

- Courbe VOUT=f(VIN) pour inverseur bipolaire
- Réponse temporelle RC passe-bas (1 ou 2 sauts)
- Réponse RC à signal carré
- Réponse RC Thévenin (VIN, Vth, VOUT)

## Installation

### Prérequis

- Python 3.8+
- Clé API Anthropic

### Étapes

1. Cloner le repository
```bash
git clone <repo_url>
cd Codes
```

2. Créer et activer l'environnement virtuel
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

4. Configurer la clé API — créer un fichier `.env` à la racine :
```env
ANTHROPIC_API_KEY=sk-ant-...
```

5. Lancer l'application
```bash
streamlit run app.py
```

## Utilisation

### Mode Résolution d'exercice

1. Cliquer la carte **Résolution d'exercice**
2. (Optionnel) Charger une image du circuit
3. Saisir l'énoncé et cliquer **Envoyer**
4. L'assistant détecte le type et répond avec une explication structurée + tracé si applicable

### Mode Simulation LTspice

1. Cliquer la carte **Simulation LTspice**
2. Choisir le type de circuit dans le menu déroulant
3. Remplir les champs numériques du formulaire **ou** choisir *Général* et décrire librement le circuit
4. Cliquer **Générer** — télécharger le fichier `.asc`

> **Note mode Général** : pour les circuits hors-template (ampli-op, RLC, oscillateur…), Claude Haiku génère le fichier `.asc` entièrement. La topologie et les valeurs sont correctes ; de légères corrections visuelles peuvent être nécessaires dans LTSpice XVII.

## Architecture

```text
.
├── app.py
├── main.py
├── ltspice_generator.py
├── prompts/
│   ├── passive.py
│   ├── diodes.py
│   ├── diode_zener.py
│   ├── transistor.py
│   └── general.py
└── templates/
    ├── diviseur_resistif_fixe.asc
    ├── diviseur_resistif_variable.asc
    ├── rc_sinus_temporel.asc
    ├── rc_sinus_frequentiel.asc
    ├── zener_diviseur.asc
    ├── stabbilisateur_tension_zener.asc
    ├── amplificateur_bipolaire.asc
    └── general.asc
```

### Fichiers principaux

- `app.py` : interface Streamlit, session state, formulaires, affichage des tracés
- `main.py` : détection du type d'exercice, extraction de paramètres, appels IA, traceurs matplotlib
- `ltspice_generator.py` : injection de paramètres dans les templates, génération IA (Haiku), analyse d'énoncé libre
- `prompts/` : prompts spécialisés par famille de circuit
- `templates/` : fichiers `.asc` LTSpice XVII vérifiés (UTF-8, coordonnées validées)

### API publique de `ltspice_generator`

```python
analyser_enonce_ia(enonce, client=None) -> dict
# Identifie le meilleur template depuis un texte libre (Haiku JSON)
# {"type_circuit": str, "parametres": {str: float}, "explication": str}

generer_asc_depuis_params(type_circuit, params, enonce_ia=None, client=None) -> dict
# Génère le .asc depuis des paramètres explicites (formulaire ou analyse IA)
# {"asc_path", "asc_content", "parametres", "type_circuit", "template_fichier", "ia_generated"}
```

## Limites actuelles

- Pas de vérification symbolique formelle
- Pas d'export PDF/PNG intégré
- Pas d'historique persistant des conversations

## Pistes d'amélioration

- Ajouter une suite de tests unitaires pour les extracteurs de paramètres
- Ajouter des tests de non-régression sur la détection de type
- Ajouter export de courbes et rapport automatique
- [x] Upload d'image de circuit pour analyse automatique
- [x] Génération `.asc` depuis énoncé textuel (7 templates + IA)
- [x] Interface formulaire structurée par type de circuit

## Ressources

- [Documentation Anthropic Claude](https://docs.anthropic.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [LTSpice XVII](https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html)

## Auteur

Créé pour les étudiants en Électronique I à l'EPFL.

## Licence

MIT — Libre d'utilisation et de modification.

---

**Questions ou problèmes ?** Vérifier que :
1. ✅ La clé API est dans `.env`
2. ✅ Les paquets sont installés (`pip list | grep streamlit`)
3. ✅ Vous êtes dans l'environnement virtuel
4. ✅ Streamlit fonctionne (`streamlit --version`)
