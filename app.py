# app.py
import streamlit as st
from main import expliquer_probleme, detecter_type_probleme, tracer_inverseur

st.title("Assistant Électronique ⚡")

question = st.text_input("Pose une question sur un circuit électronique :")

if st.button("Expliquer"):
    if question.strip() == "":
        st.warning("Veuillez entrer une question.")
    else:
        # Détecter le type de problème
        type_probleme = detecter_type_probleme(question)
        
        # Afficher le type détecté
        if type_probleme == "inverseur":
            st.info("🔍 Type détecté : **Inverseur Bipolaire**")
        elif type_probleme == "transistor":
            st.info("🔍 Type détecté : **Transistor Bipolaire**")
        elif type_probleme == "diviseur":
            st.info("🔍 Type détecté : **Diviseur de Tension**")
        else:
            st.info("🔍 Type détecté : **Problème Général**")
        
        # Obtenir la réponse
        reponse = expliquer_probleme(question)
        st.write("### Réponse de l'IA :")
        st.write(reponse)
        
        # Si c'est un inverseur, proposer de tracer la courbe
        if type_probleme == "inverseur":
            st.write("---")
            st.write("### 📊 Tracé de la courbe VOUT = f(VIN)")
            
            with st.expander("🔧 Paramètres du circuit (cliquer pour ajuster)"):
                col1, col2 = st.columns(2)
                with col1:
                    vcc = st.number_input("VCC (V)", value=5.0, min_value=0.0, key="vcc")
                    rc = st.number_input("RC (Ω)", value=2000.0, min_value=0.0, key="rc")
                    rb = st.number_input("RB (Ω)", value=10000.0, min_value=0.0, key="rb")
                with col2:
                    beta = st.number_input("β (gain)", value=200.0, min_value=0.0, key="beta")
                    vbe = st.number_input("VBE (V)", value=0.7, min_value=0.0, key="vbe")
                    vce_sat = st.number_input("VCE_sat (V)", value=0.2, min_value=0.0, key="vce_sat")
            
            # Tracer automatiquement
            fig = tracer_inverseur(vcc, rc, rb, beta, vbe, vce_sat)
            st.pyplot(fig)