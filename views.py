import streamlit.components.v1 as components
import streamlit as st

def ligne_epaisse():
    st.markdown(
        """
        <hr style="border: none; height: 3px; background-color: #4A4A4A; margin: 20px 0;">
        """,
        unsafe_allow_html=True
    )

def placer_curseur(index=0):
    # Alternance div/span pour forcer React/Streamlit à exécuter le JS à chaque rechargement
    st.session_state.toggle_focus = not st.session_state.toggle_focus
    balise = "div" if st.session_state.toggle_focus else "span"

    # On vérifie si l'utilisateur est sur la page de Connexion ou d'Inscription
    est_page_auth = st.session_state.get("etat") in ["connect", "nouveau"]
    verif_button = "" if est_page_auth else "|| active.tagName === 'BUTTON'"

    components.html(
        f"""
        <{balise}>
        <script>
        (function() {{
            const doc = window.parent.document;

            function appliquerFocus() {{
                const active = doc.activeElement;
                
                // 🛑 VÉRIFICATION : Si le curseur est DÉJÀ dans un champ, textarea ou bouton, on stoppe !
                const dejaOccupe = active && (
                    active.tagName === 'INPUT' || 
                    active.tagName === 'TEXTAREA' {verif_button}
                );

                if (dejaOccupe) {{
                    return true; // Indique qu'on n'a pas besoin de toucher au focus
                }}

                // Sinon, on cherche le champ cible et on y met le focus
                const inputs = doc.querySelectorAll('input[type="text"], input[type="password"]');
                if (inputs.length > {index}) {{
                    inputs[{index}].focus();
                    return true;
                }}
                
                return false;
            }}

            // 1. Tentative immédiate
            const fait = appliquerFocus();

            // 2. Observer de secours au cas où le champ met un instant à apparaître
            if (!fait) {{
                const observer = new MutationObserver((mutations, obs) => {{
                    if (appliquerFocus()) {{
                        obs.disconnect(); // Dès que le focus est géré ou ignoré, on stoppe l'observer
                    }}
                }});

                observer.observe(doc.body, {{ childList: true, subtree: true }});
            }}
        }})();
        </script>
        </{balise}>
        """,
        height=0,
    )
