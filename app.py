# app.py
import streamlit as st
import base64
from io import BytesIO
from PIL import ImageGrab
from main import (
    expliquer_probleme,
    detecter_type_probleme,
    extraire_parametres_passe_bas_premier_ordre,
    extraire_parametres_signal_carre_rc,
    extraire_parametres_thevenin_rc_signal_carre,
    tracer_inverseur,
    tracer_passe_bas_premier_ordre,
    tracer_signal_carre_rc,
    tracer_thevenin_rc_signal_carre,
)
from anthropic import Anthropic

DEFAULT_RC_PARAMS = {
    "resistance": 1000.0,
    "capacite": 1e-6,
    "vin_initial": 0.0,
    "vin_final": 5.0,
}

DEFAULT_RC_CARRE_PARAMS = {
    "r1": 1000.0,
    "r2": 4000.0,
    "capacite": 20e-9,
    "periode": 2e-3,
    "v_bas": 1.0,
    "v_haut": 6.0,
}

DEFAULT_THEVENIN_RC_PARAMS = {
    "r1": 1000.0,
    "r2": 2000.0,
    "r3": 1000.0,
    "capacite": 20e-9,
    "periode": 1e-3,
    "v_bas": 0.0,
    "v_haut": 5.0,
}

# Initialiser le client Anthropic
client = Anthropic()

st.title("Assistant Électronique ⚡")

# Initialiser la session state pour la conversation
if "messages" not in st.session_state:
    st.session_state.messages = []
if "image_base64" not in st.session_state:
    st.session_state.image_base64 = None
if "circuit_type" not in st.session_state:
    st.session_state.circuit_type = None
if "plot_type" not in st.session_state:
    st.session_state.plot_type = None
if "plot_params" not in st.session_state:
    st.session_state.plot_params = None
if "ui_mode" not in st.session_state:
    st.session_state.ui_mode = "exercise"
if "ltspice_resultat" not in st.session_state:
    st.session_state.ltspice_resultat = None
if "ltspice_last_type" not in st.session_state:
    st.session_state.ltspice_last_type = None

_mode = st.session_state.ui_mode
_active_col = "1" if _mode == "exercise" else "2"
st.markdown(f"""
<style>
div[data-testid="stColumn"] div[data-testid="stButton"] button {{
    background: linear-gradient(160deg, #1f2937 0%, #111827 100%) !important;
    border: 2px solid #5f6b85 !important;
    border-radius: 12px !important;
    min-height: 130px !important;
    height: auto !important;
    color: #d1d5db !important;
    white-space: pre-line !important;
    text-align: left !important;
    padding: 14px 18px !important;
    font-size: 0.9rem !important;
    line-height: 1.4 !important;
}}
div[data-testid="stColumn"] div[data-testid="stButton"] button:hover {{
    border-color: #3b82f6 !important;
    color: #f8fafc !important;
}}
div[data-testid="stColumn"]:nth-child({_active_col}) div[data-testid="stButton"] button {{
    border-color: #2563eb !important;
    color: #f8fafc !important;
}}
div[data-testid="stSelectbox"] input {{
    pointer-events: none !important;
    caret-color: transparent !important;
}}
</style>
""", unsafe_allow_html=True)

st.write("### 🎛️ Choix du mode")
mode_col1, mode_col2 = st.columns(2)

with mode_col1:
    _tag = "  ● Actif" if _mode == "exercise" else ""
    if st.button(
        f"🧠 Résolution d'exercice{_tag}\n\nAnalyse guidée, détection automatique du type d'exercice, explication pas à pas.",
        use_container_width=True,
        key="btn_mode_exercise",
    ):
        st.session_state.ui_mode = "exercise"
        st.rerun()

