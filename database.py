from datetime import datetime, timedelta
import streamlit as st
import sqlite3
import bcrypt
import libsql
import json

import time
import functools
def mesurer_temps(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t_debut = time.time()
        resultat = func(*args, **kwargs)
        t_fin = time.time()
        duree = t_fin - t_debut
        st.write(f"⏱️ **{func.__name__}** exécutée en `{duree:.4f}` s")
        return resultat
    return wrapper

# --- BASE DE DONNÉES ---
@mesurer_temps
def get_connection():
    return libsql.connect(str(st.secrets["TURSO_DATABASE_URL"]),auth_token=str(st.secrets["TURSO_AUTH_TOKEN"]))

@st.cache_resource
@mesurer_temps
def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Table Utilisateurs
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            admin INTEGER NOT NULL DEFAULT 0)
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

    # 6. Table des erreurs enregistrées par liste et utilisateur
    c.execute('''
        CREATE TABLE IF NOT EXISTS erreurs_listes (
            user_id INTEGER NOT NULL,
            liste_id INTEGER NOT NULL,
            erreurs_json TEXT NOT NULL,
            PRIMARY KEY (user_id, liste_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (liste_id) REFERENCES listes (id) ON DELETE CASCADE
        )
    ''')

    # 7. Table des sauvegardes BDD
    c.execute('''
        CREATE TABLE IF NOT EXISTS sauvegardes_bdd (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_sauvegarde TEXT NOT NULL,
            contenu_json TEXT NOT NULL
        )
    ''')

    conn.commit()

@mesurer_temps
def reinitialiser_toutes_les_bdd():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS listes")
    c.execute("DROP TABLE IF EXISTS mots")
    c.execute("DROP TABLE IF EXISTS scores")
    c.execute("DROP TABLE IF EXISTS sauvegardes_quiz")
    c.execute("DROP TABLE IF EXISTS erreurs_listes")
    conn.commit()


