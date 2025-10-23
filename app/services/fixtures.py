import pandas as pd
import streamlit as st
from sqlalchemy import text
from datetime import datetime
import pytz
from app.db import get_engine
from app.config import get_settings

@st.cache_data(show_spinner=False, ttl=300)
def get_fixture_rivals(team_id: str) -> pd.DataFrame:
    eng = get_engine()
    with eng.connect() as conn:
        df_fix = pd.read_sql(text("SELECT home_team, away_team, season FROM dim_fixture"), conn)

    if df_fix.empty:
        raise ValueError("dim_fixture está vacía.")

    # Filtrar temporada más reciente
    def _season_start(s: str) -> int:
        s = str(s).strip()
        return int(s.split("-")[0]) if "-" in s else int(s)

    df_fix["season_start"] = df_fix["season"].map(_season_start)
    max_start = df_fix["season_start"].max()
    df_fix_recent = df_fix[df_fix["season_start"] == max_start].copy()

    mask = (df_fix_recent["home_team"] == team_id) | (df_fix_recent["away_team"] == team_id)
    df_team_fixtures = df_fix_recent.loc[mask].copy()
    if df_team_fixtures.empty:
        raise ValueError("No hay fixtures del equipo base en la temporada más reciente de dim_fixture.")

    def _rival(row):
        return row["away_team"] if row["home_team"] == team_id else row["home_team"]

    df_team_fixtures["rival_id"] = df_team_fixtures.apply(_rival, axis=1)
    rivals = df_team_fixtures[["rival_id"]].drop_duplicates().reset_index(drop=True)
    return rivals

@st.cache_data(show_spinner=False, ttl=300)
def get_last_matches(team_id: str) -> pd.DataFrame:
    eng = get_engine()
    sql = text("""
        SELECT home_id, away_id, localDate, localTime, description
        FROM sw_match_data
        WHERE home_id = :tid OR away_id = :tid
        ORDER BY localDate DESC, localTime DESC
    """)
    with eng.connect() as conn:
        df = pd.read_sql(sql, conn, params={"tid": team_id})

    df["localDate"] = df["localDate"].astype(str).str.strip()
    df["localTime"] = df["localTime"].astype(str).str.strip()
    df["dt"] = pd.to_datetime(
        df["localDate"] + " " + df["localTime"],
        errors="coerce",
        format="%Y-%m-%d %H:%M:%S"
    )
    df = df.sort_values("dt", ascending=False, na_position="last").reset_index(drop=True)
    return df

@st.cache_data(show_spinner=False, ttl=300)
def get_first_future_fixture_for_base(base_team_id: str) -> pd.Series | None:
    """
    Devuelve el PRIMER registro de dim_fixture cuya fecha/hora sea > ahora (Europe/Madrid),
    tras ordenar ASC por date y time. Incluye:
      - date (YYYY-MM-DD)
      - time (HH:MM:SS)
      - home_team, away_team
      - rival_id (id del rival del base_team_id)
      - ha ("H" si base es local, "A" si base es visitante)
      - matchday (índice 1-based dentro del orden ASC)
    """
    eng = get_engine()
    with eng.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT home_team, away_team, `date`, `time`, season
                FROM dim_fixture
                WHERE home_team = :tid OR away_team = :tid
                ORDER BY `date` ASC, `time` ASC
            """),
            conn,
            params={"tid": base_team_id}
        )

    if df.empty:
        return None

    # Parse/orden/filtra por futuro (Europe/Madrid)
    tz = pytz.timezone(get_settings().TZ)
    df["date"] = df["date"].astype(str).str.strip()
    df["time"] = df["time"].astype(str).str.strip()
    df["dt"] = pd.to_datetime(df["date"] + " " + df["time"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["dt"]).copy()
    if df.empty:
        return None

    df["dt"] = df["dt"].apply(lambda x: tz.localize(x) if x.tzinfo is None else x.astimezone(tz))
    now = datetime.now(tz)

    df = df.sort_values(["date", "time"], ascending=[True, True]).reset_index(drop=True)

    # Primer futuro
    fut_mask = df["dt"] > now
    if not fut_mask.any():
        return None

    idx = fut_mask.idxmax()  # primer True
    row = df.loc[idx].copy()

    # Rival y H/A
    if str(row["home_team"]) == str(base_team_id):
        rival_id = str(row["away_team"])
        ha = "H"
    else:
        rival_id = str(row["home_team"])
        ha = "A"

    # matchday 1-based = posición + 1
    matchday = int(idx) + 1

    # Devolver como Serie con campos útiles
    return pd.Series({
        "date": str(row["date"]),
        "time": str(row["time"]),
        "home_team": str(row["home_team"]),
        "away_team": str(row["away_team"]),
        "rival_id": rival_id,
        "ha": ha,
        "matchday": matchday,
        "season": str(row["season"]),
    })


@st.cache_data(show_spinner=False, ttl=300)
def get_latest_venue_and_code_for_home_team(team_id: str) -> tuple[str | None, str | None]:
    """
    Busca en sw_match_data el registro MÁS RECIENTE donde home_id = team_id
    y devuelve (venueName, home_code).
    """
    eng = get_engine()
    with eng.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT venueName, home_code, localDate, localTime
                FROM sw_match_data
                WHERE home_id = :hid
                ORDER BY localDate DESC, localTime DESC
                LIMIT 1
            """),
            conn,
            params={"hid": team_id}
        )

    if df.empty:
        return None, None

    venue = str(df["venueName"].iloc[0] or "").strip() or None
    home_code = str(df["home_code"].iloc[0] or "").strip() or None
    return venue, home_code

