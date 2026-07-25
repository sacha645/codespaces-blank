import sqlite3
import bcrypt
import random
import smtplib
from email.mime.text import MIMEText
import streamlit as st

st.set_page_config(page_title="Réviseur", layout="wide")


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

def renvoyer_code(email):
    nouveau_code = str(random.randint(100000, 999999))
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("UPDATE users SET code_verification = ? WHERE email = ?", (nouveau_code, email))
    conn.commit()
    conn.close()
    return nouveau_code

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
    c.execute("SELECT id, username, password, est_verifie FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if user:
        user_id, username, db_password, est_verifie = user
        if not est_verifie:
            return "NON_VERIFIE", None, None
        if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
            return "OK", username, user_id
    return "ERREUR", None, None

def supprimer_compte(user_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

init_db()


# --- INITIALISATION UNIQUE DU STATE ---
if "etat" not in st.session_state:
    st.session_state.etat = "none"  # État par défaut

if "user" not in st.session_state:
    st.session_state.user = None

if "email_verif" not in st.session_state:
    st.session_state.email_verif = None


# --- BARRE DE NAVIGATION ---
# On ajuste le ratio des colonnes : 5 pour le titre, 2 pour la suppression, 1 pour la déconnexion
col_title, col_action, col_signup = st.columns([6, 1, 1])

with col_title:
    st.markdown("### 📘 Reviseur")

# Si l'utilisateur est connecté
if st.session_state.etat == "connecte":
    
    # Bouton Supprimer mon compte
    with col_action:
        if st.button("🗑️ Supprimer mon compte", type="secondary", use_container_width=True):
            user_id = st.session_state.user[1]
            supprimer_compte(user_id)
            st.session_state.user = None
            st.session_state.etat = "none"
            st.toast("Ton compte a été supprimé avec succès.", icon="⚠️")
            st.rerun()

    # Bouton Déconnexion
    with col_signup:
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.user = None
            st.session_state.etat = "none"
            st.rerun()

# Si l'utilisateur N'EST PAS connecté
else:
    with col_action:
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

        # --- BOUTON DE RENVOI DU CODE (En dehors du formulaire principal) ---
        if st.button("🔄 Renvoyer un nouveau code", use_container_width=True):
            nouveau_code = renvoyer_code(st.session_state.email_verif)
            if envoyer_code_email(st.session_state.email_verif, nouveau_code):
                st.toast("Un nouveau code vient d'être envoyé !", icon="📩")

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
                statut, username, user_id = verifier_connexion(email, mot_de_passe)
                if statut == "NON_VERIFIE":
                    st.warning("E-mail non vérifié. Saisis le code envoyé.")
                    st.session_state.email_verif = email
                    st.session_state.etat = "verif"
                    st.rerun()
                elif statut == "OK":
                    st.session_state.user = (username, user_id)
                    st.session_state.etat = "connecte"
                    st.rerun()
                else:
                    st.error("E-mail ou mot de passe incorrect.")

# 5. ÉTAT : CONNECTE (Espace utilisateur)
elif st.session_state.etat == "connecte":
    username, user_id = st.session_state.user

    # Initialisation de la sous-navigation si elle n'existe pas
    if "menu_connecte" not in st.session_state:
        st.session_state.menu_connecte = "gerer"  # Vue par défaut

    # --- LES 2 BOUTONS PRINCIPAUX DE L'ACCUEIL CONNECTÉ ---
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📚 Gérer mes listes", type="primary" if st.session_state.menu_connecte == "gerer" else "secondary", use_container_width=True):
            st.session_state.menu_connecte = "gerer"
            st.rerun()

    with col_btn2:
        if st.button("🎯 Choisir une liste", type="primary" if st.session_state.menu_connecte == "choisir" else "secondary", use_container_width=True):
            st.session_state.menu_connecte = "choisir"
            st.rerun()

    st.divider()

    # --- 1. BOUTON : GÉRER MES LISTES ---
    if st.session_state.menu_connecte == "gerer":
        
        # Centrage de la section au milieu de la page
        _, col_centre, _ = st.columns([1, 3, 1])

        with col_centre:
            # En-tête : Titre à gauche, Bouton "+" à droite
            col_titre, col_ajout = st.columns([4, 1])
            with col_titre:
                st.subheader("📋 Mes listes")
            with col_ajout:
                # Bouton de création rapide avec icône +
                if st.button("➕", use_container_width=True, help="Créer une nouvelle liste"):
                    # On verra le comportement au clic plus tard
                    pass

            st.write("") # Petit espacement visuel

            # Récupération des listes de l'utilisateur
            listes = recuperer_listes_utilisateur(user_id)

            if not listes:
                st.info("Tu n'as aucune liste pour l'instant. Clique sur ➕ pour en créer une !")
            else:
                # Affichage vertical de chaque liste
                for liste_id, nom_liste in listes:
                    col_nom, col_voir, col_edit, col_del = st.columns([5, 1, 1, 1])
                    
                    # Nom de la liste à gauche
                    with col_nom:
                        st.markdown(f"### 📄 {nom_liste}")

                    # Bouton VOIR (👁️)
                    with col_voir:
                        if st.button("👁️", key=f"voir_{liste_id}", help="Voir la liste"):
                            pass

                    # Bouton ÉDITER (✏️)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{liste_id}", help="Éditer la liste"):
                            pass

                    # Bouton SUPPRIMER (🗑️)
                    with col_del:
                        if st.button("🗑️", key=f"del_{liste_id}", help="Supprimer la liste"):
                            pass

                    st.divider()

    # --- 2. BOUTON : CHOISIR UNE LISTE ---
    elif st.session_state.menu_connecte == "choisir":
        st.subheader("🎯 Choisir une liste pour réviser")
        st.write("*(On verra cette partie plus tard !)*")