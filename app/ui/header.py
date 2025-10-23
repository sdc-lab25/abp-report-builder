import streamlit as st
from app.services.images import to_data_uri

def render_match_header(
    left_logo_bytes: bytes, left_content_type: str, title: str,
    right_logo_bytes: bytes, right_content_type: str
) -> None:
    """
    Encabezado con dos escudos (izquierda: local, derecha: visitante) y
    el título centrado (Matchday | fecha hora | estadio).
    """
    left_uri = to_data_uri(left_logo_bytes, content_type=left_content_type)
    right_uri = to_data_uri(right_logo_bytes, content_type=right_content_type)
    st.markdown(
        f"""
        <div class="match-header">
            <img class="escudo left" src="{left_uri}" />
            <div class="mh-title"><h1>{title}</h1></div>
            <img class="escudo right" src="{right_uri}" />
        </div>
        """,
        unsafe_allow_html=True
    )