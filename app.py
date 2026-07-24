import streamlit as st

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="VocabLearn", layout="wide")

# 2. INJECTION CSS POUR LA BARRE DE NAVIGATION
st.markdown("""
    <style>
    /* Style du bandeau de navigation */
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 20px;
        background-color: #f8f9fa;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 30px;
    }
    .logo {
        font-size: 24px;
        font-weight: bold;
        color: #005088;
        font-family: 'Arial', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CRÉATION DE LA BARRE HORIZONTALE (Simulée avec des colonnes)
# On utilise st.columns pour placer le titre à gauche et le bouton à droite
nav_col1, nav_col2 = st.columns([4, 1])

with nav_col1:
    st.markdown('<div class="logo">📘 VocabLearn</div>', unsafe_allow_html=True)

with nav_col2:
    if st.button("Se connecter", use_container_width=True):
        st.info("La fonction de connexion sera bientôt disponible !")

st.markdown("---") # Une ligne de séparation propre

# 4. CONTENU PRINCIPAL DU SITE
st.title("Prêt pour ta révision ?")
st.write("Choisis une catégorie pour commencer à apprendre.")

# Organisation en "tuiles" (cards)
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.subheader("🇬🇧 Anglais")
        st.write("150 mots à réviser")
        st.button("Démarrer", key="en")

with col2:
    with st.container(border=True):
        st.subheader("🇪🇸 Espagnol")
        st.write("85 mots à réviser")
        st.button("Démarrer", key="es")

with col3:
    with st.container(border=True):
        st.subheader("🇩🇪 Allemand")
        st.write("42 mots à réviser")
        st.button("Démarrer", key="de")