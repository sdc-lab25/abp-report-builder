import json
import requests
import streamlit as st
from app.utils.colors import as_hex

@st.cache_data(show_spinner=False, ttl=300)
def fetch_theme(url: str) -> dict:
    """
    Descarga un JSON de tema desde un endpoint (Google Apps Script).
    Valida claves requeridas y normaliza colores HEX.
    """
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    try:
        raw = r.json()
    except json.JSONDecodeError:
        raw = json.loads(r.text)

    required_keys = [
        "country", "team",
        "gradient_top", "gradient_bottom",
        "text", "button_bg", "button_text",
        "highlight_team", "highlight_opp"
    ]
    for k in required_keys:
        if k not in raw:
            raise KeyError(f"Falta la clave '{k}' en el JSON del tema.")

    for ck in ["gradient_top", "gradient_bottom", "text", "button_bg", "button_text", "highlight_team", "highlight_opp"]:
        raw[ck] = as_hex(raw[ck])

    return {k: raw[k] for k in required_keys}

def fetch_theme_or_fail(url: str) -> dict:
    """
    En producción no queremos fallback silencioso: si falla, paramos.
    """
    return fetch_theme(url)