with mode_col2:
    _tag = "  ● Actif" if _mode == "simulation" else ""
    if st.button(
        f"🧪 Simulation LTspice{_tag}\n\nManipulation et création de fichiers LTspice (.asc, .cir, .net).",
        use_container_width=True,
        key="btn_mode_simulation",
    ):
        st.session_state.ui_mode = "simulation"
        st.rerun()

if st.session_state.ui_mode == "simulation":
    from ltspice_generator import generer_asc_depuis_params, analyser_enonce_ia

    st.write("---")
    st.write("### 🧪 Mode Simulation LTspice")

    TYPES_CIRCUIT = {
        "Diviseur résistif (résistances fixes)":          "diviseur_resistif_fixe",
        "Diviseur résistif (résistance variable — sweep)": "diviseur_resistif_variable",
        "Circuit RC — Analyse temporelle (sinus)":        "rc_sinus_temporel",
        "Circuit RC — Analyse fréquentielle (Bode)":      "rc_sinus_frequentiel",
        "Diviseur avec diode Zener":                      "zener_diviseur",
        "Stabilisateur de tension Zener":                 "stabilisateur_tension_zener",
        "Amplificateur bipolaire NPN (émetteur commun)":  "amplificateur_bipolaire",
        "Général — description libre (IA)":               "general",
    }
    TYPES_INVERSE = {v: k for k, v in TYPES_CIRCUIT.items()}

    type_label = st.selectbox("Type de circuit", list(TYPES_CIRCUIT.keys()), key="ltspice_type_select")
    type_circuit = TYPES_CIRCUIT[type_label]

    # Réinitialiser le résultat si le type change
    if st.session_state.ltspice_last_type != type_circuit:
        st.session_state.ltspice_resultat = None
        st.session_state.ltspice_last_type = type_circuit

    if type_circuit == "general":
        enonce_sim = st.text_area(
            "Décris ton circuit",
            placeholder=(
                "Ex: Filtre RLC série R=100Ω, L=10mH, C=1µF — sinus 1kHz\n"
                "Ex: Ampli-op inverseur, R1=10k, R2=100k, alimentation ±15V\n"
                "Ex: Pont de Wheatstone, 4 résistances de 1k, source 5V"
            ),
            height=130,
            key="ltspice_enonce_general",
        )
        if st.button("Analyser et générer", use_container_width=True):
            if not enonce_sim.strip():
                st.warning("Saisis un énoncé avant de continuer.")
            else:
                with st.spinner("Analyse IA du circuit…"):
                    try:
                        analyse = analyser_enonce_ia(enonce_sim, client=client)
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse : {e}")
                        st.stop()

                type_detecte = analyse["type_circuit"]
                params_ia    = analyse["parametres"]

                if analyse.get("explication"):
                    st.info(f"💡 {analyse['explication']}")

                if type_detecte != "general":
                    label_detecte = TYPES_INVERSE.get(type_detecte, type_detecte)
                    st.success(f"Template identifié : **{label_detecte}**")
                    if params_ia:
                        st.write("**Paramètres extraits :**")
                        cols = st.columns(min(len(params_ia), 4))
                        for i, (k, v) in enumerate(params_ia.items()):
                            cols[i % 4].metric(k, f"{v:g}")
                else:
                    st.info("Aucun template correspondant — génération IA du fichier .asc…")

                with st.spinner("Génération du fichier…"):
                    try:
                        st.session_state.ltspice_resultat = generer_asc_depuis_params(
                            type_detecte, params_ia, enonce_ia=enonce_sim, client=client
                        )
                    except Exception as e:
                        st.error(f"Erreur de génération : {e}")
                        st.stop()

    else:
        with st.form(key="form_ltspice"):
            params = {}

            if type_circuit == "diviseur_resistif_fixe":
                c1, c2, c3 = st.columns(3)
                params["VIN"] = c1.number_input("VIN (V)", value=10.0, min_value=0.1, step=0.5)
                params["R1"]  = c2.number_input("R1 (Ω)", value=10000.0, min_value=1.0, step=100.0, format="%.0f")
                params["R2"]  = c3.number_input("R2 (Ω)", value=10000.0, min_value=1.0, step=100.0, format="%.0f")

            elif type_circuit == "diviseur_resistif_variable":
                c1, c2 = st.columns(2)
                params["VIN"] = c1.number_input("VIN (V)", value=10.0, min_value=0.1, step=0.5)
                params["R1"]  = c2.number_input("R1 fixe (Ω)", value=10000.0, min_value=1.0, step=100.0, format="%.0f")
                st.caption("R2 balayée automatiquement par .step param (template prédéfini)")

            elif type_circuit == "rc_sinus_temporel":
                c1, c2, c3, c4 = st.columns(4)
                params["R1"]   = c1.number_input("R (Ω)", value=1000.0, min_value=1.0, step=100.0, format="%.0f")
                params["C1"]   = c2.number_input("C (nF)", value=100.0, min_value=0.001, step=10.0) * 1e-9
                params["Vamp"] = c3.number_input("Amplitude (V)", value=1.0, min_value=0.001)
                params["freq"] = c4.number_input("Fréquence (Hz)", value=1000.0, min_value=0.1, step=100.0)

            elif type_circuit == "rc_sinus_frequentiel":
                c1, c2, c3, c4 = st.columns(4)
                params["R1"]      = c1.number_input("R (Ω)", value=1000.0, min_value=1.0, step=100.0, format="%.0f")
                params["C1"]      = c2.number_input("C (nF)", value=100.0, min_value=0.001, step=10.0) * 1e-9
                params["f_start"] = c3.number_input("f min (Hz)", value=1.0, min_value=0.01, step=1.0)
                params["f_stop"]  = c4.number_input("f max (MHz)", value=10.0, min_value=0.001, step=1.0) * 1e6

            elif type_circuit == "zener_diviseur":
                c1, c2, c3, c4 = st.columns(4)
                params["VIN"]  = c1.number_input("VIN amplitude (V)", value=12.0, min_value=0.1)
                params["R1"]   = c2.number_input("R série (Ω)", value=1000.0, min_value=1.0, step=10.0, format="%.0f")
                params["R2"]   = c3.number_input("R charge (Ω)", value=1000.0, min_value=1.0, step=100.0, format="%.0f")
                params["freq"] = c4.number_input("Fréquence (Hz)", value=1000.0, min_value=0.1, step=100.0)

            elif type_circuit == "stabilisateur_tension_zener":
                c1, c2, c3 = st.columns(3)
                params["Vamp"] = c1.number_input("Amplitude source (V)", value=20.0, min_value=0.1)
                params["freq"] = c2.number_input("Fréquence (Hz)", value=50.0, min_value=0.1, step=10.0)
                params["R1"]   = c3.number_input("R série (Ω)", value=80.0, min_value=1.0, step=10.0, format="%.0f")
                st.caption("RL balayée automatiquement par .step param (1Ω → 1MΩ)")

            elif type_circuit == "amplificateur_bipolaire":
                st.write("**Alimentation & signal d'entrée**")
                c1, c2, c3 = st.columns(3)
                params["VCC"]  = c1.number_input("VCC (V)", value=15.0, min_value=1.0, step=1.0)
                params["Vamp"] = c2.number_input("VIN amplitude (mV)", value=10.0, min_value=0.001, step=1.0) * 1e-3
                params["freq"] = c3.number_input("Fréquence (Hz)", value=1000.0, min_value=1.0, step=100.0)
                st.write("**Résistances**")
                c4, c5, c6, c7 = st.columns(4)
                params["RC"] = c4.number_input("RC collecteur (Ω)", value=2000.0, min_value=1.0, step=100.0, format="%.0f")
                params["RE"] = c5.number_input("RE émetteur (Ω)", value=1000.0, min_value=1.0, step=100.0, format="%.0f")
                params["R1"] = c6.number_input("R1 base (Ω)", value=2700.0, min_value=1.0, step=100.0, format="%.0f")
                params["R2"] = c7.number_input("R2 base (Ω)", value=12300.0, min_value=1.0, step=100.0, format="%.0f")
                st.caption("RL balayée automatiquement par .step param (50Ω → 550Ω)")

            submitted = st.form_submit_button("⚡ Générer le fichier .asc", use_container_width=True)

        if submitted:
            with st.spinner("Génération du fichier…"):
                try:
                    st.session_state.ltspice_resultat = generer_asc_depuis_params(
                        type_circuit, params, client=client
                    )
                except Exception as e:
                    st.error(f"Erreur : {e}")
                    st.stop()

    # Affichage du résultat (commun aux deux modes)
    if st.session_state.ltspice_resultat is not None:
        r = st.session_state.ltspice_resultat
        type_labels = {
            "diviseur_resistif_fixe":      "Diviseur résistif (résistances fixes)",
            "diviseur_resistif_variable":  "Diviseur résistif (résistance variable)",
            "rc_sinus_temporel":           "Circuit RC — Analyse temporelle (sinus)",
            "rc_sinus_frequentiel":        "Circuit RC — Analyse fréquentielle (Bode)",
            "zener_diviseur":              "Diviseur avec diode Zener",
            "stabilisateur_tension_zener": "Stabilisateur de tension Zener",
            "amplificateur_bipolaire":     "Amplificateur bipolaire NPN (émetteur commun)",
            "general":                     "Circuit personnalisé — généré par IA",
        }
        label = type_labels.get(r["type_circuit"], r["type_circuit"])
        st.success(f"Circuit : **{label}** — template `{r['template_fichier']}`")

        if r.get("ia_generated"):
            st.info(
                "Ce fichier a été généré entièrement par l'IA. "
                "Les positions des composants peuvent nécessiter de légères corrections "
                "visuelles dans LTSpice (déplacer/reconnecter des fils). "
                "La topologie et les valeurs sont correctes."
            )

        st.code(r["asc_content"], language="text")

        st.download_button(
            label="⬇️ Télécharger le fichier LTSpice (.asc)",
            data=r["asc_content"],
            file_name=f"circuit_{r['type_circuit']}.asc",
            mime="text/plain",
            use_container_width=True,
        )

    st.stop()

