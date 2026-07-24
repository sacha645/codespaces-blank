import streamlit as st

# 1. Configuration de la page
st.set_page_config(page_title="Mon App", layout="wide")

# 2. Gestion de l'état (Savoir si l'utilisateur veut se connecter ou s'inscrire)
if "vue_authentification" not in st.session_state:
    st.session_state.vue_authentification = None  # Valeurs possibles : None, 'connexion', 'inscription'

# 3. Barre de navigation
col_title, col_login, col_signup = st.columns([6, 1, 1])

with col_title:
    st.markdown("### 📘 Mon Application")

with col_login:
    if st.button("Se connecter", use_container_width=True):
        st.session_state.vue_authentification = "connexion"

with col_signup:
    if st.button("S'inscrire", type="primary", use_container_width=True):
        st.session_state.vue_authentification = "inscription"

st.divider()

# 4. Affichage des formulaires selon le bouton cliqué
if st.session_state.vue_authentification == "connexion":
    # On centre le formulaire grâce à des colonnes
    _, col_centre, _ = st.columns([1, 2, 1])
    
    with col_centre:
        with st.form("form_connexion"):
            st.subheader("🔑 Connexion")
            email = st.text_input("Adresse e-mail")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            valider = st.form_submit_button("Se connecter", type="primary")
            
            if valider:
                # Logique de vérification à venir
                st.success(f"Bienvenue ! Tentative de connexion pour {email}")

elif st.session_state.vue_authentification == "inscription":
    _, col_centre, _ = st.columns([1, 2, 1])
    
    with col_centre:
        with st.form("form_inscription"):
            st.subheader("📝 Créer un compte")
            nom = st.text_input("Nom d'utilisateur")
            email = st.text_input("Adresse e-mail")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            mot_de_passe_conf = st.text_input("Confirmer le mot de passe", type="password")
            valider = st.form_submit_button("S'inscrire", type="primary")
            
            if valider:
                if mot_de_passe != mot_de_passe_conf:
                    st.error("Les mots de passe ne correspondent pas !")
                else:
                    # Logique de sauvegarde à venir
                    st.success("Compte créé avec succès ! Tu peux maintenant te connecter.")

else:
    # Contenu par défaut si aucun bouton n'est cliqué
    st.title("Bienvenue sur le site !")
    st.write("Clique sur un bouton en haut à droite pour commencer.")