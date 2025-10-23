# app/services/pipeline_db.py
# -*- coding: utf-8 -*-

"""
Pipeline que replica EXACTAMENTE la lógica del notebook y escribe los CSVs
que consume la app (data/df.csv, data/df_team.csv, data/df_agr_pair.csv,
data/df_jug_team.csv, data/df_players.csv).

Depende de:
- app/utils_bbdd.py  (get_conn, clean_df)
- app/fun_calculo_metricas.py  (transform_events_agg, calcula_medidas_secuencia, calcula_medidas_compuestas)
- app/config/config.json
- app/config/query_scope.txt
- app/config/series_config_abp.json
- app/config/series_config_secuencia.json
- Tablas: dim_team, dim_player, dim_position, dim_competition, dim_competition_season, fact_team_stats,
          dim_formation, sw_match_data, sw_player_data, fact_player_season
"""

from __future__ import annotations

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

from app.utils_bbdd import get_conn, clean_df as ub_clean
import app.fun_calculo_metricas as cm
import streamlit as st
from sqlalchemy.engine import Engine

# ---------------------------------------------------------------------
# Utilidades equivalentes a las del notebook
# ---------------------------------------------------------------------
def print_header_time(msg: str | None = None) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = msg if msg else "Timestamp"
    print("\n" + "=" * 50)
    print(f"⏰ {text}: {ts}")
    print("=" * 50 + "\n")