# Section pour charger une image optionnelle
st.write("### 📸 Circuit (optionnel)")

# Tabs pour choisir entre upload fichier ou coller une image
image_tab1, image_tab2 = st.tabs(["📁 Charger un fichier", "📋 Coller du presse-papiers"])

with image_tab1:
    uploaded_image = st.file_uploader("Sélectionner une image du circuit", type=["png", "jpg", "jpeg", "gif"])
    if uploaded_image is not None and st.session_state.image_base64 is None:
        image_bytes = base64.b64encode(uploaded_image.read()).decode()
        image_ext = uploaded_image.name.split('.')[-1].lower()
        if image_ext == 'jpg':
            image_ext = 'jpeg'
        st.session_state.image_base64 = f"data:image/{image_ext};base64,{image_bytes}"
        st.image(uploaded_image, caption="Circuit fourni", width=400)

with image_tab2:
    st.write("**Cliquez sur le bouton ci-dessous pour coller une image du presse-papiers**")
    if st.button("📋 Coller une image"):
        try:
            image = ImageGrab.grabclipboard()
            if image is not None:
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                image_bytes = base64.b64encode(buffered.getvalue()).decode()
                st.session_state.image_base64 = f"data:image/png;base64,{image_bytes}"
                st.success("✅ Image collée avec succès!")
                st.image(image, caption="Image depuis presse-papiers", width=400)
            else:
                st.error("❌ Aucune image trouvée dans le presse-papiers.")
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

