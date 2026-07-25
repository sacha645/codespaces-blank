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
    
    # 1. Table Utilisateurs
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
    
    # 2. Table Listes
    c.execute('''
        CREATE TABLE IF NOT EXISTS listes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nom_liste TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # 3. Table Mots
    c.execute('''
        CREATE TABLE IF NOT EXISTS mots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            liste_id INTEGER NOT NULL,
            mot_original TEXT NOT NULL,
            traduction TEXT NOT NULL,
            FOREIGN KEY (liste_id) REFERENCES listes (id) ON DELETE CASCADE
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


# --- FONCTIONS BDD REQUISES ( À placer au-dessus de l'État 5 ) ---
def recuperer_listes_utilisateur(user_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT id, nom_liste FROM listes WHERE user_id = ?", (user_id,))
    listes = c.fetchall()
    conn.close()
    return listes

def ajouter_liste(user_id, nom_liste):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("INSERT INTO listes (user_id, nom_liste) VALUES (?, ?)", (user_id, nom_liste))
    conn.commit()
    conn.close()

def verifier_et_ajouter_ligne():
    """Vérifie si la dernière ligne affichée est remplie pour ajouter la suivante"""
    dernier_index = st.session_state.nb_lignes_mots - 1
    mot = st.session_state.get(f"mot_{dernier_index}", "").strip()
    trad = st.session_state.get(f"trad_{dernier_index}", "").strip()
    
    # Si le mot et la traduction de la dernière ligne ne sont pas vides
    if mot and trad:
        st.session_state.nb_lignes_mots += 1

def ajouter_mot(liste_id, article, mot_original, traduction):
    # Si un article est renseigné, on combine l'article et le mot
    if article.strip():
        mot_complet = f"{article.strip()} {mot_original.strip()}"
    else:
        mot_complet = mot_original.strip()

    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO mots (liste_id, mot_original, traduction) VALUES (?, ?, ?)",
        (liste_id, mot_complet, traduction.strip())
    )
    conn.commit()
    conn.close()

def recuperer_mots_liste(liste_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT mot_original, traduction FROM mots WHERE liste_id = ?", (liste_id,))
    mots = c.fetchall()
    conn.close()
    return mots

def supprimer_liste(liste_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    # Active la suppression en cascade des mots liés à cette liste
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("DELETE FROM listes WHERE id = ?", (liste_id,))
    conn.commit()
    conn.close()

def renommer_liste(liste_id, nouveau_nom):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("UPDATE listes SET nom_liste = ? WHERE id = ?", (nouveau_nom, liste_id))
    conn.commit()
    conn.close()

def remplacer_mots_liste(liste_id, nouveaux_mots):
    """Efface les anciens mots de la liste et insère les nouveaux"""
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("DELETE FROM mots WHERE liste_id = ?", (liste_id,))
    for art, mot, trad in nouveaux_mots:
        if mot.strip() and trad.strip():
            mot_complet = f"{art.strip()} {mot.strip()}" if art.strip() else mot.strip()
            c.execute("INSERT INTO mots (liste_id, mot_original, traduction) VALUES (?, ?, ?)",
                      (liste_id, mot_complet, trad.strip()))
    conn.commit()
    conn.close()


# --- Apparence ---
def ligne_epaisse():
    st.markdown(
        """
        <hr style="border: none; height: 3px; background-color: #4A4A4A; margin: 20px 0;">
        """,
        unsafe_allow_html=True
    )

            
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

ligne_epaisse()


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


# --- 5. ÉTAT : CONNECTE (Espace utilisateur) ---
elif st.session_state.etat == "connecte":
    username, user_id = st.session_state.user

    # Initialisation des sous-états
    if "action_liste" not in st.session_state:
        st.session_state.action_liste = "liste"  # "liste", "creer", "voir", "supprimer", "editer", "entrainer"
    if "liste_active_id" not in st.session_state:
        st.session_state.liste_active_id = None
    if "nb_lignes_mots" not in st.session_state:
        st.session_state.nb_lignes_mots = 2

    _, col_centre, _ = st.columns([1, 3, 1])

    with col_centre:
        
        # ----------------------------------------------------
        # CAS A : VUE FORMULAIRE DE CRÉATION DE LISTE
        # ----------------------------------------------------
        if st.session_state.action_liste == "creer":
            st.subheader("✨ Créer une nouvelle liste")
            
            nom_liste = st.text_input("Nom de la liste", placeholder="Nom de la liste")
            st.divider()

            mots_saisis = []
            toutes_lignes_visibles_remplies = True

            c_h1, c_h2, c_h3 = st.columns([1, 2, 2])
            with c_h1:
                st.caption("Article *(ex: le, un)*")
            with c_h2:
                st.caption("Mot / Nom")
            with c_h3:
                st.caption("Traduction")

            for i in range(st.session_state.nb_lignes_mots):
                col_art, col_mot, col_trad = st.columns([1, 2, 2])
                
                with col_art:
                    art = st.text_input(f"Art {i+1}", key=f"art_{i}", placeholder="le / un", label_visibility="collapsed")
                with col_mot:
                    mot = st.text_input(f"Mot {i+1}", key=f"mot_{i}", placeholder=f"Mot {i+1}", label_visibility="collapsed")
                with col_trad:
                    trad = st.text_input(f"Trad {i+1}", key=f"trad_{i}", placeholder=f"Traduction {i+1}", label_visibility="collapsed")
                
                mots_saisis.append((art, mot, trad))

                if len(mot.strip()) < 1 or len(trad.strip()) < 1:
                    toutes_lignes_visibles_remplies = False

            if toutes_lignes_visibles_remplies:
                st.session_state.nb_lignes_mots += 1
                st.rerun()

            st.write("")
            col_annuler, col_sauvegarder = st.columns(2)

            with col_annuler:
                if st.button("❌ Annuler", use_container_width=True):
                    st.session_state.action_liste = "liste"
                    st.session_state.nb_lignes_mots = 2
                    st.rerun()

            with col_sauvegarder:
                if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
                    if not nom_liste.strip():
                        st.warning("Veuillez donner un nom à la liste.")
                    else:
                        ajouter_liste(user_id, nom_liste.strip())
                        
                        listes_user = recuperer_listes_utilisateur(user_id)
                        derniere_liste_id = listes_user[-1][0]

                        nb_mots_ajoutes = 0
                        for a, m, t in mots_saisis:
                            if m.strip() and t.strip():
                                ajouter_mot(derniere_liste_id, a, m, t)
                                nb_mots_ajoutes += 1

                        st.toast(f"Liste '{nom_liste}' enregistrée !", icon="✅")
                        st.session_state.action_liste = "liste"
                        st.session_state.nb_lignes_mots = 2
                        st.rerun()

        # ----------------------------------------------------
        # CAS B : VUE ÉDITER UNE LISTE (✏️)
        # ----------------------------------------------------
        elif st.session_state.action_liste == "editer":
            liste_id = st.session_state.liste_active_id
            
            listes_user = recuperer_listes_utilisateur(user_id)
            nom_actuel = next((nom for lid, nom in listes_user if lid == liste_id), "")

            st.subheader("✏️ Éditer la liste")
            
            nouveau_nom = st.text_input("Nom de la liste", value=nom_actuel)
            st.divider()

            mots_existants = recuperer_mots_liste(liste_id)
            
            nb_lignes = max(len(mots_existants) + 1, st.session_state.nb_lignes_mots)

            mots_modifies = []
            toutes_lignes_visibles_remplies = True
            
            c_h1, c_h2, c_h3 = st.columns([1, 2, 2])
            with c_h1:
                st.caption("Article")
            with c_h2:
                st.caption("Mot / Nom")
            with c_h3:
                st.caption("Traduction")

            for i in range(nb_lignes):
                art_val, mot_val, trad_val = "", "", ""
                if i < len(mots_existants):
                    mot_or, trad_val = mots_existants[i]
                    parts = mot_or.split(" ", 1)
                    if len(parts) == 2 and parts[0].lower() in ["le", "la", "les", "un", "une", "des", "l'", "the", "a", "an", "el", "los", "las", "der", "die", "das"]:
                        art_val, mot_val = parts[0], parts[1]
                    else:
                        mot_val = mot_or

                col_art, col_mot, col_trad = st.columns([1, 2, 2])
                with col_art:
                    art = st.text_input(f"Art {i+1}", value=art_val, key=f"edit_art_{i}", label_visibility="collapsed")
                with col_mot:
                    mot = st.text_input(f"Mot {i+1}", value=mot_val, key=f"edit_mot_{i}", label_visibility="collapsed")
                with col_trad:
                    trad = st.text_input(f"Trad {i+1}", key=f"edit_trad_{i}", value=trad_val, label_visibility="collapsed")

                mots_modifies.append((art, mot, trad))

                if len(mot.strip()) < 1 or len(trad.strip()) < 1:
                    toutes_lignes_visibles_remplies = False

            if toutes_lignes_visibles_remplies:
                st.session_state.nb_lignes_mots = nb_lignes + 1
                st.rerun()

            st.write("")
            col_annuler, col_sauvegarder = st.columns(2)

            with col_annuler:
                if st.button("❌ Annuler", use_container_width=True):
                    st.session_state.action_liste = "liste"
                    st.session_state.liste_active_id = None
                    st.session_state.nb_lignes_mots = 2
                    st.rerun()

            with col_sauvegarder:
                if st.button("💾 Enregistrer les modifications", type="primary", use_container_width=True):
                    if not nouveau_nom.strip():
                        st.warning("Le nom de la liste ne peut pas être vide.")
                    else:
                        renommer_liste(liste_id, nouveau_nom.strip())
                        remplacer_mots_liste(liste_id, mots_modifies)
                        
                        st.toast("Modifications enregistrées !", icon="✅")
                        st.session_state.action_liste = "liste"
                        st.session_state.liste_active_id = None
                        st.session_state.nb_lignes_mots = 2
                        st.rerun()

        # ----------------------------------------------------
        # CAS C : VUE VOIR UNE LISTE (👁️)
        # ----------------------------------------------------
        elif st.session_state.action_liste == "voir":
            liste_id = st.session_state.liste_active_id
            
            listes_user = recuperer_listes_utilisateur(user_id)
            nom_actuel = next((nom for lid, nom in listes_user if lid == liste_id), "Liste")

            st.subheader(f"📖 {nom_actuel}")
            ligne_epaisse()

            mots = recuperer_mots_liste(liste_id)

            if not mots:
                st.info("Cette liste ne contient aucun mot.")
            else:
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    st.markdown("**Mot / Expression**")
                with c_m2:
                    st.markdown("**Traduction**")
                st.divider()

                for mot_or, trad in mots:
                    cm1, cm2 = st.columns(2)
                    cm1.write(mot_or)
                    cm2.write(trad)

            st.divider()
            if st.button("🔙 Retour", use_container_width=True):
                st.session_state.action_liste = "liste"
                st.session_state.liste_active_id = None
                st.rerun()

        # ----------------------------------------------------
        # CAS D : CONFIRMATION DE SUPPRESSION (🗑️)
        # ----------------------------------------------------
        elif st.session_state.action_liste == "supprimer":
            liste_id = st.session_state.liste_active_id
            
            listes_user = recuperer_listes_utilisateur(user_id)
            nom_actuel = next((nom for lid, nom in listes_user if lid == liste_id), "cette liste")

            st.warning(f"⚠️ Es-tu sûr de vouloir supprimer la liste **'{nom_actuel}'** ? Cette action est irréversible.")
            
            col_non, col_oui = st.columns(2)
            
            with col_non:
                if st.button("❌ Annuler", use_container_width=True):
                    st.session_state.action_liste = "liste"
                    st.session_state.liste_active_id = None
                    st.rerun()

            with col_oui:
                if st.button("🗑️ Oui, supprimer", type="primary", use_container_width=True):
                    supprimer_liste(liste_id)
                    st.toast(f"La liste '{nom_actuel}' a été supprimée.", icon="🗑️")
                    st.session_state.action_liste = "liste"
                    st.session_state.liste_active_id = None
                    st.rerun()

        # ----------------------------------------------------
        # CAS E : VUE NORMALE (AFFICHAGE DES LISTES)
        # ----------------------------------------------------
        else:
            col_titre, col_ajout = st.columns([4, 1])
            with col_titre:
                st.subheader("📋 Mes listes")
            with col_ajout:
                if st.button("➕", use_container_width=True, help="Créer une nouvelle liste"):
                    st.session_state.action_liste = "creer"
                    st.session_state.nb_lignes_mots = 2
                    st.rerun()

            st.write("")
            ligne_epaisse()

            listes = recuperer_listes_utilisateur(user_id)

            if not listes:
                st.info("Tu n'as aucune liste pour l me/instants. Clique sur ➕ pour en créer une !")
            else:
                for liste_id, nom_liste in listes:
                    col_nom, col_voir, col_edit, col_train, col_del = st.columns([4, 1, 1, 1, 1])
                    
                    with col_nom:
                        st.markdown(f"### 📄 {nom_liste}")

                    # NOUVEAU BOUTON : S'ENTRAÎNER (🎯)
                    with col_train:
                        if st.button("🎯", key=f"train_{liste_id}", help="S'entraîner sur cette liste"):
                            st.session_state.action_liste = "entrainer"
                            st.session_state.liste_active_id = liste_id
                            st.rerun()

                    with col_voir:
                        if st.button("👁️", key=f"voir_{liste_id}", help="Voir la liste"):
                            st.session_state.action_liste = "voir"
                            st.session_state.liste_active_id = liste_id
                            st.rerun()

                    with col_edit:
                        if st.button("✏️", key=f"edit_{liste_id}", help="Éditer la liste"):
                            st.session_state.action_liste = "editer"
                            st.session_state.liste_active_id = liste_id
                            st.session_state.nb_lignes_mots = 2
                            st.rerun()

                    with col_del:
                        if st.button("🗑️", key=f"del_{liste_id}", help="Supprimer la liste"):
                            st.session_state.action_liste = "supprimer"
                            st.session_state.liste_active_id = liste_id
                            st.rerun()

                    st.divider()