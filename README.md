# Assistant Electronique

Application Streamlit qui assiste la resolution d'exercices d'electronique (analyse guidee + traces automatiques), avec detection automatique du type d'enonce et routage vers des prompts specialises.

## Fonctionnalites

### UI a deux modes
- **Mode Resolution d'exercice** : workflow actuel (detection automatique, explication pas a pas, traces si applicable)
- **Mode Simulation LTspice** : nouvelle interface dediee (upload de fichiers `.asc/.cir/.net/.txt` + zone d'instructions)
- Selection visuelle via cartes cliquables avec etat actif
- Style contraste eleve (cartes sombres, texte clair, bordures renforcees)
- Note : la logique backend de simulation LTspice est prevue ensuite (UI en place, execution non active)

### Detection automatique des exercices
- Diode silicium simple
- Diode en boites noires (X/Y)
- Diode Zener simple
- Inverseur bipolaire
- Transistor bipolaire
- Diviseur de tension
- Exercices de puissance (serie, parallele, deux sources)
- RC premier ordre passe-bas (saut simple ou deux sauts)
- RC premier ordre sous signal carre
- RC signal carre en regime de cretes (periode courte)
- RC avec reduction de Thevenin : R1-(R2 // C)-R3
- Fallback probleme general

### Explications pedagogiques
- Demarche pas a pas
- Equations et substitutions numeriques
- Verification physique des resultats
- Conclusion synthetique
- Formatage LaTeX dans les reponses

### Traces automatiques (matplotlib)
- Courbe VOUT=f(VIN) pour inverseur bipolaire
- Reponse temporelle RC passe-bas (1 saut ou 2 sauts)
- Reponse RC a signal carre
- Reponse RC Thevenin (VIN, Vth et Vout)

## Installation

### Prerequis
- Python 3.8+
- Cle API Anthropic

### Etapes
1. Cloner le repository
```bash
git clone <repo_url>
cd Codes
```

2. Creer et activer l'environnement virtuel
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Installer les dependances
```bash
pip install -r requirements.txt
```

4. Configurer la cle API
Creer un fichier `.env` a la racine :
```env
ANTHROPIC_API_KEY=sk-ant-...
```

5. Lancer l'application
```bash
streamlit run app.py
```

## Utilisation

1. Choisir un mode dans le menu de cartes :
	- **Resolution d'exercice**
	- **Simulation LTspice**
2. En mode Resolution : saisir un enonce puis cliquer sur Envoyer
3. L'assistant detecte le type de probleme et route vers le prompt specialise
4. Lire l'explication et, si applicable, le trace genere automatiquement
5. En mode Simulation LTspice : importer des fichiers et preparer les instructions (UI disponible, traitement backend a venir)

## Exemples d'enonces RC couverts

### Exercice 1.a (passe-bas, saut unique)
"R=1kOhm, C=1uF, Vin passe de 1V a 6V a t=0."

### Exercice 1.b (deux sauts)
"R=1kOhm, C=1uF, saut de -5V a t=0 puis saut de +5V a t=10ms."

### Exercice 2.a (signal carre, charge/decharge complete)
"R1=1kOhm, R2=4kOhm, C=20nF, signal carre de periode T=2ms, niveau bas 1V, niveau haut 6V."

### Exercice 2.b (signal carre, regime de cretes)
"Meme circuit RC, periode tres courte, calculer Vmax, Vmin et l'ondulation."

### Exercice 3 (Thevenin)
"R1=1k, R2=2k, R3=1k, C=20nF, R2 en parallele avec C, signal carre 0 a 5V, T=1ms."

### Exercices puissance couverts

**Puissances dans une maille série :**
> On considère une seule maille composée d'une source $V_{IN}=10V$, puis de deux résistances $R_1=1k\Omega$ et $R_2=4k\Omega$. Calculer la puissance absorbée par chaque résistance et la puissance fournie par $V_{IN}$.

**Puissances avec source de courant en parallèle :**
> Source de courant $I_0=1mA$ en parallèle avec $R_1=1k\Omega$ et $R_2=4k\Omega$. Calculer la puissance absorbée par chaque résistance et la puissance fournie par la source.

**Puissances avec deux sources de tension :**
> Je souhaite calculer les puissances fournies et absorbées. Je propose une maille avec deux sources de tension $V_1=2V$ et $V_2=5V$ séparées par une résistance $R=1k\Omega$. Calculer les trois puissances et dire qui absorbe et qui fournit.

## Architecture

```text
.
|- app.py
|- main.py
|- prompts/
|  |- passive.py
|  |- diodes.py
|  |- diode_zener.py
|  |- transistor.py
|  |- general.py
```

### Fichiers
- `app.py` : interface Streamlit, session state, affichage des traces
- `main.py` : detection, extraction de parametres, appels IA, traceurs
- `prompts/passive.py` : prompts RC, puissance, diviseur

### Routage principal
`detecter_type_probleme(question)`

Ordre de priorite actuel (resume) :
1. Diodes
2. RC signal carre cretes
3. RC Thevenin
4. RC signal carre
5. RC passe-bas
6. Inverseur / puissance / transistor / diviseur
7. General

## Fonctions cle ajoutees pour RC

### Explication IA
- `expliquer_premier_ordre_passe_bas()`
- `expliquer_premier_ordre_signal_carre()`
- `expliquer_premier_ordre_signal_carre_crete()`
- `expliquer_thevenin_rc_signal_carre()`

### Extraction de parametres
- `extraire_parametres_rc()` : extracteur RC commun pour les cas passe-bas, signal carre et Thevenin
- `extraire_parametres_passe_bas_premier_ordre()`
- `extraire_parametres_signal_carre_rc()`
- `extraire_parametres_thevenin_rc_signal_carre()`

Gestion des unites/préfixes : `k`, `m`, `u`, `micro`, `n`, `nano`, `p`, `meg`.
Normalisation amont des énoncés RC : texte copié depuis PDF/Word, symboles Unicode, indices éclatés sur plusieurs lignes, espaces autour de `=`.

### Traceurs
- `tracer_passe_bas_premier_ordre()`
- `tracer_signal_carre_rc()`
- `tracer_thevenin_rc_signal_carre()`

## Corrections techniques importantes

### Nettoyage de code non desire dans les reponses IA
- Ajout d'un filtre backend `nettoyer_reponse_sans_code()` pour supprimer blocs ```...``` et imports parasites.

### Correction regex mots-cles courts
- Correction de l'usage de `\b` avec `re.escape(...)` pour eviter les faux positifs/faux negatifs.

### Correction parsing unites
- Ajout de la prise en charge explicite de `micro` et `nano` dans les extracteurs.

### Correction extraction RC et valeurs par defaut
- Factorisation de l'extraction RC dans une fonction commune pour les differents exercices RC.
- Ajout d'une normalisation des énoncés avant regex pour gérer les copier-coller depuis PDF/Word.
- Correction du cas où les tracés retombaient sur les valeurs par défaut faute d'extraction des paramètres.

### Correction bug de formatage des prompts (critique)
- Erreur resolue : `KeyError: '-t/\\tau'` due aux accolades LaTeX non echappees lors de `.format()`.
- Solution : doubles accolades pour les blocs LaTeX litteraux dans les prompts.

## Limites actuelles
- Pas de verification symbolique formelle
- Pas d'export PDF/PNG integre
- Pas d'historique persistant des conversations

## Pistes d'amelioration
- Ajouter une suite de tests unitaires pour les extracteurs regex
- Ajouter des tests de non-regression sur la detection de type
- Ajouter export de courbes et rapport automatique
- [x] Upload d'image de circuit pour analyse automatique
- [ ] Activer le backend du mode Simulation LTspice (creation/modification de fichiers)

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
