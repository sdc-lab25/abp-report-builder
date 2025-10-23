# image_builders.py
# Generadores de imágenes (PNG) para insertar en Word manteniendo tamaño/posición.

from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # backend sin UI
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import random, string, os
import seaborn as sns


def plot_shot_creating_actions(df, action_type, action_subtype="", defensive=False, team=None):
    if action_type=="corner":
        pitch = VerticalPitch(pitch_color='#575757', line_color='white',
                      stripe_color='#696464', stripe=False, half=True,
                      pitch_type='opta',pad_bottom=-30)
    elif action_type=="ifkbox":
        pitch = VerticalPitch(pitch_color='#575757', line_color='white',
                      stripe_color='#696464', stripe=False, half=True,
                      pitch_type='opta',pad_bottom=30)
        
    else:
        pitch = VerticalPitch(pitch_color='#575757', line_color='white',
                      stripe_color='#696464', stripe=False, half=True,
                      pitch_type='opta',pad_bottom=-10)

    if defensive:
        team_col = "oppositionTeamName"
    else:
        team_col = "teamName"

    if len(action_subtype)>0:
        action_subtype += "_"
        
    ## LEFT
    ### OUTSWINGING
    fig, ax = pitch.draw()
    if action_type=="corner":
        if "left" not in action_subtype and "right" not in action_subtype:
            pitch.scatter(100, 100, alpha = 1, s = 80,lw=3, ax=ax,color='#575757',edgecolors="yellow",zorder=2)
            pitch.scatter(100, 0, alpha = 1, s = 80,lw=3, ax=ax,color='#575757',edgecolors="yellow",zorder=2)
        elif "left" in action_subtype:
            pitch.scatter(100, 100, alpha = 1, s = 80,lw=3, ax=ax,color='#575757',edgecolors="yellow",zorder=2)
        else:
            pitch.scatter(100, 0, alpha = 1, s = 80,lw=3, ax=ax,color='#575757',edgecolors="yellow",zorder=2)
            
    # Corners sacados (acciones)
    df_fase = df[(df["actions_{}from{}".format(action_subtype,action_type)]==1) & (df[team_col] == team)]
    pitch.arrows(df_fase.x, df_fase.y,
                 df_fase.endX, df_fase.endY,
                 alpha=.25, color="red", ax=ax, width=1,headwidth=4,headlength=4, label = "Not Success")
    
    # Corners rematados (shots)
    df_fase = df[(df["actions_{}succ_from{}".format(action_subtype,action_type)]==1) & (df[team_col] == team)]
    
    
    pitch.arrows(
        df_fase.x, df_fase.y,
        df_fase.endX, df_fase.endY,
        alpha=.75, color="red", ax=ax,
        width=1, headwidth=0, headlength=0
    )
    
    # Círculo rojo en el punto final
    pitch.scatter(
        df_fase.endX, df_fase.endY,
        s=75, color="#575757", edgecolors="red", zorder=3, ax=ax, label = "Success - Contact"
    )
    
    df_fase = df[(df["shots_created_{}from{}".format(action_subtype,action_type)]==1) & (df[team_col] == team)]
    
    
    pitch.arrows(
        df_fase.x, df_fase.y,
        df_fase.endX, df_fase.endY,
        alpha=1, color="red", ax=ax,
        width=1, headwidth=0, headlength=0
    )
    
    # Círculo rojo en el punto final
    pitch.scatter(
        df_fase.endX, df_fase.endY,
        s=75, color="red", edgecolors="black", zorder=3, ax=ax, label = "Success - Leading to Shot"
    )
    
    
    plt.legend(loc='lower center', fontsize=8)
    
    plt.show()

