import re
import pandas as pd
import streamlit as st
from rapidfuzz import process, fuzz
from sqlalchemy import text
from app.db import get_engine

def _season_start(season_str: str) -> int:
    m = re.match(r"^(\d{4})-(\d{4})$", str(season_str).strip())
    if not m:
        raise ValueError(f"Formato de season inválido: {season_str}")
    return int(m.group(1))

@st.cache_data(show_spinner=False, ttl=300)
def get_dim_team_df() -> pd.DataFrame:
    eng = get_engine()
    with eng.connect() as conn:
        df = pd.read_sql(
            text("SELECT teamId, teamName, countryName, season, img_logo FROM dim_team"),
            conn
        )
    expected = {"teamId", "teamName", "countryName", "season", "img_logo"}
    if not expected.issubset(df.columns):
        raise KeyError("La tabla dim_team no tiene las columnas esperadas.")
    return df

def filter_most_recent_season(df: pd.DataFrame, season_col: str = "season") -> pd.DataFrame:
    starts = df[season_col].map(_season_start)
    max_start = starts.max()
    return df[starts == max_start].copy()

def fuzzy_match_country(df: pd.DataFrame, target_country: str) -> str:
    unique_countries = df["countryName"].dropna().astype(str).unique().tolist()
    if not unique_countries:
        raise ValueError("No hay países en dim_team para la temporada más reciente.")
    best = process.extractOne(target_country, unique_countries, scorer=fuzz.WRatio)
    if not best:
        raise ValueError("No se pudo determinar país por fuzzy matching.")
    best_country, score, _ = best
    return best_country

def fuzzy_match_team(df_country: pd.DataFrame, target_team: str) -> pd.Series:
    names = df_country["teamName"].fillna("").astype(str).tolist()
    if not names:
        raise ValueError("No hay equipos en el país filtrado.")
    best = process.extractOne(target_team, names, scorer=fuzz.WRatio)
    if not best:
        raise ValueError("No se pudo determinar equipo por fuzzy matching.")
    best_name, score, _ = best
    row = df_country[df_country["teamName"] == best_name].iloc[0]
    return row

@st.cache_data(show_spinner=False, ttl=300)
def map_team_ids_to_names(team_ids: list[str]) -> pd.DataFrame:
    if not team_ids:
        return pd.DataFrame(columns=["teamId", "teamName"])

    eng = get_engine()
    with eng.connect() as conn:
        df = pd.read_sql(
            text("SELECT teamId, teamName, season FROM dim_team WHERE teamId IN :ids"),
            conn,
            params={"ids": tuple(team_ids)}
        )

    if df.empty:
        return pd.DataFrame(columns=["teamId", "teamName"])

    df["season_start"] = df["season"].map(_season_start)
    df_sorted = df.sort_values(["teamId", "season_start"], ascending=[True, False])
    df_latest = df_sorted.groupby("teamId", as_index=False).first()[["teamId", "teamName"]]
    return df_latest

@st.cache_data(show_spinner=False, ttl=300)
def map_team_ids_to_brand(team_ids: list[str]) -> pd.DataFrame:
    """
    Devuelve, para cada teamId, el teamName y img_logo de la temporada más reciente disponible.
    Columnas: teamId, teamName, img_logo
    """
    if not team_ids:
        return pd.DataFrame(columns=["teamId", "teamName", "img_logo"])

    eng = get_engine()
    with eng.connect() as conn:
        df = pd.read_sql(
            text("SELECT teamId, teamName, img_logo, season FROM dim_team WHERE teamId IN :ids"),
            conn,
            params={"ids": tuple(set(team_ids))}
        )

    if df.empty:
        return pd.DataFrame(columns=["teamId", "teamName", "img_logo"])

    # Ordena por inicio de season (desc) y toma la más reciente por teamId
    df["season_start"] = (
        df["season"].astype(str).str.extract(r"^(\d{4})", expand=False).fillna("0").astype(int)
    )
    df = df.sort_values(["teamId", "season_start"], ascending=[True, False])
    latest = df.groupby("teamId", as_index=False).first()[["teamId", "teamName", "img_logo"]]
    return latest