def get_series_config(ruta_config: str) -> dict:
    """Lee un JSON de configuración de series."""
    with open(f"{ruta_config}.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_query(ruta: str = "app/config/query_scope.txt") -> str:
    """Lee y compacta el SQL del scope (sin saltos/indentación)."""
    with open(ruta, "r", encoding="utf-8") as f:
        query = f.read()
    query = " ".join(line.strip() for line in query.splitlines())
    return query


# ---------------------------------------------------------------------
# Funciones de acceso a BBDD (equivalentes a las del notebook)
# ---------------------------------------------------------------------
def looper(conn) -> pd.DataFrame:
    lp = pd.read_sql("""select distinct season, competition from dim_team""", conn)
    return ub_clean(lp)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_events_bbdd(query: str, conn) -> pd.DataFrame:
    event_data = pd.read_sql(query, conn)
    return ub_clean(event_data)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_dim_competition_season(conn) -> pd.DataFrame:
    df = pd.read_sql("""select distinct * from dim_competition_season""", conn)
    return ub_clean(df)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_dim_competition(conn) -> pd.DataFrame:
    df = pd.read_sql("""select distinct * from dim_competition""", conn)
    return ub_clean(df)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_dim_team(season: str, competition: str, conn) -> pd.DataFrame:
    df = pd.read_sql(
        f"""select distinct * 
            from dim_team 
           where season = '{season}' and competition = '{competition}'""",
        conn,
    )
    return ub_clean(df)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_match_data(match_id: str, conn) -> pd.DataFrame:
    df = pd.read_sql(
        f"""select distinct * 
              from sw_match_data 
             where matchId = '{match_id}'""",
        conn,
    )
    return ub_clean(df)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_player_data(match_id: str, conn) -> pd.DataFrame:
    df = pd.read_sql(
        f"""select distinct * 
              from sw_player_data 
             where matchId = '{match_id}'""",
        conn,
    )
    return ub_clean(df)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_dim_player(conn) -> pd.DataFrame:
    df = pd.read_sql("""select distinct * from dim_player where actual_sn = 1""", conn)
    return ub_clean(df)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_teamstats(team_name: str, conn) -> pd.DataFrame:
    df = pd.read_sql(
        f"""
        select 
            ts.field,
            ts.teamId,
            ts.teamName,
            ts.matchId,
            ts.changes_num,
            df.*,
            md.competition,
            md.season
        from fact_team_stats ts
        left join dim_formation df
               on df.team_formation = ts.team_formation
        left join sw_match_data md
               on md.matchId = ts.matchId
        where ts.teamName = '{team_name}'
        """,
        conn,
    )
    return ub_clean(df)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_dim_position(conn) -> pd.DataFrame:
    df = pd.read_sql("""select distinct * from dim_position""", conn)
    return ub_clean(df)

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_playerstats(season: str, conn) -> pd.DataFrame:
    """
    Agrega por playerId y flags de lanzadores, sumando métricas por la(s) temporada(s) que empiecen
    por la primera parte de `season` (p. ej., '2025-2026' -> '2025%').
    """
    base = season.split("-")[0]
    sql = f"""
        with seasons as (
            select distinct season
            from dim_competition_season
            where season like '%{base}%'
        )
        select
            playerId,
            ss.season,
            goals_sp, xg_sp, shots_sp,
            passes_sp, passes_succ_sp,
            actions_fromcorner, actions_succ_fromcorner,
            actions_fromifk, actions_succ_fromifk,
            actions_fromifkbox, actions_succ_fromifkbox,
            actions_fromthrowinbox, actions_succ_fromthrowinbox,
            shots_fromdfk, xg_fromdfk,
            case when shots_fromdfk > 0 then 1 else 0 end as dfk_taker_sn,
            case when actions_fromifkbox > 0 then 1 else 0 end as ifk_taker_sn,
            case when actions_fromthrowinbox > 0 then 1 else 0 end as throwin_taker_sn,
            case when actions_fromcorner > 0 then 1 else 0 end as corner_taker_sn
        from fact_player_season pp
        inner join seasons ss on ss.season = pp.season
    """
    df = pd.read_sql(sql, conn)
    df = ub_clean(df)
    df_gr = (
        df.groupby(
            by=[
                "playerId",
                "dfk_taker_sn",
                "ifk_taker_sn",
                "throwin_taker_sn",
                "corner_taker_sn",
            ],
            as_index=False,
        )[
            [
                "goals_sp",
                "xg_sp",
                "shots_sp",
                "passes_sp",
                "passes_succ_sp",
                "actions_fromcorner",
                "actions_succ_fromcorner",
                "actions_fromifk",
                "actions_succ_fromifk",
                "actions_fromifkbox",
                "actions_succ_fromifkbox",
                "actions_fromthrowinbox",
                "actions_succ_fromthrowinbox",
                "shots_fromdfk",
                "xg_fromdfk",
            ]
        ].sum()
    )
    return df_gr

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={Engine: lambda _: None})
def get_players(dft: pd.DataFrame, equipo: str, rival: str, season: str, conn) -> pd.DataFrame:
    """
    Replica el flujo del notebook: reúne plantilla implicada en los matchId de dft y
    enriquece con dim_player, teamName, stats y posición.
    """
    df_players = pd.DataFrame()

    # 1) Squad  dorsales de los partidos implicados por equipo/rival
    mask = (dft["teamName"] == equipo) | (dft["teamName"] == rival)
    for m in dft.loc[mask, "matchId"].dropna().unique():
        pl = get_player_data(m, conn)
        df_players = pd.concat([df_players, pl], ignore_index=True)

    # 2) Catálogos
    jugadores = get_dim_player(conn)
    positions = get_dim_position(conn)  # <-- ASIGNAMOS ANTES DE CUALQUIER USO

    # 3) Teams vinculados a dft (idéntico a notebook)
    teams = (
        dft.loc[mask, ["teamId", "teamName"]]
           .drop_duplicates(subset="teamId", keep="first")
           .copy()
    )

    # 4) Activos de la season  dorsal (si hay)
    df_players = pd.merge(
        jugadores[(jugadores["season"] == season) & (jugadores["teamId"].isin(teams["teamId"].unique()))],
        df_players[["playerId", "shirtNo"]],
        how="left",
        on="playerId",
    )

    # 5) Añadir teamName
    df_players = pd.merge(df_players, teams, how="left", on="teamId")

    # 6) Stats y posición (1 solo merge con 'positions', después de asignarlo)
    stats = get_playerstats(season, conn)
    df_players = pd.merge(df_players, stats, how="left", on=["playerId"])
    df_players = pd.merge(
        df_players,
        positions[["position_data", "orden"]],
        how="left",
        left_on="position",
        right_on="position_data",
    )

    # 7) Columna POS (como en el notebook)
    if "position" in df_players.columns:
        if "position2" not in df_players.columns:
            df_players["position2"] = np.nan
        df_players["POS"] = np.where(
            df_players["position2"].isna(),
            df_players["position"],
            df_players["position"] + "/" + df_players["position2"],
        )

    df_players = df_players.drop_duplicates(subset=["playerId", "season"], keep="first")
    return df_players


