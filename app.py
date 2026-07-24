import sqlite3
import bcrypt
import random
import smtplib
from email.mime.text import MIMEText
import streamlit as st

# Config de la page
st.set_page_config(page_title="Mon App", layout="wide")

# --- CONFIGURATION EMAIL (À remplir avec tes identifiants) ---
EMAIL_EXPEDITEUR = "ton.email@gmail.com"
MOT_DE_PASSE_APP = "xxxx xxxx xxxx xxxx"  # Mot de passe d'application Gmail

def envoyer_code_email(email_destinataire, code):
    """Envoie le code de confirmation par e-mail via Gmail"""
    sujet = "Ton code de vérification"
    contenu = f"Bonjour,\n\nVoici ton code de vérification : {code}\n\nÀ bientôt !"
    
    msg = MIMEText(contenu)
    msg['Subject'] = sujet
    msg['From'] = EMAIL_EXPEDITEUR
    msg['To'] = email_destinataire

    try:
        # Connexion au serveur SMTP de Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_APP)
            server.sendmail(EMAIL_EXPEDITEUR, email_destinataire, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erreur d'envoi de l'e-mail : {e}")
        return False

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            code_verification TEXT,
            est_verifie INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def pre_inscrire_utilisateur(email, username, password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    code = str(random.randint(100000, 999999)) # Code à 6 chiffres

    try:
        conn = sqlite3.connect("utilisateurs.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO users (email, username, password, code_verification, est_verifie) 
            VALUES (?, ?, ?, ?, 0)
        """, (email, username, hashed_password, code))
        conn.commit()
        conn.close()
        return code
    except sqlite3.IntegrityError:
        return None

def valider_code(email, code_saisi):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT code_verification FROM users WHERE email = ?", (email,))
    res = c.fetchone()
    
    if res and res[0] == code_saisi:
        c.execute("UPDATE users SET est_verifie = 1, code_verification = NULL WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def verifier_connexion(email, password):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT username, password, est_verifie FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if user:
        username, db_password, est_verifie = user
        if not est_verifie:
            return "NON_VERIFIE"
        if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
            return username
    return None

init_db()

# --- SESSIONS ---
if "user_connecte" not in st.session_state:
    st.session_state.user_connecte = None
if "vue_authentification" not in st.session_state:
    st.session_state.vue_authentification = None
if "email_en_cours_verification" not in st.session_state:
    st.session_state.email_en_cours_verification = None

# --- NAV BAR ---
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

# --- FORMULAIRES ---

# 1. Écran de validation du code
if st.session_state.vue_authentification == "verification":
    _, col_centre, _ = st.columns([1, 2, 1])
    with col_centre:
        st.subheader("📩 Vérification de ton e-mail")
        st.write(f"Un code à 6 chiffres a été envoyé à **{st.session_state.email_en_cours_verification}**.")
        
        with st.form("form_code"):
            code_saisi = st.text_input("Code de confirmation", max_chars=6)
            valider_code_btn = st.form_submit_button("Valider mon compte", type="primary")
            
            if valider_code_btn:
                if valider_code(st.session_state.email_en_cours_verification, code_saisi.strip()):
                    st.success("Compte validé avec succès ! Tu peux maintenant te connecter.")
                    st.session_state.vue_authentification = "connexion"
                    st.rerun()
                else:
                    st.error("Code incorrect, réessaie.")

# 2. Formulaire d'inscription
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
                    st.warning("Remplis tous les champs.")
                elif mot_de_passe != mot_de_passe_conf:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    code = pre_inscrire_utilisateur(email, nom, mot_de_passe)
                    if code:
                        # Envoi de l'e-mail
                        if envoyer_code_email(email, code):
                            st.session_state.email_en_cours_verification = email
                            st.session_state.vue_authentification = "verification"
                            st.rerun()
                    else:
                        st.error("Cet e-mail est déjà utilisé.")

# 3. Formulaire de connexion
elif st.session_state.vue_authentification == "connexion":
    _, col_centre, _ = st.columns([1, 2, 1])
    with col_centre:
        with st.form("form_connexion"):
            st.subheader("🔑 Connexion")
            email = st.text_input("Adresse e-mail")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            valider = st.form_submit_button("Se connecter", type="primary")

            if valider:
                res = verifier_connexion(email, mot_de_passe)
                if res == "NON_VERIFIE":
                    st.warning("Ton e-mail n'a pas encore été vérifié !")
                    st.session_state.email_en_cours_verification = email
                    st.session_state.vue_authentification = "verification"
                    st.rerun()
                elif res:
                    st.session_state.user_connecte = res
                    st.session_state.vue_authentification = None
                    st.rerun()
                else:
                    st.error("E-mail ou mot de passe incorrect.")

else:
    if st.session_state.user_connecte:
        st.title(f"Bienvenue, {st.session_state.user_connecte} ! 👋")
    else:
        st.title("Bienvenue sur le site !")