@st.cache_data(show_spinner=False, ttl=300)
def get_next_fixture_vs_rival(base_team_id: str, rival_team_id: str) -> pd.Series | None:
    """
    Devuelve el PRIMER enfrentamiento FUTURO entre base_team_id y rival_team_id
    (ordenado ASC por fecha/hora) y su 'matchday' como el índice (1-based)
    dentro del calendario ASC del base_team_id.

    Retorna Serie con: date, time, home_team, away_team, ha ("H"/"A"), matchday, rival_id.
    """
    eng = get_engine()
    with eng.connect() as conn:
        # 1) Todos los enfrentamientos entre ambos equipos (ASC)
        df_pair = pd.read_sql(
            text("""
                SELECT home_team, away_team, `date`, `time`, season
                FROM dim_fixture
                WHERE (home_team = :a AND away_team = :b) OR (home_team = :b AND away_team = :a)
                ORDER BY `date` ASC, `time` ASC
            """),
            conn,
            params={"a": base_team_id, "b": rival_team_id}
        )

        if df_pair.empty:
            return None

        # 2) Calendario completo del base (ASC) para calcular matchday = índice 1-based
        df_base = pd.read_sql(
            text("""
                SELECT home_team, away_team, `date`, `time`, season
                FROM dim_fixture
                WHERE home_team = :tid OR away_team = :tid
                ORDER BY `date` ASC, `time` ASC
            """),
            conn,
            params={"tid": base_team_id}
        )

    tz = pytz.timezone(get_settings().TZ)
    def _prep(df):
        df = df.copy()
        df["date"] = df["date"].astype(str).str.strip()
        df["time"] = df["time"].astype(str).str.strip()
        df["dt"] = pd.to_datetime(df["date"] + " " + df["time"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["dt"])
        df["dt"] = df["dt"].apply(lambda x: tz.localize(x) if x.tzinfo is None else x.astimezone(tz))
        return df.sort_values(["date", "time"], ascending=[True, True]).reset_index(drop=True)

    df_pair = _prep(df_pair)
    df_base = _prep(df_base)
    if df_pair.empty or df_base.empty:
        return None

    now = datetime.now(tz)
    fut_pair = df_pair[df_pair["dt"] > now]
    if fut_pair.empty:
        return None

    # 3) Primer futuro de la pareja
    row = fut_pair.iloc[0]

    # 4) H/A y rival_id (desde perspectiva del base)
    if str(row["home_team"]) == str(base_team_id):
        ha = "H"
        rival_id = str(row["away_team"])
    else:
        ha = "A"
        rival_id = str(row["home_team"])

    # 5) Matchday: índice 1-based dentro del calendario del base
    mask = (
        (df_base["home_team"].astype(str) == str(row["home_team"])) &
        (df_base["away_team"].astype(str) == str(row["away_team"])) &
        (df_base["date"].astype(str) == str(row["date"])) &
        (df_base["time"].astype(str) == str(row["time"]))
    )
    if not mask.any():
        return None
    idx = int(mask.idxmax())  # posición 0-based
    matchday = idx + 1

    return pd.Series({
        "date": str(row["date"]),
        "time": str(row["time"]),
        "home_team": str(row["home_team"]),
        "away_team": str(row["away_team"]),
        "rival_id": rival_id,
        "ha": ha,
        "matchday": matchday,
        "season": str(row["season"])
    })

@st.cache_data(show_spinner=False, ttl=300)
def get_sw_match_data_for_team(team_name: str, limit_n: int) -> list[dict]:
    """
    Devuelve como lista de dicts las filas (orden DESC por fecha/hora) de db_watford.sw_match_data
    en las que el equipo aparece como local o visitante.

    Campos usados por el generador page2:
      - localDate (YYYY-MM-DD)
      - localTime (HH:MM:SS)
      - home_name
      - away_name
      - season
      - competition_name
    """
    eng = get_engine()
    sql = text("""
        SELECT localDate, localTime, home_name, away_name, home_shortName, away_shortName, season, competition_name
        FROM db_watford.sw_match_data
        WHERE UPPER(home_name) = UPPER(:name) OR UPPER(away_name) = UPPER(:name)
        ORDER BY localDate DESC, localTime DESC
        LIMIT :lim
    """)
    with eng.connect() as conn:
        df = pd.read_sql(sql, conn, params={"name": team_name, "lim": int(limit_n)})
    return df.to_dict(orient="records")
