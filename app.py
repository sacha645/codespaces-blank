import streamlit as st
import sqlite3
import random
import bcrypt
import json

st.set_page_config(page_title="Réviseur", layout="wide")


# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    # 1. Table Utilisateurs
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # 2. Table Listes (avec type_liste : 'vocabulaire' ou 'verbe')
    c.execute('''
        CREATE TABLE IF NOT EXISTS listes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nom_liste TEXT NOT NULL,
            type_liste TEXT NOT NULL DEFAULT 'vocabulaire',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # 3. Table Mots (avec colonnes pour verbes)
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

    # 4. Table Scores (Meilleurs scores par utilisateur et par liste)
    c.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            liste_id INTEGER NOT NULL,
            score_vers_fr REAL DEFAULT 0,
            total_vers_fr REAL DEFAULT 0,
            score_depuis_fr REAL DEFAULT 0,
            total_depuis_fr REAL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (liste_id) REFERENCES listes (id) ON DELETE CASCADE,
            UNIQUE(user_id, liste_id)
        )
    ''')

    # 5. Table Sauvegardes d'entraînement (quiz en pause)
    c.execute('''
        CREATE TABLE IF NOT EXISTS sauvegardes_quiz (
            user_id INTEGER NOT NULL,
            liste_id INTEGER PRIMARY KEY,
            donnees_json TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
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
        conn.close()
        return False

def verifier_connexion(username, password):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        user_id, db_username, db_password = user

        if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
            return True, db_username, user_id
        
    return False, None, None

def authentifier_connexion(username, password) :
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        db_password = user[0]

        if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
            return True
        
    return False

def modifier_profil_bdd(user_id, nouveau_username, nouveau_password):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    try:
        # Si un nouveau mot de passe est fourni (non vide)
        if nouveau_password and nouveau_password.strip():
            # 1. On hache le nouveau mot de passe
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(nouveau_password.encode('utf-8'), salt).decode('utf-8')
            
            # 2. On met à jour le pseudo ET le mot de passe haché
            c.execute(
                "UPDATE users SET username = ?, password = ? WHERE id = ?",
                (nouveau_username, hashed_password, user_id)
            )

        else:
            # Sinon, on ne met à jour QUE le pseudo
            c.execute(
                "UPDATE users SET username = ? WHERE id = ?",
                (nouveau_username, user_id)
            )
            
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.IntegrityError:
        conn.close()
        return False

def supprimer_compte(user_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
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

def ajouter_élément_liste(liste_id, inf_ou_mot, present="", preterit="", pp="", traduction=""):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO mots (liste_id, mot_original, present, preterit, participe_passe, traduction) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (liste_id, inf_ou_mot.strip(), present.strip(), preterit.strip(), pp.strip(), traduction.strip()))
    conn.commit()
    conn.close()

def recuperer_mots_liste(liste_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT id, mot_original, present, preterit, participe_passe, traduction FROM mots WHERE liste_id = ?", (liste_id,))
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

def remplacer_mots_liste(liste_id, nouveaux_mots, type_liste):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("DELETE FROM mots WHERE liste_id = ?", (liste_id,))
    
    for item in nouveaux_mots:
        if type_liste == "verbe":
            inf, pres, pret, pp, trad = item
            if inf.strip() and trad.strip():
                c.execute("""
                    INSERT INTO mots (liste_id, mot_original, present, preterit, participe_passe, traduction) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (liste_id, inf.strip(), pres.strip(), pret.strip(), pp.strip(), trad.strip()))
        else:
            art, mot, trad = item
            if mot.strip() and trad.strip():
                mot_complet = f"{art.strip()} {mot.strip()}" if art.strip() else mot.strip()
                c.execute("""
                    INSERT INTO mots (liste_id, mot_original, traduction) 
                    VALUES (?, ?, ?)
                """, (liste_id, mot_complet, trad.strip()))
                
    conn.commit()
    conn.close()

def importer_liste_par_id(liste_id_origine, nouvel_user_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    c.execute("SELECT nom_liste, type_liste FROM listes WHERE id = ?", (liste_id_origine,))
    res = c.fetchone()
    
    if not res:
        conn.close()
        return False, "Aucune liste trouvée avec cet ID."
    
    nom_liste_origine, type_liste = res
    nouveau_nom = f"{nom_liste_origine} (copie)"
    
    c.execute("INSERT INTO listes (user_id, nom_liste, type_liste) VALUES (?, ?, ?)", 
              (nouvel_user_id, nouveau_nom, type_liste))
    nouvelle_liste_id = c.lastrowid
    
    c.execute("SELECT mot_original, present, preterit, participe_passe, traduction FROM mots WHERE liste_id = ?", (liste_id_origine,))
    mots = c.fetchall()
    
    for mot_or, pres, pret, pp, trad in mots:
        c.execute("""
            INSERT INTO mots (liste_id, mot_original, present, preterit, participe_passe, traduction) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nouvelle_liste_id, mot_or, pres, pret, pp, trad))
        
    conn.commit()
    conn.close()
    return True, f"Liste '{nouveau_nom}' importée avec succès !"

def partager_liste_a_utilisateur(liste_id_origine, ami_user_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    c.execute("SELECT id, username FROM users WHERE id = ?", (ami_user_id,))
    ami = c.fetchone()
    if not ami:
        conn.close()
        return False, "Aucun utilisateur trouvé avec cet ID."
    
    c.execute("SELECT nom_liste, type_liste FROM listes WHERE id = ?", (liste_id_origine,))
    res = c.fetchone()
    if not res:
        conn.close()
        return False, "La liste d'origine n'existe plus."
    
    nom_liste, type_liste = res
    nouveau_nom = f"{nom_liste} (partagée)"
    
    c.execute("INSERT INTO listes (user_id, nom_liste, type_liste) VALUES (?, ?, ?)", 
              (ami_user_id, nouveau_nom, type_liste))
    nouvelle_liste_id = c.lastrowid
    
    c.execute("SELECT mot_original, present, preterit, participe_passe, traduction FROM mots WHERE liste_id = ?", (liste_id_origine,))
    mots = c.fetchall()
    
    for mot_or, pres, pret, pp, trad in mots:
        c.execute("""
            INSERT INTO mots (liste_id, mot_original, present, preterit, participe_passe, traduction) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nouvelle_liste_id, mot_or, pres, pret, pp, trad))
        
    conn.commit()
    conn.close()
    return True, f"Liste partagée avec succès à {ami[1]} !"

def importer_liste_depuis_fichier(user_id, nom_liste, type_liste, contenu_fichier):
    lignes = contenu_fichier.splitlines()
    mots_a_inserer = []
    
    # 1. Analyse et validation préalable du fichier
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            continue
        
        parts = [p.strip() for p in ligne.split(",")]
        
        # Vérification stricte : exactement 2 colonnes pour vocabulaire, 5 pour verbes
        if type_liste == "vocabulaire" and len(parts) == 2:
            mots_a_inserer.append((parts[0], "", "", "", parts[1]))
            
        elif type_liste == "verbe" and len(parts) == 5:
            mots_a_inserer.append((parts[0], parts[1], parts[2], parts[3], parts[4]))

    # 2. Si aucun mot n'est valide (mauvais format/séparateur), on n'insère rien en BDD
    if not mots_a_inserer:
        return 0

    # 3. Insertion en BDD uniquement si le format est correct
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    c.execute("INSERT INTO listes (user_id, nom_liste, type_liste) VALUES (?, ?, ?)", 
              (user_id, nom_liste, type_liste))
    nouvelle_liste_id = c.lastrowid
    
    for mot_or, pres, pret, pp, trad in mots_a_inserer:
        c.execute("""
            INSERT INTO mots (liste_id, mot_original, present, preterit, participe_passe, traduction) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nouvelle_liste_id, mot_or, pres, pret, pp, trad))

    conn.commit()
    conn.close()
    
    return len(mots_a_inserer)

def demeler_questions(questions):
    n = len(questions)
    if n <= 2:
        return questions

    milieu = n // 2
    i = 1

    while i < len(questions):
        # Si la question actuelle a le même mot que la précédente
        if questions[i]["item"] == questions[i - 1]["item"]:
            item_a_deplacer = questions.pop(i)

            if i <= milieu:
                # Envoi à la fin
                questions.append(item_a_deplacer)
            else:
                # Envoi au début
                questions.insert(0, item_a_deplacer)
                i += 1
        else:
            # Pas de doublon : on avance normalement
            i += 1

    return questions

def preparer_quiz_verbes_aleatoire(mots_verbes):
    # mots_verbes = [(id_mot, infinitif, present, preterit, participe_passe, traduction), ...]
    formes_infos = [
        (1, "Infinitif"),
        (2, "Présent"),
        (3, "Prétérit"),
        (4, "Participe Passé"),
        (5, "Traduction")
    ]
    
    questions_finales = []
    
    # Pour chaque verbe, on génère un ordre aléatoire unique de ses 5 formes (sans remise)
    # Ainsi chaque forme servira EXACTEMENT 1 fois d'indice sur les 5 tours.
    tirages_par_verbe = {
        verbe[0]: random.sample(range(5), 5) for verbe in mots_verbes
    }
    
    for tour in range(5):
        for verbe in mots_verbes:
            id_mot = verbe[0]
            # Forme choisie pour ce tour (0 à 4)
            idx_tirage = tirages_par_verbe[id_mot][tour]
            idx_tuple_fourni, nom_fourni = formes_infos[idx_tirage]
            valeur_fournie = verbe[idx_tuple_fourni]
            
            # Les 4 autres formes à deviner
            attentes = []
            for idx_tuple, nom_f in formes_infos:
                if idx_tuple != idx_tuple_fourni:
                    attentes.append({
                        "idx_tuple": idx_tuple,
                        "nom": nom_f,
                        "reponse_attendue": verbe[idx_tuple]
                    })
            
            question = {
                "id_mot": id_mot,
                "nom_fourni": nom_fourni,
                "valeur_fournie": valeur_fournie,
                "attentes": attentes,
                "verbe_tuple": verbe
            }
            questions_finales.append(question)
            
    return questions_finales

def obtenir_type_liste(liste_id):
    """
    Retourne le type d'une liste ('vocabulaire', 'verbes', etc.) à partir de son ID.
    """

    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT type_liste FROM listes WHERE id = ?", (liste_id,))
    resultat = c.fetchone()
    conn.close()
    
    if resultat:
        return resultat[0]
    return None


# --- APPARENCE ---
def ligne_epaisse():
    st.markdown(
        """
        <hr style="border: none; height: 3px; background-color: #4A4A4A; margin: 20px 0;">
        """,
        unsafe_allow_html=True
    )


# --- GESTION DU MEILLEUR SCORE ---
def enregistrer_meilleur_score(user_id, liste_id, s_vers, t_vers, s_depuis, t_depuis):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    
    c.execute("SELECT score_vers_fr, score_depuis_fr FROM scores WHERE user_id = ? AND liste_id = ?", (user_id, liste_id))
    existant = c.fetchone()
    
    if existant:
        anc_v, anc_d = existant
        nouveau_s_vers = max(anc_v, s_vers)
        nouveau_s_depuis = max(anc_d, s_depuis)
        
        c.execute("""
            UPDATE scores 
            SET score_vers_fr = ?, total_vers_fr = ?, score_depuis_fr = ?, total_depuis_fr = ?
            WHERE user_id = ? AND liste_id = ?
        """, (nouveau_s_vers, t_vers, nouveau_s_depuis, t_depuis, user_id, liste_id))
    else:
        c.execute("""
            INSERT INTO scores (user_id, liste_id, score_vers_fr, total_vers_fr, score_depuis_fr, total_depuis_fr)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, liste_id, s_vers, t_vers, s_depuis, t_depuis))
        
    conn.commit()
    conn.close()

def recuperer_score_liste(user_id, liste_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("""
        SELECT score_vers_fr, total_vers_fr, score_depuis_fr, total_depuis_fr 
        FROM scores 
        WHERE user_id = ? AND liste_id = ?
    """, (user_id, liste_id))
    score = c.fetchone()
    conn.close()
    return score

def reinitialiser_score_liste(user_id, liste_id):
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("DELETE FROM scores WHERE user_id = ? AND liste_id = ?", (user_id, liste_id))
    conn.commit()
    conn.close()


# --- Bouton pause ---
def sauvegarder_partie(user_id, liste_id, donnees_dict):
    """Enregistre ou met à jour la progression d'un quiz sous forme de texte JSON."""
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    donnees_json = json.dumps(donnees_dict)
    c.execute('''
        INSERT INTO sauvegardes_quiz (user_id, liste_id, donnees_json)
        VALUES (?, ?, ?)
        ON CONFLICT(liste_id) DO UPDATE SET donnees_json = excluded.donnees_json
    ''', (user_id, liste_id, donnees_json))
    conn.commit()
    conn.close()

def charger_partie_sauvegardee(liste_id):
    """Récupère les données sauvegardées d'un quiz pour une liste donnée."""
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("SELECT donnees_json FROM sauvegardes_quiz WHERE liste_id = ?", (liste_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def supprimer_sauvegarde_partie(liste_id):
    """Supprime la sauvegarde d'un quiz (quand le quiz est terminé)."""
    conn = sqlite3.connect("utilisateurs.db")
    c = conn.cursor()
    c.execute("DELETE FROM sauvegardes_quiz WHERE liste_id = ?", (liste_id,))
    conn.commit()
    conn.close()


# --- INITIALISATION DU STATE ---
if "etat" not in st.session_state:
    st.session_state.etat = "none"

if "user" not in st.session_state:
    st.session_state.user = None


# --- BARRE DE NAVIGATION ---
if st.session_state.etat == "connecte" : 
    col_title, col_compte, col_signup, col_action = st.columns([4, 2, 2, 2])

    with col_compte : 
        if st.button("Profil", use_container_width=True):
            st.session_state.action = "compte"
            st.rerun()

    with col_action:
        if st.button("🗑️ Supprimer mon compte", type="secondary", use_container_width=True):
            st.session_state.action = "suppr_compte"
            st.rerun()
                
    with col_signup:
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.user = None
            st.session_state.etat = "none"
            st.rerun()
else : 
    col_title, col_action, col_signup = st.columns([6, 2, 2])

    with col_action:
        if st.button("Se connecter", use_container_width=True):
            st.session_state.etat = "connect"
            st.rerun()
                
    with col_signup:
        if st.button("S'inscrire", type="primary", use_container_width=True):
            st.session_state.etat = "nouveau"
            st.rerun()


with col_title:
    st.markdown("""
        <style>
        /* Force la taille H1 sur le bouton tertiaire ET tous ses éléments internes */
        button[kind="tertiary"], 
        button[kind="tertiary"] p {
            font-size: 2.25rem !important;
            font-weight: 700 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if st.button("📘 Réviseur", key="btn_titre_accueil", type="tertiary"):
        # 1. Si déconnecté
        if st.session_state.get("etat") in ["nouveau", "connect", "none", "None"]:
            st.session_state.etat = "none"

        # 2. Si connecté et en plein entraînement
        elif st.session_state.get("action") == "entrainer":
            user_id = st.session_state.user[1] if st.session_state.get("user") else None
            liste_id = st.session_state.get("liste_active_id")
            type_liste = obtenir_type_liste(liste_id)

            if user_id and liste_id:
                if type_liste == "vocabulaire":
                    etat_a_sauver = {
                        "quiz_index": st.session_state.get("quiz_index", 0),
                        "quiz_mots": st.session_state.get("quiz_mots", []),
                        "score_vers_fr": st.session_state.get("score_vers_fr", 0.0),
                        "total_vers_fr": st.session_state.get("total_vers_fr", 0.0),
                        "score_depuis_fr": st.session_state.get("score_depuis_fr", 0.0),
                        "total_depuis_fr": st.session_state.get("total_depuis_fr", 0.0),
                        "erreurs_commises": st.session_state.get("erreurs_commises", [])
                    }
                    
                    sauvegarder_partie(user_id, liste_id, etat_a_sauver)
                    
                    for clef in ["quiz_mots", "quiz_index", "quiz_liste_id", "score_vers_fr", 
                                 "total_vers_fr", "score_depuis_fr", "total_depuis_fr", "erreurs_commises"]:
                        st.session_state.pop(clef, None)

                else:
                    etat_a_sauver = {
                        "quiz_index": st.session_state.get("quiz_index", 0),
                        "quiz_mots": st.session_state.get("quiz_mots", []),
                        "score_verbes": st.session_state.get("score_verbes", 0.0),
                        "total_verbes": st.session_state.get("total_verbes", 0.0),
                        "erreurs_compteur": st.session_state.get("erreurs_compteur", {}),
                        "erreurs_verbes_detail": st.session_state.get("erreurs_verbes_detail", [])
                    }

                    sauvegarder_partie(user_id, liste_id, etat_a_sauver)
                    
                    clefs_a_supprimer = ["quiz_mots", "quiz_index", "quiz_liste_id", "score_verbes", "total_verbes", "erreurs_compteur", "erreurs_verbes_detail"]
                    for clef in clefs_a_supprimer:
                        if clef in st.session_state:
                            del st.session_state[clef]

            st.session_state.action = "liste"

        # 3. Si connecté sur une autre vue
        else:
            st.session_state.action = "liste"
            st.session_state.nb_lignes_mots = 2
            st.session_state.liste_active_id = None

        st.rerun()
            
    if st.session_state.etat == "connecte":
        username, user_id = st.session_state.user
        st.caption(f"Connecté en tant que **{username}** (Ton ID : `{user_id}`)")
    
ligne_epaisse()


# --- AFFICHAGE SELON L'ÉTAT ---

# 1. ÉTAT : NONE (Accueil public)
if st.session_state.etat == "none":
    _, col_texte, _ = st.columns([1, 3, 1])

# 2. ÉTAT : NOUVEAU (Inscription)
elif st.session_state.etat == "nouveau":
    st.write("")
    _, col_centre, _ = st.columns([1, 2, 1])
    with col_centre:
        with st.form("form_inscription"):
            st.subheader("📝 Créer un compte")

            st.write("")

            nom = st.text_input("Nom d'utilisateur")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            mot_de_passe_conf = st.text_input("Confirmer le mot de passe", type="password")

            st.write("")

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

# 3. ÉTAT : CONNECT (Connexion)
elif st.session_state.etat == "connect":
    st.write("")
    _, col_centre, _ = st.columns([1, 2, 1])
    with col_centre:
        with st.form("form_connexion"):
            st.subheader("🔑 Connexion")

            st.write("")

            nom = st.text_input("Nom d'utilisateur")
            mot_de_passe = st.text_input("Mot de passe", type="password")

            st.write("")

            valider = st.form_submit_button("Se connecter", type="primary")

            if valider:
                succes, username, user_id = verifier_connexion(nom, mot_de_passe)
                if succes :
                    st.session_state.user = (username, user_id)
                    st.session_state.etat = "connecte"
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect.")


# --- 4. ÉTAT : CONNECTE (Espace utilisateur) ---
elif st.session_state.etat == "connecte":
    username, user_id = st.session_state.user

    if "action" not in st.session_state:
        st.session_state.action = "liste"
    if "liste_active_id" not in st.session_state:
        st.session_state.liste_active_id = None
    if "nb_lignes_mots" not in st.session_state:
        st.session_state.nb_lignes_mots = 2

    _, col_centre, _ = st.columns([1, 3, 1])

    with col_centre:

        # CAS A VUE/MODIFICATIONS PROFIL
        if st.session_state.action == "compte":
            st.subheader("👤 Mon Profil")

            # 1. Champs de saisie
            nouveau_pseudo = st.text_input("Pseudo", value=st.session_state.temp_new_username) if "temp_new_username" in st.session_state else st.text_input("Pseudo", value=username)
            nouveau_mdp = st.text_input("Nouveau mot de passe", value=st.session_state.temp_new_password, type="password", placeholder="Entrer un nouveau mot de passe") if "temp_new_password" in st.session_state else st.text_input("Nouveau mot de passe", type="password", placeholder="Entrer un nouveau mot de passe")

            # 2. Vérification des modifications
            pseudo_modifie = nouveau_pseudo.strip() != username
            mdp_modifie = len(nouveau_mdp.strip()) > 0
            a_modifie = pseudo_modifie or mdp_modifie

            st.write("") # Espacement

            # 3. Boutons d'action
            col_save, col_back = st.columns(2)

            with col_save:
                if st.button("💾 Sauvegarder", type="primary", use_container_width=True, disabled=not a_modifie):
                    # Enregistrement temporaire des saisies
                    st.session_state.temp_new_username = nouveau_pseudo.strip()
                    st.session_state.temp_new_password = nouveau_mdp.strip()
                    # Passage à l'écran de confirmation
                    st.session_state.action = "confirmation_compte"
                    st.rerun()

            with col_back:
                if st.button("🔙 Retour", use_container_width=True):
                    st.session_state.pop("temp_new_username", None)
                    st.session_state.pop("temp_new_password", None)
                    st.session_state.action = "liste"
                    st.rerun()

        # CAS B : CONFIRMATION MODIFICATION DU PROFIL
        elif st.session_state.action == "confirmation_compte":
            st.subheader("🔒 Confirmation des modifications")

            pseudo_modifie = st.session_state.temp_new_username != username
            mdp_modifie = len(st.session_state.temp_new_password) > 0

            # Cas A : Seulement le pseudo a été modifié
            if pseudo_modifie and not mdp_modifie:
                st.info("Vous êtes sur le point de modifier votre pseudo.")
                mdp_actuel = st.text_input(
                    "Mot de passe actuel",
                    type="password",
                    placeholder="Veuillez confirmer votre mot de passe"
                )
                confirm_mdp = None  # Non nécessaire dans ce cas

            # Cas B : Le mot de passe (ou les deux) a été modifié
            else:
                st.info("Vous êtes sur le point de modifier des informations sensibles.")
                confirm_mdp = st.text_input(
                    "Confirmer le nouveau mot de passe",
                    type="password",
                    placeholder="Saisissez à nouveau votre nouveau mot de passe"
                )
                mdp_actuel = st.text_input(
                    "Mot de passe actuel",
                    type="password",
                    placeholder="Veuillez confirmer votre mot de passe actuel"
                )

            st.write("") # Espacement

            col_confirm, col_cancel = st.columns(2)

            with col_confirm:
                if st.button("✅ Confirmer", type="primary", use_container_width=True):
                    # Validation du mot de passe actuel avec la BDD
                    if authentifier_connexion(username, mdp_actuel):
                        
                        # Vérification supplémentaire si le nouveau mot de passe devait être confirmé
                        if mdp_modifie and confirm_mdp != st.session_state.temp_new_password:
                            st.error("Le nouveau mot de passe et sa confirmation ne correspondent pas.")
                        else:
                            # Mise à jour en base de données
                            final_username = st.session_state.temp_new_username if pseudo_modifie else username
                            final_password = st.session_state.temp_new_password if mdp_modifie else mdp_actuel

                            modifier_profil_bdd(user_id, final_username, final_password)

                            # Mise à jour de la session
                            username = final_username
                            st.toast("Profil mis à jour avec succès !", icon="✅")

                            # Nettoyage des données temporaires et retour accueil
                            st.session_state.pop("temp_new_username", None)
                            st.session_state.pop("temp_new_password", None)
                            st.session_state.action = "accueil"
                            st.rerun()
                    else:
                        st.error("Le mot de passe actuel est incorrect.")

            with col_cancel:
                if st.button("❌ Annuler", use_container_width=True):
                    # Retour à l'écran du profil sans effacer la saisie
                    st.session_state.action = "compte"
                    st.rerun()

        # CAS C : CONFIRMATION DE SUPPRESSION DE COMPTE
        elif st.session_state.action == "suppr_compte":

            st.write("")
            st.error("⚠️ **ATTENTION :** Es-tu vraiment sûr de vouloir supprimer ton compte ? Toutes tes listes et tous tes mots seront définitivement perdus.")
            st.write("")

            col_annuler_compte, col_confirmer_compte = st.columns(2)
            
            with col_annuler_compte:
                if st.button("❌ Annuler", use_container_width=True):
                    st.session_state.action = "liste"
                    st.rerun()

            with col_confirmer_compte:
                if st.button("🗑️ Oui, supprimer mon compte", type="primary", use_container_width=True):
                    supprimer_compte(user_id)
                    st.session_state.user = None
                    st.session_state.etat = "none"
                    st.session_state.action = "liste"
                    st.rerun()

        # CAS D : VUE IMPORTER UNE LISTE (📥)
        elif st.session_state.action == "importer":
            st.subheader("📥 Importer une liste")
            
            tab_id, tab_fichier = st.tabs(["🔢 Par ID de liste", "📄 Depuis un fichier texte"])
            
            with tab_id:
                st.write("Saisis l'**ID de la liste** qu'on t'a partagé :")
                id_saisi = st.text_input("ID de la liste :", placeholder="Ex: 12", key="import_id_input")
                
                if st.button("📥 Importer la liste via ID", type="primary", use_container_width=True):
                    if id_saisi.isdigit():
                        succes, msg = importer_liste_par_id(int(id_saisi), user_id)
                        if succes:
                            st.session_state.action = "liste"
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Veuillez entrer un ID valide.")

            with tab_fichier:
                st.write("Téléverse un fichier texte (`.txt`) contenant tes mots ou verbes.")
                
                type_import = st.radio(
                    "Type de liste à importer :", 
                    ["Vocabulaire", "Verbes"],
                    horizontal=True,
                    key="type_import_file"
                )
                type_import_code = "verbe" if type_import == "Verbes" else "vocabulaire"

                if type_import_code == "verbe":
                    st.info("💡 **Format attendu :** `infinitif, présent, prétérit, participe passé, traduction` (un verbe par ligne)")
                else:
                    st.info("💡 **Format attendu :** `mot, traduction` (un mot par ligne)")
                
                nom_nouvelle_liste = st.text_input("Nom de la nouvelle liste :", placeholder="Ex: Verbes Irréguliers")
                fichier_uploade = st.file_uploader("Choisis un fichier .txt", type=["txt", "csv"])
                
                if st.button("📥 Importer depuis le fichier", type="primary", use_container_width=True):
                    if not nom_nouvelle_liste.strip():
                        st.warning("Donne un nom à la nouvelle liste.")
                    elif fichier_uploade is None:
                        st.warning("Veuillez sélectionner un fichier.")
                    else:
                        contenu = fichier_uploade.getvalue().decode("utf-8")
                        nb_mots = importer_liste_depuis_fichier(user_id, nom_nouvelle_liste.strip(), type_import_code, contenu)
                        
                        if nb_mots > 0:
                            st.session_state.action = "liste"
                            st.rerun()
                        else:
                            st.error("Aucun élément n'a pu être extrait. Vérifie que le format correspond bien aux consignes.")

            ligne_epaisse()

            if st.button("🔙 Retour", use_container_width=True):
                st.session_state.action = "liste"
                st.rerun()

        # CAS E : VUE FORMULAIRE DE CRÉATION DE LISTE
        elif st.session_state.action == "creer":
            st.subheader("✨ Créer une nouvelle liste")
            ligne_epaisse()

            st.write("")
            nom_liste = st.text_input("Nom de la liste", placeholder="Nom de la liste")
            st.write("")

            type_liste_choisi = st.radio(
                "Type de liste :", 
                ["Vocabulaire (Article, Mot, Traduction)", "Verbes (5 formes)"],
                horizontal=True
            )
            
            is_verbe = "Verbes" in type_liste_choisi
            type_code = "verbe" if is_verbe else "vocabulaire"
            
            st.divider()

            mots_saisis = []
            toutes_lignes_visibles_remplies = True

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
                    
                    mots_saisis.append(("", inf, pres, pret, pp, trad))
                    if not (inf.strip() and trad.strip()):
                        toutes_lignes_visibles_remplies = False
                else:
                    c1, c2, c3 = st.columns([1, 2, 2])
                    art = c1.text_input(f"art_{i}", key=f"art_{i}", label_visibility="collapsed")
                    mot = c2.text_input(f"mot_{i}", key=f"mot_{i}", label_visibility="collapsed")
                    trad = c3.text_input(f"trad_{i}", key=f"trad_{i}", label_visibility="collapsed")
                    
                    mots_saisis.append((art, mot, "", "", "", trad))
                    if not (mot.strip() and trad.strip()):
                        toutes_lignes_visibles_remplies = False

            if toutes_lignes_visibles_remplies:
                st.session_state.nb_lignes_mots += 1
                st.rerun()

            st.write("")
            st.write("")
            col_annuler, col_sauvegarder = st.columns(2)

            with col_annuler:
                if st.button("❌ Annuler", use_container_width=True):
                    st.session_state.action = "liste"
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

                        for art, inf_mot, pres, pret, pp, trad in mots_saisis:
                            if is_verbe:
                                if inf_mot.strip() and trad.strip():
                                    ajouter_élément_liste(derniere_liste_id, inf_mot, pres, pret, pp, trad)
                            else:
                                if inf_mot.strip() and trad.strip():
                                    mot_comp = f"{art.strip()} {inf_mot.strip()}" if art.strip() else inf_mot.strip()
                                    ajouter_élément_liste(derniere_liste_id, mot_comp, "", "", "", trad)

                        st.session_state.action = "liste"
                        st.session_state.nb_lignes_mots = 2
                        st.rerun()

        # CAS F : VUE VOIR UNE LISTE (👁️)
        elif st.session_state.action == "voir":
            liste_id = st.session_state.liste_active_id
            
            listes_user = recuperer_listes_utilisateur(user_id)
            info_liste = next(((nom, type_l) for lid, nom, type_l in listes_user if lid == liste_id), ("Liste", "vocabulaire"))
            nom_actuel, type_liste = info_liste

            st.subheader(f"📖 {nom_actuel}")

            ligne_epaisse()
            st.write("")

            mots = recuperer_mots_liste(liste_id)

            if not mots:
                st.info("Cette liste ne contient aucun élément.")
            else:
                compteur_err = st.session_state.get(f"erreurs_liste_{liste_id}", {})

                if type_liste == "verbe":
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.markdown("<u>**Infinitif :**</u>", unsafe_allow_html=True)
                    c2.markdown("<u>**Présent :**</u>", unsafe_allow_html=True)
                    c3.markdown("<u>**Prétérit :**</u>", unsafe_allow_html=True)
                    c4.markdown("<u>**Participe Passé :**</u>", unsafe_allow_html=True)
                    c5.markdown("<u>**Traduction :**</u>", unsafe_allow_html=True)
                    st.write("")

                    for mot in mots:
                        id_m, inf, pres, pret, pp, trad = mot
                        errs = compteur_err.get(id_m, {1: 0, 2: 0, 3: 0, 4: 0, 5: 0})
                        
                        def fmt_v(texte, idx_f):
                            if isinstance(errs, dict) and errs.get(idx_f, 0) >= 2:
                                return f"<span style='color: #FF4B4B; font-weight: bold;'>{texte}</span>"
                            return texte

                        col1, col2, col3, col4, col5 = st.columns(5)
                        col1.markdown(fmt_v(inf, 1), unsafe_allow_html=True)
                        col2.markdown(fmt_v(pres, 2), unsafe_allow_html=True)
                        col3.markdown(fmt_v(pret, 3), unsafe_allow_html=True)
                        col4.markdown(fmt_v(pp, 4), unsafe_allow_html=True)
                        col5.markdown(fmt_v(trad, 5), unsafe_allow_html=True)
                else:
                    c_m1, c_m2 = st.columns(2)
                    c_m1.markdown("<u>**Mot :**</u>", unsafe_allow_html=True)
                    c_m2.markdown("<u>**Traduction :**</u>", unsafe_allow_html=True)
                    st.write("")

                    for mot in mots:
                        id_m, mot_or, _, _, _, trad = mot
                        
                        # Récupération des erreurs spécifiques par sens
                        # err_info = {"vers_fr": True/False, "depuis_fr": True/False}
                        err_info = compteur_err.get(id_m, {}) if isinstance(compteur_err, dict) else {}
                        
                        # Si l'erreur était vers le français (question en langue étrangère -> faute sur la traduction)
                        err_trad = err_info.get("vers_fr", False)
                        # Si l'erreur était depuis le français (question en français -> faute sur le mot étranger)
                        err_orig = err_info.get("depuis_fr", False)

                        # Coloration uniquement du côté erroné
                        mot_disp = f"<span style='color: #FF4B4B; font-weight: bold;'>{mot_or}</span>" if err_orig else mot_or
                        trad_disp = f"<span style='color: #FF4B4B; font-weight: bold;'>{trad}</span>" if err_trad else trad

                        cm1, cm2 = st.columns(2)
                        cm1.markdown(mot_disp, unsafe_allow_html=True)
                        cm2.markdown(trad_disp, unsafe_allow_html=True)

            ligne_epaisse()
            st.write("")

            if st.button("🔙 Retour", use_container_width=True):
                st.session_state.action = "liste"
                st.session_state.liste_active_id = None
                st.rerun()

        # CAS G : VUE ÉDITER UNE LISTE (✏️)
        elif st.session_state.action == "editer":
            liste_id = st.session_state.liste_active_id
            
            listes_user = recuperer_listes_utilisateur(user_id)
            info_liste = next(((nom, type_l) for lid, nom, type_l in listes_user if lid == liste_id), ("", "vocabulaire"))
            nom_actuel, type_liste = info_liste

            st.subheader("✏️ Éditer la liste")
            ligne_epaisse()
            
            st.write("")
            nouveau_nom = st.text_input("Nom de la liste", value=nom_actuel)
            st.divider()

            mots_existants = recuperer_mots_liste(liste_id)
            nb_lignes = max(len(mots_existants) + 1, st.session_state.nb_lignes_mots)

            mots_modifies = []
            toutes_lignes_visibles_remplies = True
            
            if type_liste == "verbe":
                cols_h = st.columns([2, 2, 2, 2, 2])
                headers = ["Infinitif", "Présent", "Prétérit", "Participe Passé", "Traduction"]
                for col, h in zip(cols_h, headers):
                    col.caption(h)

                for i in range(nb_lignes):
                    inf_v, pres_v, pret_v, pp_v, trad_v = "", "", "", "", ""
                    if i < len(mots_existants):
                        _, inf_v, pres_v, pret_v, pp_v, trad_v = mots_existants[i]

                    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
                    inf = c1.text_input(f"edit_inf_{i}", value=inf_v, key=f"edit_inf_{i}", label_visibility="collapsed")
                    pres = c2.text_input(f"edit_pres_{i}", value=pres_v, key=f"edit_pres_{i}", label_visibility="collapsed")
                    pret = c3.text_input(f"edit_pret_{i}", value=pret_v, key=f"edit_pret_{i}", label_visibility="collapsed")
                    pp = c4.text_input(f"edit_pp_{i}", value=pp_v, key=f"edit_pp_{i}", label_visibility="collapsed")
                    trad = c5.text_input(f"edit_vtrad_{i}", value=trad_v, key=f"edit_vtrad_{i}", label_visibility="collapsed")

                    mots_modifies.append((inf, pres, pret, pp, trad))

                    if len(inf.strip()) < 1 or len(trad.strip()) < 1:
                        toutes_lignes_visibles_remplies = False

            else:
                cols_h = st.columns([1, 2, 2])
                headers = ["Article", "Mot / Nom", "Traduction"]
                for col, h in zip(cols_h, headers):
                    col.caption(h)

                for i in range(nb_lignes):
                    art_val, mot_val, trad_val = "", "", ""
                    if i < len(mots_existants):
                        _, mot_or, _, _, _, trad_val = mots_existants[i]
                        parts = mot_or.split(" ", 1)
                        if len(parts) == 2 and parts[0].lower() in ["le", "la", "les", "un", "une", "des", "l'", "the", "a", "an", "el", "los", "las", "der", "die", "das"]:
                            art_val, mot_val = parts[0], parts[1]
                        else:
                            mot_val = mot_or

                    c1, c2, c3 = st.columns([1, 2, 2])
                    art = c1.text_input(f"edit_art_{i}", value=art_val, key=f"edit_art_{i}", label_visibility="collapsed")
                    mot = c2.text_input(f"edit_mot_{i}", value=mot_val, key=f"edit_mot_{i}", label_visibility="collapsed")
                    trad = c3.text_input(f"edit_trad_{i}", value=trad_val, key=f"edit_trad_{i}", label_visibility="collapsed")

                    mots_modifies.append((art, mot, trad))

                    if len(mot.strip()) < 1 or len(trad.strip()) < 1:
                        toutes_lignes_visibles_remplies = False

            if toutes_lignes_visibles_remplies:
                st.session_state.nb_lignes_mots = nb_lignes + 1
                st.rerun()

            st.write("")
            st.write("")
            col_annuler, col_sauvegarder = st.columns(2)

            with col_annuler:
                if st.button("❌ Annuler", use_container_width=True):
                    st.session_state.action = "liste"
                    st.session_state.liste_active_id = None
                    st.session_state.nb_lignes_mots = 2
                    st.rerun()

            with col_sauvegarder:
                if st.button("💾 Enregistrer les modifications", type="primary", use_container_width=True):
                    if not nouveau_nom.strip():
                        st.warning("Le nom de la liste ne peut pas être vide.")
                    else:
                        renommer_liste(liste_id, nouveau_nom.strip())
                        remplacer_mots_liste(liste_id, mots_modifies, type_liste)
                        
                        st.session_state.action = "liste"
                        st.session_state.liste_active_id = None
                        st.session_state.nb_lignes_mots = 2
                        reinitialiser_score_liste(user_id, liste_id)
                        st.rerun()

        # CAS H : VUE ENTRAÎNEMENT (🎯)
        elif st.session_state.action == "entrainer":
            liste_id = st.session_state.liste_active_id
            listes_user = recuperer_listes_utilisateur(user_id)
            info_liste = next(((nom, type_l) for lid, nom, type_l in listes_user if lid == liste_id), ("Liste", "vocabulaire"))
            nom_actuel, type_liste = info_liste

            st.subheader(f"🎯 Entraînement : {nom_actuel}")
            ligne_epaisse()
            st.write("")

            # --- S'IL S'AGIT D'UNE LISTE DE VOCABULAIRE ---
            if type_liste == "vocabulaire":

                # 1. INITIALISATION / REPRISE DU QUIZ VOCABULAIRE
                if "quiz_mots" not in st.session_state or st.session_state.get("quiz_liste_id") != liste_id:
                    partie_sauvee = charger_partie_sauvegardee(liste_id)

                    # Demande si une sauvegarde existe
                    if partie_sauvee and "choix_reprise" not in st.session_state:
                        st.info("💾 Une sauvegarde d'entraînement existe pour cette liste.")
                        st.write("")
                        col_c1, col_c2 = st.columns(2)
                        
                        with col_c1:
                            if st.button("▶️ Charger la sauvegarde", type="primary", use_container_width=True):
                                st.session_state.choix_reprise = "charger"
                                st.rerun()

                        with col_c2:
                            if st.button("🔄 Recommencer à zéro", type="secondary", use_container_width=True):
                                supprimer_sauvegarde_partie(liste_id)
                                st.session_state.choix_reprise = "nouveau"
                                st.rerun()

                        st.stop()

                    # Chargement ou Création
                    if partie_sauvee and st.session_state.get("choix_reprise") == "charger":
                        st.session_state.quiz_mots = partie_sauvee["quiz_mots"]
                        st.session_state.quiz_index = partie_sauvee["quiz_index"]
                        st.session_state.score_vers_fr = partie_sauvee["score_vers_fr"]
                        st.session_state.total_vers_fr = partie_sauvee["total_vers_fr"]
                        st.session_state.score_depuis_fr = partie_sauvee["score_depuis_fr"]
                        st.session_state.total_depuis_fr = partie_sauvee["total_depuis_fr"]
                        st.session_state.erreurs_commises = partie_sauvee["erreurs_commises"]
                        st.session_state.quiz_liste_id = liste_id
                        st.toast("⚡ Sauvegarde chargée !")
                    else:
                        mots_bruts = recuperer_mots_liste(liste_id)
                        articles_connus = ["le", "la", "les", "un", "une", "des", "l'", "the", "a", "an", "el", "los", "las", "der", "die", "das"]
                        
                        mots_traites = []
                        for id_m, mot_or, _, _, _, trad in mots_bruts:
                            parts = mot_or.strip().split(" ", 1)
                            if len(parts) == 2 and parts[0].lower() in articles_connus:
                                art, mot = parts[0], parts[1]
                            else:
                                art, mot = "", mot_or.strip()
                            
                            mots_traites.append({
                                "id_mot": id_m,
                                "article": art,
                                "mot": mot,
                                "traduction": trad.strip()
                            })

                        # On crée la liste de questions avec les 2 sens (exactement comme dans ton code d'origine)
                        questions = []
                        for item in mots_traites:
                            questions.append({"item": item, "sens": "vers_francais"})
                            questions.append({"item": item, "sens": "depuis_francais"})
                        
                        # Mélange 1 : Aléatoire
                        random.shuffle(questions)

                        # Mélange 2 : Démêlage (qui reçoit maintenant la bonne structure avec 'item')
                        questions = demeler_questions(questions)

                        # Enregistrement dans la session
                        st.session_state.quiz_mots = questions
                        st.session_state.quiz_index = 0
                        st.session_state.score_vers_fr = 0.0
                        st.session_state.total_vers_fr = 0.0
                        st.session_state.score_depuis_fr = 0.0
                        st.session_state.total_depuis_fr = 0.0
                        st.session_state.erreurs_commises = []
                        st.session_state.quiz_liste_id = liste_id

                    # Nettoyage du choix temporaire
                    if "choix_reprise" in st.session_state:
                        del st.session_state.choix_reprise

                questions = st.session_state.quiz_mots
                index = st.session_state.quiz_index

                # 2. VUE FINALE : BILAN DU QUIZ ET SAUVEGARDE EN BDD
                if index >= len(questions):
                    s_v = st.session_state.score_vers_fr
                    t_v = st.session_state.total_vers_fr
                    s_d = st.session_state.score_depuis_fr
                    t_d = st.session_state.total_depuis_fr

                    score_actuel_bdd = recuperer_score_liste(user_id, liste_id)
                    est_nouveau_record = False

                    if score_actuel_bdd is None:
                        est_nouveau_record = True
                    else:
                        anc_v, _, anc_d, _ = score_actuel_bdd
                        if s_v > anc_v or s_d > anc_d:
                            est_nouveau_record = True

                    enregistrer_meilleur_score(user_id, liste_id, s_v, t_v, s_d, t_d)
                    supprimer_sauvegarde_partie(liste_id)

                    mots_err = {}
                    for err in st.session_state.erreurs_commises:
                        if "id_mot" in err:
                            id_m = err["id_mot"]
                            sens = err.get("sens", "")
                            if id_m not in mots_err:
                                mots_err[id_m] = {"vers_fr": False, "depuis_fr": False}
                            
                            if sens == "vers_fr":
                                mots_err[id_m]["vers_fr"] = True
                            elif sens == "depuis_fr":
                                mots_err[id_m]["depuis_fr"] = True

                    st.session_state[f"erreurs_liste_{liste_id}"] = mots_err

                    st.write("### 📊 Tes résultats :")

                    if est_nouveau_record:
                        st.success("🥳 **Nouveau meilleur score !**")
                    elif score_actuel_bdd:
                        anc_v, anc_tv, anc_d, anc_td = score_actuel_bdd
                        st.write(f"🏆 **Meilleur score :** 🌐 `{anc_v:g}/{anc_tv:g}` &nbsp;|&nbsp; 🇫🇷 `{anc_d:g}/{anc_td:g}`")

                    st.write("")

                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        score_v = st.session_state.score_vers_fr
                        tot_v = st.session_state.total_vers_fr
                        st.metric(label="🌐 Vers la langue étrangère", value=f"{score_v:g} / {tot_v:g}")

                    with col_res2:
                        score_d = st.session_state.score_depuis_fr
                        tot_d = st.session_state.total_depuis_fr
                        st.metric(label="🇫🇷 Vers le français", value=f"{score_d:g} / {tot_d:g}")

                    erreurs = st.session_state.erreurs_commises
                    st.divider()

                    if erreurs:
                        st.write("### ❌ Liste des erreurs commises")
                        st.caption("Seuls les éléments erronés sont affichés en rouge :")
                        st.write("")

                        col_q, col_rep, col_att = st.columns([2, 2, 2])
                        col_q.markdown("<u>**Question posée :**</u>", unsafe_allow_html=True)
                        col_rep.markdown("<u>**Ta réponse:**</u>", unsafe_allow_html=True)
                        col_att.markdown("<u>**Réponse attendue :**</u>", unsafe_allow_html=True)

                        for err in erreurs:
                            c1, c2, c3 = st.columns([2, 2, 2])
                            c1.markdown(f"Traduction de <u>**{err['question']}**</u>", unsafe_allow_html=True)
                            c2.markdown(err["reponse_user_html"], unsafe_allow_html=True)
                            c3.markdown(f"🟢 {err['reponse_attendue']}")
                    else:
                        st.balloons()
                        st.info("⭐ Félicitations ! Tu as fait un sans-faute parfait.")

                    ligne_epaisse()
                    st.write("")
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("🔙 Retour aux listes", type="primary", use_container_width=True):
                            if "quiz_mots" in st.session_state:
                                del st.session_state.quiz_mots
                            st.session_state.action = "liste"
                            st.rerun()
                    with col_b2:
                        if st.button("🔄 Recommencer", use_container_width=True):
                            if "quiz_mots" in st.session_state:
                                del st.session_state.quiz_mots
                            st.rerun()

                # 3. VUE DE QUESTION EN COURS
                else:
                    q = questions[index]
                    item = q["item"]
                    sens = q["sens"]
                    has_article = bool(item["article"].strip())

                    st.progress(index / len(questions), text=f"Question {index + 1} / {len(questions)}")

                    with st.form(key=f"form_quiz_{index}"):
                        if sens == "vers_francais":
                            st.markdown(f"### Traduis en langue étrangère : **{item['traduction']}**")
                            if has_article:
                                c_art, c_mot = st.columns([1, 3])
                                user_art = c_art.text_input("Article (si présent)", key=f"art_in_{index}")
                                user_mot = c_mot.text_input("Mot / Nom", key=f"mot_in_{index}")
                            else:
                                user_art = ""
                                user_mot = st.text_input("Mot / Nom", key=f"mot_in_{index}")
                            user_trad = ""
                        else:
                            mot_affiche = f"{item['article']} {item['mot']}".strip()
                            st.markdown(f"### Traduis en français : **{mot_affiche}**")
                            user_art = ""
                            user_mot = ""
                            user_trad = st.text_input("Traduction", key=f"trad_in_{index}")

                        st.write("")
                        valider = st.form_submit_button("Suivant 🚀", type="primary")

                    if valider:
                        points_gagnes = 0.0
                        total_q = 1.0

                        u_art = user_art.strip()
                        u_mot = user_mot.strip() if sens == "vers_francais" else user_trad.strip()

                        if sens == "vers_francais":
                            art_correct = (u_art.lower() == item["article"].lower()) if has_article else True
                            mot_correct = (u_mot.lower() == item["mot"].lower())
                            
                            q_txt = item['traduction']
                            rep_att = f"{item['article']} {item['mot']}".strip()

                            if has_article:
                                if art_correct:
                                    points_gagnes += 0.5
                                if mot_correct:
                                    points_gagnes += 0.5
                            else:
                                if mot_correct:
                                    points_gagnes += 1.0

                            if points_gagnes < 1.0:
                                partie_art_html = f"<span style='color:red;'>{u_art if u_art else '(vide)'}</span>" if not art_correct else u_art
                                partie_mot_html = f"<span style='color:red;'>{u_mot if u_mot else '(vide)'}</span>" if not mot_correct else u_mot
                                
                                rep_user_formatted = f"{partie_art_html} {partie_mot_html}".strip() if has_article else partie_mot_html

                                st.session_state.erreurs_commises.append({
                                    "id_mot": item["id_mot"],
                                    "sens": "depuis_fr",
                                    "question": q_txt,
                                    "reponse_user_html": rep_user_formatted,
                                    "reponse_attendue": rep_att
                                })

                        else:
                            mot_correct = (u_mot.lower() == item["traduction"].lower())
                            mot_affiche = f"{item['article']} {item['mot']}".strip()
                            q_txt = mot_affiche
                            rep_att = item["traduction"]

                            if mot_correct:
                                points_gagnes = 1.0
                            else:
                                points_gagnes = 0.0
                                partie_mot_html = f"<span style='color:red;'>{u_mot if u_mot else '(vide)'}</span>"
                                
                                st.session_state.erreurs_commises.append({
                                    "id_mot": item["id_mot"],
                                    "sens": "vers_fr",
                                    "question": q_txt,
                                    "reponse_user_html": partie_mot_html,
                                    "reponse_attendue": rep_att
                                })

                        if sens == "vers_francais":
                            st.session_state.score_vers_fr += points_gagnes
                            st.session_state.total_vers_fr += total_q
                        else:
                            st.session_state.score_depuis_fr += points_gagnes
                            st.session_state.total_depuis_fr += total_q

                        st.session_state.quiz_index += 1

                        # 💾 SAUVEGARDE AUTOMATIQUE À CHAQUE QUESTION VALIDÉE
                        etat_a_sauver = {
                            "quiz_index": st.session_state.quiz_index,
                            "quiz_mots": st.session_state.quiz_mots,
                            "score_vers_fr": st.session_state.score_vers_fr,
                            "total_vers_fr": st.session_state.total_vers_fr,
                            "score_depuis_fr": st.session_state.score_depuis_fr,
                            "total_depuis_fr": st.session_state.total_depuis_fr,
                            "erreurs_commises": st.session_state.erreurs_commises
                        }
                        sauvegarder_partie(user_id, liste_id, etat_a_sauver)

                        st.rerun()

                    # --- BOUTONS PAUSE ET ABANDON ---
                    st.write("")
                    col_b1, col_b2 = st.columns(2)

                    with col_b1:
                        if st.button("⏸️ Mettre en pause", use_container_width=True, type="secondary"):
                            etat_a_sauver = {
                                "quiz_index": st.session_state.quiz_index,
                                "quiz_mots": st.session_state.quiz_mots,
                                "score_vers_fr": st.session_state.get("score_vers_fr", 0.0),
                                "total_vers_fr": st.session_state.get("total_vers_fr", 0.0),
                                "score_depuis_fr": st.session_state.get("score_depuis_fr", 0.0),
                                "total_depuis_fr": st.session_state.get("total_depuis_fr", 0.0),
                                "erreurs_commises": st.session_state.get("erreurs_commises", [])
                            }
                            
                            sauvegarder_partie(user_id, liste_id, etat_a_sauver)
                            
                            clefs_a_supprimer = [
                                "quiz_mots", "quiz_index", "quiz_liste_id", 
                                "score_vers_fr", "total_vers_fr", 
                                "score_depuis_fr", "total_depuis_fr", "erreurs_commises"
                            ]
                            for clef in clefs_a_supprimer:
                                if clef in st.session_state:
                                    del st.session_state[clef]
                            

                            st.session_state.action = "liste"
                            st.rerun()

                    with col_b2:
                        if st.button("🛑 Abandonner l'entraînement", use_container_width=True, type="secondary"):
                            clefs_a_supprimer = [
                                "quiz_mots", "quiz_index", "quiz_liste_id", 
                                "score_vers_fr", "total_vers_fr", 
                                "score_depuis_fr", "total_depuis_fr", "erreurs_commises"
                            ]
                            for clef in clefs_a_supprimer:
                                if clef in st.session_state:
                                    del st.session_state[clef]

                            st.session_state.action = "liste"
                            supprimer_sauvegarde_partie(liste_id)
                            st.rerun()

            # --- S'IL S'AGIT D'UNE LISTE DE VERBES ---
            else:
                # 1. INITIALISATION DU QUIZ VERBES
                if "quiz_mots" not in st.session_state or st.session_state.get("quiz_liste_id") != liste_id:
                    # On vérifie si une sauvegarde existe en BDD
                    partie_sauvee = charger_partie_sauvegardee(liste_id)

                    if partie_sauvee and "choix_reprise" not in st.session_state:
                        # Demande de confirmation à l'utilisateur
                        st.info("💾 Une sauvegarde d'entraînement existe pour cette liste de verbes.")
                        st.write("")
                        col_c1, col_c2 = st.columns(2)
                        
                        with col_c1:
                            if st.button("▶️ Charger la sauvegarde", type="primary", use_container_width=True):
                                st.session_state.choix_reprise = "charger"
                                st.rerun()

                        with col_c2:
                            if st.button("🔄 Recommencer à zéro", type="secondary", use_container_width=True):
                                supprimer_sauvegarde_partie(liste_id)
                                st.session_state.choix_reprise = "nouveau"
                                st.rerun()

                        st.stop()  # Stoppe l'affichage tant que l'utilisateur n'a pas choisi

                    # Applique le choix fait par l'utilisateur
                    if partie_sauvee and st.session_state.get("choix_reprise") == "charger":
                        st.session_state.quiz_mots = partie_sauvee["quiz_mots"]
                        st.session_state.quiz_index = partie_sauvee["quiz_index"]
                        st.session_state.score_verbes = partie_sauvee["score_verbes"]
                        st.session_state.total_verbes = partie_sauvee["total_verbes"]
                        st.session_state.erreurs_compteur = partie_sauvee["erreurs_compteur"]
                        st.session_state.erreurs_verbes_detail = partie_sauvee["erreurs_verbes_detail"]
                        st.session_state.quiz_liste_id = liste_id
                        st.toast("⚡ Sauvegarde chargée !")

                    else:
                        mots_bruts = recuperer_mots_liste(liste_id)
                        st.session_state.quiz_mots = preparer_quiz_verbes_aleatoire(mots_bruts)
                        st.session_state.quiz_index = 0
                        st.session_state.score_verbes = 0.0
                        st.session_state.total_verbes = float(len(st.session_state.quiz_mots))
                        st.session_state.erreurs_compteur = {}
                        st.session_state.erreurs_verbes_detail = []
                        st.session_state.quiz_liste_id = liste_id

                    # Nettoyage de la variable de choix temporaire
                    if "choix_reprise" in st.session_state:
                        del st.session_state.choix_reprise

                questions = st.session_state.quiz_mots
                index = st.session_state.quiz_index

                # 2. VUE FINALE : BILAN ET SAUVEGARDE
                if index >= len(questions):
                    s_v = st.session_state.score_verbes
                    t_v = st.session_state.total_verbes

                    # Sauvegarde des erreurs en session
                    st.session_state[f"erreurs_liste_{liste_id}"] = st.session_state.erreurs_compteur

                    # Enregistrement du meilleur score
                    enregistrer_meilleur_score(user_id, liste_id, s_v, t_v, 0, 0)

                    # Suppression de la partie sauvegardée
                    supprimer_sauvegarde_partie(liste_id)

                    st.write("### 📊 Tes résultats :")
                    st.metric(label="⚡ Score global Verbes", value=f"{s_v:g} / {t_v:g}")

                    # --- RECAPITULATIF DES ERREURS POUR VERBES ---
                    err_details = st.session_state.get("erreurs_verbes_detail", [])
                    st.divider()

                    if err_details:
                        st.write("### ❌ Récapitulatif des erreurs commises")
                        st.caption("Voici les formes sur lesquelles tu t'es trompé(e) :")
                        st.write("")

                        col_v, col_f, col_rep, col_att = st.columns([2, 2, 2, 2])
                        col_v.markdown("<u>**Infinitif :**</u>", unsafe_allow_html=True)
                        col_f.markdown("<u>**Forme demandée :**</u>", unsafe_allow_html=True)
                        col_rep.markdown("<u>**Ta réponse :**</u>", unsafe_allow_html=True)
                        col_att.markdown("<u>**Réponse attendue :**</u>", unsafe_allow_html=True)

                        for err in err_details:
                            c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                            c1.markdown(f"**{err['verbe']}**")
                            c2.markdown(err["forme"])
                            c3.markdown(f"<span style='color:red;'>{err['rep_user'] if err['rep_user'] else '(vide)'}</span>", unsafe_allow_html=True)
                            c4.markdown(f"🟢 `{err['rep_attendue']}`")
                    else:
                        st.balloons()
                        st.info("⭐ Félicitations ! Un sans-faute parfait sur les verbes !")

                    ligne_epaisse()
                    st.write("")
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("🔙 Retour aux listes", type="primary", use_container_width=True):
                            del st.session_state.quiz_mots
                            st.session_state.action = "liste"
                            st.rerun()
                    with col_b2:
                        if st.button("🔄 Recommencer", use_container_width=True):
                            del st.session_state.quiz_mots
                            st.rerun()
                    

                # 3. VUE DE QUESTION EN COURS
                else:
                    q = questions[index]
                    st.progress(index / len(questions), text=f"Question {index + 1} / {len(questions)}")

                    with st.form(key=f"form_verbe_{index}"):
                        reponses_user = {}
                        
                        ordre_formes = [
                            (1, "Infinitif"),
                            (2, "Présent"),
                            (3, "Prétérit"),
                            (4, "Participe Passé"),
                            (5, "Traduction")
                        ]
                        
                        for idx_t, nom_f in ordre_formes:
                            if idx_t in [att["idx_tuple"] for att in q["attentes"]]:
                                reponses_user[idx_t] = st.text_input(f"{nom_f} :", key=f"inp_{index}_{idx_t}")
                            else:
                                st.text_input(f"{nom_f} (donné) :", value=q["valeur_fournie"], disabled=True, key=f"dis_{index}_{idx_t}")

                        st.write("")
                        valider = st.form_submit_button("Suivant 🚀", type="primary")

                    if valider:
                        pts_gagnes = 0.0
                        id_mot = q["id_mot"]

                        if id_mot not in st.session_state.erreurs_compteur:
                            st.session_state.erreurs_compteur[id_mot] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

                        for att in q["attentes"]:
                            idx_t = att["idx_tuple"]
                            rep_u = reponses_user.get(idx_t, "").strip()
                            rep_att = att["reponse_attendue"].strip()

                            if rep_u.lower() == rep_att.lower():
                                pts_gagnes += 0.25
                            else:
                                st.session_state.erreurs_compteur[id_mot][idx_t] += 1
                                # Détail de l'erreur pour le bilan final
                                st.session_state.erreurs_verbes_detail.append({
                                    "verbe": q["verbe_tuple"][1],
                                    "forme": att["nom"],
                                    "rep_user": rep_u,
                                    "rep_attendue": rep_att
                                })

                        st.session_state.score_verbes += pts_gagnes

                        st.session_state.quiz_index += 1

                        # 💾 SAUVEGARDE AUTOMATIQUE À CHAQUE QUESTION VALIDÉE
                        etat_a_sauver = {
                            "quiz_index": st.session_state.get("quiz_index", 0),
                            "quiz_mots": st.session_state.get("quiz_mots", []),
                            "score_verbes": st.session_state.get("score_verbes", 0.0),
                            "total_verbes": st.session_state.get("total_verbes", 0.0),
                            "erreurs_compteur": st.session_state.get("erreurs_compteur", {}),
                            "erreurs_verbes_detail": st.session_state.get("erreurs_verbes_detail", [])
                        }
                        sauvegarder_partie(user_id, liste_id, etat_a_sauver)

                        st.rerun()

                    st.write("")
                    col_b1, col_b2 = st.columns(2)

                    with col_b1:
                        if st.button("⏸️ Mettre en pause", use_container_width=True, type="secondary"):
                            # 1. On prépare le dictionnaire des données de la session
                            etat_a_sauver = {
                                "quiz_index": st.session_state.quiz_index,
                                "quiz_mots": st.session_state.quiz_mots,
                                "score_verbes": st.session_state.get("score_verbes", 0.0),
                                "total_verbes": st.session_state.get("total_verbes", 0.0),
                                "erreurs_compteur": st.session_state.get("erreurs_compteur", {}),
                                "erreurs_verbes_detail": st.session_state.get("erreurs_verbes_detail", [])
                            }
                            
                            # 2. Sauvegarde en BDD
                            sauvegarder_partie(user_id, liste_id, etat_a_sauver)
                            
                            # 3. Nettoyage de la session active
                            clefs_a_supprimer = ["quiz_mots", "quiz_index", "quiz_liste_id", "score_verbes", "total_verbes", "erreurs_compteur", "erreurs_verbes_detail"]
                            for clef in clefs_a_supprimer:
                                if clef in st.session_state:
                                    del st.session_state[clef]
                            
                            st.session_state.action = "liste"
                            st.rerun()

                    with col_b2:
                        if st.button("🛑 Abandonner l'entraînement", use_container_width=True, type="secondary"):
                            clefs_a_supprimer = ["quiz_mots", "quiz_index", "quiz_liste_id", "score_verbes", "total_verbes", "erreurs_compteur", "erreurs_verbes_detail"]
                            for clef in clefs_a_supprimer:
                                if clef in st.session_state:
                                    del st.session_state[clef]

                            st.session_state.action = "liste"
                            supprimer_sauvegarde_partie(liste_id)
                            st.rerun()

        # CAS I : VUE PARTAGER UNE LISTE (🔗)
        elif st.session_state.action == "partager":
            liste_id = st.session_state.liste_active_id
            st.subheader("🔗 Partager la liste")
            
            tab_id, tab_direct = st.tabs(["📋 Obtenir l'ID de la liste", "👤 Envoyer à un ami"])
            
            with tab_id:
                st.write("Donne cet **ID de liste** à ton ami(e) pour qu'il/elle puisse l'importer de son côté :")
                st.code(str(liste_id), language="text")
            
            with tab_direct:
                st.write("Saisis l'**ID de ton ami(e)** pour lui envoyer une copie directement dans son compte :")
                id_ami = st.text_input("ID de l'utilisateur destinataire :", placeholder="Ex: 5")
                
                if st.button("📤 Envoyer la liste", type="primary", use_container_width=True):
                    if id_ami.isdigit():
                        succes, msg = partager_liste_a_utilisateur(liste_id, int(id_ami))
                        if succes:
                            st.session_state.action = "liste"
                            st.session_state.liste_active_id = None
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Veuillez entrer un ID d'utilisateur valide.")

            ligne_epaisse()
            if st.button("🔙 Retour", use_container_width=True):
                st.session_state.action = "liste"
                st.session_state.liste_active_id = None
                st.rerun()

        # CAS J : CONFIRMATION DE SUPPRESSION (🗑️)
        elif st.session_state.action == "supprimer":
            liste_id = st.session_state.liste_active_id
            
            listes_user = recuperer_listes_utilisateur(user_id)
            nom_actuel = next((nom for lid, nom, _ in listes_user if lid == liste_id), "cette liste")

            st.write("")
            st.warning(f"⚠️ Es-tu sûr de vouloir supprimer la liste **'{nom_actuel}'** ? Cette action est irréversible.")
            st.write("")

            col_non, col_oui = st.columns(2)
            
            with col_non:
                if st.button("❌ Annuler", use_container_width=True):
                    st.session_state.action = "liste"
                    st.session_state.liste_active_id = None
                    st.rerun()

            with col_oui:
                if st.button("🗑️ Oui, supprimer", type="primary", use_container_width=True):
                    supprimer_liste(liste_id)
                    st.session_state.action = "liste"
                    st.session_state.liste_active_id = None
                    st.rerun()
        
        # CAS K : VUE NORMALE (AFFICHAGE DES LISTES)
        else:
            st.write("")
            col_titre, col_import, col_ajout = st.columns([3, 1, 1])
            with col_titre:
                st.subheader("📋 Mes listes")

            with col_import:
                if st.button("📥", use_container_width=True, help="Importer une liste"):
                    st.session_state.action = "importer"
                    st.rerun()
            
            with col_ajout:
                if st.button("➕", use_container_width=True, help="Créer une nouvelle liste"):
                    st.session_state.action = "creer"
                    st.session_state.nb_lignes_mots = 2
                    st.rerun()

            ligne_epaisse()

            listes = recuperer_listes_utilisateur(user_id)

            if not listes:
                st.info("Tu n'as aucune liste pour l'instant. Clique sur ➕ pour en créer une !")

            else:
                    for liste_id, nom_liste, type_liste in listes:
                        col_nom, col_voir, col_edit, col_train, col_share, col_del = st.columns([3, 1, 1, 1, 1, 1])
                        
                        with col_nom:
                            if type_liste == "verbe":
                                st.markdown(f"<h3 style='color: #8A2BE2; margin:0;'>⚡ {nom_liste} <span style='font-size:12px; background-color:#8A2BE2; color:white; padding:2px 8px; border-radius:10px;'>VERBES</span></h3>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<h3 style='color: #1E90FF; margin:0;'>📖 {nom_liste} <span style='font-size:12px; background-color:#1E90FF; color:white; padding:2px 8px; border-radius:10px;'>VOCABULAIRE</span></h3>", unsafe_allow_html=True)

                        with col_voir:
                            st.write("")
                            if st.button("👁️", key=f"voir_{liste_id}", help="Voir la liste"):
                                st.session_state.action = "voir"
                                st.session_state.liste_active_id = liste_id
                                st.rerun()

                        with col_edit:
                            st.write("")
                            if st.button("✏️", key=f"edit_{liste_id}", help="Éditer la liste"):
                                st.session_state.action = "editer"
                                st.session_state.liste_active_id = liste_id
                                st.session_state.nb_lignes_mots = 2
                                st.rerun()

                        with col_share:
                            st.write("")
                            if st.button("🔗", key=f"share_{liste_id}", help="Partager cette liste"):
                                st.session_state.action = "partager"
                                st.session_state.liste_active_id = liste_id
                                st.rerun()

                        with col_train:
                            st.write("")
                            if st.button("🎯", key=f"train_{liste_id}", help="S'entraîner sur cette liste"):
                                st.session_state.action = "entrainer"
                                st.session_state.liste_active_id = liste_id
                                st.rerun()

                        with col_del:
                            st.write("")
                            if st.button("🗑️", key=f"del_{liste_id}", help="Supprimer la liste"):
                                st.session_state.action = "supprimer"
                                st.session_state.liste_active_id = liste_id
                                st.rerun()

                        # --- AFFICHAGE DU MEILLEUR SCORE CENTRÉ AVEC INFOBULLES ---
                        score_record = recuperer_score_liste(user_id, liste_id)

                        st.write("")
                        if score_record:
                            s_v, t_v, s_d, t_d = score_record
                            
                            if type_liste == "verbe":
                                partie_verbe = f"<span title='Score global aux verbes'>⚡ <code>{s_v:g}/{t_v:g}</code></span>"
                                texte_score = f"🏆 <b>Meilleur score :</b> {partie_verbe}"

                            else:
                                partie_globe = f"<span title='Traduction vers la langue étrangère'>🌐 <code>{s_v:g}/{t_v:g}</code></span>"
                                partie_drapeau = f"<span title='Traduction vers le français'>🇫🇷 <code>{s_d:g}/{t_d:g}</code></span>"

                                texte_score = f"🏆 <b>Meilleur score :</b> {partie_globe} &nbsp;|&nbsp; {partie_drapeau}"

                        else:
                            texte_score = "🏆 <b>Meilleur score :</b> Pas encore d'essai"

                        # Affichage avec taille personnalisable (font-size)
                        st.markdown(f"<div style='text-align: left; color: gray; font-size: 1rem;'>{texte_score}</div>", unsafe_allow_html=True)

                        st.divider()


# On utilise un expander pour garder l'interface propre
#with st.expander("🛠️ Console de débogage (Session State)", expanded=False):
#    st.caption("Affiche en temps réel le contenu de st.session_state")
#    
#    # Affiche l'état complet sous forme JSON/dictionnaire lisible
#    st.json(dict(st.session_state))
#    
#    # Optionnel : Bouton pour vider la session et recommencer à zéro
#    if st.button("🗑️ Vider le session_state"):
#        for key in list(st.session_state.keys()):
#            del st.session_state[key]
#        st.rerun()