st.write("---")

# Afficher l'historique de la conversation
st.write("### 💬 Conversation")

# Afficher le type détecté si on l'a
if st.session_state.circuit_type:
    if st.session_state.circuit_type == "diode_zener_simple":
        st.info("🔍 Type détecté : **Circuit à Diode Zener (Simple)**")
    elif st.session_state.circuit_type == "diode_simple":
        st.info("🔍 Type détecté : **Circuit à Diode (Simple)**")
    elif st.session_state.circuit_type == "diode_boites":
        st.info("🔍 Type détecté : **Circuit à Diode (Boîtes Noires)**")
    elif st.session_state.circuit_type == "inverseur":
        st.info("🔍 Type détecté : **Inverseur Bipolaire**")
    elif st.session_state.circuit_type == "premier_ordre_passe_bas":
        st.info("🔍 Type détecté : **Filtre Passe-Bas RC du Premier Ordre**")
    elif st.session_state.circuit_type == "premier_ordre_signal_carre":
        st.info("🔍 Type détecté : **RC du Premier Ordre - Signal Carré**")
    elif st.session_state.circuit_type == "premier_ordre_signal_carre_crete":
        st.info("🔍 Type détecté : **RC Signal Carré (Période Courte - Valeurs de Crête)**")
    elif st.session_state.circuit_type == "thevenin_rc_signal_carre":
        st.info("🔍 Type détecté : **RC Thévenin — R1-(R2//C)-R3 signal carré**")
    elif st.session_state.circuit_type == "transistor":
        st.info("🔍 Type détecté : **Transistor Bipolaire**")
    elif st.session_state.circuit_type == "puissance_deux_sources":
        st.info("🔍 Type détecté : **Puissance (Deux Sources + Résistance)**")
    elif st.session_state.circuit_type == "puissance_parallele":
        st.info("🔍 Type détecté : **Puissance (Parallèle)**")
    elif st.session_state.circuit_type == "puissance_serie":
        st.info("🔍 Type détecté : **Puissance (Série)**")
    elif st.session_state.circuit_type == "diviseur":
        st.info("🔍 Type détecté : **Diviseur de Tension**")
    else:
        st.info("🔍 Type détecté : **Problème Général**")
    st.write("---")

