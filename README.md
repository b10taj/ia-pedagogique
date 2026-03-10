# Assistant Électronique ⚡

Une application interactive basée sur l'IA pour résoudre des exercices d'électronique. Détecte automatiquement le type de problème et fournit une explication structurée avec formules, méthode de résolution et résultats numériques.

## ✨ Fonctionnalités

### 🔍 Détection Automatique de Problèmes
- **Diviseur de tension** : formules clés, démarche, résultat numérique
- **Transistor bipolaire** : régimes, paramètres clés, calculs détaillés
- **Inverseur bipolaire** : 3 régimes, transitions, pente, courbe VOUT=f(VIN)
- **Problèmes généraux** : assistant flexible pour d'autres circuits

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
- Clé API Anthropic (A retrouver sur [console.anthropic.com](https://console.anthropic.com))

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

## 🔧 Configuration Avancée

### Modifier les tokens max
Éditer `main.py` :
```python
max_tokens=1200  # Augmenter pour réponses plus longues
```

### Ajouter un nouveau type d'exercice
1. Ajouter des mots-clés dans `detecter_type_probleme()`
2. Créer une fonction `expliquer_nouveau_type()`
3. Ajouter le cas dans `expliquer_probleme()`
4. Mettre à jour `app.py` pour l'affichage

## 📊 Exemple de Sortie

Pour un inverseur bipolaire, vous obtenez :

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

## ⚙️ Limitations Actuelles

- Ne valide pas automatiquement les résultats
- Pas de historique de conversations
- Limité aux types d'exercices détectés
- Pas de sauvegarde des résultats

## 🚧 Améliorations Futures

- [ ] Cache des réponses récurrentes
- [ ] Export PNG/PDF des courbes
- [ ] Historique de conversations
- [ ] Support amplificateur à émetteur commun
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
