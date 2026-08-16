import time

from collections import Counter
import streamlit as st
import random

st.write(f"\n--- Nouveau clic / Rechargement : {time.strftime('%H:%M:%S')} ---")

from database import *
st.write(f"\n--- Nouveau clic / Rechargement : {time.strftime('%H:%M:%S')} ---")

from quiz_logic import *
st.write(f"\n--- Nouveau clic / Rechargement : {time.strftime('%H:%M:%S')} ---")

from views import *
st.write(f"\n--- Nouveau clic / Rechargement : {time.strftime('%H:%M:%S')} ---")

st.set_page_config(page_title="Réviseur", layout="wide")

init_db()
st.write(f"\n--- Nouveau clic / Rechargement : {time.strftime('%H:%M:%S')} ---")

verifier_et_sauvegarder_hebdo()
st.write(f"\n--- Nouveau clic / Rechargement : {time.strftime('%H:%M:%S')} ---")

# --- APPARENCE ---
# Centrer les éléments
st.markdown(
    """
    <style>
    /* Centrer les en-têtes de tous les st.tabs de l'application */
    div[data-baseweb="tab-list"] {
        justify-content: center;
    }

    /* 2. Centrer tous les titres (st.title, st.header, st.subheader) */
    h1, h2, h3 {
        text-align: center;
    }
    
    .centre {
    text-align: center;
    align-items: center;
    justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- INITIALISATION DU STATE ---
if "etat" not in st.session_state:
    st.session_state.etat = "none"

if "user" not in st.session_state:
    st.session_state.user = None

if "toggle_focus" not in st.session_state:
    st.session_state.toggle_focus = False


# --- BARRE DE NAVIGATION ---
if st.session_state.etat == "connecte" : 
    if st.session_state.get("user", ("", "", False))[2] :
        col_title, col_admin, col_compte, col_signup, col_action = st.columns([4, 2, 2, 2, 2])

        with col_admin :
            if st.button("Admin", use_container_width=True):
                pass

    else :
        col_title, col_compte, col_signup, col_action = st.columns([4, 2, 2, 2])

    if st.session_state.get("action", None) :
        with col_compte : 
            if st.button("Profil", use_container_width=True):
                st.session_state.action = "compte"
                st.session_state.nb_lignes_mots = 2
                st.session_state.liste_active_id = None
                st.session_state.pop("mots_temp", None)
                st.session_state.pop("id_a_suppr", None)
                st.session_state.pop("liste_valide", None)
                st.rerun()

        with col_signup:
            if st.button("Déconnexion", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key != "toggle_focus" :
                        del st.session_state[key]
                st.rerun()

        with col_action:
                if st.button("🗑️ Supprimer mon compte", type="secondary", use_container_width=True):
                    st.session_state.action = "supprimer"
                    st.session_state.action_suppr = "compte"
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

    if st.button("📘 Réviseur", type="tertiary"):
        # 1. Si déconnecté
        if st.session_state.get("etat") in ["nouveau", "connect", "none", "None"]:
            st.session_state.etat = "none"

        # 2. Si connecté et en plein entraînement
        elif st.session_state.get("action") == "entrainer" or st.session_state.get("action") == "err_entrainer" :
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
                        "erreurs_commises": st.session_state.get("erreurs_commises", []),
                        "type" : "normal" if st.session_state.get("action") == "entrainer" else "erreur"
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
                        "erreurs_verbes_detail": st.session_state.get("erreurs_verbes_detail", []),
                        "type" : "normal" if st.session_state.get("action") == "entrainer" else "erreur"
                    }

                    sauvegarder_partie(user_id, liste_id, etat_a_sauver)
                    
                    clefs_a_supprimer = ["quiz_mots", "quiz_index", "quiz_liste_id", "score_verbes", "total_verbes", "erreurs_compteur", "erreurs_verbes_detail"]
                    for clef in clefs_a_supprimer:
                        if clef in st.session_state:
                            st.session_state.pop(clef, None)

            st.session_state.action = "liste"

        # 3. Si connecté sur une autre vue
        else:
            st.session_state.action = "liste"
            st.session_state.nb_lignes_mots = 2
            st.session_state.liste_active_id = None
            st.session_state.pop("mots_temp", None)
            st.session_state.pop("id_a_suppr", None)
            st.session_state.pop("liste_valide", None)

        st.rerun()
            
    if st.session_state.etat == "connecte":
        username, user_id, admin = st.session_state.user
        st.caption(f"Connecté en tant que **{username}** (Ton ID : `{user_id}`)")
    
ligne_epaisse()


# --- AFFICHAGE SELON L'ÉTAT ---
# 1. ÉTAT : NOUVEAU (Inscription)
if st.session_state.etat == "nouveau":
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

# 2. ÉTAT : CONNECT (Connexion)
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
                succes, username, user_id, admin = verifier_connexion(nom, mot_de_passe)
                if succes :
                    st.session_state.user = (username, user_id, admin)
                    st.session_state.etat = "connecte"
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect.")


# --- 3. ÉTAT : NONE ou CONNECTE (AIDE DU SITE) ---
elif st.session_state.etat == "none" or (st.session_state.etat == "connecte" and st.session_state.get("action") == "infos") :
    _, col_texte, _ = st.columns([1, 3, 1])

    with col_texte :
        st.markdown("<h1 style='text-align: center;'>ℹ️ Centre d'aide - Le Réviseur</h1>", unsafe_allow_html=True)
        
        st.divider()

        # --- PRÉSENTATION GÉNÉRALE ---
        st.info("**Le Réviseur** est une plateforme intuitive conçue pour vous accompagner dans l'apprentissage et la mémorisation de votre vocabulaire et de vos verbes d'une langue étrangère. Créez vos listes sur-mesure, entraînez-vous et suivez vos progrès !")

        st.write("")

        # --- SOMMAIRE AVEC ST.TABS ---
        tab_compte, tab_listes, tab_social, tab_revisions, tab_astuces = st.tabs(["🛠️ Gérer mon compte", "📁 Créer et gérer mes listes", "🔗 Social", "🎯 Entraînement & Révisions", "💡 Astuces & Syntaxe"])

        # 1. Gérer son compte
        with tab_compte : 
            st.header("🛠️ Gérer Mon compte")

            st.write("")

            st.write("""
<ul style="list-style-type: '➢ ';">
    <li><u><i><b>Identifiants & Connexion :</b></i></u> La création de votre compte ainsi que la connexion s'effectuent via votre pseudo et votre mot de passe. Par conséquent, si vous perdez votre mot de passe, il sera <u><i><b>impossible</b></i></u> de récupérer votre compte !<br><i>Conseil :</i> En cas de perte de votre mot de passe, conservez l'ID de vos listes afin de pouvoir les importer sur un nouveau compte (voir l'onglet ...).</li><br>
    <li><u><i><b>Pseudo sensible à la case :</b></i></u> le pseudo \"Jean\" est différent du pseudo \"jean\". Lorsque vous renseignez votre pseudo, respectez les majuscules et les minuscules !</li><br>
    <li><u><i><b>Modification du compte :</b></i></u> Une fois connecté, vous pouvez modifier les informations de votre compte depuis la page <b>\"Profil\"</b> accessible via le bouton situé en haut dans la barre de navigation. Votre mot de passe vous sera demandé par sécurité.</li><br>
    <li><u><i><b>ID unique du compte :</b></i></u> Chaque compte possède un ID unique, affiché en haut à gauche du site lorsque vous êtes connecté. Cet identifiant vous sera utile pour certaines fonctionnalités avancées (voir onglet).</li><br>
    <li><u><i><b>Suppression du compte :</b></i></u> Vous pouvez supprimer définitivement votre compte à tout moment via le bouton <b>\"Supprimer mon compte\"</b> situé en haut dans la barre de navigation.<br>⚠️ </i></b>Attention : cette action est <u>irréversible</u> et supprimera <u>l'intégralité</u> de vos listes enregistrées.</b></i></li>
</ul>""",  unsafe_allow_html=True)

        # 2. CRÉER ET GÉRER SES LISTES
        with tab_listes:
            st.header("📁 Créer et gérer Mes listes")

            st.write("")
            
            st.markdown("""
<ul style="list-style-type: none;">
    <li style="list-style-type: none; padding-left: 0; margin-left: 0;">➢ Le site vous permet de créer deux types de listes selon vos besoins :</li>
    <li>
        <ul style="list-style-type: '❖ ';">
            <li><b>Listes de Vocabulaire classique :</b> Pour apprendre des mots, des expressions ou des tournures de phrases...</li>
            <li><b>Listes de Verbes :</b> Spécialement conçues pour travailler toutes les formes des verbes : <i>Infinitif, Présent, Prétérit, Participe Passé, Traduction</i>. Idéal pour apprendre des verbes irrégulier par exemple !</li>
        </ul>
    </li>
</ul>


<ul style="list-style-type: none;">
    <li style="list-style-type: none; padding-left: 0; margin-left: 0;">➢ 🛠️ Comment créer une liste ?</li>
    <li>
        <ol>
            <li>Allez dans le menu d'édition de votre liste situé tout en haut à gauche de la page d'accueil (cliquez sur le bouton \"➕\").</li>
            <li>Faites votre choix entre vocabulaire et verbes :
                <ul style="list-style-type: '❖ ';">
                    <li>Pour une liste de vocabulaire, vous devez remplir la case \"<b>mot</b>\" et la case \"<b>traduction</b>\". La case article est falcultative, elle sert notament dans les langues où les articles sont important (par exemple en allemand).</li>
                    <li>Pour une liste de verbe, vous devez remplir les 5 cases : <i>Infinitif, Présent, Prétérit, Participe Passé, Traduction</i>.</li>
                </ul>
            </li>
            <li>Appuyez sur \"Enregistrez votre liste\" une fois que vous avez terminé.</li>
        </ol>
    </li>
</ul>


<ul style="list-style-type: none;">
    <li style="list-style-type: none; padding-left: 0; margin-left: 0;">➢ Une fois votre liste créée elle apparait sur la page d'accueil. Vous pouvez alors :</li>
    <li>
        <ol>
            <li>La consulter en appuyant sur le bouton \"👁️\"</li>
            <li>La modifier en appuyant sur le bouton \"✏️\"</li>
            <li>Vous entrainer dessus en appuyant sur le bouton \"🎯\" (voir onglet)</li>
            <li>La partager en appuyant sur le bouton \"🔗\" (voir onglet \"\")</li>
            <li>La supprimer en appuyant sur le bouton \"🗑️\". ⚠️ <strong>Attention : cette action est <u>irréversible</u></li>
        </ol>
    </li>
</ul>


<ul style="list-style-type: none; padding-left: 0; margin-left: 0;">
    <li style="list-style-type: none; padding-left: 0; margin-left: 0;">➢ <b>À savoir</b> :</li>
    <li>
        <ul style="list-style-type: '❖ ';">
            <li>Vous pouvez importer une liste à partir d'une liste déjà existante ou via un fichier .txt (voir onglet )</li>
            <li>Vous pouvez exporter une liste déjà existante en un fichier.txt (voir onglet )</li>
        </ul>
    </li>
</ul>
""", unsafe_allow_html=True)

        # 3. Social
        with tab_social :
            st.header("🔗 Social")

            st.write("")

            st.write("""
<ul style="list-style-type: '➢ ';">
    <li>À votre compte est associé un identifiant unique visible en haut à gauche du site après vous être connecté. Cet id vous servira pour l'option de partage des listes (bouton : \"🔗\").
        <ul style="list-style-type: '❖ ';">
            <li><u><b>Envoyer une liste à un ami :</b></u> vous pouvez partager l'une de vos liste avec une autre personne. Pour ce faire vous aurez besoin de l'id associé à <b>son</b> compte. Une fois la liste envoyé elle apparaitra directement sur le compte de votre ami(e).<br>Si ce dernier modifie ou supprime la liste, cela n'affectera pas votre liste originale.</li>
        </ul>
    </li>
    <br>
    <li>Si vous ne connaissez pas l'id de votre ami(e) ce n'est pas un problème. À chaque liste est associé un autre id unique (à ne pas confondre avec celui de votre compte, celui-ci se trouve dans le menu de partage de la liste (bouton : \"🔗\"), onglet \"📋 Obtenir l'ID de la liste\".
        <ul style="list-style-type: '❖ ';">
            <li><u><b>Importer une liste depuis un id :</b></u> rendez-vous dans le menu d'import (bouton : \"📥\", en haut à droite de la page d'accueil). Il ne vous reste plus qu'à entrer l'id de la liste et celle-ci apparaitra directement sur votre page d'accueil.<br><i>Astuce :</i> vous pouvez donc envoyer l'id de la liste que vous voulez partager à votre ami(e) pour qu'il l'importe directement depuis son compte.</li>
        </ul>
    </li>
</ul>
""", unsafe_allow_html=True)

        # 4. ENTRAÎNEMENT & RÉVISIONS
        with tab_revisions:
            st.header("🎯 Entraînement & Révisions")

            st.write("")

            st.markdown("<p style='text-align: center;'>Une fois votre liste créée, vous pouvez tester vos connaissances à tout moment via le bouton \"🎯\"</p>", unsafe_allow_html=True)

            st.write("")

            st.write("""
<ul style="list-style-type: '❖ ';">
    <li>Pour une liste de vocabulaire il existe 2 sens de révision :
        <ul>
            <li><b>🌐 Vers la langue étrangère :</b> La traduction française vous est donnée, à vous de retrouver le mot original (ainsi que son article si présent).</li>
            <li><b>🇫🇷 Vers le français :</b> Le mot étranger vous est présenté, à vous de retrouver sa traduction en français.</li>
        </ul>
    </li>
    <li>Pour une liste de verbes :
        <ul>
            <li>L'une des 5 formes du verbe vous est donné, à vous de retrouvé les 4 autres formes. Chacunes des 5 formes du verbes vous sera donné pendant un entrainement en alternance avec les formes des autres verbes.</li>
        </ul>
    </li>
</ul>

<br>
<ul style="list-style-type: '➢ ';">
    <li>Votre progression est automatiquement sauvegardé. Si jamais vous quittez le site par inadvertance, pas de panique, vous pourrez reprendre là où vous en étiez !</li><br>
    <li>Si jamais vous devez interrompre un entrainement mais que vous ne voulez pas perdre votre progression, il y a le bouton \"Mettre en pause\" situé en bas de la page qui vous renverra sur la page d'accueil tout en sauvegardant votre progression.</li><br>
    <li>Si jamais vous voulez interrompre un entrainement et écraser votre progression actuelle, il y a le bouton \"Abandonner l'entrainement\" situé en bas de la page qui vous renverra sur la page d'accueil tout en supprimant votre progression.</li><br>
    <li>À la fin de votre entrainement votre score vous sera donné, ainsi que la liste de vos erreurs. Vous pourrez alors recommencer l'entrainement ou retourner à la page d'accueil.</li><br>
    <li>Après votre entrainement vous pouvez allez visualiser la liste (via le boutton \"👁️\" sur la page d'accueil). Les mots pour lesquelles vous avez fait une faute apparaitrons en rouge. Vous pourrez alors décider de réviser uniquement vos lacunes via le bouton "Réviser mes erreurs".</li>
</ul>

""", unsafe_allow_html=True)

        # 5. ASTUCES & SYNTAXE
        with tab_astuces:
            st.header("💡 Astuces & Syntaxe spéciale")
            st.write("Pour que le site sépare correctement les articles des mots, voici deux règles simples à connaître :\n\n#### 1. Gestion des articles\n* Si vous écrivez `der Hund`, le site comprendra automatiquement que **\"der\"** est l'article et **\"Hund\"** est le mot.\n\n#### 2. Cas des expressions avec espaces (`!`)\n* Si votre mot contient des espaces qui ne servent pas à séparer un article (ex: une expression comme *\"auf jeden Fall\"*), laissez la case article vide et **placez un point d'exclamation `!` au tout début du mot**.\n* **Exemple :** `!auf jeden Fall` $\\rightarrow$ Le site saura qu'il ne faut pas chercher d'article au début !")


# --- 4. ÉTAT : CONNECTE (Espace utilisateur) ---
elif st.session_state.etat == "connecte":
    username, user_id, admin = st.session_state.user

    if "action" not in st.session_state:
        st.session_state.action = "liste"
        st.rerun()
    if "liste_active_id" not in st.session_state:
        st.session_state.liste_active_id = None
    if "nb_lignes_mots" not in st.session_state:
        st.session_state.nb_lignes_mots = 2

    _, col_centre, _ = st.columns([1, 3, 1])

    with col_centre:

        # CAS A : VUE/MODIFICATIONS PROFIL
        if st.session_state.action == "compte":
            st.subheader("👤 Mon Profil")

            st.write("")

            # 1. Champs de saisie
            nouveau_pseudo = st.text_input("Pseudo", value=st.session_state.temp_new_username) if "temp_new_username" in st.session_state else st.text_input("Pseudo", value=username)

            st.write("")

            nouveau_mdp = st.text_input("Nouveau mot de passe", value=st.session_state.temp_new_password, type="password", placeholder="Entrer un nouveau mot de passe") if "temp_new_password" in st.session_state else st.text_input("Nouveau mot de passe", type="password", placeholder="Entrer un nouveau mot de passe")

            # 2. Vérification des modifications
            pseudo_modifie = nouveau_pseudo.strip() != username and bool(nouveau_pseudo.strip())
            mdp_modifie = len(nouveau_mdp.strip()) > 0 
            a_modifie = pseudo_modifie or mdp_modifie

            st.write("") 
            st.write("")

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

            st.write("")

            # Cas A : Seulement le pseudo a été modifié
            if pseudo_modifie and not mdp_modifie:
                st.info("Vous êtes sur le point de modifier votre pseudo.")

                st.write("")

                mdp_actuel = st.text_input(
                    "Mot de passe actuel",
                    type="password",
                    placeholder="Veuillez confirmer votre mot de passe"
                )

                confirm_mdp = None  # Non nécessaire dans ce cas

            # Cas B : Le mot de passe (ou les deux) a été modifié
            else:
                st.info("Vous êtes sur le point de modifier des informations sensibles.")

                st.write("")

                confirm_mdp = st.text_input(
                    "Confirmer le nouveau mot de passe",
                    type="password",
                    placeholder="Saisissez à nouveau votre nouveau mot de passe"
                )

                st.write("")

                mdp_actuel = st.text_input(
                    "Mot de passe actuel",
                    type="password",
                    placeholder="Veuillez confirmer votre mot de passe actuel"
                )

            st.write("")
            st.write("")

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

                            if not modifier_profil_bdd(user_id, final_username, final_password) : 
                                st.error("Le nom d'utilisateur choisi est déjà pris.")

                            else :
                                # Mise à jour de la session
                                username = final_username

                                # Nettoyage des données temporaires et retour accueil
                                st.session_state.pop("temp_new_username", None)
                                st.session_state.pop("temp_new_password", None)
                                st.session_state.user = (final_username, user_id, admin)
                                st.session_state.action = "liste"
                                st.rerun()
                    else:
                        st.error("Le mot de passe actuel est incorrect.")

            with col_cancel:
                if st.button("❌ Annuler", use_container_width=True):
                    # Retour à l'écran du profil sans effacer la saisie
                    st.session_state.action = "compte"
                    st.rerun()

        # CAS C : IMPORTER UNE LISTE (📥)
        elif st.session_state.action == "importer":
            st.subheader("📥 Importer une liste")

            st.write("")
            
            tab_id, tab_fichier = st.tabs(["🔢 Par ID de liste", "📄 Depuis un fichier texte"])

            with tab_id:
                st.write("")

                st.write("Saisis l'**ID de la liste** qu'on t'a partagé :")

                st.write("")

                id_saisi = st.text_input("ID de la liste :", placeholder="Ex: 12", key="import_id_input")

                st.write("")

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
                st.write("")
                
                st.write("Téléverse un fichier texte (`.txt`) contenant tes mots ou verbes.")

                st.write("")
                
                type_import = st.radio(
                    "Type de liste à importer :", 
                    ["Vocabulaire", "Verbes"],
                    horizontal=True,
                    key="type_import_file"
                )
                type_import_code = "verbe" if type_import == "Verbes" else "vocabulaire"

                st.write("")

                nom_nouvelle_liste = st.text_input("Nom de la nouvelle liste :", placeholder="Ex: Verbes Irréguliers")

                st.write("")
                st.write("")

                if type_import_code == "verbe":
                    st.info("💡 **Format attendu :** `infinitif, présent, prétérit, participe passé, traduction en français`  \n(un verbe par ligne)")
                else:
                    st.info("**Format attendu :** `article mot, traduction en français` (un mot par ligne)  \n\n"
                            "**IMPORTANT :**  \n"
                            "- L'article est facultatif  \n"
                            "- Si l'un de vos mots de vocabulaire utilise des espaces qui ne servent pas à séparer l'article du mot (comme dans une expression, par exemple), il faut mettre un point d'exclamation (!) au début de la ligne.")

                fichier_uploade = st.file_uploader("Choisis un fichier .txt", type=["txt"], accept_multiple_files=False)

                st.write("")
                st.write("")
                
                if st.button("📥 Importer depuis le fichier", type="primary", use_container_width=True):
                    if not (0 < len(nom_nouvelle_liste.strip()) <= 40) :
                        st.warning("Veuillez donner un nom valide à la liste. (1 à 40 caractères max)")
                        
                    elif fichier_uploade is None:
                        st.warning("Veuillez sélectionner un fichier.")

                    else:
                        contenu = fichier_uploade.getvalue().decode("utf-8")
                        succes, pb = importer_liste_depuis_fichier(user_id, nom_nouvelle_liste.strip(), type_import_code, contenu)
                        
                        if succes is True :
                            st.session_state.action = "liste"
                            st.rerun()

                        else :
                            if succes == 0 :
                                st.error("Aucun élément n'a pu être extrait. Vérifie que les séparateurs utilisés correspondent bien aux formats requis.")

                            elif succes == 1 :
                                st.error(f"Tous les articles ne sont pas valides ! Ils doivent faire entre 1 et 7 caractères max.   \nProblème ligne : {pb}")

                            elif succes == 2 :
                                st.error(f"Mot manquant ou trop long ! Ils doivent faire entre 1 et 30 caractères max.   \nProblème ligne : {pb}")

                            elif succes == 3 :
                                st.error(f"Traduction manquante ou trop longue ! Elle doit faire entre 1 et 30 caractères max.   \nProblème ligne : {pb}")

                            elif succes == 4 :
                                st.error(f"L'une des formes du verbe est manquante ou trop longue ! Elle doit faire entre 1 et 30 caractères max.   \nProblème ligne : {pb}")

            st.write("")
            ligne_epaisse()

            if st.button("🔙 Retour", use_container_width=True):
                st.session_state.action = "liste"
                st.rerun()

        # CAS D : CREER LISTE
        elif st.session_state.action == "creer":
            st.subheader("✨ Créer une nouvelle liste")
            ligne_epaisse()

            st.write("")
            nom_liste = st.text_input("Nom de la liste", placeholder="Nom de la liste")
            st.write("")

            type_liste_choisi = st.radio("Type de liste :", ["Vocabulaire (Article, Mot, Traduction)", "Verbes (5 formes)"], horizontal=True, on_change=lambda: st.session_state.update({"mots_temp": {}} if "mots_temp" in st.session_state else {}))
           
            is_verbe = "Verbes" in type_liste_choisi
            type_code = "verbe" if is_verbe else "vocabulaire"

            st.divider()

            if is_verbe:
                cols_h = st.columns([2, 2, 2, 2, 2, 1])
                headers = ["Infinitif", "Présent", "Prétérit", "Participe Passé", "Traduction", ""]
                for col, h in zip(cols_h, headers):
                    col.caption(h)
            else:
                cols_h = st.columns([1, 2, 2, 1])
                headers = ["Article", "Mot", "Traduction", ""]
                for col, h in zip(cols_h, headers):
                    col.caption(h)


            toutes_lignes_visibles_remplies = True
            if "mots_temp" not in st.session_state :
                st.session_state.mots_temp = {}
            st.session_state.id_a_suppr = None


            for i in range(st.session_state.nb_lignes_mots):
                valeur = st.session_state.mots_temp.get(i, ("", "", "", "", "", ""))

                if is_verbe:
                    c1, c2, c3, c4, c5, suppr = st.columns([2, 2, 2, 2, 2, 1])
                    with suppr :
                        if st.button("🗑️", key=i, help="Supprimer cette ligne"):
                            st.session_state.id_a_suppr = i

                    inf = c1.text_input(f"inf_{i}", label_visibility="collapsed", value=valeur[1])
                    pres = c2.text_input(f"pres_{i}", label_visibility="collapsed", value=valeur[2])
                    pret = c3.text_input(f"pret_{i}", label_visibility="collapsed", value=valeur[3])
                    pp = c4.text_input(f"pp_{i}", label_visibility="collapsed", value=valeur[4])
                    trad = c5.text_input(f"trad_{i}", label_visibility="collapsed", value=valeur[5])

                    st.session_state.mots_temp[i] = ("", inf, pres, pret, pp, trad)

                    if not (inf.strip() and trad.strip()):
                        toutes_lignes_visibles_remplies = False

                else:
                    c1, c2, c3, suppr = st.columns([1, 2, 2, 1])
                    with suppr :
                        if st.button("🗑️", key=i, help="Supprimer cette ligne"):
                            st.session_state.id_a_suppr = i

                    
                    art = c1.text_input(f"art_{i}", label_visibility="collapsed", value=valeur[0])
                    mot = c2.text_input(f"mot_{i}", label_visibility="collapsed", value=valeur[1])
                    trad = c3.text_input(f"trad_{i}", label_visibility="collapsed", value=valeur[5])

                    st.session_state.mots_temp[i] = (art, mot, "", "", "", trad)

                    if not (mot.strip() and trad.strip()):
                        toutes_lignes_visibles_remplies = False


            if st.session_state.id_a_suppr is not None :
                if st.session_state.nb_lignes_mots > 2:
                    st.session_state.mots_temp.pop(st.session_state.id_a_suppr, None)
                    st.session_state.mots_temp = {x:y for x, y in enumerate(list(st.session_state.mots_temp.values()))}
                    st.session_state.nb_lignes_mots -= 1

                else :
                    st.session_state.mots_temp[st.session_state.id_a_suppr] = ("", "", "", "", "", "")

                st.rerun()

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
                    st.session_state.pop("mots_temp", None)
                    st.session_state.pop("id_a_suppr", None)
                    st.session_state.pop("liste_valide", None)
                    st.rerun()
            with col_sauvegarder:
                if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
                    if not (0 < len(nom_liste.strip()) <= 40) :
                        st.warning("Veuillez donner un nom valide à la liste. (1 à 40 caractères max)")

                    else:
                        if "liste_valide" not in st.session_state :
                            st.session_state.liste_valide = True
                        else : 
                            st.session_state.liste_valide = True

                        last_ligne = st.session_state.get("mots_temp", {}).get(st.session_state.get("nb_lignes_mots", 1) - 1, ())
                        toutes_lignes_visibles_remplies = True
                        if is_verbe :
                            for case in last_ligne[1:] :
                                if case.strip() :
                                    toutes_lignes_visibles_remplies = False
                        else :
                            if len(last_ligne) >=6 :
                                if bool(str(last_ligne[1]).strip()) != bool(str(last_ligne[5]).strip()):
                                    toutes_lignes_visibles_remplies = False


                        for ligne in (list(st.session_state.mots_temp.values())[:-1] if toutes_lignes_visibles_remplies else list(st.session_state.mots_temp.values())):
                            if is_verbe:
                                for case in ligne[1:] :
                                    if not(0 < len(case.strip()) <= 30) :
                                        st.session_state.liste_valide = False
                                        st.warning(f"L'une des formes du verbe est manquante ou trop longue ! Elle doit faire entre 1 et 30 caractères max.")
                                    
                            else:
                                if len(ligne[0].strip()) > 7 :
                                    st.warning("Tous les articles ne sont pas valides ! (7 caractères max)")
                                    st.session_state.liste_valide = False

                                if not(0 < len(ligne[1].strip()) <= 30) :
                                    st.warning("Tous les mots ne sont pas valides ! (1 à 30 caractères max)")
                                    st.session_state.liste_valide = False


                                if not(0 < len(ligne[5].strip()) <= 30) :
                                    st.warning("Toutes les traductions ne sont pas valides ! (1 à 30 caractères max)")
                                    st.session_state.liste_valide = False

                        if st.session_state.liste_valide:
                            ajouter_liste(user_id, nom_liste.strip(), type_code)
                            listes_user = recuperer_listes_utilisateur(user_id)
                            derniere_liste_id = listes_user[-1][0]

                            for art, inf_mot, pres, pret, pp, trad in st.session_state.mots_temp.values():
                                if is_verbe:
                                    if inf_mot.strip() and pres.strip() and pret.strip() and pp.strip() and trad.strip():
                                        ajouter_élément_liste(derniere_liste_id, inf_mot, pres, pret, pp, trad)

                                else:
                                    inf_mot_strip = inf_mot.strip()
                                    art_strip = art.strip()
                                    if inf_mot.strip() and trad.strip():
                                        mot_comp = f"{art_strip} {inf_mot_strip}" if art_strip else "!" + inf_mot_strip if " " in inf_mot_strip and not inf_mot_strip.startswith("!") else inf_mot_strip
                                        ajouter_élément_liste(derniere_liste_id, mot_comp, "", "", "", trad.strip())

                            st.session_state.action = "liste"
                            st.session_state.nb_lignes_mots = 2
                            st.session_state.pop("mots_temp", None)
                            st.session_state.pop("id_a_suppr", None)
                            st.session_state.pop("liste_valide", None)
                            st.rerun() 

            if not is_verbe :
                st.info("Si l'un de vos mots de vocabulaire utilise des espaces qui ne servent pas à séparer l'article du mot (comme dans une expression, par exemple), laissez la case article vide et mettez un point d'exclamation (!) au début de la case \"Mot\".")

        # CAS E : VOIR UNE LISTE (👁️)
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
                compteur_err = charger_erreurs(user_id, liste_id)
                has_errors = 0

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
                            is_err = isinstance(errs, dict) and errs.get(idx_f, 0) >= 2
                            if is_err:
                                return f"<span style='color: #FF4B4B; font-weight: bold;'>{texte}</span>", 1
                            return texte, 0

                        cols = st.columns(5)
                        elements = [(inf, 1), (pres, 2), (pret, 3), (pp, 4), (trad, 5)]

                        for col, (texte, idx) in zip(cols, elements):
                            txt_html, k = fmt_v(texte, idx)
                            col.markdown(txt_html, unsafe_allow_html=True)
                            has_errors += k
                else:
                    c_m1, c_m2 = st.columns(2)
                    c_m1.markdown("<u>**Mot :**</u>", unsafe_allow_html=True)
                    c_m2.markdown("<u>**Traduction :**</u>", unsafe_allow_html=True)
                    st.write("")

                    for mot in mots:
                        id_m, mot_or, _, _, _, trad = mot

                        # Supprime les éventuels "!"
                        mot_or = mot_or.removeprefix("!")
                        
                        # Récupération des erreurs spécifiques par sens
                        # err_info = {"vers_fr": True/False, "depuis_fr": True/False}
                        err_info = compteur_err.get(id_m, {}) if isinstance(compteur_err, dict) else {}
                        
                        # Si l'erreur était vers le français (question en langue étrangère -> faute sur la traduction)
                        err_trad = err_info.get("vers_fr", False)
                        # Si l'erreur était depuis le français (question en français -> faute sur le mot étranger)
                        err_orig = err_info.get("depuis_fr", False)

                        # Coloration uniquement du côté erroné
                        if err_orig :
                            mot_disp = f"<span style='color: #FF4B4B; font-weight: bold;'>{mot_or}</span>" 
                            has_errors += 1
                        else : 
                            mot_disp = mot_or

                        if err_trad :
                            trad_disp = f"<span style='color: #FF4B4B; font-weight: bold;'>{trad}</span>" 
                            has_errors += 1
                        else :
                            trad_disp = trad

                        cm1, cm2 = st.columns(2)
                        cm1.markdown(mot_disp, unsafe_allow_html=True)
                        cm2.markdown(trad_disp, unsafe_allow_html=True)

            ligne_epaisse()
            st.write("")

            cols = st.columns(2) if has_errors else [st.container()]
            with cols[0]:
                if st.button("🔙 Retour", use_container_width=True):
                    st.session_state.action = "liste"
                    st.session_state.liste_active_id = None
                    st.rerun()

            if has_errors :
                with cols[1]:
                    if st.button(f"🎯 Revoir mes erreurs ({has_errors})", use_container_width=True):
                        st.session_state.action = "err_entrainer"
                        st.rerun()

        # CAS F : ÉDITER UNE LISTE (✏️)
        elif st.session_state.action == "editer":
            liste_id = st.session_state.liste_active_id
            listes_user = recuperer_listes_utilisateur(user_id)
            nom_actuel, type_liste = next(((nom, type_l) for lid, nom, type_l in listes_user if lid == liste_id), ("", "vocabulaire"))

            st.subheader("✏️ Éditer la liste")
            ligne_epaisse()
            
            st.write("")
            nouveau_nom = st.text_input("Nom de la liste", value=nom_actuel)
            st.divider()

            
            toutes_lignes_visibles_remplies = True
            if "mots_temp" not in st.session_state :
                mots_existants = recuperer_mots_liste(liste_id)

                if type_liste == "verbe":
                    st.session_state.mots_temp = {x: (inf, pres, pret, participe, trad) for x, (_, inf, pres, pret, participe, trad) in enumerate(mots_existants)}

                else :
                    def séparer_article(mot_or, trad_val):     
                        if mot_or.startswith("!") :
                            return ("", mot_or, trad_val)
                        
                        else:
                            parts = mot_or.split(" ", 1) 
                            art, mot = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])                   

                            return (art, mot, trad_val)
                    st.session_state.mots_temp = {x : séparer_article(mot_or, trad_val) for x, (_, mot_or, _, _, _, trad_val) in enumerate(mots_existants)}

                st.session_state.nb_lignes_mots = len(st.session_state.mots_temp) + 1

            st.session_state.id_a_suppr = None


            if type_liste == "verbe":
                cols_h = st.columns([2, 2, 2, 2, 2, 1])
                headers = ["Infinitif", "Présent", "Prétérit", "Participe Passé", "Traduction", ""]
                for col, h in zip(cols_h, headers):
                    col.caption(h)
            else :
                cols_h = st.columns([1, 2, 2, 1])
                headers = ["Article", "Mot", "Traduction", ""]
                for col, h in zip(cols_h, headers):
                    col.caption(h)


            for i in range(st.session_state.nb_lignes_mots):
                if type_liste == "verbe":
                    c1, c2, c3, c4, c5, suppr = st.columns([2, 2, 2, 2, 2, 1])
                    with suppr :
                        if st.button("🗑️", key=i, help="Supprimer cette ligne"):
                            st.session_state.id_a_suppr = i


                    valeur = st.session_state.mots_temp.get(i, ("", "", "", "", ""))
                    inf = c1.text_input(f"edit_inf_{i}", value=valeur[0], label_visibility="collapsed")
                    pres = c2.text_input(f"edit_pres_{i}", value=valeur[1], label_visibility="collapsed")
                    pret = c3.text_input(f"edit_pret_{i}", value=valeur[2], label_visibility="collapsed")
                    pp = c4.text_input(f"edit_pp_{i}", value=valeur[3], label_visibility="collapsed")
                    trad = c5.text_input(f"edit_vtrad_{i}", value=valeur[4], label_visibility="collapsed")

                    st.session_state.mots_temp[i] = (inf, pres, pret, pp, trad)

                    if not (inf.strip() and trad.strip()):
                        toutes_lignes_visibles_remplies = False

                else :
                    c1, c2, c3, suppr = st.columns([1, 2, 2, 1])
                    with suppr :
                        if st.button("🗑️", key=i, help="Supprimer cette ligne"):
                            st.session_state.id_a_suppr = i


                    valeur = st.session_state.mots_temp.get(i, ("", "", ""))
                    art = c1.text_input(f"edit_art_{i}", value=valeur[0], label_visibility="collapsed")
                    mot = c2.text_input(f"edit_mot_{i}", value=valeur[1], label_visibility="collapsed")
                    trad = c3.text_input(f"edit_trad_{i}", value=valeur[2], label_visibility="collapsed")

                    st.session_state.mots_temp[i] = (art, mot, trad)

                    if not (mot.strip() and trad.strip()):
                        toutes_lignes_visibles_remplies = False


            if st.session_state.id_a_suppr is not None :
                if st.session_state.nb_lignes_mots > 2:
                    st.session_state.mots_temp.pop(st.session_state.id_a_suppr, None)
                    st.session_state.mots_temp = {x:y for x, y in enumerate(list(st.session_state.mots_temp.values()))}
                    st.session_state.nb_lignes_mots -= 1

                else :
                    if type_liste == "verbe" :
                        st.session_state.mots_temp[st.session_state.id_a_suppr] = ("", "", "", "", "")
                    else:
                        st.session_state.mots_temp[st.session_state.id_a_suppr] = ("", "", "")

                st.rerun()

            if toutes_lignes_visibles_remplies:
                st.session_state.nb_lignes_mots += 1
                st.rerun()

            st.write("")
            st.write("")

            col_annuler, col_sauvegarder = st.columns(2)
            with col_annuler:
                if st.button("❌ Annuler", use_container_width=True):
                    st.session_state.action = "liste"
                    st.session_state.liste_active_id = None
                    st.session_state.nb_lignes_mots = 2
                    st.session_state.pop("mots_temp", None)
                    st.session_state.pop("id_a_suppr", None)
                    st.rerun()
            with col_sauvegarder:
                if st.button("💾 Enregistrer les modifications", type="primary", use_container_width=True):
                    if not (0 < len(nouveau_nom.strip()) <= 40) :
                        st.warning("Veuillez donner un nom valide à la liste. (1 à 40 caractères max)")

                    else:
                        succes = remplacer_mots_liste(liste_id, st.session_state.mots_temp.values(), type_liste)

                        if succes is True :
                            renommer_liste(liste_id, nouveau_nom.strip())
                            st.session_state.action = "liste"
                            st.session_state.liste_active_id = None
                            st.session_state.nb_lignes_mots = 2
                            st.session_state.pop("mots_temp", None)
                            st.session_state.pop("id_a_suppr", None)
                            reinitialiser_score_liste(user_id, liste_id)
                            st.rerun()

                        else :
                            if succes == 0 :
                                st.warning("Tous les articles ne sont pas valides ! (7 caractères max)")

                            elif succes == 1 :
                                st.warning("Tous les mots ne sont pas valides ! (1 à 30 caractères max)")

                            elif succes == 2 :
                                st.warning("Toutes les traductions ne sont pas valides ! (1 à 30 caractères max)")

                            elif succes == 3 :
                                st.warning(f"L'une des formes du verbe est manquante ou trop longue ! Elle doit faire entre 1 et 30 caractères max.")

            if not type_liste == "verbe" :
                st.info("Si l'un de vos mots de vocabulaire utilise des espaces qui ne servent pas à séparer l'article du mot (comme dans une expression, par exemple), laissez la case article vide et mettez un point d'exclamation (!) au début de la case \"Mot\".")

        # CAS G : ENTRAÎNEMENT (🎯)
        elif st.session_state.action == "entrainer" or st.session_state.action == "err_entrainer":
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
                    if st.session_state.action == "err_entrainer" :
                        mots_bruts = recuperer_mots_liste(liste_id)
                        erreurs = charger_erreurs(user_id, liste_id)
                        
                        # On crée la liste de questions 
                        questions = []
                        for id_m, mot_or, _, _, _, trad in mots_bruts:
                            # Supprime les éventuels "!"
                            mot_or = mot_or.strip()

                            # Récupération des erreurs spécifiques par sens
                            # err_info = {"vers_fr": True/False, "depuis_fr": True/False}
                            err_info = (erreurs or {}).get(id_m, {})

                            # Si l'erreur était vers le français (question en langue étrangère -> faute sur la traduction)
                            err_vfr = err_info.get("vers_fr", False)
                            # Si l'erreur était depuis le français (question en français -> faute sur le mot étranger)
                            err_dfr = err_info.get("depuis_fr", False)

                            if err_vfr or err_dfr :                    
                                if mot_or.startswith("!") :
                                    art, mot = "", mot_or.removeprefix("!")

                                else:
                                    parts = mot_or.split(" ", 1) 

                                    art, mot = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])

                                if err_vfr :
                                    questions.append({"item": {"id_mot": id_m, "article": art, "mot": mot, "traduction": trad}, "sens": "depuis_francais"})
                                if err_dfr : 
                                    questions.append({"item": {"id_mot": id_m, "article": art, "mot": mot, "traduction": trad}, "sens": "vers_francais"})
                
                        # Mélange 1 : Aléatoire
                        random.shuffle(questions)

                        # Mélange 2 : Démêlage
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
                    else : 
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
                            st.session_state.action = "err_entrainer" if partie_sauvee["type"] == "erreur" else "entrainer"
                            st.toast("⚡ Sauvegarde chargée !")
                        else:
                            mots_bruts = recuperer_mots_liste(liste_id)
                            
                            mots_traites = []
                            for id_m, mot_or, _, _, _, trad in mots_bruts:
                                mot_or_strip = mot_or.strip()

                                if mot_or_strip.startswith("!") :
                                    art, mot = "", mot_or_strip.removeprefix("!")
                                else:
                                    parts = mot_or_strip.split(" ", 1) 

                                    art, mot = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])
                                
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

                            # Mélange 2 : Démêlage
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
                        st.session_state.pop("choix_reprise", None)

                questions = st.session_state.quiz_mots
                index = st.session_state.quiz_index

                # 2. VUE FINALE : BILAN DU QUIZ ET SAUVEGARDE EN BDD
                if index >= len(questions):
                    supprimer_sauvegarde_partie(liste_id)

                    s_v = st.session_state.score_vers_fr
                    t_v = st.session_state.total_vers_fr
                    s_d = st.session_state.score_depuis_fr
                    t_d = st.session_state.total_depuis_fr

                    # Enregistrement des erreurs
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

                    sauvegarder_erreurs(user_id, liste_id, mots_err)

                    st.write("### &nbsp;&nbsp;&nbsp;📊 Tes résultats")

                    # Animation du nouveau meilleur score et résultats
                    if st.session_state.action == "entrainer" :
                        score_actuel_bdd = recuperer_score_liste(user_id, liste_id)
                        est_nouveau_record = False

                        if score_actuel_bdd is None:
                            est_nouveau_record = True
                        else:
                            anc_v, _, anc_d, _ = score_actuel_bdd
                            if s_v > anc_v or s_d > anc_d:
                                est_nouveau_record = True

                        if est_nouveau_record:
                            enregistrer_meilleur_score(user_id, liste_id, s_v, t_v, s_d, t_d)
                            st.success("🥳 **Nouveau meilleur score !**")
                        elif score_actuel_bdd:
                            anc_v, anc_tv, anc_d, anc_td = score_actuel_bdd
                            st.markdown(f"<div style='text-align: center;'>🏆 <b>Meilleur score :</b> 🌐 <code>{anc_v:g}/{anc_tv:g}</code> | 🇫🇷 <code>{anc_d:g}/{anc_td:g}</code></div>", unsafe_allow_html=True)

                        st.write("")
                        st.write("")

                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.markdown(f"<div style='text-align: center; margin: 10px 0;'><span style='font-size: 0.9em; color: white;'>🌐 Vers la langue étrangère</span><div style='font-size: 2rem; font-weight: 500;'>{s_v:g} / {t_v:g}</div></div>", unsafe_allow_html=True)

                        with col_res2:
                            st.markdown(f"<div style='text-align: center; margin: 10px 0;'><span style='font-size: 0.9em; color: white;'>🇫🇷 Vers le français</span><div style='font-size: 2rem; font-weight: 500;'>{s_d:g} / {t_d:g}</div></div>", unsafe_allow_html=True)

                    # Résultats révision erreurs
                    else:
                        st.write("")

                        cols = st.columns(2) if (t_v and t_d) else st.columns(1)

                        if t_v :
                            with cols[0]:
                                st.markdown(f"<div style='text-align: center; margin: 10px 0;'><span style='font-size: 0.9em; color: white;'>🌐 Vers la langue étrangère</span><div style='font-size: 2rem; font-weight: 500;'>{s_v:g} / {t_v:g}</div></div>", unsafe_allow_html=True)

                        if t_d :
                            col_dest = cols[1] if (t_v and t_d) else cols[0]
                            with col_dest :
                                st.markdown(f"<div style='text-align: center; margin: 10px 0;'><span style='font-size: 0.9em; color: white;'>🇫🇷 Vers le français</span><div style='font-size: 2rem; font-weight: 500;'>{s_d:g} / {t_d:g}</div></div>", unsafe_allow_html=True)

                    st.divider()

                    erreurs = st.session_state.erreurs_commises
                    if erreurs:
                        if st.session_state.action == "entrainer" :
                            st.write("### ❌ Liste des erreurs commises")
                        else : 
                            st.write("### ❌ Liste des erreurs qu'il te reste à réviser")
                        st.markdown("<p style='text-align: center; color: #808495; font-size: 0.875rem;'>Seuls les éléments erronés sont affichés en rouge :</p>", unsafe_allow_html=True)

                        st.write("")

                        col_q, col_rep, col_att = st.columns([2, 2, 2])
                        col_q.markdown("""<div style='text-align: center;'><u><b>Question posée :</b></u></div>""", unsafe_allow_html=True)
                        col_rep.markdown("""<div style='text-align: center;'><u><b>Ta réponse:</b></u></div>""", unsafe_allow_html=True)
                        col_att.markdown("""<div style='text-align: center;'><u><b>Réponse attendue :</b></u></div>""", unsafe_allow_html=True)

                        for x, err in enumerate(erreurs, 1):
                            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
                            c1, c2, c3 = st.columns([2, 2, 2])
                            c1.markdown(f"""<div style='text-align: center;'>Traduction de : <u><b>{err['question']}</b></u></div>""", unsafe_allow_html=True)
                            c2.markdown(f"""<div style='text-align: center;'>{err["reponse_user_html"]}</div>""", unsafe_allow_html=True)
                            c3.markdown(f"""<div style='text-align: center;'>🟢 {err['reponse_attendue']}</div>""", unsafe_allow_html=True)
                            nb_err = x

                        st.write("")
                        
                    else:
                        st.balloons()
                        if st.session_state.action == "entrainer" :
                            st.info("⭐ Félicitations ! Tu as fait un sans-faute parfait.")
                        else : 
                            st.info("⭐ Félicitations ! Tu as corrigé toutes tes erreurs.")
                        
                    ligne_epaisse()
                    st.write("")

                    if erreurs :
                        col_b1, col_b2, col_b3 = st.columns(3)
                        with col_b3:
                            if st.button(f"🎯 Revoir mes erreurs ({nb_err})", use_container_width=True):
                                st.session_state.action = "err_entrainer"
                                st.session_state.pop("quiz_mots", None)
                                st.rerun()
                    else :
                        col_b1, col_b2 = st.columns(2)
                    
                    with col_b1:
                        if st.button("🔙 Retour aux listes", type="primary", use_container_width=True):
                            st.session_state.pop("quiz_mots", None)
                            st.session_state.action = "liste"
                            st.rerun()

                    with col_b2:
                        if st.button("🔄 Recommencer", use_container_width=True):
                            st.session_state.pop("quiz_mots", None)
                            st.session_state.action = "entrainer"
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

                            c_art, c_mot = st.columns([1, 3])
                            user_art = c_art.text_input("Article (si présent)", key=f"art_in_{index}")
                            user_mot = c_mot.text_input("Mot", key=f"mot_in_{index}")
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
                            art_correct = (u_art.lower() == item["article"].strip().lower())
                            mot_correct = (u_mot.lower() == item["mot"].strip().lower())
                            
                            if art_correct:
                                points_gagnes += 0.5 if bool(item["article"]) else 0
                            if mot_correct:
                                points_gagnes += 1 if not bool(item["article"]) and art_correct else 0.5

                            if points_gagnes < 1.0:
                                q_txt = item['traduction']
                                rep_att = f"{item['article']} {item['mot']}".strip()

                                partie_art_html = f"<span style='color:red;'>{u_art if u_art else '(vide)'}</span>" if not art_correct else u_art
                                partie_mot_html = f"<span style='color:red;'>{u_mot if u_mot else '(vide)'}</span>" if not mot_correct else u_mot
                                
                                rep_user_formatted = f"{partie_art_html} {partie_mot_html}".strip() 

                                st.session_state.erreurs_commises.append({
                                    "id_mot": item["id_mot"],
                                    "sens": "depuis_fr",
                                    "question": q_txt,
                                    "reponse_user_html": rep_user_formatted,
                                    "reponse_attendue": rep_att
                                })

                            st.session_state.score_vers_fr += points_gagnes
                            st.session_state.total_vers_fr += total_q

                        else:
                            mot_correct = (u_mot.lower() == item["traduction"].lower())

                            if mot_correct:
                                points_gagnes = 1.0
                            else:
                                mot_affiche = f"{item['article']} {item['mot']}".strip()
                                q_txt = mot_affiche
                                rep_att = item["traduction"]

                                points_gagnes = 0.0
                                partie_mot_html = f"<span style='color:red;'>{u_mot if u_mot else '(vide)'}</span>"
                                
                                st.session_state.erreurs_commises.append({
                                    "id_mot": item["id_mot"],
                                    "sens": "vers_fr",
                                    "question": q_txt,
                                    "reponse_user_html": partie_mot_html,
                                    "reponse_attendue": rep_att
                                })

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
                            "erreurs_commises": st.session_state.erreurs_commises,
                            "type" : "normal" if st.session_state.get("action") == "entrainer" else "erreur"
                        }
                        sauvegarder_partie(user_id, liste_id, etat_a_sauver)

                        st.rerun()

                    # --- BOUTONS PAUSE ET ABANDON ---
                    st.write("")
                    col_b2, col_b1  = st.columns(2)

                    with col_b1:
                        if st.button("⏸️ Mettre en pause", use_container_width=True, type="secondary"):
                            etat_a_sauver = {
                                "quiz_index": st.session_state.quiz_index,
                                "quiz_mots": st.session_state.quiz_mots,
                                "score_vers_fr": st.session_state.get("score_vers_fr", 0.0),
                                "total_vers_fr": st.session_state.get("total_vers_fr", 0.0),
                                "score_depuis_fr": st.session_state.get("score_depuis_fr", 0.0),
                                "total_depuis_fr": st.session_state.get("total_depuis_fr", 0.0),
                                "erreurs_commises": st.session_state.get("erreurs_commises", []),
                                "type" : "normal" if st.session_state.get("action") == "entrainer" else "erreur"
                            }
                            
                            sauvegarder_partie(user_id, liste_id, etat_a_sauver)
                            
                            clefs_a_supprimer = [
                                "quiz_mots", "quiz_index", "quiz_liste_id", 
                                "score_vers_fr", "total_vers_fr", 
                                "score_depuis_fr", "total_depuis_fr", "erreurs_commises"
                            ]
                            for clef in clefs_a_supprimer:
                                if clef in st.session_state:
                                    st.session_state.pop(clef, None)
                            

                            st.session_state.action = "liste"
                            st.rerun()

                    with col_b2:
                        if st.button("🛑 Abandonner l'entraînement", use_container_width=True, type="secondary"):
                            if st.session_state.action == "entrainer" :
                                st.session_state.action_suppr = "abandon"
                            else : 
                                st.session_state.action_suppr = "abandon2"
                            st.session_state.action = "supprimer"
                            st.rerun()

            # --- S'IL S'AGIT D'UNE LISTE DE VERBES ---
            else:
                # 1. INITIALISATION DU QUIZ VERBES
                if "quiz_mots" not in st.session_state or st.session_state.get("quiz_liste_id") != liste_id:
                    if st.session_state.action == "err_entrainer" :
                        mots_bruts = recuperer_mots_liste(liste_id)
                        erreurs = charger_erreurs(user_id, liste_id)

                        # On crée la liste de questions 
                        questions = []
                        formes_infos = ["Infinitif", "Présent", "Prétérit", "Participe Passé", "Traduction"]
                        for x in mots_bruts :
                            id_m, inf, pres, pret, pp, trad = x
                            err_info = (erreurs or {}).get(id_m, {})

                            # Vérification de où est l'erreur
                            errs = [i for i in range(1, 6) if err_info.get(i, 0) >= 2]

                            if errs :
                                if len(errs) == 5:
                                    questions.append({"id_mot" : id_m, 
                                                    "attentes" : [{"idx_tuple": z, "reponse_attendue": x[z], "nom" : formes_infos[z-1]} for z in range(2, 6) if z in errs], 
                                                    "verbe_tuple" : x,
                                                    "tout_faux" : True})
                                    
                                    questions.append({"id_mot" : id_m, 
                                                    "attentes" : [{"idx_tuple": z, "reponse_attendue": x[z], "nom" : formes_infos[z-1]} for z in range(1, 5) if z in errs], 
                                                    "verbe_tuple" : x,
                                                    "tout_faux" : True})
                                else :
                                    questions.append({"id_mot" : id_m, 
                                                    "attentes" : [{"idx_tuple": z, "reponse_attendue": x[z], "nom" : formes_infos[z-1]} for z in range(1, 6) if z in errs], 
                                                    "verbe_tuple" : x})

                        random.shuffle(questions)

                        demeler_questions_erreurs(questions)

                        st.session_state.quiz_mots = questions
                        st.session_state.quiz_index = 0
                        st.session_state.score_verbes = 0.0
                        st.session_state.total_verbes = sum((0.625 if x.get("tout_faux", False) else 1) * len(x["attentes"]) for x in questions)
                        st.session_state.erreurs_compteur = {}
                        st.session_state.erreurs_verbes_detail = []
                        st.session_state.quiz_liste_id = liste_id

                    else :
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
                            st.session_state.action = "err_entrainer" if partie_sauvee["type"] == "erreur" else "entrainer"
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
                        st.session_state.pop("choix_reprise", None)

                questions = st.session_state.quiz_mots
                index = st.session_state.quiz_index

                # 2. VUE FINALE : BILAN ET SAUVEGARDE
                if index >= len(questions):
                    sauvegarder_erreurs(user_id, liste_id, st.session_state.erreurs_compteur)
                    supprimer_sauvegarde_partie(liste_id)

                    s_v = st.session_state.score_verbes
                    t_v = st.session_state.total_verbes

                    st.write("### &nbsp;&nbsp;&nbsp;📊 Tes résultats")

                    if st.session_state.action == "entrainer" :
                        score_actuel_bdd = recuperer_score_liste(user_id, liste_id)
                        est_nouveau_record = False

                        if score_actuel_bdd is None:
                            est_nouveau_record = True
                        else:
                            anc_score, _, _, _ = score_actuel_bdd
                            if s_v > anc_score :
                                est_nouveau_record = True


                        if est_nouveau_record:
                            enregistrer_meilleur_score(user_id, liste_id, s_v, t_v, 0, 0)
                            st.success("🥳 **Nouveau meilleur score !**")
                        elif score_actuel_bdd:
                            anc_v, anc_tv, _, _ = score_actuel_bdd
                            st.markdown(f"""<div class="centre">🏆 <b>Meilleur score :</b> ⚡ <code>{anc_v:g}/{anc_tv:g}</code></div>""", unsafe_allow_html=True)

                        st.write("")

                        st.markdown(f"""<div class="centre" style="margin: 10px 0;"><span style="font-size: 1em; color: white;">⚡ Score :</span><div style="font-size: 2rem; font-weight: 500;">{s_v:g} / {t_v:g}</div></div>""", unsafe_allow_html=True)

                    else :
                        st.write("")

                        st.markdown(f"""<div class="centre" style="margin: 10px 0;"><span style="font-size: 1em; color: white;">⚡ Score :</span><div style="font-size: 2rem; font-weight: 500;">{s_v:g} / {t_v:g}</div></div>""", unsafe_allow_html=True)

                    # --- RECAPITULATIF DES ERREURS POUR VERBES ---
                    st.divider()

                    err_details = st.session_state.get("erreurs_verbes_detail", [])
                    st.session_state.pop("erreurs_verbes_detail", None)

                    if err_details:
                        err_details = [dict(dict_tuple) | {"nombre" : nb} for dict_tuple, nb in Counter(tuple(d.items()) for d in err_details).items()]

                        if st.session_state.action == "entrainer" :
                            st.write("### ❌ Récapitulatif des erreurs commises")
                        else :
                            st.write("### ❌ Récapitulatif des erreurs qu'il te reste à réviser")
                        st.markdown("<p style='text-align: center; color: #808495; font-size: 0.875rem;'>Voici les formes sur lesquelles tu t'es trompé(e) :</p>", unsafe_allow_html=True)

                        st.write("")

                        col_v, col_f, col_rep, col_att, col_nb = st.columns([2, 2, 2, 2, 1])
                        col_v.markdown("""<div style='text-align: center;'><u><b>Verbes :</b></u></div>""", unsafe_allow_html=True)
                        col_f.markdown("""<div style='text-align: center;'><u><b>Forme demandée :</b></u></div>""", unsafe_allow_html=True)
                        col_rep.markdown("""<div style='text-align: center;'><u><b>Ta réponse :</b></u></div>""", unsafe_allow_html=True)
                        col_att.markdown("""<div style='text-align: center;'><u><b>Réponse attendue :</b></u></div>""", unsafe_allow_html=True)
                        col_nb.markdown("""<div style='text-align: center;'><u><b>Nombre :</b></u></div>""", unsafe_allow_html=True)

                        for err in err_details :
                            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
                            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                            c1.markdown(f"""<div style='text-align: center;'><b>{err['verbe']}</b></div>""", unsafe_allow_html=True)
                            c2.markdown(f"""<div style='text-align: center;'>{err["forme"]}</div>""", unsafe_allow_html=True)
                            c3.markdown(f"""<div style='text-align: center;'><span style='color:red;'>{err['rep_user'] if err['rep_user'] else '(vide)'}</span></div>""", unsafe_allow_html=True)
                            c4.markdown(f"""<div style='text-align: center;'>🟢 <code>{err['rep_attendue']}</code></div>""", unsafe_allow_html=True)
                            c5.markdown(f"""<div style='text-align: center;'>x{err["nombre"]}</div>""", unsafe_allow_html=True)

                        st.write("")

                    else:
                        st.balloons()
                        if st.session_state.action == "entrainer" :
                            st.info("⭐ Félicitations ! Un sans-faute parfait sur les verbes !")
                        else :
                            st.info("⭐ Félicitations ! Tu as corrigé toutes tes erreurs.")

                    ligne_epaisse()
                    st.write("")

                    nb_err = sum(sum(x[i] >= 2 for i in range(1, 6)) for x in st.session_state.erreurs_compteur.values())
                    if nb_err :
                        col_b1, col_b2, col_b3 = st.columns(3)

                        with col_b3:
                            if st.button(f"🎯 Revoir mes erreurs ({nb_err})", use_container_width=True):
                                st.session_state.action = "err_entrainer"
                                st.session_state.pop("quiz_mots", None)
                                st.rerun()
                    else :
                        col_b1, col_b2 = st.columns(2)

                    with col_b1:
                        if st.button("🔙 Retour aux listes", type="primary", use_container_width=True):
                            st.session_state.pop("quiz_mots", None)
                            st.session_state.action = "liste"
                            st.rerun()

                    with col_b2:
                        if st.button("🔄 Recommencer", use_container_width=True):
                            st.session_state.pop("quiz_mots", None)
                            st.session_state.action = "entrainer"
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

                            else :
                                st.text_input(f"{nom_f} :", value=q["verbe_tuple"][idx_t], disabled=True, key=f"dis_{index}_{idx_t}")

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
                            v_tout_faux = q.get("tout_faux", False)

                            if rep_u.lower() == rep_att.lower():
                                pts_gagnes += 0.25 if st.session_state.action == "entrainer" else 0.625 if v_tout_faux else 1

                            else:
                                st.session_state.erreurs_compteur[id_mot][idx_t] += 1 if st.session_state.action == "entrainer" else 2

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
                            "erreurs_verbes_detail": st.session_state.get("erreurs_verbes_detail", []),
                            "type" : "normal" if st.session_state.get("action") == "entrainer" else "erreur"
                        }
                        sauvegarder_partie(user_id, liste_id, etat_a_sauver)

                        st.rerun()

                    st.write("")
                    col_b2, col_b1 = st.columns(2)

                    with col_b1:
                        if st.button("⏸️ Mettre en pause", use_container_width=True, type="secondary"):
                            # 1. On prépare le dictionnaire des données de la session
                            etat_a_sauver = {
                                "quiz_index": st.session_state.quiz_index,
                                "quiz_mots": st.session_state.quiz_mots,
                                "score_verbes": st.session_state.get("score_verbes", 0.0),
                                "total_verbes": st.session_state.get("total_verbes", 0.0),
                                "erreurs_compteur": st.session_state.get("erreurs_compteur", {}),
                                "erreurs_verbes_detail": st.session_state.get("erreurs_verbes_detail", []),
                                "type" : "normal" if st.session_state.get("action") == "entrainer" else "erreur"
                            }
                            
                            # 2. Sauvegarde en BDD
                            sauvegarder_partie(user_id, liste_id, etat_a_sauver)
                            
                            # 3. Nettoyage de la session active
                            clefs_a_supprimer = ["quiz_mots", "quiz_index", "quiz_liste_id", "score_verbes", "total_verbes", "erreurs_compteur", "erreurs_verbes_detail"]
                            for clef in clefs_a_supprimer:
                                if clef in st.session_state:
                                    st.session_state.pop(clef, None)
                            
                            st.session_state.action = "liste"
                            st.rerun()

                    with col_b2:
                        if st.button("🛑 Abandonner l'entraînement", use_container_width=True, type="secondary"):
                            if st.session_state.action == "entrainer" :
                                st.session_state.action_suppr = "abandon"
                            else : 
                                st.session_state.action_suppr = "abandon2"
                            st.session_state.action = "supprimer"

        # CAS H : VUE PARTAGER UNE LISTE (🔗)
        elif st.session_state.action == "partager":
            liste_id = st.session_state.liste_active_id
            st.subheader("🔗 Partager la liste")

            st.write("")

            tab_direct, tab_id = st.tabs(["📋 Obtenir l'ID de la liste", "👤 Envoyer à un ami"])
            
            with tab_id:
                st.write("")

                st.write("Donne cet **ID de liste** à ton ami(e) pour qu'il/elle puisse l'importer de son côté :")

                st.write("")

                st.code(str(liste_id), language="text")
            
            with tab_direct:
                st.write("")

                st.write("Saisis l'**ID de ton ami(e)** pour lui envoyer une copie directement dans son compte :")

                st.write("")

                id_ami = st.text_input("ID de l'utilisateur destinataire :", placeholder="Ex: 5")

                st.write("")

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

            st.write("")
            ligne_epaisse()

            if st.button("🔙 Retour", use_container_width=True):
                st.session_state.action = "liste"
                st.session_state.liste_active_id = None
                st.rerun()

        # CAS I : SUPRESSION/ABANDON
        elif st.session_state.action == "supprimer" :
            # CAS I.A : SUPPRIMER UN COMPTE
            if st.session_state.action_suppr == "compte":
                st.write("")
                st.error("⚠️ **ATTENTION :** Es-tu vraiment sûr de vouloir supprimer ton compte ? Toutes tes listes et tous tes mots seront définitivement perdus.")
                st.write("")

            # CAS I.B : SUPPRIMER UNE LISTE
            elif st.session_state.action_suppr == "liste":
                liste_id = st.session_state.liste_active_id
                nom_actuel = next((nom for lid, nom, _ in recuperer_listes_utilisateur(user_id) if lid == liste_id), "cette liste")

                st.write("")
                st.warning(f"⚠️ Es-tu sûr de vouloir supprimer la liste **'{nom_actuel}'** ? Cette action est irréversible.")
                st.write("")

            # CAS I.C : ABANDONNER UN ENTRAINEMENT
            elif st.session_state.action_suppr == "abandon" or st.session_state.action_suppr == "abandon2" :
                st.write("")
                st.warning("⚠️ **Es-tu sûr de vouloir abandonner ?** Ta progression actuelle sera perdue.")
                st.write("")

            # CAS I.D : AUTRE
            else:
                st.session_state.action = "liste"
                st.rerun()


            col_confirmer, col_annuler = st.columns(2)

            with col_confirmer : 
                if st.session_state.action_suppr == "compte":
                    if st.button("🗑️ Oui, supprimer mon compte", type="primary", use_container_width=True):
                        supprimer_compte(user_id)
                        for key in list(st.session_state.keys()):
                            if key != "toggle_focus" :
                                del st.session_state[key]
                        st.rerun()

                elif st.session_state.action_suppr == "liste":
                    if st.button("🗑️ Oui, supprimer la liste", type="primary", use_container_width=True):
                        supprimer_liste(liste_id)
                        st.session_state.action = "liste"
                        st.session_state.liste_active_id = None
                        st.session_state.pop("action_suppr", None)
                        st.rerun()

                elif st.session_state.action_suppr == "abandon" or st.session_state.action_suppr == "abandon2" :
                    if st.button("💥 Oui, abandonner", type="primary", use_container_width=True):
                        # A. Suppression de la sauvegarde BDD si elle existe
                        liste_id = st.session_state.get("liste_active_id")
                        if liste_id:
                            supprimer_sauvegarde_partie(liste_id)

                        # B. Nettoyage explicite des variables de quiz dans st.session_state
                        clefs = [
                            "quiz_mots", "quiz_index", "quiz_liste_id", 
                            "score_vers_fr", "total_vers_fr", "score_depuis_fr", "total_depuis_fr", 
                            "score_verbes", "total_verbes", "erreurs_commises", 
                            "erreurs_compteur", "erreurs_verbes_detail", "abandon_en_cours", "action_suppr"
                        ]
                        for clef in clefs:
                            st.session_state.pop(clef, None)

                        # C. Retour à la liste des listes
                        st.session_state.action = "liste"
                        st.session_state.liste_active_id = None
                        st.rerun()

            with col_annuler :
                if st.button("❌ Annuler", use_container_width=True):
                    if st.session_state.action_suppr == "abandon" :
                        st.session_state.action = "entrainer"

                    elif st.session_state.action_suppr == "abandon2" :
                        st.session_state.action = "err_entrainer"

                    else: 
                        st.session_state.liste_active_id = None
                        st.session_state.action = "liste"

                    st.session_state.pop("action_suppr", None)
                    st.rerun()

        # CAS J : VUE NORMALE (AFFICHAGE DES LISTES)
        else:
            st.write("")

            col_titre, col_import, col_ajout, col_infos = st.columns([3, 1, 1, 1])

            with col_titre:
                st.markdown("<h3 style='text-align: left;'>📋 Mes listes</h3>", unsafe_allow_html=True)

            with col_import:
                if st.button("📥", use_container_width=True, help="Importer une liste"):
                    st.session_state.action = "importer"
                    st.rerun()
            
            with col_ajout:
                if st.button("➕", use_container_width=True, help="Créer une nouvelle liste"):
                    st.session_state.action = "creer"
                    st.session_state.nb_lignes_mots = 2
                    st.rerun()

            with col_infos :
                if st.button("ℹ️", use_container_width=True, help="Aide"):
                    st.session_state.action = "infos"
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
                            st.session_state.action_suppr = "liste"
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

                            texte_score = f"🏆 <b>Meilleur score :</b> {partie_globe} | {partie_drapeau}"

                    else:
                        texte_score = "🏆 <b>Meilleur score :</b> Pas encore d'essai"

                    # Affichage avec taille personnalisable (font-size)
                    st.markdown(f"<div style='text-align: left; color: gray; font-size: 1rem;'>{texte_score}</div>", unsafe_allow_html=True)

                    st.divider()


# --- On place l'autofocus ---
placer_curseur(0)
st.write(f"\n--- Nouveau clic / Rechargement : {time.strftime('%H:%M:%S')} ---")

# --- Déboggeur ---
# On utilise un expander pour garder l'interface propre
# with st.expander("🛠️ Console de débogage (Session State)", expanded=False):
#    st.caption("Affiche en temps réel le contenu de st.session_state")
   
#    # Affiche l'état complet sous forme JSON/dictionnaire lisible
#    st.json(dict(st.session_state))