if st.session_state.plot_type == "premier_ordre_passe_bas":
    st.write("### 📈 Réponse temporelle")
    params = st.session_state.plot_params or DEFAULT_RC_PARAMS
    fig = tracer_passe_bas_premier_ordre(**params)
    st.pyplot(fig)
    if st.session_state.plot_params is None:
        st.caption("Paramètres non détectés automatiquement: tracé affiché avec valeurs par défaut (R=1kΩ, C=1µF, VIN: 0V→5V).")
    st.write("---")

if st.session_state.plot_type == "premier_ordre_signal_carre":
    st.write("### 📈 Réponse temporelle au signal carré")
    params = st.session_state.plot_params or DEFAULT_RC_CARRE_PARAMS
    fig = tracer_signal_carre_rc(**params)
    st.pyplot(fig)
    if st.session_state.plot_params is None:
        st.caption("Paramètres non détectés automatiquement: tracé affiché avec valeurs par défaut (R1=1kΩ, R2=4kΩ, C=20nF, T=2ms, niveaux 1V/6V).")
    st.write("---")

if st.session_state.plot_type == "premier_ordre_signal_carre_crete":
    st.write("### 📈 Réponse temporelle au signal carré")
    params = st.session_state.plot_params or DEFAULT_RC_CARRE_PARAMS
    fig = tracer_signal_carre_rc(**params)
    st.pyplot(fig)
    if st.session_state.plot_params is None:
        st.caption("Paramètres non détectés automatiquement: tracé affiché avec valeurs par défaut (R1=1kΩ, R2=4kΩ, C=20nF, T=2ms, niveaux 1V/6V).")
    st.write("---")

