# -*- coding: utf-8 -*-
import streamlit as st
import io, base64
from PIL import Image
import re

# Módulos de la app
from app.config import get_settings
from app.theme import fetch_theme_or_fail
from app.services.images import fetch_raster_image, to_data_uri, download_image_bytes, normalize_png_for_favicon
from app.services.teams import (
    get_dim_team_df, filter_most_recent_season,
    fuzzy_match_country, fuzzy_match_team, map_team_ids_to_names,
    map_team_ids_to_brand
)
from app.services.fixtures import (
    get_fixture_rivals, get_last_matches,
    get_first_future_fixture_for_base, get_latest_venue_and_code_for_home_team,
    get_next_fixture_vs_rival, get_sw_match_data_for_team
)
from app.ui.styles import render_custom_css
from app.ui.header import render_match_header


from app.table_builders import _pc_corners, team_stats_detailed
from pathlib import Path
import pandas as pd

import tempfile

# NEW: pipeline que escribe los CSVs desde MySQL replicando la lógica del notebook
from app.services.pipeline_db import build_all_and_save

# ==============================================
# 1) Cargar configuración y tema
# ==============================================
settings = get_settings()

try:
    THEME = fetch_theme_or_fail(settings.THEME_URL)
except Exception as e:
    st.error(f"Error cargando el tema desde la sheet: {e}")
    st.stop()

# Alias de colores
GRAD_TOP    = THEME["gradient_top"]
GRAD_BOTTOM = THEME["gradient_bottom"]
TEXT_COLOR  = THEME["text"]
BTN_BG      = THEME["button_bg"]
BTN_TEXT    = THEME["button_text"]

# ==============================================
# 2) Carga datos iniciales (dim_team) + fuzzy
# ==============================================
try:
    dim_team_df = get_dim_team_df()
except Exception as e:
    st.error(f"Error conectando/consultando la base de datos: {e}")
    st.stop()

try:
    df_team_recent = filter_most_recent_season(dim_team_df, season_col="season")
    best_country = fuzzy_match_country(df_team_recent, THEME["country"])
    sub = df_team_recent[df_team_recent["countryName"] == best_country].copy()
    selected_row = fuzzy_match_team(sub, THEME["team"])
except Exception as e:
    st.error(f"Error en fuzzy matching (country/team): {e}")
    st.stop()

BASE_TEAM_ID = str(selected_row["teamId"])
BASE_TEAM_NAME = str(selected_row["teamName"])
LOGO_URL = str(selected_row["img_logo"])

# ==============================================
# 3) Descargar escudo (favicon/cabecera)
# ==============================================
try:
    logo_bytes, logo_ctype = fetch_raster_image(LOGO_URL)
    raw = download_image_bytes(LOGO_URL)
    favicon_png = normalize_png_for_favicon(raw, size=64, remove_alpha=False)
except Exception as e:
    st.error(f"No se pudo usar img_logo de la BD: {e}")
    st.stop()

