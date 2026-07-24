import random
import streamlit as st

st.title("🧠 Révision de Vocabulaire")

VOCABULAIRE = {
    "Apple": "Pomme",
    "Book": "Livre",
    "Cat": "Chat",
    "House": "Maison",
    "Sun": "Soleil",
}

if "mot_courant" not in st.session_state:
    st.session_state.mot_courant = random.choice(list(VOCABULAIRE.keys()))
if "score" not in st.session_state:
    st.session_state.score = 0

st.write(f"### Score : {st.session_state.score}")
st.write(f"Traduis le mot suivant en français : **{st.session_state.mot_courant}**")

reponse = st.text_input("Ta réponse :", key="saisie_utilisateur")

if st.button("Valider"):
    traduction_exacte = VOCABULAIRE[st.session_state.mot_courant]

    if reponse.strip().lower() == traduction_exacte.lower():
        st.success("Bravo ! Bonne réponse. 🎉")
        st.session_state.score += 1
    else:
        st.error(f"Dommage ! La réponse était : **{traduction_exacte}**")

    st.session_state.mot_courant = random.choice(list(VOCABULAIRE.keys()))
    st.button("Mot suivant ➡️")