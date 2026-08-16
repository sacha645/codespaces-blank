import random

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

def demeler_questions_erreurs(questions):
    n = len(questions)

    if n <= 2:
        return questions

    milieu = n // 2
    i = 1

    while i < len(questions):
        # Si la question actuelle a le même mot que la précédente
        if questions[i]["id_mot"] == questions[i - 1]["id_mot"]:
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
    tirages_par_verbe = {verbe[0]: random.sample(range(5), 5) for verbe in mots_verbes}
    
    for tour in range(5):
        for verbe in mots_verbes:
            id_mot = verbe[0]
            # Forme choisie pour ce tour (0 à 4)
            idx_tirage = tirages_par_verbe[id_mot][tour]
            idx_tuple_fourni, nom_fourni = formes_infos[idx_tirage]
            
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
                "attentes": attentes,
                "verbe_tuple": verbe
            }
            questions_finales.append(question)
            
    return questions_finales