# ==============================================
# 4) Page Config y estilos
# ==============================================
st.set_page_config(
    page_title="Generador de informe prepartido",
    page_icon=Image.open(io.BytesIO(favicon_png)),
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_custom_css(
    grad_top=GRAD_TOP, grad_bottom=GRAD_BOTTOM, text_color=TEXT_COLOR,
    btn_bg=BTN_BG, btn_text=BTN_TEXT
)

# ==============================================
# 5) Cabecera
# ==============================================
header_ph = st.container()

# ==============================================
# 6) Rival: dropdown + mapeo de nombres
# ==============================================
try:
    rivals_df = get_fixture_rivals(BASE_TEAM_ID)
    rival_ids = rivals_df["rival_id"].dropna().astype(str).unique().tolist()
    id2name_df = map_team_ids_to_names(rival_ids)  # teamId, teamName
    id_to_name = dict(zip(id2name_df["teamId"].astype(str), id2name_df["teamName"].astype(str)))
    rivals_sorted = sorted(id_to_name.items(), key=lambda kv: kv[1].lower())
    team_options_names = [name for (_id, name) in rivals_sorted]
    name_to_id = {name: _id for (_id, name) in rivals_sorted}
except Exception as e:
    st.error(f"Error preparando el listado de rivales: {e}")
    st.stop()

# Calcular rival por defecto y datos del primer FUTURO
default_index = None
upcoming = None
try:
    upcoming = get_first_future_fixture_for_base(BASE_TEAM_ID)
    if upcoming is not None:
        default_rival_id = str(upcoming["rival_id"])
        default_rival_name = id_to_name.get(default_rival_id)
        if default_rival_name in team_options_names:
            default_index = team_options_names.index(default_rival_name)
        st.session_state["__default_matchday_idx"] = int(upcoming["matchday"])
except Exception as e:
    st.info(f"No se pudo calcular el rival por defecto: {e}")
    default_index = None

# ==============================================
# 7) UI principal
# ==============================================
row1 = st.columns([2, 1, 1], gap="large")

with row1[0]:
    # Si falla el cálculo del default, caemos al primer elemento (si existe)
    safe_index = default_index if default_index is not None else (0 if team_options_names else 0)
    selected_team_name = st.selectbox(
        "Equipo Rival",
        options=team_options_names,
        index=safe_index,
        placeholder="Selecciona un equipo..."
    )
    selected_team_id = name_to_id.get(selected_team_name) if selected_team_name else None

    # ===== Título de cabecera + escudos (recalculado según el RIVAL seleccionado) =====
    matchday_text = None
    matchday_secondary = None
    away_logo_bytes = None
    away_logo_ctype = None

    try:
        if selected_team_id:
            pair_upcoming = get_next_fixture_vs_rival(BASE_TEAM_ID, selected_team_id)
            if pair_upcoming is not None:
                yyyy_mm_dd = str(pair_upcoming["date"]).strip()
                hhmm = str(pair_upcoming["time"]).strip()[:5]
                matchday_num = int(pair_upcoming["matchday"])
                ha_flag = str(pair_upcoming["ha"])

                # Venue: SIEMPRE del equipo local del fixture
                home_team_id = str(pair_upcoming["home_team"]).strip()
                venue_name, _ = get_latest_venue_and_code_for_home_team(home_team_id)
                venue_str = venue_name or "Venue no disponible"

                # Código: SIEMPRE el del RIVAL
                rival_team_id = str(pair_upcoming["rival_id"]).strip()
                _, rival_code = get_latest_venue_and_code_for_home_team(rival_team_id)
                code_str = rival_code or "CODE?"

                # Textos (no se imprimen en UI; irán a debug)
                matchday_text = f"Matchday {matchday_num} | {yyyy_mm_dd} {hhmm} h | {venue_str}"
                matchday_secondary = f"Matchday {matchday_num} | {code_str} ({ha_flag})"

                st.session_state["__matchday_num"] = matchday_num
                st.session_state["__ha_flag"] = ha_flag
                st.session_state["__rival_name"] = selected_team_name

                # === Season desde el fixture seleccionado (fallback: upcoming) ===
                season_val = None
                try:
                    if pair_upcoming is not None and pair_upcoming.get("season"):
                        season_val = str(pair_upcoming["season"])
                    elif upcoming is not None and upcoming.get("season"):
                        season_val = str(upcoming["season"])
                except Exception:
                    season_val = None
                st.session_state["__season"] = season_val

                # Logos: local (izq) y visitante (dcha)
                away_team_id = str(pair_upcoming["away_team"]).strip()
                brand_df = map_team_ids_to_brand([home_team_id, away_team_id])
                id_to_logo = dict(zip(brand_df["teamId"].astype(str), brand_df["img_logo"].astype(str)))

                # Descarga de logos (con fallbacks)
                home_logo_bytes = home_logo_ctype = None
                try:
                    home_logo_url = id_to_logo.get(home_team_id)
                    if home_logo_url:
                        home_logo_bytes, home_logo_ctype = fetch_raster_image(home_logo_url)
                except Exception:
                    pass

                try:
                    away_logo_url = id_to_logo.get(away_team_id)
                    if away_logo_url:
                        away_logo_bytes, away_logo_ctype = fetch_raster_image(away_logo_url)
                except Exception:
                    pass

                if home_logo_bytes is None:
                    home_logo_bytes, home_logo_ctype = logo_bytes, "image/png"
                if away_logo_bytes is None:
                    away_logo_bytes, away_logo_ctype = logo_bytes, "image/png"

                # Pintar header superior con dos escudos y el título
                with header_ph:
                    render_match_header(
                        left_logo_bytes=home_logo_bytes, left_content_type=home_logo_ctype,
                        title=matchday_text,
                        right_logo_bytes=away_logo_bytes, right_content_type=away_logo_ctype
                    )
    except Exception as e:
        st.info(f"No se pudo construir el encabezado de Matchday: {e}")

with row1[1]:
    n_partidos = st.number_input("Número de partidos", min_value=1, max_value=100, value=10, step=1)

with row1[2]:
    st.markdown("<div class='mt-button-fix'></div>", unsafe_allow_html=True)
    gen_clicked = st.button("Generar informe PDF", use_container_width=True, key="btn_rojo_pdf")

# Título sección últimos N
st.markdown(
    f"<h3 class='section-title'>Últimos {n_partidos} partidos{' del ' + selected_team_name if selected_team_name else ''}</h3>",
    unsafe_allow_html=True
)

# Cargar últimos partidos (si hay rival)
import pandas as pd
if selected_team_id:
    try:
        matches_df = get_last_matches(selected_team_id)
        topN = matches_df.head(int(n_partidos)).copy()
        options_descriptions = topN["description"].fillna("").astype(str).tolist()
    except Exception as e:
        st.error(f"Error obteniendo últimos partidos para el equipo seleccionado: {e}")
        topN = pd.DataFrame(columns=["localDate", "localTime", "description", "home_id", "away_id", "dt"])
        options_descriptions = []
else:
    topN = pd.DataFrame(columns=["localDate", "localTime", "description", "home_id", "away_id", "dt"])
    options_descriptions = []

# === Reset de selección al cambiar de rival: seleccionar TODO por defecto ===
prev_rival_id = st.session_state.get("prev_selected_team_id")
if selected_team_id and selected_team_id != prev_rival_id:
    st.session_state["ui_partidos_sel"] = options_descriptions[:]  # copia
    st.session_state["prev_selected_team_id"] = selected_team_id
    st.session_state["ui_partidos_initialized"] = True

# Estado del multiselect — por defecto TODOS seleccionados la primera vez
current_sel = st.session_state.get("ui_partidos_sel", [])
current_sel = [x for x in current_sel if x in options_descriptions]
st.session_state["ui_partidos_sel"] = current_sel

if options_descriptions and not st.session_state.get("ui_partidos_initialized", False):
    st.session_state["ui_partidos_sel"] = options_descriptions
    st.session_state["ui_partidos_initialized"] = True

col_left, col_mid, col_right = st.columns([1, 3, 1.4], gap="large")

with col_left:
    st.markdown("<div style='margin-top: .35rem'></div>", unsafe_allow_html=True)
    if st.button("Seleccionar todo", use_container_width=True, key="btn_sel_all"):
        st.session_state["ui_partidos_sel"] = options_descriptions
    if st.button("Vaciar selección", use_container_width=True, key="btn_clear_all"):
        st.session_state["ui_partidos_sel"] = []

with col_mid:
    st.multiselect(
        "Últimos partidos",
        options=options_descriptions,
        key="ui_partidos_sel",
        label_visibility="hidden",
        placeholder="Selecciona partidos..."
    )

with col_right:
    zip_file = st.file_uploader(
        "Plantillas Word",
        type=["zip"],
        accept_multiple_files=False,
        key="u_plantillas_word_zip",
        label_visibility="hidden"
    )

partidos_seleccionados = st.session_state.get("ui_partidos_sel", [])
n_sel = len(partidos_seleccionados)

# ===============================================================
# 6.1) Ejecutar pipeline DESPUÉS de conocer los chips seleccionados
#      lastn = nº real de chips (o n_partidos si la selección está vacía)
# ===============================================================
try:
    team_name  = str(BASE_TEAM_NAME)
    rival_name = str(st.session_state.get("__rival_name") or selected_team_name or "").strip()
    season_val = str(st.session_state.get("__season") or "").strip()

    # field desde __ha_flag -> 'home' / 'away'
    ha_flag = (st.session_state.get("__ha_flag") or "").upper()
    field = "home" if ha_flag == "H" else "away"

    # lastn = chips seleccionados (si ninguno, usamos el número del widget)
    lastn = int(n_sel) if int(n_sel) > 0 else int(n_partidos)

    # competition desde dim_team_df (preferir la de esa season para el base team)
    competition = None
    try:
        if season_val:
            _cands = (
                dim_team_df[
                    (dim_team_df["teamName"].astype(str) == team_name)
                    & (dim_team_df["season"].astype(str) == season_val)
                ]["competition"].astype(str).dropna().unique().tolist()
            )
            if _cands:
                competition = _cands[0]
        if not competition:
            _tmp = dim_team_df[dim_team_df["teamName"].astype(str) == team_name]\
                    .sort_values("season", ascending=False)
            if not _tmp.empty:
                competition = str(_tmp["competition"].iloc[0])
    except Exception:
        pass
    if not competition:
        competition = "championship"

    # Evitar recomputar si no cambian los parámetros clave
    _new_params = (team_name, rival_name, season_val, field, competition, int(lastn))
    _old_params = st.session_state.get("__pipeline_params")
    if _new_params != _old_params:
        with st.spinner("Construyendo datos desde la BBDD…"):
            build_all_and_save(
                team=team_name,
                rival=rival_name,
                competition=competition,
                field=field,
                season=season_val,
                lastn=int(lastn),
                out_dir="data"
            )
        st.success(
            f"Datos actualizados:\n"
            f"  team={team_name}\n"
            f"  rival={rival_name}\n"
            f"  competition={competition}\n"
            f"  field={field}\n"
            f"  season={season_val}\n"
            f"  lastn={int(lastn)}"
        )
        st.json({
            "team": team_name,
            "rival": rival_name,
            "competition": competition,
            "field": field,
            "season": season_val,
            "lastn": int(lastn),
        })

        st.session_state["__pipeline_params"] = _new_params
except Exception as e:
    st.warning(f"⚠️ No se pudo refrescar los CSV desde BBDD: {e}")

# ==============================================
# 8) Generación y descarga automática
# ==============================================
if gen_clicked:
    if zip_file is None:
        st.error("Sube un ZIP con las plantillas Word.")
    elif selected_team_id is None or not matchday_secondary:
        st.error("Falta información del fixture para construir el texto abreviado.")
    else:
        try:
            # === SIEMPRE escudo del RIVAL (equipo_rival_id) ===
            rival_logo_bytes = None
            rival_logo_ctype = None
            try:
                brand_df = map_team_ids_to_brand([selected_team_id])
                id_to_logo = dict(zip(brand_df["teamId"].astype(str), brand_df["img_logo"].astype(str)))
                rival_logo_url = id_to_logo.get(str(selected_team_id))
                if rival_logo_url:
                    rival_logo_bytes, rival_logo_ctype = fetch_raster_image(rival_logo_url)
            except Exception:
                pass

            # Fallback final por si algo falla
            if not (rival_logo_bytes and isinstance(rival_logo_bytes, (bytes, bytearray))):
                rival_logo_bytes = logo_bytes  # al menos tenemos algo válido

            # === Generar PDF con el escudo del RIVAL ===
            ha = (st.session_state.get("__ha_flag") or "").upper()
            rival_name = st.session_state.get("__rival_name") or selected_team_name or "Rival"
            
            # Índice ascendente: usaremos el matchday como aproximación del "índice" ascendente
            fixture_idx_asc = int(st.session_state.get("__default_matchday_idx"))

            # Datos tabla page2 (últimos n_sel partidos del rival en sw_match_data)
            table_rows = []
            try:
                if rival_name and n_sel > 0:
                    table_rows = get_sw_match_data_for_team(rival_name, n_sel)
            except Exception as _:
                table_rows = []

            from hashlib import md5
            from pathlib import Path
            import re

            def _slugify(s: str) -> str:
                return re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')

            # Base absoluta: ...\app_gpt\app
            APP_DIR = Path(__file__).resolve().parent / "app"

            key_str = f"{team_name}|{rival_name}|{competition}|{field}|{season_val}|{int(lastn)}"
            key_hash = md5(key_str.encode("utf-8")).hexdigest()[:10]
            cache_dir = APP_DIR / "data" / "cache" / f"{_slugify(team_name)}__{_slugify(rival_name)}__{_slugify(season_val)}__{key_hash}"

            df_team_path = str(cache_dir / "df_team.csv")

            from app.docgen import generate_report_pdf
            pdf_bytes = generate_report_pdf(
                zip_bytes=zip_file.getvalue(),
                texto_abreviado=matchday_secondary,     # p.ej. "Matchday 7 | CHA (A)"
                rival_badge_bytes=rival_logo_bytes,
                texto_completo=matchday_text,           # p.ej. "Matchday 7 | 2025-08-09 13:30 h | The Valley "
                rival_name=rival_name,
                ha=ha,
                n_selected=n_sel,
                fixture_idx_asc=fixture_idx_asc,
                page2_table_rows=table_rows,
                df_team_path=df_team_path,               
                base_team=BASE_TEAM_NAME,                
                highlight_team=THEME["highlight_team"],  
                highlight_opp=THEME["highlight_opp"],
                base_badge_bytes=logo_bytes,
                season=st.session_state.get("__season"),  # 👈 PASAR SEASON AL DOCGEN
             )

            # === Descarga automática ===
            b64 = base64.b64encode(pdf_bytes).decode("ascii")
            md = st.session_state.get("__matchday_num")
            ha = (st.session_state.get("__ha_flag") or "").upper()
            rival_name = st.session_state.get("__rival_name") or selected_team_name or "Rival"

            safe_rival = re.sub(r'[\\/*?:"<>|]+', "-", str(rival_name)).strip()
            file_name = f"GW{md} {safe_rival} ({ha}) - ABP - SET PIECES.pdf"

            dl_html = f"""
            <html>
              <body>
                <a id="__auto_dl" href="data:application/pdf;base64,{b64}" download="{file_name}"></a>
                <script>
                  const a = document.getElementById("__auto_dl");
                  if (a) a.click();
                </script>
              </body>
            </html>
            """
            st.components.v1.html(dl_html, height=0)

        except Exception as e:
            st.error(f"Error generando PDF: {e}")