def plot_shot_actions(df, action_type, action_subtype="", defensive=False, team=None):
    if action_type=="corner":
        pitch = VerticalPitch(pitch_color='#575757', line_color='white',
                          stripe_color='#696464', stripe=False, half=True,
                          pitch_type='opta',pad_bottom=-10)
    elif action_type=="dfk":
        pitch = VerticalPitch(pitch_color='#575757', line_color='white',
                          stripe_color='#696464', stripe=False, half=True,
                          pitch_type='opta',pad_bottom=-20)
    else:
        pitch = VerticalPitch(pitch_color='#575757', line_color='white',
                          stripe_color='#696464', stripe=False, half=True,
                          pitch_type='opta')

    
    
    
    if defensive:
        team_col = "oppositionTeamName"
    else:
        team_col = "teamName"

    if len(action_subtype)>0:
        action_subtype += "_"
        
    ## LEFT
    ### OUTSWINGING
    fig, ax = pitch.draw()
    if action_type=="corner":
        if "left" not in action_subtype and "right" not in action_subtype:
            pitch.scatter(100, 100, alpha = 1, s = 80,lw=3, ax=ax,color='#575757',edgecolors="yellow",zorder=2)
            pitch.scatter(100, 0, alpha = 1, s = 80,lw=3, ax=ax,color='#575757',edgecolors="yellow",zorder=2)
        elif "left" in action_subtype:
            pitch.scatter(100, 100, alpha = 1, s = 80,lw=3, ax=ax,color='#575757',edgecolors="yellow",zorder=2)
        else:
            pitch.scatter(100, 0, alpha = 1, s = 80,lw=3, ax=ax,color='#575757',edgecolors="yellow",zorder=2)
    
    # Datos
    
    df_shot = df[(df["shots_{}from{}".format(action_subtype, action_type)] == 1) 
             & (df[team_col] == team) 
             & (df["goals_{}from{}".format(action_subtype, action_type)] != 1)]

    df_shot_blocked = df[(df["shots_blocked_{}from{}".format(action_subtype, action_type)] == 1) 
                         & (df[team_col] == team)]
    
    df_shot_miss = df[(df["shots_miss_{}from{}".format(action_subtype, action_type)] == 1) 
                      & (df[team_col] == team)]
    
    df_goal = df[(df["goals_{}from{}".format(action_subtype, action_type)] == 1) 
                 & (df[team_col] == team)]
    
    
    
    # Scatter plots con leyenda clara
    
    
    
    pitch.scatter(df_shot.x, df_shot.y,
                  alpha=1, s=100, ax=ax,
                  color='red', edgecolors="black",
                  zorder=1, label="Shot - on Target")
    
    if action_type!="dfk":
        df_shot_header = df[(df["shots_header_{}from{}".format(action_subtype, action_type)] == 1) 
                            & (df[team_col] == team) 
                            & (df["goals_header_{}from{}".format(action_subtype, action_type)] != 1)]
        pitch.scatter(df_shot_header.x, df_shot_header.y,
                      alpha=1, s=100, ax=ax,
                      color='navy', edgecolors="black",
                      zorder=1, label="Shot Header - on Target")
        
    pitch.scatter(df_shot_blocked.x, df_shot_blocked.y,
                  alpha=1, s=100, ax=ax,
                  color='#575757', edgecolors="red",
                  zorder=2, label="Shot - Blocked")
    
    if action_type!="dfk":
        df_shot_header_blocked = df[(df["shots_header_blocked_{}from{}".format(action_subtype, action_type)] == 1) 
                                    & (df[team_col] == team)]
        pitch.scatter(df_shot_header_blocked.x, df_shot_header_blocked.y,
                      alpha=1, s=100, ax=ax,
                      color='#575757', edgecolors="navy",
                      zorder=2, label="Shot Header - Blocked")
    
    pitch.scatter(df_shot_miss.x, df_shot_miss.y,
                  alpha=1, s=100, ax=ax,
                  color='lightyellow', edgecolors="red",
                  zorder=2, label="Shot - Miss")

    if action_type!="dfk":
        df_shot_header_miss = df[(df["shots_header_miss_{}from{}".format(action_subtype, action_type)] == 1) 
                                 & (df[team_col] == team)]
        pitch.scatter(df_shot_header_miss.x, df_shot_header_miss.y,
                      alpha=1, s=100, ax=ax,
                      color='lightyellow', edgecolors="navy",
                      zorder=2, label="Shot Header - Miss")
    
    
    pitch.scatter(df_goal.x, df_goal.y,
                  alpha=1, s=140, ax=ax, marker='*',
                  color='red', edgecolors="black",
                  zorder=4, label="Goal")

    if action_type!="dfk":
        df_goal_header = df[(df["goals_header_{}from{}".format(action_subtype, action_type)] == 1) 
                        & (df[team_col] == team)]
        pitch.scatter(df_goal_header.x, df_goal_header.y,
                      alpha=1, s=140, ax=ax, marker='*',
                      color='navy', edgecolors="black",
                      zorder=4, label="Goal Header")
    
    # Añadir leyenda
    plt.legend( loc='lower center', fontsize=8)
    plt.show()

