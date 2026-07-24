import streamlit as st

# Configuration de la page en mode large
st.set_page_config(page_title="Mon App", layout="wide")

# Création de la barre de navigation avec des colonnes
# [6, 1, 1] signifie : 60% pour le titre, 20% par bouton
col_title, col_login, col_signup = st.columns([6, 1, 1])

with col_title:
    st.markdown("### 📘 Mon Application")

with col_login:
    if st.button("Se connecter", use_container_width=True):
        st.toast("Formulaire de connexion")

with col_signup:
    if st.button("S'inscrire", type="primary", use_container_width=True):
        st.toast("Formulaire d'inscription")

# Ligne de séparation sous la barre de navigation
st.divider()

# Reste de ta page vide pour l'instant
st.write("Bienvenue sur le site !")