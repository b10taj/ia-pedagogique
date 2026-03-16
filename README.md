# Assistant Électronique ⚡

Une application interactive basée sur l'IA pour résoudre des exercices d'électronique. Détecte automatiquement le type de problème et fournit une explication structurée avec formules, méthode de résolution et résultats numériques.

## ✨ Fonctionnalités

### 🔍 Détection Automatique de Problèmes
- **Diviseur de tension** : formules clés, démarche, résultat numérique
- **Transistor bipolaire** : régimes, paramètres clés, calculs détaillés
- **Inverseur bipolaire** : 3 régimes, transitions, pente, courbe VOUT=f(VIN)
- **Circuit à diode** : 2 types d'analyse (simple avec R+D explicites, ou boîtes noires X/Y indéterminées)
- **Problèmes généraux** : assistant flexible pour d'autres circuits

### 📐 Formatage Automatique LaTeX
Tous les paramètres mathématiques sont **automatiquement formatés en LaTeX** :
- `V_OUT` → $V_{OUT}$ (indice visible)
- `I_D` → $I_D$ (indice visible)
- `V_BE` → $V_{BE}$ (indice visible)
- `R_C` → $R_C$ (indice visible)
- Toutes les formules affichées avec indices propres

### 📊 Tracé Automatique pour Inverseurs
- Génération de la courbe VOUT = f(VIN)
- Zones colorées (bloquée, active, saturée)
- Paramètres ajustables (VCC, RC, RB, β, VBE, VCE_sat)
- Marquage automatique des transitions

### 💡 Explications Complètes
- Décomposition étape par étape
- Formules et équations utilisées
- Calculs numériques détaillés
- Explications intuitives
- Résumé synthétisé final

## 🚀 Installation

