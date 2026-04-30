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

# Sélecteur de mode (UI)
st.markdown(
    """
    <style>
    .mode-card {
        border: 2px solid #5f6b85;
        border-radius: 12px;
        padding: 14px;
        background: linear-gradient(160deg, #1f2937 0%, #111827 100%);
        min-height: 130px;
        box-shadow: 0 2px 10px rgba(17, 24, 39, 0.35);
    }
    .mode-title {
        font-weight: 700;
        font-size: 1.02rem;
        margin-bottom: 6px;
        color: #f8fafc;
    }
    .mode-desc {
        color: #d1d5db;
        font-size: 0.92rem;
        line-height: 1.35;
    }
    .mode-badge {
        display: inline-block;
        margin-top: 8px;
        padding: 2px 8px;
        border-radius: 999px;
        background: #2563eb;
        color: #eff6ff;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid #93c5fd;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.write("### 🎛️ Choix du mode")
mode_col1, mode_col2 = st.columns(2)

with mode_col1:
    badge = "<span class='mode-badge'>Actif</span>" if st.session_state.ui_mode == "exercise" else ""
    st.markdown(
        f"""
        <div class="mode-card">
            <div class="mode-title">🧠 Résolution d'exercice</div>
            <div class="mode-desc">Analyse guidée, détection automatique du type d'exercice, explication pas à pas.</div>
            {badge}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Choisir Résolution", use_container_width=True):
        st.session_state.ui_mode = "exercise"
        st.rerun()

with mode_col2:
    badge = "<span class='mode-badge'>Actif</span>" if st.session_state.ui_mode == "simulation" else ""
    st.markdown(
        f"""
        <div class="mode-card">
            <div class="mode-title">🧪 Simulation LTspice</div>
            <div class="mode-desc">Manipulation et création de fichiers LTspice (.asc, .cir, .net).</div>
            {badge}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Choisir Simulation", use_container_width=True):
        st.session_state.ui_mode = "simulation"
        st.rerun()

if st.session_state.ui_mode == "simulation":
    st.write("---")
    st.write("### 🧪 Mode Simulation LTspice")
    st.info("UI en place. La logique de création/modification des fichiers LTspice sera ajoutée ensuite.")
    st.write("#### Fichiers LTspice (optionnel)")
    st.file_uploader(
        "Importer un schéma ou netlist",
        type=["asc", "cir", "net", "txt"],
        accept_multiple_files=True,
        key="ltspice_files",
    )
    st.text_area(
        "Instruction pour l'IA (simulation)",
        placeholder="Ex: Crée une netlist RC passe-bas avec R=1k, C=100n, source sinusoïdale 1kHz.",
        height=120,
        key="ltspice_prompt",
    )
    st.button("Lancer (bientôt)", disabled=True, use_container_width=True)
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