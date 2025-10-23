import streamlit as st

def render_custom_css(grad_top: str, grad_bottom: str, text_color: str, btn_bg: str, btn_text: str) -> None:
    """
    Inyecta el CSS personalizado. Mantiene los estilos del script original
    y añade el header con dos escudos (.match-header) centrados junto al título.
    """
    CUSTOM_CSS = f"""
    <style>
    /* =================== Fondo + tipografía =================== */
    .stApp {{
        background: linear-gradient(180deg, {grad_top} 0%, {grad_bottom} 100%);
        color: {text_color};
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
    }}

    /* =================== Botones =================== */
    .stButton > button {{
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        font-weight: 700 !important;
        transition: transform 0.02s ease-in-out !important;
    }}
    .stButton > button:hover {{ transform: translateY(-1px); filter: brightness(1.02); }}

    /* =================== Multiselect: chips =================== */
    .stMultiSelect [data-baseweb="tag"] {{
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        max-width: 240px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}
    .stMultiSelect [data-baseweb="tag"] span {{ color: {btn_text} !important; }}
    .stMultiSelect [data-baseweb="tag"] svg path {{ fill: {btn_text} !important; }}

    /* =================== File uploader =================== */
    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploader"] button[kind="secondary"],
    [data-testid="stFileUploader"] button *,
    [data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderBrowseButton"] {{
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 800 !important;
        padding: .55rem 1rem !important;
        box-shadow: 0 2px 6px rgba(0,0,0,.12);
    }}

    /* =================== Labels centradas =================== */
    .stSelectbox label,
    .stNumberInput label,
    [data-testid="stFileUploader"] label {{
        display:block !important;
        text-align:center !important;
        font-weight:700 !important;
        color: {text_color} !important;
    }}

    /* =================== Títulos de sección =================== */
    .section-title {{
        text-align:center;
        font-weight:800;
        margin-top:.5rem;
        margin-bottom:.25rem;
    }}

    /* =================== Number input =================== */
    .stNumberInput button {{
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border: 1px solid {btn_bg} !important;
        box-shadow: none !important;
    }}
    .stNumberInput button svg path {{ fill: {btn_text} !important; }}
    .stNumberInput button:hover,
    .stNumberInput button:active {{
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border-color: {btn_bg} !important;
    }}
    .stNumberInput button:hover svg path,
    .stNumberInput button:active svg path {{ fill: {btn_text} !important; }}
    .stNumberInput button:focus,
    .stNumberInput button:focus:not(:focus-visible) {{
        background: {btn_bg} !important;
        border-color: {btn_bg} !important;
        box-shadow: none !important;
    }}
    .stNumberInput button:focus-visible {{
        outline: 2px solid rgba(0,0,0,.35) !important;
        outline-offset: 2px !important;
    }}

    /* =================== Header NUEVO: dos escudos + título (centrados juntos) =================== */
    .match-header {{
        display:flex; align-items:center; justify-content:center;   /* centra todo el bloque */
        gap:10px; padding:8px 4px; margin-bottom:.5rem;
    }}
    .match-header .escudo {{ height:56px; width:auto; display:block; }}
    .match-header .mh-title {{ flex:0 0 auto; text-align:center; }}  /* el título no se estira */
    .match-header .mh-title h1 {{
        margin:0; font-weight:900; font-size:2rem; color:{text_color} !important; letter-spacing:.3px;
        line-height:1.1; position: relative;
    }}

    /* ⛓️ Oculta el icono/enlace de ancla que Streamlit añade a los h1 */
    .match-header .mh-title h1 a,
    .match-header .mh-title h1 .stAnchor,
    .match-header .mh-title h1 .anchor-link,
    .match-header .mh-title h1 svg {{
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        pointer-events: none !important;
    }}

    @media (max-width: 640px) {{
        .match-header .escudo {{ height:44px; }}
        .match-header .mh-title h1 {{ font-size:1.25rem; }}
    }}

    /* =================== (Opcional) Header antiguo — ya no usado, pero no molesta =================== */
    .app-header {{
        display:flex; align-items:center; gap:12px; padding:8px 4px; justify-content:center;
    }}
    .app-header h1 {{
        margin:0; font-weight:900; font-size:2.4rem; color:{text_color} !important; text-align:center; letter-spacing:.3px;
    }}
    .app-header img.escudo {{ height:60px; width:auto; display:block; }}

    /* =================== Utilidades =================== */
    .mt-button-fix {{ margin-top: 24px; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    .stApp::before, .stApp::after {{ content: none !important; display: none !important; }}
    </style>
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