# ---------------------------------------------------------------------
# Núcleo del pipeline (equivale al flujo del notebook)
# ---------------------------------------------------------------------
def _compute_local_visitante(field: str, equipo: str, rival: str) -> tuple[str, str]:
    if str(field).strip().lower() == "home":
        return equipo, rival
    else:
        return rival, equipo

from pathlib import Path
APP_DIR = Path(__file__).resolve().parents[1]   # .../app
DEFAULT_DATA_DIR = APP_DIR / "data"

def build_all_and_save(
    team: str,
    rival: str,
    competition: str,
    field: str,
    season: str,
    lastn: int,
    out_dir: str | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Ejecuta TODA la lógica del notebook y escribe los CSVs en `out_dir` con los nombres
    que espera la app. Devuelve los DataFrames por si se quieren usar en memoria.

    Salidas:
      - df                 -> data/df.csv
      - df_team            -> data/df_team.csv
      - df_agr_pair        -> data/df_agr_pair.csv
      - df_jug_team        -> data/df_jug_team.csv
      - df_players         -> data/df_players.csv
    """
    # --- CACHE HIT: si ya tenemos los CSV para EXACTAMENTE esta combinación, devolvemos al instante
    import hashlib, shutil, re
    from pathlib import Path

    def _slugify(s: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')

    # Usamos el mismo directorio base de datos que el resto de la app
    cache_root = (DEFAULT_DATA_DIR / "cache")
    cache_root.mkdir(parents=True, exist_ok=True)

    key_str = f"{team}|{rival}|{competition}|{field}|{season}|{int(lastn)}"
    key_hash = hashlib.md5(key_str.encode("utf-8")).hexdigest()[:10]
    cache_dir = cache_root / f"{_slugify(team)}__{_slugify(rival)}__{_slugify(season)}__{key_hash}"

    expected = {
        "df": cache_dir / "df.csv",
        "df_team": cache_dir / "df_team.csv",
        "df_agr_pair": cache_dir / "df_agr_pair.csv",
        "df_jug_team": cache_dir / "df_jug_team.csv",
        "df_players": cache_dir / "df_players.csv",
    }
    
    if all(p.exists() for p in expected.values()):
        # Devolver directos desde cache (NO copiar a data/)
        return {
            "df": pd.read_csv(expected["df"]),
            "df_team": pd.read_csv(expected["df_team"]),
            "df_agr_pair": pd.read_csv(expected["df_agr_pair"]),
            "df_jug_team": pd.read_csv(expected["df_jug_team"]),
            "df_players": pd.read_csv(expected["df_players"]),
        }

    # --- Si no hay caché, seguimos con el pipeline normal
    print_header_time("Inicio pipeline_db")

    # Nos aseguramos de que la carpeta de cache exista
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 1) Parámetros derivados: local/visitante
    local, visitante = _compute_local_visitante(field, team, rival)

    # 2) Conexión
    conn = get_conn("app/config")

    # 3) Cargar config y query
    series_config_abp = get_series_config("app/config/series_config_abp")
    series_config_secuencia = get_series_config("app/config/series_config_secuencia")
    query_tpl = get_query("app/config/query_scope.txt")

    # 4) Preparar query final (mismo order del notebook: equipo, equipo, local, visitante, season, competition, local, visitante, lastn)
    #    OJO: se respeta el orden de placeholders de tu query_scope.txt
    query = query_tpl.format(team, team, local, visitante, season, competition, local, visitante, lastn)

    # 5) Lecturas base
    events = get_events_bbdd(query, conn)
    dim_competition_season = get_dim_competition_season(conn)
    dim_competition = get_dim_competition(conn)
    teams = get_dim_team(season, competition, conn)

    # 6) Transformaciones de eventos a nivel acción/posesión
    dft_base = cm.transform_events_agg(events, series_config_abp, ["id", "teamId", "teamName"])
    dft = pd.merge(events, dft_base, how="left", on=["id", "teamId", "teamName"])

    # 7) Secuencias por partido
    df = pd.DataFrame()
    for match in dft["matchId"].dropna().unique():
        dfg = dft[dft["matchId"] == match].copy()
        dfg = cm.calcula_medidas_secuencia(dfg, series_config_secuencia)
        df = pd.concat([df, dfg], ignore_index=True)

    df = df.fillna(0)

    # 8) Info de partido (fechas) y merge
    df_match = pd.DataFrame()
    for m in dft["matchId"].dropna().unique():
        match_df = get_match_data(m, conn)
        df_match = pd.concat([df_match, match_df], ignore_index=True)

    if not df_match.empty and "matchId" in df_match.columns and "localDate" in df_match.columns:
        df = pd.merge(df, df_match[["matchId", "localDate"]], how="left", on="matchId")

    # === 8.b) REPLICA NOTEBOOK: df_team_system (para Page 4) ===
    #     Equivale a get_team_system(df_match, rival, conn)
    try:
        # 1) Team stats del RIVAL (como en tu notebook)
        df_ts = get_teamstats(rival, conn)

        # 2) Merge con info de partido para tener home/away/localDate/week
        #    (df_match ya lo has construido en el paso 8)
        cols_match = [c for c in ["home_name", "away_name", "matchId", "week", "localDate"] if c in df_match.columns]
        if "matchId" in df_ts.columns and cols_match:
            df_team_system = pd.merge(
                df_ts,
                df_match[cols_match],
                how="inner",
                on="matchId"
            )
        else:
            # Si por algún motivo no hay columnas, deja un DF vacío pero con columnas clave
            df_team_system = pd.DataFrame(columns=[
                "teamName","home_name","away_name","localDate","field","team_formation_desc","changes_num","matchId"
            ])

        # 3) Guarda EXACTAMENTE lo que tu notebook pasaba al builder
        df_team_system.to_csv(cache_dir / "df_team_system.csv", index=False)

    except Exception as e:
        # No rompas el pipeline por esto; la docgen hará fallback si no está
        pd.DataFrame().to_csv(cache_dir / "df_team_system.csv", index=False)

    # 9) Agregados (team, opposition, pair)
    #    Columnas numéricas: todas las que no están en events ni en df_match
    events_cols = set(events.columns)
    match_cols = set(df_match.columns) if not df_match.empty else set()
    cols_df = [c for c in df.columns if c not in events_cols and c not in match_cols]

    # teamName
    df_agr = df.groupby(by=["teamName"], as_index=False)[cols_df].sum()

    # oppositionTeamName
    df_agr_agg = df.groupby(by=["oppositionTeamName"], as_index=False)[cols_df].sum()

    # pair (teamName, oppositionTeamName)
    # - localDate: min
    # - resto: suma
    agg_dict = {"localDate": "min"}
    for c in cols_df:
        if c != "localDate":
            agg_dict[c] = "sum"

    df_agr_pair = (
        df.groupby(by=["teamName", "oppositionTeamName"], as_index=False)
        .agg(agg_dict)
        .copy()
    )

    # 10) Medidas compuestas en df / df_agr / df_agr_agg / df_agr_pair
    for dd in [df, df_agr, df_agr_agg, df_agr_pair]:
        cm.calcula_medidas_compuestas(dd)

    # 11) Prefijo opp_ para df_agr_agg (todas las columnas salvo las de nombres de equipo)
    df_agr_agg_ren = df_agr_agg.copy()
    for col in list(df_agr_agg_ren.columns):
        if "team" not in col.lower():
            df_agr_agg_ren.rename(columns={col: f"opp_{col}"}, inplace=True)

    # 12) df_team = merge df_agr (team) con df_agr_agg prefijado (opposition) por teamName/oppositionTeamName
    df_team = pd.merge(
        df_agr,
        df_agr_agg_ren,
        how="left",
        left_on="teamName",
        right_on="oppositionTeamName",
    )

    # 13) Filtrar df_team a equipos existentes en dim_team
    if "teamName" in teams.columns:
        df_team = df_team[df_team["teamName"].isin(teams["teamName"].unique())]

    # 14) df_jug_team: agregación por jugador sobre cols_df
    df_jug_team = (
        df.groupby(by=["playerId", "playerName"], as_index=False)[cols_df].sum().copy()
    )

    # 14.1) **Notebook parity**: limitar a jugadores del RIVAL de este análisis
    # (en el notebook: df_jug_team = df_jug[df_jug.playerId.isin(df[df.teamName==rival].playerId.unique())])
    rival_player_ids = (
        df.loc[df["teamName"] == rival, "playerId"].dropna().unique()
        if "playerId" in df.columns and "teamName" in df.columns else []
    )
    df_jug_team = df_jug_team[df_jug_team["playerId"].isin(rival_player_ids)].copy()

    # 14.2) **Notebook parity**: calcular medidas compuestas (e.g. columnas *_pct) también a nivel jugador
    # En el notebook existen columnas de % en df_jug_team; aquí replicamos ese paso.
    cm.calcula_medidas_compuestas(df_jug_team)

    # 15) Añadir columna games = lastn a df_team y df_jug_team
    for dd in [df_team, df_jug_team]:
        dd["games"] = lastn

    # 16) df_players: plantilla enriquecida
    df_players = get_players(dft, team, rival, season, conn)

    # 17) Guardar SOLO en cache
    pd.DataFrame(df).to_csv(cache_dir / "df.csv", index=False)
    pd.DataFrame(df_team).to_csv(cache_dir / "df_team.csv", index=False)
    pd.DataFrame(df_agr_pair).to_csv(cache_dir / "df_agr_pair.csv", index=False)
    pd.DataFrame(df_jug_team).to_csv(cache_dir / "df_jug_team.csv", index=False)
    pd.DataFrame(df_players).to_csv(cache_dir / "df_players.csv", index=False)

    # --- CACHE SAVE: guardar también en caché persistente esta combinación
    import hashlib, re
    from pathlib import Path

    def _slugify(s: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')

    cache_root = (DEFAULT_DATA_DIR / "cache")
    cache_root.mkdir(parents=True, exist_ok=True)

    key_str = f"{team}|{rival}|{competition}|{field}|{season}|{int(lastn)}"
    key_hash = hashlib.md5(key_str.encode("utf-8")).hexdigest()[:10]
    cache_dir = cache_root / f"{_slugify(team)}__{_slugify(rival)}__{_slugify(season)}__{key_hash}"
    cache_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(df).to_csv(cache_dir / "df.csv", index=False)
    pd.DataFrame(df_team).to_csv(cache_dir / "df_team.csv", index=False)
    pd.DataFrame(df_agr_pair).to_csv(cache_dir / "df_agr_pair.csv", index=False)
    pd.DataFrame(df_jug_team).to_csv(cache_dir / "df_jug_team.csv", index=False)
    pd.DataFrame(df_players).to_csv(cache_dir / "df_players.csv", index=False)

    return {
        "df": df,
        "df_team": df_team,
        "df_agr_pair": df_agr_pair,
        "df_jug_team": df_jug_team,
        "df_players": df_players,
    }
