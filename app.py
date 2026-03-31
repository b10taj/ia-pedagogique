# app.py
import streamlit as st
import base64
from io import BytesIO
from PIL import ImageGrab
from main import expliquer_probleme, detecter_type_probleme, tracer_inverseur
from anthropic import Anthropic

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
        
        # Déterminer si c'est la première question
        is_first_question = len([m for m in st.session_state.messages if m["role"] == "user"]) == 1
        
        if is_first_question:
            # Première question : détecter le type et utiliser le prompt spécialisé
            st.session_state.circuit_type = detecter_type_probleme(user_input)
            response_text = expliquer_probleme(user_input, st.session_state.image_base64)
        else:
            # Questions suivantes : continuer la conversation avec l'IA
            # Préparer les messages pour l'API Anthropic
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