def _save_current_fig(path: Path, dpi=180, transparent=False, bbox_inches="tight", pad_inches=0.1):
    """Guarda la figura actual y la cierra."""
    fig = plt.gcf()
    path = Path(path)
    fig.savefig(path, dpi=dpi, transparent=transparent, bbox_inches=bbox_inches, pad_inches=pad_inches)
    plt.close(fig)
    return str(path)

def _ensure_tmp(ctx) -> Path:
    td = ctx.get("tmpdir", None)
    if not td:
        # fallback (no se recomienda, pero evita crashear)
        td = Path.cwd() / "tmp_images"
        td.mkdir(parents=True, exist_ok=True)
        return td
    return Path(td)

def _get_df(ctx):
    # Usa un df global llamado 'df' (como indicas en tu código), o permítenos recibirlo por ctx
    if "df" in ctx:
        return ctx["df"]
    try:
        # __main__.df si existe
        import __main__
        return getattr(__main__, "df")
    except Exception:
        raise RuntimeError("No se encuentra 'df' ni en ctx ni en __main__.")

# NUEVO: cargar DF correcto para page4 si ctx["df"] no tiene lo que necesitamos
def _df_for_team_overview(ctx):
    import pandas as pd
    from app.db import get_engine

    # 1) Intenta usar el DF del contexto
    df_ctx = _get_df(ctx)
    needed = {"field", "team_formation_desc", "changes_num", "matchId", "season"}
    if isinstance(df_ctx, pd.DataFrame) and needed.issubset(set(df_ctx.columns)):
        return df_ctx

    # 2) Si no está, consulta a BD (mismo enfoque que tu notebook)
    team = ctx.get("opponent") or ctx.get("team")
    if not team:
        raise ValueError("No encuentro 'opponent'/'team' en ctx para construir el DF de team_overview.")

    sql = """
        SELECT
            ts.field,
            ts.teamId,
            ts.teamName,
            ts.matchId,
            ts.changes_num,
            df.team_formation_desc,
            md.competition,
            md.season
        FROM fact_team_stats ts
        LEFT JOIN dim_formation df ON df.team_formation = ts.team_formation
        LEFT JOIN sw_match_data md ON md.matchId = ts.matchId
        WHERE ts.teamName = %(team)s
    """
    eng = get_engine()
    df = pd.read_sql(sql, eng, params={"team": team})

    # Limpieza ligera (como en tu notebook/UB):
    # aquí puedes ubicar cualquier clean_df si lo tuvieras; lo dejo básico.
    for col in ["team_formation_desc"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return df

def _team_for(defensive: bool, ctx):
    # Si es defensivo, usamos el rival; si no, el propio equipo
    if defensive:
        return ctx.get("opponent")
    return ctx.get("team")

# ------------- Builders concretos (nombres que pondrás en el JSON) -------------

# PÁGINA 7: plot_shot_creating_actions(df,"corner","left",True) y ...("right",True)
def sca_corner_left_right_def(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    paths = []

    team = _team_for(True, ctx)

    # left
    plot_shot_creating_actions(df, "corner", "left", True, team=team)
    p1 = tmp / "p7_sca_corner_left_def.png"
    _save_current_fig(p1); paths.append(p1)

    # right
    plot_shot_creating_actions(df, "corner", "right", True, team=team)
    p2 = tmp / "p7_sca_corner_right_def.png"
    _save_current_fig(p2); paths.append(p2)

    return [str(p1), str(p2)]

# PÁGINA 8: plot_shot_actions(df,"corner","left",True) y ...("right",True)
def sa_corner_left_right_def(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    paths = []

    team = _team_for(True, ctx)

    plot_shot_actions(df, "corner", "left", True, team=team)
    p1 = tmp / "p8_sa_corner_left_def.png"
    _save_current_fig(p1); paths.append(p1)

    plot_shot_actions(df, "corner", "right", True, team=team)
    p2 = tmp / "p8_sa_corner_right_def.png"
    _save_current_fig(p2); paths.append(p2)

    return [str(p1), str(p2)]

# PÁGINA 12: SCA IFK box (def?) y SA IFK (def?) -> tú lo has pedido sin 'defensive=True'
# Usaremos el equipo propio por defecto.
def sca_ifkbox_and_sa_ifk(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    paths = []

    team = _team_for(False, ctx)

    plot_shot_creating_actions(df, "ifkbox", "", False, team=team)
    p1 = tmp / "p12_sca_ifkbox.png"
    _save_current_fig(p1); paths.append(p1)

    plot_shot_actions(df, "ifk", "", False, team=team)
    p2 = tmp / "p12_sa_ifk.png"
    _save_current_fig(p2); paths.append(p2)

    return [str(p1), str(p2)]

# PÁGINA 15: SCA throwinbox y SA throwin
def sca_throwinbox_and_sa_throwin(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    paths = []

    team = _team_for(False, ctx)

    plot_shot_creating_actions(df, "throwinbox", "", False, team=team)
    p1 = tmp / "p15_sca_throwinbox.png"
    _save_current_fig(p1); paths.append(p1)

    plot_shot_actions(df, "throwin", "", False, team=team)
    p2 = tmp / "p15_sa_throwin.png"
    _save_current_fig(p2); paths.append(p2)

    return [str(p1), str(p2)]

# PÁGINA 20: tres esquinas izquierda (long_in, short, long_out)
def sca_corner_left_triple(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    paths = []
    team = _team_for(False, ctx)

    for sub, stub in [("left_long_in","lin"), ("left_short","ls"), ("left_long_out","lout")]:
        plot_shot_creating_actions(df, "corner", sub, False, team=team)
        p = tmp / f"p20_sca_corner_{stub}.png"
        _save_current_fig(p); paths.append(p)

    return [str(p) for p in paths]

# PÁGINA 21: tres esquinas derecha (long_in, short, long_out)
def sca_corner_right_triple(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    paths = []
    team = _team_for(False, ctx)

    for sub, stub in [("right_long_in","rin"), ("right_short","rs"), ("right_long_out","rout")]:
        plot_shot_creating_actions(df, "corner", sub, False, team=team)
        p = tmp / f"p21_sca_corner_{stub}.png"
        _save_current_fig(p); paths.append(p)

    return [str(p) for p in paths]

# PÁGINA 22: SA corner left y right (ataque)
def sa_corner_left_right(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    paths = []
    team = _team_for(False, ctx)

    plot_shot_actions(df, "corner", "left", False, team=team)
    p1 = tmp / "p22_sa_corner_left.png"
    _save_current_fig(p1); paths.append(p1)

    plot_shot_actions(df, "corner", "right", False, team=team)
    p2 = tmp / "p22_sa_corner_right.png"
    _save_current_fig(p2); paths.append(p2)

    return [str(p1), str(p2)]

# PÁGINA 26: SCA ifkbox (una)
def sca_ifkbox(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    team = _team_for(False, ctx)
    plot_shot_creating_actions(df, "ifkbox", "", False, team=team)
    p = tmp / "p26_sca_ifkbox.png"
    _save_current_fig(p)
    return [str(p)]

# PÁGINA 27: SA ifk (una)
def sa_ifk(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    team = _team_for(False, ctx)
    plot_shot_actions(df, "ifk", "", False, team=team)
    p = tmp / "p27_sa_ifk.png"
    _save_current_fig(p)
    return [str(p)]

# PÁGINA 30: SCA throwinbox left y right
def sca_throwinbox_left_right(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    paths = []
    team = _team_for(False, ctx)

    plot_shot_creating_actions(df, "throwinbox", "left", False, team=team)
    p1 = tmp / "p30_sca_throwinbox_left.png"
    _save_current_fig(p1); paths.append(p1)

    plot_shot_creating_actions(df, "throwinbox", "right", False, team=team)
    p2 = tmp / "p30_sca_throwinbox_right.png"
    _save_current_fig(p2); paths.append(p2)

    return [str(p1), str(p2)]

# PÁGINA 31: SA throwin (una)
def sa_throwin(ctx):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    team = _team_for(False, ctx)
    plot_shot_actions(df, "throwin", "", False, team=team)
    p = tmp / "p31_sa_throwin.png"
    _save_current_fig(p)
    return [str(p)]

def _tmp_png(ctx, prefix="img"):
    tmpdir = Path(ctx.get("tmpdir", "."))
    tmpdir.mkdir(parents=True, exist_ok=True)
    salt = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return str(tmpdir / f"{prefix}_{salt}.png")

def _safe_read_df_players(ctx):
    # Permite sobreescribir ruta vía ctx["df_players_path"]; por defecto, data/df_players.csv
    data_dir = Path(ctx.get("data_dir", "data"))
    csv_path = Path(ctx.get("df_players_path", data_dir / "df_players.csv"))
    if not csv_path.exists():
        raise RuntimeError(f"No se encuentra df_players.csv en: {csv_path}")
    return pd.read_csv(csv_path)

def team_square_image(ctx, *, team: str):
    """
    Genera una imagen cuadrada (PNG) de 500x500 con el nombre del equipo.
    team: "coach_team" | "opponent_team"
    """

    if team == "coach_team":
        p = ctx.get("badge_coach_path")
    else:
        p = ctx.get("badge_rival_path")
    if p and os.path.exists(p):
        return p

    label = ctx.get("team") if team == "coach_team" else ctx.get("opponent")
    if not label:
        label = "TEAM"

    size = (500, 500)
    img = Image.new("RGB", size, color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (size[0]-1, size[1]-1)], outline=(80, 80, 80), width=4)

    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font = ImageFont.load_default()

    text = label.upper()
    tw, th = draw.textbbox((0, 0), text, font=font)[2:]
    draw.text(((size[0]-tw)/2, (size[1]-th)/2), text, fill=(30, 30, 30), font=font)

    out = _tmp_png(ctx, prefix="team")
    img.save(out, format="PNG")
    return out

def _plot_heights_exact(df: pd.DataFrame, team: str, rival: str | None):
    """
    Replica EXACTAMENTE la lógica de la función `plot_heights(df, team)` que has pasado,
    incluyendo los estilos y sns.despine(). Solo hace 'rival' explícito.
    """
    # Filtramos por equipo
    df_team = df[df["teamName"] == team].copy()

    # Etiquetas: "Nº. NOMBRE" (misma lógica, pero aplicada sobre df_team)
    df_team["playerName"] = df_team.apply(
        lambda x: (f"{int(x['shirtNo'])}. " if pd.notna(x.get('shirtNo')) else "") + str(x["playerName"]).upper(),
        axis=1
    )

    # Quitamos NaN en altura
    df_team = df_team.dropna(subset=["height"])

    # Ordenamos de mayor a menor
    df_team = df_team.sort_values("height", ascending=False)

    # Calcular media
    mean_height = df_team["height"].mean()

    # Gráfico: color según si el team es el rival
    c = "red" if (rival is not None and team == rival) else "yellow"

    plt.figure(figsize=(12, 4))
    bars = plt.bar(
        df_team["playerName"],
        df_team["height"],
        color=c,
        lw=2,
        edgecolor="black"   # bordes negros
    )

    # Añadir valores encima de las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.5,   # un poco por encima de la barra
            f"{height:.0f}",
            ha="center",
            va="bottom",
            fontsize=12,
            weight="bold"
        )

    # Línea horizontal con la media
    plt.axhline(mean_height, color="black", linestyle="--", linewidth=1.5, zorder=0, label=f"Media: {mean_height:.0f} cm")
    plt.text(
        max(len(df_team) - 0.5, 0), mean_height + 0.5,
        f"{mean_height:.1f}",
        color="black", fontsize=14, ha="right", weight="bold"
    )

    # Ajustes del gráfico
    plt.xticks(rotation=40, ha="right", fontsize=8)
    plt.ylim(150, 200)
    plt.tight_layout()
    sns.despine()
    # NO hacemos plt.show(); dejamos que el caller guarde la figura actual

def bars_heights_coach(ctx):
    """
    Builder para HOJA 3: barras de alturas del equipo del entrenador.
    Lee data/df_players.csv (o ctx['df_players_path']).
    Devuelve ruta del PNG generado.
    """
    dfp = _safe_read_df_players(ctx)        # usa data/df_players.csv por defecto
    team = ctx.get("team") or "TEAM"
    rival = ctx.get("opponent")             # para la lógica del color

    _plot_heights_exact(dfp, team, rival)

    out = _tmp_png(ctx, prefix="bars_coach")
    _save_current_fig(out, dpi=200, bbox_inches="tight")
    return out


def bars_heights_rival(ctx):
    """
    Builder para HOJA 3: barras de alturas del equipo rival.
    Lee data/df_players.csv (o ctx['df_players_path']).
    Devuelve ruta del PNG generado.
    """
    dfp = _safe_read_df_players(ctx)
    team = ctx.get("opponent") or "OPPONENT"
    rival = ctx.get("opponent")             # aquí team == rival → color rojo

    _plot_heights_exact(dfp, team, rival)

    out = _tmp_png(ctx, prefix="bars_rival")
    _save_current_fig(out, dpi=200, bbox_inches="tight")
    return out


def builder_plot_shot_creating_actions(ctx, action_type, action_subtype="", defensive=False, team=None):
    df = _get_df(ctx)                # usa df del contexto
    tmp = _ensure_tmp(ctx)           # carpeta temporal del pipeline
    # si no nos dan 'team', lo deducimos (defensive -> rival; si no -> propio)
    team_to_use = team if team is not None else _team_for(defensive, ctx)

    # pinta
    plot_shot_creating_actions(df, action_type, action_subtype, defensive, team=team_to_use)

    # guarda
    out = _tmp_png(ctx, prefix=f"sca_{action_type}_{action_subtype or 'all'}_{'def' if defensive else 'att'}")
    _save_current_fig(out, dpi=200, bbox_inches="tight")
    return str(out)

def builder_plot_shot_actions(ctx, action_type, action_subtype="", defensive=False, team=None):
    df = _get_df(ctx)
    tmp = _ensure_tmp(ctx)
    team_to_use = team if team is not None else _team_for(defensive, ctx)

    # pinta
    plot_shot_actions(df, action_type, action_subtype, defensive, team=team_to_use)

    # guarda
    out = _tmp_png(ctx, prefix=f"sa_{action_type}_{action_subtype or 'all'}_{'def' if defensive else 'att'}")
    _save_current_fig(out, dpi=200, bbox_inches="tight")
    return str(out)


def plot_team_overview(ctx, field, gby, season):
    """
    Builder para la app: genera un barh y devuelve la ruta del PNG.
    Se apoya en ctx['df'] (cargado en docgen.py como df_main) y guarda en ctx['tmpdir'].
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    from pathlib import Path

    # 1) DF base desde el contexto
    df_ts = _df_for_team_overview(ctx)

    # 2) Resolver season si viene como placeholder del JSON
    if isinstance(season, str) and season.startswith("{{") and season.endswith("}}"):
        season_key = season.strip("{}")
        season = ctx.get(season_key, "")  # si no está, se deja vacío

    # 3) Filtrado por temporada y campo
    df_plot = df_ts.copy()
    if isinstance(season, str) and season:
        # si llega "2024-25", me quedo con el primer año para el contains
        season_token = season.split("-")[0]
        if "season" in df_plot.columns and isinstance(df_plot["season"].dtype, pd.StringDtype) or df_plot["season"].dtype==object:
            df_plot = df_plot[df_plot["season"].astype(str).str.contains(str(season_token), na=False)]

    if "field" in df_plot.columns:
        df_plot = df_plot[df_plot["field"] == field]

    # 4) Agrupar por gby y contar partidos
    df_plot = (
        df_plot.groupby(by=[gby], as_index=False)[["matchId"]]
               .nunique()
               .sort_values(by="matchId", ascending=True)
    )
    df_plot[gby] = df_plot[gby].astype(str)

    # 5) Etiquetas amigables según gby
    if gby == "changes_num":
        df_plot.rename(columns={"matchId": "Games", gby: "Substitutions"}, inplace=True)
        x_col, y_col = "Games", "Substitutions"
    elif gby == "team_formation_desc":
        df_plot.rename(columns={"matchId": "Games", gby: "Formation"}, inplace=True)
        x_col, y_col = "Games", "Formation"
    else:
        x_col, y_col = "matchId", gby

    # 6) Pintar
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.barh(df_plot[y_col], df_plot[x_col], color="red")
    ax.set_xlabel("Games", fontsize=8)
    ax.set_ylabel("")
    ax.set_xticks([])
    for i, v in enumerate(df_plot[x_col]):
        ax.text(v + 0.1, i, str(v), va='center')
    plt.tight_layout()

    # 7) Guardar y devolver ruta
    tmp = _ensure_tmp(ctx)
    out = tmp / f"page4_{field}_{gby}.png"
    _save_current_fig(out)
    return str(out)