if st.session_state.plot_type == "thevenin_rc_signal_carre":
    st.write("### 📈 Réponse VOUT(t) après réduction Thévenin")
    params = st.session_state.plot_params or DEFAULT_THEVENIN_RC_PARAMS
    fig = tracer_thevenin_rc_signal_carre(**params)
    st.pyplot(fig)
    if st.session_state.plot_params is None:
        st.caption("Paramètres non détectés automatiquement: tracé avec valeurs par défaut (R1=1kΩ, R2=2kΩ, R3=1kΩ, C=20nF, T=1ms, 0V/5V).")
    st.write("---")

for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        # Pour la première question utilisateur, afficher juste un résumé court
        if i == 0:
            content_preview = message['content'][:100] + "..." if len(message['content']) > 100 else message['content']
            st.write(f"**Vous :** {content_preview}")
        else:
            # Les questions suivantes s'affichent entièrement
            st.write(f"**Vous :** {message['content']}")
    else:
        st.write(f"**Assistant :** {message['content']}")

# Entrée utilisateur
user_input = st.text_input("Votre question :")

if st.button("Envoyer"):
    if user_input.strip() == "":
        st.warning("Veuillez entrer une question.")
    else:
        # Ajouter le message utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Détection à chaque nouveau message pour activer le tracé si l'utilisateur enchaîne plusieurs questions.
        type_detecte = detecter_type_probleme(user_input)
        if type_detecte == "premier_ordre_passe_bas":
            st.session_state.circuit_type = type_detecte
            st.session_state.plot_type = "premier_ordre_passe_bas"
            st.session_state.plot_params = extraire_parametres_passe_bas_premier_ordre(user_input)
        elif type_detecte == "premier_ordre_signal_carre_crete":
            st.session_state.circuit_type = type_detecte
            st.session_state.plot_type = "premier_ordre_signal_carre_crete"
            st.session_state.plot_params = extraire_parametres_signal_carre_rc(user_input)
        elif type_detecte == "premier_ordre_signal_carre":
            st.session_state.circuit_type = type_detecte
            st.session_state.plot_type = "premier_ordre_signal_carre"
            st.session_state.plot_params = extraire_parametres_signal_carre_rc(user_input)
        elif type_detecte == "thevenin_rc_signal_carre":
            st.session_state.circuit_type = type_detecte
            st.session_state.plot_type = "thevenin_rc_signal_carre"
            st.session_state.plot_params = extraire_parametres_thevenin_rc_signal_carre(user_input)
        elif type_detecte != "general":
            st.session_state.circuit_type = type_detecte
            st.session_state.plot_type = None
            st.session_state.plot_params = None
        
        # Déterminer si c'est la première question
        is_first_question = len([m for m in st.session_state.messages if m["role"] == "user"]) == 1
        
        if is_first_question:
            # Première question : détecter le type et utiliser le prompt spécialisé
            st.session_state.circuit_type = type_detecte
            if st.session_state.circuit_type not in {"premier_ordre_passe_bas", "premier_ordre_signal_carre", "premier_ordre_signal_carre_crete", "thevenin_rc_signal_carre"}:
                st.session_state.plot_type = None
                st.session_state.plot_params = None
            response_text = expliquer_probleme(user_input, st.session_state.image_base64)
        else:
            # Pour un nouvel énoncé spécialisé, on garde le routage spécialisé même après la première question.
            if type_detecte != "general":
                response_text = expliquer_probleme(user_input, st.session_state.image_base64)
            else:
                # Questions générales suivantes : continuer la conversation avec l'IA
                messages_for_api = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]

                response = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=2000,
                    system="Tu es un assistant expert en électronique. Tu aides les étudiants à comprendre les circuits et les problèmes d'analyse. Sois clair, rigoureux et pédagogue.",
                    messages=messages_for_api
                )
                response_text = response.content[0].text.strip()
        
        # Ajouter la réponse à l'historique
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        # Rafraîchir pour afficher les nouveaux messages
        st.rerun()