### Prérequis
- Python 3.8+
- Clé API Anthropic (gratuite sur [console.anthropic.com](https://console.anthropic.com))

### Étapes

1. **Cloner le repo**
```bash
git clone <repo_url>
cd Codes
```

2. **Créer un environnement virtuel**
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate   # macOS/Linux
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer la clé API**
Créer un fichier `.env` à la racine :
```
ANTHROPIC_API_KEY=sk-ant-...
```

5. **Lancer l'application**
```bash
streamlit run app.py
```

L'application s'ouvre à `http://localhost:8501`

## 📖 Utilisation

### Interface Simple
1. Posez votre question sur un circuit électronique
2. Cliquez sur **"Expliquer"**
3. L'IA détecte le type et fournit une réponse structurée

### Exemples de Questions

**Diviseur de tension :**
> Calculer la tension de sortie Vout d'un diviseur avec R1=1kΩ, R2=2kΩ et Vin=12V.

**Transistor bipolaire :**
> Un transistor BJT NPN avec β=100, Vbe=0.7V, Ic=2mA. Calculer Ib et Vce si Vcc=10V et Rc=2kΩ.

**Inverseur bipolaire :**
> Analyse d'un inverseur bipolaire. Transistor NPN, β=200, Vcc=5V, Rc=2kΩ, Rb=10kΩ. Dessiner la courbe VOUT=f(VIN), calculer la pente et les tensions limites.

**Circuit à diode :**
> **Type 1 - Simple :** Analyse un circuit à diode D et résistance R=1kΩ. La diode est en série avec R entre VIN et la masse. Examine tous les cas de montage (R-D ou D-R) et polarité (VIN = ±5V).

> **Type 2 - Boîtes noires :** [Schéma fourni avec X et Y]. Sachant que X et Y peuvent être une diode au silicium et une résistance (dans l'un des deux ordres possibles), analyser tous les cas. VIN = ±5V, diode en 2 orientations.

## 🏗️ Architecture

### Fichiers Principaux

```
.
├── app.py              # Interface Streamlit
├── main.py             # Logique IA et traçage
├── .env                # Configuration (clé API)
└── .venv/              # Environnement virtuel
```

### Fonction de Détection
```python
detecter_type_probleme(question)
```
Analyse les mots-clés pour identifier :
- Inverseur (haute priorité)
- Transistor bipolaire
- Diviseur de tension
- Problème général

### Assistants Spécialisés
- `expliquer_diviseur_tension()` : prompt 300 tokens
- `expliquer_transistor_bipolaire()` : prompt 600 tokens
- `expliquer_inverseur_bipolaire()` : prompt 1500 tokens
- `expliquer_diode_simple()` : prompt 1500 tokens (R et D explicites)
- `expliquer_diode_boites()` : prompt 2400 tokens (boîtes noires X, Y indéterminées)
- `expliquer_probleme_general()` : prompt 300 tokens

### Traçage
```python
tracer_inverseur(vcc, rc, rb, beta, vbe, vce_sat)
```
Génère la courbe de transfert avec matplotlib et Streamlit.

## 💰 Coûts API

**Modèle utilisé :** Claude Haiku 4.5 (le plus économique)

- **Output tokens :** $4.00 par 1M tokens
- **Une réponse type :** ~0.0002¢
- **1000 réponses :** ~$0.02

Très économique pour un usage étudiant ! 💚

## 🔧 Types d'Exercices sur les Diodes

Le système détecte et traite **2 types distincts** d'exercices diode :

### Type 1️⃣ : Diode Simple (R et D Explicites)
**Situation :** Circuit avec une résistance R et une diode D au silicium entre VIN et la masse.

**Variables :**
- **Ordre des éléments** (2 cas) : R-D ou D-R
- **Orientation de la diode** (2 cas) : normal (anode vers VIN) ou inverse
- **Polarité de VIN** (2 cas) : positive ou négative
- **Total : 2 × 2 × 2 = 8 cas à analyser**

**Analyse :** Pour chaque configuration, déterminer l'état de la diode (conduction : Vd ≈ 0.7V ou blocage : Id = 0), les courants et tensions.

**Mots-clés de détection :** "R et D", "R puis D", "D puis R", "configuration"

---

### Type 2️⃣ : Boîtes Noires Indéterminées (X et Y)
**Situation :** Schéma fourni avec deux boîtes noires (X et Y) qui peuvent être :
- Configuration 1 : X = Diode au silicium, Y = Résistance
- Configuration 2 : X = Résistance, Y = Diode au silicium

**Variables (par configuration) :**
- **Type d'élément** (2 cas) : X=D/Y=R ou X=R/Y=D
- **Orientation de la diode** (2 cas) : normal ou inverse
- **Polarité de VIN** (2 cas) : positive ou négative
- **Total : 2 configurations × 2 orientations × 2 polarités = 8 cas par paire**

**Analyse :** Déterminer quels éléments sont X et Y, puis analyser tous les régimes de fonctionnement.

**Mots-clés de détection :** "boîte noire", "boîtes noires", "X et Y", "indéterminé"

---

## 🔧 Configuration Avancée

### Stratégie de Détection des Diodes

Le système détecte automatiquement le **type d'exercice diode** :

1. **Présence de mots-clés diode** : "diode", "silicium", "anode", "cathode", "redressement"
2. **Sous-distinction :**
   - Contient "boîte noire", "boîtes noires", "X et Y" → **Type 2 (boîtes noires)**
   - Sinon → **Type 1 (simple R+D explicites)**
3. **Ordre de priorité global** : Diode > Inverseur > Transistor > Diviseur > Général

### Ajouter un nouveau type d'exercice
1. Ajouter des mots-clés dans `detecter_type_probleme()`
2. Créer une fonction `expliquer_nouveau_type()`
3. Ajouter le cas dans `expliquer_probleme()`
4. Mettre à jour `app.py` pour l'affichage

## 📊 Exemple de Sortie

### Pour un inverseur bipolaire :

✅ **Explication complète :**
- Régimes de fonctionnement avec équations
- Calculs numériques détaillés
- Transitions : VIN₁ = 0.7V, VIN₂ ≈ 0.82V
- Pente : -40 V/V
- Résumé des 3 zones

✅ **Courbe automatique :**
- Tracé VOUT vs VIN
- Zones colorées
- Transitions marquées

### Pour un circuit à diode :

**Type 1 - Simple :**
✅ **Analyse des 8 cas** (4 configurations × 2 polarités)
- Configuration : ordre (R-D ou D-R) + orientation (normal/inverse)
- Pour chaque cas + VIN (±) : état de la diode (conduction/blocage)
- Calculs : Id, Vd, VR, V_OUT
- Tableau récapitulatif final

**Type 2 - Boîtes noires :**
✅ **Analyse des 2 configurations principales** (chacune × 2 orientations × 2 polarités = 8 cas)
- Configuration A : X = Diode, Y = Résistance
- Configuration B : X = Résistance, Y = Diode
- Pour chaque : tous les cas (direct/reverse, ± polarité)
- Tableau final : Id, Vd, V_OUT cohérent
- Tableau récapitulatif avec tous les cas
- État final : conducting/blocking/reverse-blocking

## ⚙️ Limitations Actuelles

- Ne valide pas automatiquement les résultats
- Pas de historique de conversations
- Limité aux types d'exercices détectés
- Pas de sauvegarde des résultats

## 🚧 Améliorations Futures

- [ ] Cache des réponses récurrentes
- [ ] Export PNG/PDF des courbes
- [ ] Historique de conversations
- [ ] Upload d'image de circuit pour analyse automatique
- [ ] Support amplificateur à émetteur commun
- [ ] Support redresseurs à diodes multiples
- [ ] Validation mathématique des résultats
- [ ] Librairie étendue de circuits
- [ ] Mode "quiz" pédagogique

## 📚 Ressources

- [Documentation Anthropic Claude](https://docs.anthropic.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Matplotlib Tutorial](https://matplotlib.org/stable/tutorials/index.html)

## 👨‍💼 Auteur

Créé pour les étudiants en Électronique I à l'EPFL.

## 📄 Licence

MIT - Libre d'utilisation et de modification.

---

**Questions ou problèmes ?** Vérifiez que :
1. ✅ La clé API est dans `.env`
2. ✅ Les paquets sont installés (`pip list | grep streamlit`)
3. ✅ Vous êtes dans l'environnement virtuel
4. ✅ Streamlit fonctionne (`streamlit --version`)