# --- Utilisateurs ---
@mesurer_temps
def inscrire_utilisateur(username, password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    try:
        conn = get_connection()
        c = conn.cursor()

        c.execute("""
            INSERT INTO users (username, password) 
            VALUES (?, ?)
        """, (username, hashed_password))

        conn.commit()

        return True
    
    except sqlite3.IntegrityError:
        return False

@mesurer_temps
def verifier_connexion(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, password, admin FROM users WHERE username = ?", (username,))
    user = c.fetchone()

    if user:
        user_id, db_username, db_password, admin = user

        if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
            return True, db_username, user_id, admin
        
    return False, None, None, None

@mesurer_temps
def authentifier_connexion(username, password) :
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = c.fetchone()

    if user:
        db_password = user[0]

        if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
            return True
        
    return False

@mesurer_temps
def modifier_profil_bdd(user_id, nouveau_username, nouveau_password):
    conn = get_connection()
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

        return True
        
    except sqlite3.IntegrityError:
        return False

@mesurer_temps
def supprimer_compte(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()


# --- LISTES ---
@mesurer_temps
def recuperer_listes_utilisateur(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nom_liste, type_liste FROM listes WHERE user_id = ?", (user_id,))
    listes = c.fetchall()    
    return listes

@mesurer_temps
def ajouter_liste(user_id, nom_liste, type_liste="vocabulaire"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO listes (user_id, nom_liste, type_liste) VALUES (?, ?, ?)", 
              (user_id, nom_liste, type_liste))
    conn.commit()

@mesurer_temps
def ajouter_élément_liste(liste_id, inf_ou_mot, present="", preterit="", pp="", traduction=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO mots (liste_id, mot_original, present, preterit, participe_passe, traduction) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (liste_id, inf_ou_mot.strip(), present.strip(), preterit.strip(), pp.strip(), traduction.strip()))
    conn.commit()

@mesurer_temps
def recuperer_mots_liste(liste_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, mot_original, present, preterit, participe_passe, traduction FROM mots WHERE liste_id = ?", (liste_id,))
    mots = c.fetchall()
    return mots

@mesurer_temps
def supprimer_liste(liste_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("DELETE FROM listes WHERE id = ?", (liste_id,))
    conn.commit()

@mesurer_temps
def renommer_liste(liste_id, nouveau_nom):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE listes SET nom_liste = ? WHERE id = ?", (nouveau_nom, liste_id))
    conn.commit()

@mesurer_temps
def remplacer_mots_liste(liste_id, nouveaux_mots, type_liste):
    """
    Return des code d'erreur. Si pas d'erreur, return True :
    - True : liste créée
    - 0 : article trop long (voc)
    - 1 : mot inexistant ou trop long (voc)
    - 2 : traduction inexistante ou trop long (voc)
    - 3 : forme manquante ou trop longue (verbe)
    """

    # 1. Analyse et validation préalable du fichier
    is_voc = True if type_liste == "vocabulaire" else False
    last_ligne = list(nouveaux_mots)[-1]

    toutes_lignes_visibles_remplies = True

    if is_voc :
        if len(last_ligne) >=3 :
            if bool(str(last_ligne[0]).strip()) or (bool(str(last_ligne[1]).strip()) != bool(str(last_ligne[2]).strip())) :
                toutes_lignes_visibles_remplies = False

    else :
        for case in last_ligne :
            if case.strip() :
                toutes_lignes_visibles_remplies = False

    for ligne in list(nouveaux_mots)[:-1] if toutes_lignes_visibles_remplies else nouveaux_mots:
        if is_voc :
            art, mot, trad = ligne

            if len(art.strip()) > 7 :
                return 0

            if not(0 < len(mot.strip()) <= 30) :
                return 1

            if not(0 < len(trad.strip()) <= 30) :
                return 2

        else :
            inf, pres, pret, pp, trad = ligne
            variables = [inf, pres, pret, pp, trad]

            if any(not (0 < len(v.strip()) <= 30) for v in variables):
                return 3


    # 2. Insertion en BDD uniquement si le format est correct
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM mots WHERE liste_id = ?", (liste_id,))
    
    for item in nouveaux_mots:
        if type_liste == "verbe":
            inf, pres, pret, pp, trad = item
            if inf.strip() and pres.strip() and pret.strip() and pp.strip() and trad.strip():
                c.execute("""
                    INSERT INTO mots (liste_id, mot_original, present, preterit, participe_passe, traduction) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (liste_id, inf.strip(), pres.strip(), pret.strip(), pp.strip(), trad.strip()))

        else:
            art, mot, trad = item

            if mot.strip() and trad.strip():
                mot_strip = mot.strip()
                art_strip = art.strip()

                mot_complet = f"{art_strip} {mot_strip}" if art_strip else "!" + mot_strip if " " in mot_strip and not mot_strip.startswith("!") else mot_strip

                c.execute("""
                    INSERT INTO mots (liste_id, mot_original, traduction) 
                    VALUES (?, ?, ?)
                """, (liste_id, mot_complet, trad.strip()))
                
    conn.commit()

    return True

@mesurer_temps
def importer_liste_par_id(liste_id_origine, nouvel_user_id):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT nom_liste, type_liste FROM listes WHERE id = ?", (liste_id_origine,))
    res = c.fetchone()
    
    if not res:
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
    return True, f"Liste '{nouveau_nom}' importée avec succès !"

@mesurer_temps
def partager_liste_a_utilisateur(liste_id_origine, ami_user_id):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT id, username FROM users WHERE id = ?", (ami_user_id,))
    ami = c.fetchone()
    if not ami:
        return False, "Aucun utilisateur trouvé avec cet ID."
    
    c.execute("SELECT nom_liste, type_liste FROM listes WHERE id = ?", (liste_id_origine,))
    res = c.fetchone()
    if not res:
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
    return True, f"Liste partagée avec succès à {ami[1]} !"

@mesurer_temps
def importer_liste_depuis_fichier(user_id, nom_liste, type_liste, contenu_fichier):
    """
    Return des code d'erreur. Si pas d'erreur, return True :
    - True : liste créée
    - 0 : mauvais séparateur (voc et verbes)
    - 1 : article trop long (voc)
    - 2 : mot inexistant ou trop long (voc)
    - 3 : traduction inexistante ou trop long (voc)
    - 4 : forme manquante ou trop longue (verbe)
    """

    lignes = contenu_fichier.splitlines()
    mots_a_inserer = []
    is_voc = True if type_liste == "vocabulaire" else False
    
    # 1. Analyse et validation préalable du fichier
    for num_ligne, ligne in enumerate(lignes, 1) :
        ligne = ligne.strip()
        if not ligne:
            continue
        
        parts = [p.strip() for p in ligne.split(",")]
        
        # Vérification stricte : exactement 2 colonnes pour vocabulaire, 5 pour verbes t si les mot font la bonne taille
        if is_voc and len(parts) == 2:
            mots_a_inserer.append((parts[0], "", "", "", parts[1]))

            if not(0 < len(mots_a_inserer[-1][4].strip()) <= 30) :
                return 3, num_ligne 


            colonne_mot = mots_a_inserer[-1][0].strip()
            if " " in colonne_mot and "!" not in colonne_mot[0] :
                art, mot = colonne_mot.split(" ", 1)
            else:
                art, mot = "", colonne_mot

            if len(art.strip()) > 7 :
                return 1, num_ligne

            if not(0 < len(mot.strip()) <= 30) :
                return 2, num_ligne 
            
        elif not is_voc and len(parts) == 5:
            mots_a_inserer.append((parts[0], parts[1], parts[2], parts[3], parts[4]))

            for x in mots_a_inserer[-1] :
                if not(0 < len(x.strip()) <= 30) :
                    return 4, num_ligne

    # 2. Si aucun mot n'est valide (mauvais format/séparateur), on n'insère rien en BDD
    if not mots_a_inserer:
        return 0, None
    
    # 3. Insertion en BDD uniquement si le format est correct
    conn = get_connection()
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
    
    return True, None

@mesurer_temps
def obtenir_type_liste(liste_id):
    """
    Retourne le type d'une liste ('vocabulaire', 'verbes', etc.) à partir de son ID.
    """

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT type_liste FROM listes WHERE id = ?", (liste_id,))
    resultat = c.fetchone()
    
    if resultat:
        return resultat[0]
    return None

@mesurer_temps
def sauvegarder_erreurs(user_id, liste_id, dictionnaire_erreurs):
    conn = get_connection()
    c = conn.cursor()
    
    # On transforme le dictionnaire en chaîne de texte JSON
    erreurs_texte = json.dumps(dictionnaire_erreurs)
    
    c.execute('''
        INSERT INTO erreurs_listes (user_id, liste_id, erreurs_json)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, liste_id) DO UPDATE SET erreurs_json = excluded.erreurs_json
    ''', (user_id, liste_id, erreurs_texte))
    
    conn.commit()

@mesurer_temps
def charger_erreurs(user_id, liste_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT erreurs_json FROM erreurs_listes WHERE user_id = ? AND liste_id = ?", (user_id, liste_id))
    row = c.fetchone()
    
    if row and row[0]:
        data = json.loads(row[0])
        res = {}

        if obtenir_type_liste(liste_id) == "verbe" :
            for k, v in data.items():
                id_mot = int(k)
                if isinstance(v, dict):
                    # Convertit aussi les clés internes ("1", "2", etc.) en entiers (1, 2, etc.)
                    res[id_mot] = {int(sub_k): sub_v for sub_k, sub_v in v.items()}
                else:
                    res[id_mot] = v

        else :
            for k, v in data.items():
                res[int(k)] = v
                
        return res
    return {}


# --- GESTION DU MEILLEUR SCORE ---
@mesurer_temps
def enregistrer_meilleur_score(user_id, liste_id, s_vers, t_vers, s_depuis, t_depuis):
    conn = get_connection()
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

@mesurer_temps
def recuperer_score_liste(user_id, liste_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT score_vers_fr, total_vers_fr, score_depuis_fr, total_depuis_fr 
        FROM scores 
        WHERE user_id = ? AND liste_id = ?
    """, (user_id, liste_id))
    score = c.fetchone()
    return score

@mesurer_temps
def reinitialiser_score_liste(user_id, liste_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM scores WHERE user_id = ? AND liste_id = ?", (user_id, liste_id))
    conn.commit()


# --- Bouton pause ---
@mesurer_temps
def sauvegarder_partie(user_id, liste_id, donnees_dict):
    """Enregistre ou met à jour la progression d'un quiz sous forme de texte JSON."""
    conn = get_connection()
    c = conn.cursor()
    donnees_json = json.dumps(donnees_dict)
    c.execute('''
        INSERT INTO sauvegardes_quiz (user_id, liste_id, donnees_json)
        VALUES (?, ?, ?)
        ON CONFLICT(liste_id) DO UPDATE SET donnees_json = excluded.donnees_json
    ''', (user_id, liste_id, donnees_json))
    conn.commit()

@mesurer_temps
def charger_partie_sauvegardee(liste_id):
    """Récupère les données sauvegardées d'un quiz pour une liste donnée."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT donnees_json FROM sauvegardes_quiz WHERE liste_id = ?", (liste_id,))
    row = c.fetchone()

    if row:
        return json.loads(row[0])
    return None

@mesurer_temps
def supprimer_sauvegarde_partie(liste_id):
    """Supprime la sauvegarde d'un quiz (quand le quiz est terminé)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sauvegardes_quiz WHERE liste_id = ?", (liste_id,))
    conn.commit()


# --- Sauvegarde ---
@mesurer_temps
def creer_sauvegarde_interne():
    """Exporte l'intégralité des tables dans une table d'archivage."""
    conn = get_connection()
    c = conn.cursor()
    
    # 2. Récupération des données de chaque table
    tables = ["users", "listes", "mots", "scores", "sauvegardes_quiz", "erreurs_listes"]
    export_donnees = {}
    
    for table in tables:
        c.execute(f"SELECT * FROM {table}")
        export_donnees[table] = c.fetchall()
        
    # 3. Enregistrement de l'instantané avec la date courante
    date_actuelle = datetime.now().isoformat()
    json_donnees = json.dumps(export_donnees)
    
    c.execute('''
        INSERT INTO sauvegardes_bdd (date_sauvegarde, contenu_json)
        VALUES (?, ?)
    ''', (date_actuelle, json_donnees))
    
    conn.commit()

@st.cache_data(ttl=86400)
@mesurer_temps
def verifier_et_sauvegarder_hebdo():
    """Déclenche la sauvegarde automatique si la dernière date de plus de 7 jours."""
    conn = get_connection()
    c = conn.cursor()
    
    # Vérification de l'existence de la table et de la dernière date
    try:
        c.execute("SELECT date_sauvegarde FROM sauvegardes_bdd ORDER BY id DESC LIMIT 1")
        resultat = c.fetchone()
    except Exception:
        resultat = None
    
    doit_sauvegarder = False
    
    if not resultat:
        doit_sauvegarder = True
    else:
        derniere_date = datetime.fromisoformat(resultat[0])
        # Compare si 7 jours ou plus se sont écoulés
        if datetime.now() - derniere_date >= timedelta(days=7):
            doit_sauvegarder = True
            
    if doit_sauvegarder:
        creer_sauvegarde_interne()
