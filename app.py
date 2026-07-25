import sqlite3
import bcrypt
import streamlit as st

st.set_page_config(page_title="Réviseur", layout="wide")
def reinitialiser_toutes_les_bdd():
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    # Supprime les 3 tables
    c.execute("DROP TABLE IF EXISTS mots")
    c.execute("DROP TABLE IF EXISTS listes")
    c.execute("DROP TABLE IF EXISTS users")
    conn.commit()
    conn.close()

# Décommente cette ligne, lance l'application une fois, puis recommente-la :
reinitialiser_toutes_les_bdd()
# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Ajout de 'type_liste' ('vocabulaire' ou 'verbe')
    c.execute('''
        CREATE TABLE IF NOT EXISTS listes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nom_liste TEXT NOT NULL,
            type_liste TEXT NOT NULL DEFAULT 'vocabulaire',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Ajout des colonnes pour les verbes : present, preterit, participe_passe
    c.execute('''
        CREATE TABLE IF NOT EXISTS mots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            liste_id INTEGER NOT NULL,
            mot_original TEXT NOT NULL,
            present TEXT,
            preterit TEXT,
            participe_passe TEXT,
            traduction TEXT NOT NULL,
            FOREIGN KEY (liste_id) REFERENCES listes (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def inscrire_utilisateur(username, password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    try:
        conn = sqlite3.connect("utilisateurs.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO users (username, password) 
            VALUES (?, ?)
        """, (username, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Nom d'utilisateur déjà pris

def verifier_connexion(username, password):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        user_id, db_username, db_password = user
        if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
            return "OK", db_username, user_id
    return "ERREUR", None, None

def supprimer_compte(user_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

init_db()


# --- FONCTIONS BDD LISTES ET MOTS ---
def recuperer_listes_utilisateur(user_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT id, nom_liste, type_liste FROM listes WHERE user_id = ?", (user_id,))
    listes = c.fetchall()
    conn.close()
    return listes

def ajouter_liste(user_id, nom_liste, type_liste="vocabulaire"):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("INSERT INTO listes (user_id, nom_liste, type_liste) VALUES (?, ?, ?)", 
              (user_id, nom_liste, type_liste))
    conn.commit()
    conn.close()

def ajouter_mot(liste_id, article, mot_original, traduction):
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
    c.execute("SELECT mot_original, present, preterit, participe_passe, traduction FROM mots WHERE liste_id = ?", (liste_id,))
    mots = c.fetchall()
    conn.close()
    return mots

def supprimer_liste(liste_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
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

def importer_liste_par_id(liste_id_origine, nouvel_user_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    c.execute("SELECT nom_liste FROM listes WHERE id = ?", (liste_id_origine,))
    res = c.fetchone()
    
    if not res:
        conn.close()
        return False, "Aucune liste trouvée avec cet ID."
    
    nom_liste_origine = res[0]
    nouveau_nom = f"{nom_liste_origine} (copie)"
    
    c.execute("INSERT INTO listes (user_id, nom_liste) VALUES (?, ?)", (nouvel_user_id, nouveau_nom))
    nouvelle_liste_id = c.lastrowid
    
    c.execute("SELECT mot_original, traduction FROM mots WHERE liste_id = ?", (liste_id_origine,))
    mots = c.fetchall()
    
    for mot_or, trad in mots:
        c.execute("INSERT INTO mots (liste_id, mot_original, traduction) VALUES (?, ?, ?)",
                  (nouvelle_liste_id, mot_or, trad))
        
    conn.commit()
    conn.close()
    return True, f"Liste '{nouveau_nom}' importée avec succès !"

def partager_liste_a_utilisateur(liste_id_origine, ami_user_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    # Vérifie que l'ami existe
    c.execute("SELECT id, username FROM users WHERE id = ?", (ami_user_id,))
    ami = c.fetchone()
    if not ami:
        conn.close()
        return False, "Aucun utilisateur trouvé avec cet ID."
    
    # Récupère la liste d'origine
    c.execute("SELECT nom_liste FROM listes WHERE id = ?", (liste_id_origine,))
    res = c.fetchone()
    if not res:
        conn.close()
        return False, "La liste d'origine n'existe plus."
    
    nom_liste = res[0]
    nouveau_nom = f"{nom_liste} (partagée)"
    
    # Crée la copie pour l'ami
    c.execute("INSERT INTO listes (user_id, nom_liste) VALUES (?, ?)", (ami_user_id, nouveau_nom))
    nouvelle_liste_id = c.lastrowid
    
    # Copie les mots
    c.execute("SELECT mot_original, traduction FROM mots WHERE liste_id = ?", (liste_id_origine,))
    mots = c.fetchall()
    
    for mot_or, trad in mots:
        c.execute("INSERT INTO mots (liste_id, mot_original, traduction) VALUES (?, ?, ?)",
                  (nouvelle_liste_id, mot_or, trad))
        
    conn.commit()
    conn.close()
    return True, f"Liste partagée avec succès à {ami[1]} !"

def importer_liste_depuis_fichier(user_id, nom_liste, type_liste, contenu_fichier):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    c.execute("INSERT INTO listes (user_id, nom_liste, type_liste) VALUES (?, ?, ?)", 
              (user_id, nom_liste, type_liste))
    nouvelle_liste_id = c.lastrowid
    
    nb_mots = 0
    lignes = contenu_fichier.splitlines()
    
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            continue
        
        parts = [p.strip() for p in ligne.split(",")]
        
        if type_liste == "vocabulaire" and len(parts) >= 2:
            c.execute("INSERT INTO mots (liste_id, mot_original, traduction) VALUES (?, ?, ?)",
                      (nouvelle_liste_id, parts[0], parts[1]))
            nb_mots += 1
            
        elif type_liste == "verbe" and len(parts) >= 5:
            # Infinitif, Présent, Prétérit, Participe Passé, Traduction
            c.execute("""
                INSERT INTO mots (liste_id, mot_original, present, preterit, participe_passe, traduction) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nouvelle_liste_id, parts[0], parts[1], parts[2], parts[3], parts[4]))
            nb_mots += 1

    conn.commit()
    conn.close()
    return nb_mots

        
# --- Apparence ---
def ligne_epaisse():
    st.markdown(
        """
        <hr style="border: none; height: 3px; background-color: #4A4A4A; margin: 20px 0;">
        """,
        unsafe_allow_html=True
    )

            
# --- INITIALISATION DU STATE ---
if "etat" not in st.session_state:
    st.session_state.etat = "none"

if "user" not in st.session_state:
    st.session_state.user = None


# --- BARRE DE NAVIGATION ---
col_title, col_action, col_signup = st.columns([6, 1, 1])

with col_title:
    st.markdown("### 📘 Reviseur")
    if st.session_state.etat == "connecte":
        # Affiche l'ID de l'utilisateur de manière discrète mais claire
        username, user_id = st.session_state.user
        st.caption(f"Connecté en tant que **{username}** (Ton ID : `{user_id}`)")

if st.session_state.etat == "connecte":
    with col_action:
        if st.button("🗑️ Supprimer mon compte", type="secondary", use_container_width=True):
            st.session_state.confirmer_suppr_compte = True
            st.rerun()

    with col_signup:
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.user = None
            st.session_state.etat = "none"
            st.rerun()

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


# --- AFFICHAGE SELON L'ÉTAT ---

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
            mot_de_passe = st.text_input("Mot de passe", type="password")
            mot_de_passe_conf = st.text_input("Confirmer le mot de passe", type="password")
            valider = st.form_submit_button("S'inscrire", type="primary")

            if valider:
                if not nom or not mot_de_passe:
                    st.warning("Remplis tous les champs.")
                elif mot_de_passe != mot_de_passe_conf:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    succes = inscrire_utilisateur(nom, mot_de_passe)
                    if succes:
                        st.success("Compte créé avec succès ! Connecte-toi maintenant.")
                        st.session_state.etat = "connect"
                        st.rerun()
                    else:
                        st.error("Ce nom d'utilisateur est déjà pris.")

# 3. ÉTAT : CONNECT (Formulaire de connexion)
elif st.session_state.etat == "connect":
    _, col_centre, _ = st.columns([1, 2, 1])
    with col_centre:
        with st.form("form_connexion"):
            st.subheader("🔑 Connexion")
            nom = st.text_input("Nom d'utilisateur")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            valider = st.form_submit_button("Se connecter", type="primary")

            if valider:
                statut, username, user_id = verifier_connexion(nom, mot_de_passe)
                if statut == "OK":
                    st.session_state.user = (username, user_id)
                    st.session_state.etat = "connecte"
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect.")


# --- 4. ÉTAT : CONNECTE (Espace utilisateur) ---
elif st.session_state.etat == "connecte":
    username, user_id = st.session_state.user

    if "action_liste" not in st.session_state:
        st.session_state.action_liste = "liste"
    if "liste_active_id" not in st.session_state:
        st.session_state.liste_active_id = None
    if "nb_lignes_mots" not in st.session_state:
        st.session_state.nb_lignes_mots = 2
    if "confirmer_suppr_compte" not in st.session_state:
        st.session_state.confirmer_suppr_compte = False

    _, col_centre, _ = st.columns([1, 3, 1])

    with col_centre:

        # ----------------------------------------------------
        # CONFIRMATION DE SUPPRESSION DE COMPTE
        # ----------------------------------------------------
        if st.session_state.confirmer_suppr_compte:
            st.error("⚠️ **ATTENTION :** Es-tu vraiment sûr de vouloir supprimer ton compte ? Toutes tes listes et tous tes mots seront définitivement perdus.")
            
            col_annuler_compte, col_confirmer_compte = st.columns(2)
            
            with col_annuler_compte:
                if st.button("❌ Annuler", use_container_width=True):
                    st.session_state.confirmer_suppr_compte = False
                    st.rerun()

            with col_confirmer_compte:
                if st.button("🗑️ Oui, supprimer mon compte", type="primary", use_container_width=True):
                    supprimer_compte(user_id)
                    st.session_state.user = None
                    st.session_state.etat = "none"
                    st.session_state.confirmer_suppr_compte = False
                    st.toast("Ton compte a été supprimé avec succès.", icon="⚠️")
                    st.rerun()
        
        # CAS A : VUE FORMULAIRE DE CRÉATION DE LISTE
        if st.session_state.action_liste == "creer":
            st.subheader("✨ Créer une nouvelle liste")
            
            nom_liste = st.text_input("Nom de la liste", placeholder="Nom de la liste")
            type_liste_choisi = st.radio(
                "Type de liste :", 
                ["Vocabulaire (Mot, Traduction)", "Verbes irréguliers (5 formes)"],
                horizontal=True
            )
            
            is_verbe = "Verbes" in type_liste_choisi
            type_code = "verbe" if is_verbe else "vocabulaire"
            
            st.divider()

            mots_saisis = []
            toutes_lignes_visibles_remplies = True

            # Entêtes dynamiques
            if is_verbe:
                cols_h = st.columns([2, 2, 2, 2, 2])
                headers = ["Infinitif", "Présent", "Prétérit", "Participe Passé", "Traduction"]
                for col, h in zip(cols_h, headers):
                    col.caption(h)
            else:
                cols_h = st.columns([1, 2, 2])
                headers = ["Article", "Mot / Nom", "Traduction"]
                for col, h in zip(cols_h, headers):
                    col.caption(h)

            for i in range(st.session_state.nb_lignes_mots):
                if is_verbe:
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
                    inf = c1.text_input(f"inf_{i}", key=f"inf_{i}", label_visibility="collapsed")
                    pres = c2.text_input(f"pres_{i}", key=f"pres_{i}", label_visibility="collapsed")
                    pret = c3.text_input(f"pret_{i}", key=f"pret_{i}", label_visibility="collapsed")
                    pp = c4.text_input(f"pp_{i}", key=f"pp_{i}", label_visibility="collapsed")
                    trad = c5.text_input(f"trad_{i}", key=f"vtrad_{i}", label_visibility="collapsed")
                    
                    mots_saisis.append((inf, pres, pret, pp, trad))
                    if not (inf.strip() and trad.strip()):
                        toutes_lignes_visibles_remplies = False
                else:
                    c1, c2, c3 = st.columns([1, 2, 2])
                    art = c1.text_input(f"art_{i}", key=f"art_{i}", label_visibility="collapsed")
                    mot = c2.text_input(f"mot_{i}", key=f"mot_{i}", label_visibility="collapsed")
                    trad = c3.text_input(f"trad_{i}", key=f"trad_{i}", label_visibility="collapsed")
                    
                    mot_complet = f"{art.strip()} {mot.strip()}".strip()
                    mots_saisis.append((mot_complet, "", "", "", trad))
                    if not (mot.strip() and trad.strip()):
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
                        ajouter_liste(user_id, nom_liste.strip(), type_code)
                        listes_user = recuperer_listes_utilisateur(user_id)
                        derniere_liste_id = listes_user[-1][0]

                        for item in mots_saisis:
                            inf_mot, pres, pret, pp, trad = item
                            if inf_mot.strip() and trad.strip():
                                ajouter_élément_liste(derniere_liste_id, inf_mot, pres, pret, pp, trad)

                        st.toast(f"Liste '{nom_liste}' enregistrée !", icon="✅")
                        st.session_state.action_liste = "liste"
                        st.session_state.nb_lignes_mots = 2
                        st.rerun()
        
        # CAS B : VUE ÉDITER UNE LISTE (✏️)
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

        # CAS C : VUE VOIR UNE LISTE (👁️)
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

        # CAS D : CONFIRMATION DE SUPPRESSION (🗑️)
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

        # CAS E : VUE PARTAGER UNE LISTE (🔗)
        elif st.session_state.action_liste == "partager":
            liste_id = st.session_state.liste_active_id
            st.subheader("🔗 Partager la liste")
            
            tab_id, tab_direct = st.tabs(["📋 Obtenir l'ID de la liste", "👤 Envoyer à un ami"])
            
            # --- OPTION 1 : Obtenir l'ID de la liste ---
            with tab_id:
                st.write("Donne cet **ID de liste** à ton ami(e) pour qu'il/elle puisse l'importer de son côté :")
                st.code(str(liste_id), language="text")
            
            # --- OPTION 2 : Envoyer directement via l'ID de l'utilisateur ---
            with tab_direct:
                st.write("Saisis l'**ID de ton ami(e)** pour lui envoyer une copie directement dans son compte :")
                id_ami = st.text_input("ID de l'utilisateur destinataire :", placeholder="Ex: 5")
                
                if st.button("📤 Envoyer la liste", type="primary", use_container_width=True):
                    if id_ami.isdigit():
                        succes, msg = partager_liste_a_utilisateur(liste_id, int(id_ami))
                        if succes:
                            st.toast(msg, icon="✅")
                            st.session_state.action_liste = "liste"
                            st.session_state.liste_active_id = None
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Veuillez entrer un ID d'utilisateur valide.")

            st.divider()
            if st.button("🔙 Retour", use_container_width=True):
                st.session_state.action_liste = "liste"
                st.session_state.liste_active_id = None
                st.rerun()

        # CAS F : VUE IMPORTER UNE LISTE (📥)
        elif st.session_state.action_liste == "importer":
            st.subheader("📥 Importer une liste")
            
            tab_id, tab_fichier = st.tabs(["🔢 Par ID de liste", "📄 Depuis un fichier texte"])
            
            # --- OPTION 1 : Importer par ID ---
            with tab_id:
                st.write("Saisis l'**ID de la liste** qu'on t'a partagé :")
                id_saisi = st.text_input("ID de la liste :", placeholder="Ex: 12", key="import_id_input")
                
                if st.button("📥 Importer la liste via ID", type="primary", use_container_width=True):
                    if id_saisi.isdigit():
                        succes, msg = importer_liste_par_id(int(id_saisi), user_id)
                        if succes:
                            st.toast(msg, icon="✅")
                            st.session_state.action_liste = "liste"
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Veuillez entrer un ID valide.")

            # --- OPTION 2 : Importer depuis un fichier texte ---
            with tab_fichier:
                st.write("Téléverse un fichier texte (`.txt`) contenant tes mots.")
                st.caption("💡 Format attendu dans le fichier : `mot, traduction` (un par ligne)")
                
                type_import = st.radio(
                    "Type de contenu dans le fichier :", 
                    ["Vocabulaire (mot, traduction)", "Verbes (infinitif, présent, prétérit, participe passé, traduction)"],
                    key="type_import_file"
                )
                type_import_code = "verbe" if "Verbes" in type_import else "vocabulaire"

                nom_nouvelle_liste = st.text_input("Nom de la nouvelle liste :", placeholder="Ex: Verbes Irréguliers Anglais")
                fichier_uploade = st.file_uploader("Choisis un fichier .txt", type=["txt", "csv"])

                if st.button("📥 Importer depuis le fichier", type="primary", use_container_width=True):
                    if not nom_nouvelle_liste.strip() or fichier_uploade is None:
                        st.warning("Remplis le nom et choisis un fichier.")
                    else:
                        contenu = fichier_uploade.getvalue().decode("utf-8")
                        nb = importer_liste_depuis_fichier(user_id, nom_nouvelle_liste.strip(), type_import_code, contenu)
                        if nb > 0:
                            st.toast(f"Liste importée avec {nb} éléments !", icon="✅")
                            st.session_state.action_liste = "liste"
                            st.rerun()
                        else:
                            st.error("Impossible de lire les éléments. Vérifie le séparateur (virgules) et le nombre de colonnes.")

            st.divider()
            if st.button("🔙 Retour", use_container_width=True):
                st.session_state.action_liste = "liste"
                st.rerun()

        # CAS G : VUE NORMALE (AFFICHAGE DES LISTES)
        else:
            # Si on est en train de demander la confirmation de suppression de compte,
            # on N'AFFICHE PAS le reste de la page
            if st.session_state.confirmer_suppr_compte:
                pass  # Le message de confirmation s'affiche déjà tout seul au-dessus !
                
            else:
                col_titre, col_import, col_ajout = st.columns([3, 1, 1])
                with col_titre:
                    st.subheader("📋 Mes listes")
                with col_import:
                    if st.button("📥", use_container_width=True, help="Importer une liste via un ID"):
                        st.session_state.action_liste = "importer"
                        st.rerun()
                with col_ajout:
                    if st.button("➕", use_container_width=True, help="Créer une nouvelle liste"):
                        st.session_state.action_liste = "creer"
                        st.session_state.nb_lignes_mots = 2
                        st.rerun()

                st.write("")
                ligne_epaisse()

                listes = recuperer_listes_utilisateur(user_id)

                if not listes:
                    st.info("Tu n'as aucune liste pour l'instant. Clique sur ➕ pour en créer une !")
                else:
                    for liste_id, nom_liste, type_liste in listes:
                        col_nom, col_voir, col_edit, col_share, col_train, col_del = st.columns([3, 1, 1, 1, 1, 1])
                        
                        with col_nom:
                            if type_liste == "verbe":
                                # Affichage en violet pour les verbes
                                st.markdown(
                                    f"<h3 style='color: #8A2BE2; margin:0;'>⚡ {nom_liste} <span style='font-size:12px; background-color:#8A2BE2; color:white; padding:2px 8px; border-radius:10px;'>VERBES</span></h3>", 
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(f"### 📄 {nom_liste}")

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

                        with col_share:
                            if st.button("🔗", key=f"share_{liste_id}", help="Partager cette liste"):
                                st.session_state.action_liste = "partager"
                                st.session_state.liste_active_id = liste_id
                                st.rerun()

                        with col_train:
                            if st.button("🎯", key=f"train_{liste_id}", help="S'entraîner sur cette liste"):
                                st.session_state.action_liste = "entrainer"
                                st.session_state.liste_active_id = liste_id
                                st.rerun()

                        with col_del:
                            if st.button("🗑️", key=f"del_{liste_id}", help="Supprimer la liste"):
                                st.session_state.action_liste = "supprimer"
                                st.session_state.liste_active_id = liste_id
                                st.rerun()

                        st.divider()

listes = recuperer_listes_utilisateur(user_id)

