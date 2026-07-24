import sqlite3
import bcrypt
import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Mon App", layout="wide")

# --- GESTION DE LA BASE DE DONNÉES (SQLite) ---
def init_db():
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    # Création de la table si elle n'existe pas
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def ajouter_utilisateur(email, username, password):
    # Hachage du mot de passe pour la sécurité
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    try:
        conn = sqlite3.connect("utilisateurs.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
                  (email, username, hashed_password.decode('utf-8')))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Email déjà utilisé

def verifier_utilisateur(email, password):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT username, password FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if user:
        db_username, db_password = user
        # Vérification du mot de passe
        if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
            return db_username
    return None

# Initialisation de la base de données
init_db()

# --- INITIALISATION DE LA SESSION ---
if "user_connecte" not in st.session_state:
    st.session_state.user_connecte = None
if "vue_authentification" not in st.session_state:
    st.session_state.vue_authentification = None

# --- BARRE DE NAVIGATION ---
col_title, col_login, col_signup = st.columns([6, 1, 1])

with col_title:
    st.markdown("### 📘 Mon Application")

if st.session_state.user_connecte:
    with col_signup:
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.user_connecte = None
            st.session_state.vue_authentification = None
            st.rerun()
else:
    with col_login:
        if st.button("Se connecter", use_container_width=True):
            st.session_state.vue_authentification = "connexion"

    with col_signup:
        if st.button("S'inscrire", type="primary", use_container_width=True):
            st.session_state.vue_authentification = "inscription"

st.divider()

# --- AFFICHAGE SELON L'ÉTAT DE CONNEXION ---

# 1. Si l'utilisateur est connecté
if st.session_state.user_connecte:
    st.title(f"Bienvenue, {st.session_state.user_connecte} ! 👋")
    st.write("Tu es maintenant connecté à ton espace personnel.")

# 2. Formulaire de Connexion
elif st.session_state.vue_authentification == "connexion":
    _, col_centre, _ = st.columns([1, 2, 1])
    with col_centre:
        with st.form("form_connexion"):
            st.subheader("🔑 Connexion")
            email = st.text_input("Adresse e-mail")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            valider = st.form_submit_button("Se connecter", type="primary")

            if valider:
                username = verifier_utilisateur(email, mot_de_passe)
                if username:
                    st.session_state.user_connecte = username
                    st.session_state.vue_authentification = None
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.error("E-mail ou mot de passe incorrect.")

# 3. Formulaire d'Inscription
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
                if not nom or not email or not mot_de_passe:
                    st.warning("Merci de remplir tous les champs.")
                elif mot_de_passe != mot_de_passe_conf:
                    st.error("Les mots de passe ne correspondent pas !")
                else:
                    succes = ajouter_utilisateur(email, nom, mot_de_passe)
                    if succes:
                        st.success("Compte créé avec succès ! Tu peux maintenant te connecter.")
                        st.session_state.vue_authentification = "connexion"
                    else:
                        st.error("Un compte existe déjà avec cet e-mail.")

# 4. Page d'accueil par défaut
else:
    st.title("Bienvenue sur le site !")
    st.write("Clique sur un bouton en haut à droite pour te connecter ou créer un compte.")