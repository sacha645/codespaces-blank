import sqlite3
import bcrypt
import random
import smtplib
from email.mime.text import MIMEText
import streamlit as st

st.set_page_config(page_title="Mon App", layout="wide")

# --- CONFIGURATION EMAIL ---
EMAIL_EXPEDITEUR = "sachapollpay@gmail.com"
MOT_DE_PASSE_APP = "vjlf efer eagd lsvq"

def envoyer_code_email(email_destinataire, code):
    msg = MIMEText(f"Bonjour,\n\nVoici ton code de vérification : {code}")
    msg['Subject'] = "Ton code de vérification"
    msg['From'] = EMAIL_EXPEDITEUR
    msg['To'] = email_destinataire
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_APP)
            server.sendmail(EMAIL_EXPEDITEUR, email_destinataire, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erreur d'envoi d'e-mail : {e}")
        return False

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    # ⚠️ AJOUTE CETTE LIGNE POUR REMETTRE À ZÉRO :
    c.execute("DROP TABLE IF EXISTS users")
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
    code = str(random.randint(100000, 999999))
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
            return "NON_VERIFIE", None
        if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
            return "OK", username
    return "ERREUR", None

init_db()

# --- INITIALISATION UNIQUE DU STATE ---
if "etat" not in st.session_state:
    st.session_state.etat = "none"  # État par défaut

if "user" not in st.session_state:
    st.session_state.user = None

if "email_verif" not in st.session_state:
    st.session_state.email_verif = None

# --- BARRE DE NAVIGATION ---
col_title, col_login, col_signup = st.columns([6, 1, 1])

with col_title:
    st.markdown("### 📘 Mon Application")

# Boutons conditionnels selon l'état
if st.session_state.etat == "connecte":
    with col_signup:
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.etat = "none"
            st.session_state.user = None
            st.rerun()
else:
    with col_login:
        if st.button("Se connecter", use_container_width=True):
            st.session_state.etat = "connect"
            st.rerun()
    with col_signup:
        if st.button("S'inscrire", type="primary", use_container_width=True):
            st.session_state.etat = "nouveau"
            st.rerun()

st.divider()

# --- AFFICHAGE SELON L'ÉTAT (MACHINE À ÉTATS) ---

# 1. ÉTAT : NONE (Accueil public)
if st.session_state.etat == "none":
    st.title("Bienvenue sur le site !")
    st.write("Clique sur un bouton en haut à droite pour te connecter ou créer un compte.")

# 2. ÉTAT : NOUVEAU (Inscription)
elif st.session_state.etat == "nouveau":
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
                    if code and envoyer_code_email(email, code):
                        st.session_state.email_verif = email
                        st.session_state.etat = "verif"  # Passage à l'état de vérification
                        st.rerun()
                    elif not code:
                        st.error("Cet e-mail est déjà utilisé.")

# 3. ÉTAT : VERIF (Saisie du code e-mail)
elif st.session_state.etat == "verif":
    _, col_centre, _ = st.columns([1, 2, 1])
    with col_centre:
        st.subheader("📩 Vérification de ton e-mail")
        st.write(f"Un code à 6 chiffres a été envoyé à **{st.session_state.email_verif}**.")
        with st.form("form_code"):
            code_saisi = st.text_input("Code de confirmation", max_chars=6)
            valider_code_btn = st.form_submit_button("Valider mon compte", type="primary")
            
            if valider_code_btn:
                if valider_code(st.session_state.email_verif, code_saisi.strip()):
                    st.success("Compte validé ! Connecte-toi maintenant.")
                    st.session_state.etat = "connect"  # Passage à l'état de connexion
                    st.rerun()
                else:
                    st.error("Code incorrect.")

# 4. ÉTAT : CONNECT (Formulaire de connexion)
elif st.session_state.etat == "connect":
    _, col_centre, _ = st.columns([1, 2, 1])
    with col_centre:
        with st.form("form_connexion"):
            st.subheader("🔑 Connexion")
            email = st.text_input("Adresse e-mail")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            valider = st.form_submit_button("Se connecter", type="primary")

            if valider:
                statut, username = verifier_connexion(email, mot_de_passe)
                if statut == "NON_VERIFIE":
                    st.warning("E-mail non vérifié. Saisis le code envoyé.")
                    st.session_state.email_verif = email
                    st.session_state.etat = "verif"
                    st.rerun()
                elif statut == "OK":
                    st.session_state.user = username
                    st.session_state.etat = "connecte"  # Passage à l'état connecté !
                    st.rerun()
                else:
                    st.error("E-mail ou mot de passe incorrect.")

# 5. ÉTAT : CONNECTE (Espace utilisateur connecté)
elif st.session_state.etat == "connecte":
    st.title(f"Bienvenue, {st.session_state.user} ! 👋")
    st.write("Tu es connecté à ton espace membre.")