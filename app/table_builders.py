# table_builders.py
# Generadores de DataFrames para tablas de ABP / Set Pieces

import pandas as pd
import numpy as np

def _col(df, defensive: bool, base: str):
    name = f"opp_{base}" if defensive else base
    return name if name in df.columns else None

def _fmt_int(s):    return pd.to_numeric(s, errors="coerce").round().astype("Int64")
def _fmt_float2(s): return pd.to_numeric(s, errors="coerce").round(2)

def _ensure_cols(df: pd.DataFrame, cols: dict):
    out = pd.DataFrame()
    for label, colname in cols.items():
        out[label] = df[colname] if (colname is not None and colname in df.columns) else np.nan
    return out

def _sort_by_second_then_rest(df: pd.DataFrame, descending: bool = True) -> pd.DataFrame:
    cols = list(df.columns)
    if len(cols) <= 1:
        return df.reset_index(drop=True)
    keys = cols[1:]
    tmp = df.copy()
    sort_cols, ascending = [], []
    for c in keys:
        s = pd.to_numeric(tmp[c], errors="coerce")
        if s.notna().sum() > 0:
            tmp[c + "::__num"] = s
            sort_cols.append(c + "::__num"); ascending.append(not descending)
        else:
            tmp[c + "::__str"] = tmp[c].astype(str)
            sort_cols.append(c + "::__str"); ascending.append(True)
    tmp["__tie"] = tmp[cols[0]].astype(str)
    sort_cols.append("__tie"); ascending.append(True)
    tmp = tmp.sort_values(sort_cols, ascending=ascending, na_position="last")
    return df.loc[tmp.index].reset_index(drop=True)

# --------- Builders (usar estos nombres en el JSON) ---------

def mk_set_pieces(df, defensive: bool):
    cols = {
        "Team Name": "teamName",
        "Games": "games",
        "SP Goals": _col(df, defensive, "goals_sp"),
        "SP xG": _col(df, defensive, "xg_sp"),
        "SP Shots": _col(df, defensive, "shots_sp"),
        "Goals/SP": _col(df, defensive, "goals_sp_pct"),
        "xG/SP": _col(df, defensive, "xg_sp_pct"),
        "Shots/SP": _col(df, defensive, "shots_sp_pct"),
    }
    out = _ensure_cols(df, cols)
    out["Games"] = _fmt_int(out["Games"])
    for c in ["SP Goals","SP Shots"]: out[c] = _fmt_int(out[c])
    for c in ["SP xG","Goals/SP","xG/SP","Shots/SP"]: out[c] = _fmt_float2(out[c])
    return _sort_by_second_then_rest(out[["Team Name","Games","SP Goals","SP xG","SP Shots","Goals/SP","xG/SP","Shots/SP"]])

def mk_corners(df, defensive: bool):
    cols = {
        "Team Name": "teamName",
        "Corner Goals": _col(df, defensive, "goals_fromcorner"),
        "Corner xG": _col(df, defensive, "xg_fromcorner"),
        "Corner Shots": _col(df, defensive, "shots_fromcorner"),
        "Goals/Corner": _col(df, defensive, "goals_fromcorner_pct"),
        "xG/Corner": _col(df, defensive, "xg_fromcorner_pct"),
        "Shots/Corner": _col(df, defensive, "shots_fromcorner_pct"),
    }
    out = _ensure_cols(df, cols)
    for c in ["Corner Goals","Corner Shots"]: out[c] = _fmt_int(out[c])
    for c in ["Corner xG","Goals/Corner","xG/Corner","Shots/Corner"]: out[c] = _fmt_float2(out[c])
    return _sort_by_second_then_rest(out[["Team Name","Corner Goals","Corner xG","Corner Shots","Goals/Corner","xG/Corner","Shots/Corner"]])

def mk_dfk(df, defensive: bool):
    cols = {
        "Team Name": "teamName",
        "DFK Goals": _col(df, defensive, "goals_fromdfk"),
        "DFK xG": _col(df, defensive, "xg_fromdfk"),
        "DFK Shots": _col(df, defensive, "shots_fromdfk"),
        "Goals/DFK": _col(df, defensive, "goals_fromdfk_pct"),
        "xG/DFK": _col(df, defensive, "xg_fromdfk_pct"),
        "Shots/DFK": _col(df, defensive, "shots_dfk_pct"),
    }
    out = _ensure_cols(df, cols)
    for c in ["DFK Goals","DFK Shots"]: out[c] = _fmt_int(out[c])
    for c in ["DFK xG","Goals/DFK","xG/DFK","Shots/DFK"]: out[c] = _fmt_float2(out[c])
    return _sort_by_second_then_rest(out[["Team Name","DFK Goals","DFK xG","DFK Shots","Goals/DFK","xG/DFK","Shots/DFK"]])

def mk_ifk(df, defensive: bool):
    cols = {
        "Team Name": "teamName",
        "IFK Goals": _col(df, defensive, "goals_fromifk"),
        "IFK xG": _col(df, defensive, "xg_fromifk"),
        "IFK Shots": _col(df, defensive, "shots_fromifk"),
        "Goals/IFK": _col(df, defensive, "goals_fromifk_pct"),
        "xG/IFK": _col(df, defensive, "xg_fromifk_pct"),
        "Shots/IFK": _col(df, defensive, "shots_fromifk_pct"),
    }
    out = _ensure_cols(df, cols)
    for c in ["IFK Goals","IFK Shots"]: out[c] = _fmt_int(out[c])
    for c in ["IFK xG","Goals/IFK","xG/IFK","Shots/IFK"]: out[c] = _fmt_float2(out[c])
    return _sort_by_second_then_rest(out[["Team Name","IFK Goals","IFK xG","IFK Shots","Goals/IFK","xG/IFK","Shots/IFK"]])

def mk_throwins(df, defensive: bool):
    cols = {
        "Team Name": "teamName",
        "Throw-in Goals": _col(df, defensive, "goals_fromthrowin"),
        "Throw-in xG": _col(df, defensive, "xg_fromthrowin"),
        "Throw-in Shots": _col(df, defensive, "shots_fromthrowin"),
        "Goals/Throw-in": _col(df, defensive, "goals_fromthrowin_pct"),
        "xG/Throw-in": _col(df, defensive, "xg_fromthrowin_pct"),
        "Shots/Throw-in": _col(df, defensive, "shots_fromthrowin_pct"),
    }
    out = _ensure_cols(df, cols)
    for c in ["Throw-in Goals","Throw-in Shots"]: out[c] = _fmt_int(out[c])
    for c in ["Throw-in xG","Goals/Throw-in","xG/Throw-in","Shots/Throw-in"]: out[c] = _fmt_float2(out[c])
    return _sort_by_second_then_rest(out[["Team Name","Throw-in Goals","Throw-in xG","Throw-in Shots","Goals/Throw-in","xG/Throw-in","Shots/Throw-in"]])

def _summ_corners(df, side: str = "right", defensive: bool = True, rival: str | None = None):
    """
    Devuelve un DF con FILAS = métricas y COLUMNAS = equipos (o jugadores en ofensivo),
    con la primera columna textual exacta: 'Per Opposition'.
    Esta forma es la que espera _fill_dfk_table_with_headers_and_totals (docgen).
    """
    import pandas as pd
    import numpy as np

    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["Per Opposition"])

    t = str(side).strip().lower()
    if t not in ("right", "left"):
        t = "right"

    if defensive:
        col2 = 'teamName'              # columna con el nombre que queremos como CABECERA (equipos)
        col1 = 'oppositionTeamName'    # para filtrar rival si viene
        tmp = df.copy()
        if rival is not None and col1 in tmp.columns:
            tmp = tmp[tmp[col1] == rival]
        if 'localDate' in tmp.columns:
            try:
                tmp = tmp.sort_values(by="localDate", ascending=True)
            except Exception:
                pass
        # columnas crudas que intentaremos tomar si existen
        keep = [col2,
                f'actions_{t}_fromcorner',
                f'actions_{t}_rightfoot_fromcorner',
                f'actions_{t}_leftfoot_fromcorner',
                f'actions_{t}_pfoot_fromcorner',
                f'actions_{t}_ofoot_fromcorner',
                f'actions_{t}_short_fromcorner',
                f'actions_{t}_long_in_fromcorner',
                f'actions_{t}_long_out_fromcorner',
                f'actions_{t}_long_str_fromcorner',
                f'actions_{t}_ppenalty_fromcorner',
                f'actions_{t}_smallbox_fromcorner',
                f'actions_{t}_1p_fromcorner',
                f'actions_{t}_2p_fromcorner',
                f'actions_{t}_toolong_fromcorner',
                f'actions_{t}_near_fromcorner',
                f'actions_{t}_frontbox_fromcorner',
                f'actions_{t}_succ_fromcorner',
                f'shots_created_{t}_fromcorner',
                f'xg_created_{t}_fromcorner',
                f'shots_{t}_fromcorner',
                f'goals_{t}_fromcorner',
                f'xg_{t}_fromcorner']
        tmp = tmp[[c for c in keep if c in tmp.columns]]

        # mapeo → etiquetas (primera col “Team” sin sufijo Name)
        cols = {
            f"{col2.replace('Name','').title()}": col2,
            "Actions":                           f'actions_{t}_fromcorner',
            "Foot: Right":                       f'actions_{t}_rightfoot_fromcorner',
            "Foot: Left":                        f'actions_{t}_leftfoot_fromcorner',
            "Foot Approach: Natural":            f'actions_{t}_pfoot_fromcorner',
            "Foot Approach: Opposite":           f'actions_{t}_ofoot_fromcorner',
            "Kind: Short":                       f'actions_{t}_short_fromcorner',
            "Kind: Long (In)":                   f'actions_{t}_long_in_fromcorner',
            "Kind: Long (Out)":                  f'actions_{t}_long_out_fromcorner',
            "Kind: Long (Straight)":             f'actions_{t}_long_str_fromcorner',
            "End: P. Penalty":                   f'actions_{t}_ppenalty_fromcorner',
            "End: Smallbox":                     f'actions_{t}_smallbox_fromcorner',
            "End: 1p":                           f'actions_{t}_1p_fromcorner',
            "End: 2p":                           f'actions_{t}_2p_fromcorner',
            "End: Opposite":                     f'actions_{t}_toolong_fromcorner',
            "End: Near":                         f'actions_{t}_near_fromcorner',
            "End: Front Box":                    f'actions_{t}_frontbox_fromcorner',
            "Outcome: Success":                  f'actions_{t}_succ_fromcorner',
            "Inmediate Outcome: Shot":           f'shots_created_{t}_fromcorner',
            "Inmediate Outcome: xG":             f'xg_created_{t}_fromcorner',
            "Outcome: Shot":                     f'shots_{t}_fromcorner',
            "Outcome: Goal":                     f'goals_{t}_fromcorner',
            "Outcome: xG":                       f'xg_{t}_fromcorner',
        }
    else:
        col2 = 'playerName'  # ofensivo: por jugador
        tmp = df.copy()
        if 'actions_fromcorner' in tmp.columns:
            tmp = tmp[tmp['actions_fromcorner'] > 0]
        keep = [col2,
                f'actions_{t}_fromcorner',
                f'actions_{t}_rightfoot_fromcorner',
                f'actions_{t}_leftfoot_fromcorner',
                f'actions_{t}_pfoot_fromcorner',
                f'actions_{t}_ofoot_fromcorner',
                f'actions_{t}_short_fromcorner',
                f'actions_{t}_long_in_fromcorner',
                f'actions_{t}_long_out_fromcorner',
                f'actions_{t}_long_str_fromcorner',
                f'actions_{t}_ppenalty_fromcorner',
                f'actions_{t}_smallbox_fromcorner',
                f'actions_{t}_1p_fromcorner',
                f'actions_{t}_2p_fromcorner',
                f'actions_{t}_toolong_fromcorner',
                f'actions_{t}_near_fromcorner',
                f'actions_{t}_frontbox_fromcorner',
                f'actions_{t}_succ_fromcorner',
                f'shots_created_{t}_fromcorner',
                f'xg_created_{t}_fromcorner',
                f'shots_{t}_fromcorner',
                f'goals_{t}_fromcorner',
                f'xg_{t}_fromcorner']
        tmp = tmp[[c for c in keep if c in tmp.columns]]

        cols = {
            f"{col2.replace('Name','').title()}": col2,
            "Actions":                           f'actions_{t}_fromcorner',
            "Foot: Right":                       f'actions_{t}_rightfoot_fromcorner',
            "Foot: Left":                        f'actions_{t}_leftfoot_fromcorner',
            "Foot Approach: Natural":            f'actions_{t}_pfoot_fromcorner',
            "Foot Approach: Opposite":           f'actions_{t}_ofoot_fromcorner',
            "Kind: Short":                       f'actions_{t}_short_fromcorner',
            "Kind: Long (In)":                   f'actions_{t}_long_in_fromcorner',
            "Kind: Long (Out)":                  f'actions_{t}_long_out_fromcorner',
            "Kind: Long (Straight)":             f'actions_{t}_long_str_fromcorner',
            "End: P. Penalty":                   f'actions_{t}_ppenalty_fromcorner',
            "End: Smallbox":                     f'actions_{t}_smallbox_fromcorner',
            "End: 1p":                           f'actions_{t}_1p_fromcorner',
            "End: 2p":                           f'actions_{t}_2p_fromcorner',
            "End: Opposite":                     f'actions_{t}_toolong_fromcorner',
            "End: Near":                         f'actions_{t}_near_fromcorner',
            "End: Front Box":                    f'actions_{t}_frontbox_fromcorner',
            "Outcome: Success":                  f'actions_{t}_succ_fromcorner',
            "Inmediate Outcome: Shot":           f'shots_created_{t}_fromcorner',
            "Inmediate Outcome: xG":             f'xg_created_{t}_fromcorner',
            "Outcome: Shot":                     f'shots_{t}_fromcorner',
            "Outcome: Goal":                     f'goals_{t}_fromcorner',
            "Outcome: xG":                       f'xg_{t}_fromcorner',
        }

    # 1) Construir DF intermedio con columnas = [Nombre, métricas...]
    out = _ensure_cols(tmp, cols)

    # 2) Poner el nombre (equipo/jugador) como índice, y TRANSponer
    name_col = next((k for k, v in cols.items() if v == col2), None)
    if name_col and name_col in out.columns:
        out = out.set_index(name_col)

    out = out.T  # *** filas = métricas, columnas = equipos/jugadores ***

    # 3) Insertar la primera columna textual exacta
    first_label = "Per Opposition" if defensive else "Per Player"
    out.insert(0, first_label, out.index)
    out = out.reset_index(drop=True)
    return out

def _summ_ifks(df, defensive: bool = True, rival: str | None = None):
    """
    Resumen de IFKs en formato esperado por _fill_dfk_table_with_headers_and_totals:
    FILAS = métricas, COLUMNAS = equipos/jugadores, primera columna = 'Per Opposition'.
    """
    import pandas as pd

    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["Per Opposition"])

    if defensive:
        col2 = 'teamName'               # será cabecera (columnas) tras transponer
        col1 = 'oppositionTeamName'
        tmp = df.copy()
        if rival is not None and col1 in tmp.columns:
            tmp = tmp[tmp[col1] == rival]
        if 'localDate' in tmp.columns:
            try:
                tmp = tmp.sort_values(by="localDate", ascending=True)
            except Exception:
                pass
        keep = [col2,
                'actions_fromifk',
                'actions_fromifkbox',
                'actions_other_fromifk',
                'actions_rightfoot_fromifkbox',
                'actions_leftfoot_fromifkbox',
                'actions_right_fromifkbox',
                'actions_left_fromifkbox',
                'actions_cen_fromifkbox',
                'actions_lat_fromifkbox',
                'actions_pfoot_fromifkbox',
                'actions_ofoot_fromifkbox',
                'actions_short_lastthird_fromifk',
                'actions_in_fromifkbox',
                'actions_out_fromifkbox',
                'actions_str_fromifkbox',
                'actions_ppenalty_fromifkbox',
                'actions_smallbox_fromifkbox',
                'actions_1p_fromifkbox',
                'actions_2p_fromifkbox',
                'actions_succ_fromifkbox',
                'shots_created_fromifkbox',
                'xg_created_fromifkbox',
                'shots_fromifkbox',
                'goals_fromifkbox',
                'xg_fromifkbox']
        tmp = tmp[[c for c in keep if c in tmp.columns]]
    else:
        col2 = 'playerName'
        tmp = df.copy()
        if 'actions_fromifk' in tmp.columns:
            tmp = tmp[tmp['actions_fromifk'] > 0]
        keep = [col2,
                'actions_fromifk',
                'actions_fromifkbox',
                'actions_other_fromifk',
                'actions_rightfoot_fromifkbox',
                'actions_leftfoot_fromifkbox',
                'actions_right_fromifkbox',
                'actions_left_fromifkbox',
                'actions_cen_fromifkbox',
                'actions_lat_fromifkbox',
                'actions_pfoot_fromifkbox',
                'actions_ofoot_fromifkbox',
                'actions_short_lastthird_fromifk',
                'actions_in_fromifkbox',
                'actions_out_fromifkbox',
                'actions_str_fromifkbox',
                'actions_ppenalty_fromifkbox',
                'actions_smallbox_fromifkbox',
                'actions_1p_fromifkbox',
                'actions_2p_fromifkbox',
                'actions_succ_fromifkbox',
                'shots_created_fromifkbox',
                'xg_created_fromifkbox',
                'shots_fromifkbox',
                'goals_fromifkbox',
                'xg_fromifkbox']
        tmp = tmp[[c for c in keep if c in tmp.columns]]

    # Etiquetas → columnas del DF intermedio
    cols = {
        f"{col2.replace('Name','').title()}": col2,
        "Actions":                            'actions_fromifk',
        "End: Box":                           'actions_fromifkbox',
        "End: Other":                         'actions_other_fromifk',
        "Foot: Right":                        'actions_rightfoot_fromifkbox',
        "Foot: Left":                         'actions_leftfoot_fromifkbox',
        "Foot Approach: Natural":             'actions_pfoot_fromifkbox',
        "Foot Approach: Opposite":            'actions_ofoot_fromifkbox',
        "From: Right":                        'actions_right_fromifkbox',
        "From: Left":                         'actions_left_fromifkbox',
        "From: Side":                         'actions_lat_fromifkbox',
        "From: Front":                        'actions_cen_fromifkbox',
        "Kind: Short (F3rd)":                 'actions_short_lastthird_fromifk',
        "Kind: Long (In)":                    'actions_in_fromifkbox',
        "Kind: Long (Out)":                   'actions_out_fromifkbox',
        "Kind: Long (Straight)":              'actions_str_fromifkbox',
        "End: P. Penalty":                    'actions_ppenalty_fromifkbox',
        "End: Smallbox":                      'actions_smallbox_fromifkbox',
        "End: 1p":                            'actions_1p_fromifkbox',
        "End: 2p":                            'actions_2p_fromifkbox',
        "Outcome: Success":                   'actions_succ_fromifkbox',
        "Inmediate Outcome: Shot":            'shots_created_fromifkbox',
        "Inmediate Outcome: xG":              'xg_created_fromifkbox',
        "Outcome: Shot":                      'shots_fromifkbox',
        "Outcome: Goal":                      'goals_fromifkbox',
        "Outcome: xG":                        'xg_fromifkbox',
    }

    out = _ensure_cols(tmp, cols)
    name_col = next((k for k, v in cols.items() if v == col2), None)
    if name_col and name_col in out.columns:
        out = out.set_index(name_col)

    # *** clave: columnas=equipos ⇒ transponer ***
    out = out.T

    # 1ª columna textual
    out.insert(0, "Per Opposition", out.index)
    out = out.reset_index(drop=True)
    return out

def _summ_throwins(df, side: str = "right", defensive: bool = True, rival: str | None = None):
    """
    FILAS = métricas, COLUMNAS = equipos (o jugadores en ofensivo).
    Primera columna textual: 'Per Opposition'.
    Compatible con _fill_dfk_table_with_headers_and_totals.
    """
    import pandas as pd

    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["Per Opposition"])

    t = str(side).strip().lower()
    if t not in ("right", "left"):
        t = "right"

    if defensive:
        col2 = 'teamName'               # será cabecera (columnas) tras transponer
        col1 = 'oppositionTeamName'
        tmp = df.copy()
        if rival is not None and col1 in tmp.columns:
            tmp = tmp[tmp[col1] == rival]
        if 'localDate' in tmp.columns:
            try:
                tmp = tmp.sort_values(by="localDate", ascending=True)
            except Exception:
                pass
        keep = [col2,
                f"actions_{t}_fromthrowin",
                f"actions_{t}_finalthird_fromthrowin",
                f"actions_{t}_fromthrowinbox",
                f"actions_{t}_ppenalty_fromthrowinbox",
                f"actions_{t}_smallbox_fromthrowinbox",
                f"actions_{t}_1p_fromthrowinbox",
                f"actions_{t}_2p_fromthrowinbox",
                f"actions_{t}_succ_fromthrowinbox",
                f"shots_created_{t}_fromthrowinbox",
                f"xg_created_{t}_fromthrowinbox",
                f"shots_{t}_fromthrowin",
                f"goals_{t}_fromthrowin",
                f"xg_{t}_fromthrowin"]
        tmp = tmp[[c for c in keep if c in tmp.columns]]
    else:
        col2 = 'playerName'
        tmp = df.copy()
        if 'actions_fromthrowin' in tmp.columns:
            tmp = tmp[tmp['actions_fromthrowin'] > 0]
        keep = [col2,
                f"actions_{t}_fromthrowin",
                f"actions_{t}_finalthird_fromthrowin",
                f"actions_{t}_fromthrowinbox",
                f"actions_{t}_ppenalty_fromthrowinbox",
                f"actions_{t}_smallbox_fromthrowinbox",
                f"actions_{t}_1p_fromthrowinbox",
                f"actions_{t}_2p_fromthrowinbox",
                f"actions_{t}_succ_fromthrowinbox",
                f"shots_created_{t}_fromthrowinbox",
                f"xg_created_{t}_fromthrowinbox",
                f"shots_{t}_fromthrowin",
                f"goals_{t}_fromthrowin",
                f"xg_{t}_fromthrowin"]
        tmp = tmp[[c for c in keep if c in tmp.columns]]

    # Etiquetas amigables → columnas fuente
    cols = {
        f"{col2.replace('Name','').title()}": col2,
        "Actions: FinalThird":            f"actions_{t}_fromthrowin",
        "Outcome: Box":                   f"actions_{t}_finalthird_fromthrowin",
        "End: P. Penalty":                f"actions_{t}_ppenalty_fromthrowinbox",
        "End: Smallbox":                  f"actions_{t}_smallbox_fromthrowinbox",
        "End: 1p":                        f"actions_{t}_1p_fromthrowinbox",
        "End: 2p":                        f"actions_{t}_2p_fromthrowinbox",
        "Outcome: Success":               f"actions_{t}_succ_fromthrowinbox",
        "Inmediate Outcome: Shot":        f"shots_created_{t}_fromthrowinbox",
        "Inmediate Outcome: xG":          f"xg_created_{t}_fromthrowinbox",
        "Outcome: Shot":                  f"shots_{t}_fromthrowin",
        "Outcome: Goal":                  f"goals_{t}_fromthrowin",
        "Outcome: xG":                    f"xg_{t}_fromthrowin",
    }

    out = _ensure_cols(tmp, cols)

    # index = equipo/jugador → TRANSPOSE
    name_col = next((k for k, v in cols.items() if v == col2), None)
    if name_col and name_col in out.columns:
        out = out.set_index(name_col)

    out = out.T
    out.insert(0, "Per Opposition", out.index)
    out = out.reset_index(drop=True)
    return out

def _pk_corners(df, t):
    cols = {
        "Player Name": "playerName",
        "All Events": _col(df, False, "actions_{}_fromcorner".format(t)),
        "Success - Contact": _col(df, False, "actions_{}_succ_fromcorner".format(t)),
        "Lost Out": _col(df, False, "actions_{}_lostout_fromcorner".format(t)),
        "Lost in Play": _col(df, False, "actions_{}_lostinplay_fromcorner".format(t)),
        "Success - Shot": _col(df, False, "shots_created_{}_fromcorner".format(t)),
        "xG": _col(df, False, "xg_created_{}_fromcorner".format(t)),
    }
    out = _ensure_cols(df, cols)
    out = out[out["All Events"] > 0]
    out = out.sort_values(by="All Events", ascending=False)
    return out[[
        "Player Name","All Events","Lost Out","Lost in Play",
        "Success - Contact","Success - Shot","xG"
    ]]

def _pc_corners(df):
    cols = {
        "Player Name": "playerName",
        "Contacts": _col(df, False, "actions_contacts_fromcorner"),
        "Contacts - Header": _col(df, False, "actions_contacts_header_fromcorner"),
        "Contacts (Lost in Play)": _col(df, False, "actions_contacts_lostinplay_fromcorner"),
        "Contacts (Lost Out)": _col(df, False, "actions_contacts_lostout_fromcorner"),
        "Contacts (Success)": _col(df, False, "actions_contacts_succ_fromcorner"),
        "Shot": _col(df, False, "shots_fromcorner"),
        "Shot - Header": _col(df, False, "shots_header_fromcorner"),
        "Shot (Miss)": _col(df, False, "shots_miss_fromcorner"),
        "Shot - Header (Miss)": _col(df, False, "shots_header_miss_fromcorner"),
        "Shot (Blocked)": _col(df, False, "shots_blocked_fromcorner"),
        "Shot - Header (Blocked)": _col(df, False, "shots_header_blocked_fromcorner"),
        "Shot (Stopped)": _col(df, False, "shots_stopped_fromcorner"),
        "Shot - Header (Stopped)": _col(df, False, "shots_header_stopped_fromcorner"),
        "Goal": _col(df, False, "goals_fromcorner"),
        "Goal - Header": _col(df, False, "goals_header_fromcorner"),
        "xG": _col(df, False, "xg_fromcorner"),
        "xG - Header": _col(df, False, "xg_header_fromcorner"),
    }
    out = _ensure_cols(df, cols)
    out = out[(out["Shot"] > 0)]
    out = out.sort_values(by="Shot", ascending=False).head(9)
    return out[[
        "Player Name","Contacts","Contacts - Header",
        "Contacts (Lost in Play)","Contacts (Lost Out)",
        "Contacts (Success)","Shot","Shot - Header",
        "Shot (Blocked)","Shot - Header (Blocked)",
        "Shot (Miss)","Shot - Header (Miss)",
        "Shot (Stopped)","Shot - Header (Stopped)",
        "xG","xG - Header","Goal","Goal - Header"
    ]]

def _pk_ifks(df):
    cols = {
        "Player Name": "playerName",
        "All Events": _col(df, False, "actions_fromifkbox"),
        "Success - Contact": _col(df, False, "actions_succ_fromifkbox"),
        "Lost Out": _col(df, False, "actions_lostout_fromifkbox"),
        "Lost in Play": _col(df, False, "actions_lostinplay_fromifkbox"),
        "Success - Shot": _col(df, False, "shots_created_fromifkbox"),
        "xG": _col(df, False, "xg_created_fromifkbox"),
    }
    out = _ensure_cols(df, cols)
    out = out[out["All Events"]>0]
    out = out.sort_values(by="All Events",ascending=False)
    return out[["Player Name","All Events","Lost Out", "Lost in Play","Success - Contact","Success - Shot","xG"]]

def _pc_ifks(df):
    cols = {
        "Player Name": "playerName",
        "Contacts": _col(df, False, "actions_contacts_fromifkbox"),
        "Contacts - Header": _col(df, False, "actions_contacts_header_fromifkbox"),
        "Contacts (Lost in Play)": _col(df, False, "actions_contacts_lostinplay_fromifkbox"),
        "Contacts (Lost Out)": _col(df, False, "actions_contacts_lostout_fromifkbox"),
        "Contacts (Success)": _col(df, False, "actions_contacts_succ_fromifkbox"),
        "Shot": _col(df, False, "shots_fromifk"),
        "Shot - Header": _col(df, False, "shots_header_fromifk"),
        "Shot (Miss)": _col(df, False, "shots_miss_fromifk"),
          "Shot - Header (Miss)": _col(df, False, "shots_header_miss_fromifk"),
        "Shot (Blocked)": _col(df, False, "shots_blocked_fromifk"),
        "Shot - Header (Blocked)": _col(df, False, "shots_header_blocked_fromifk"),
        "Shot (Stopped)": _col(df, False, "shots_stopped_fromifk"),
        "Shot - Header (Stopped)": _col(df, False, "shots_header_stopped_fromifk"),
        "Goal": _col(df, False, "goals_fromifk"),
                     "Goal - Header": _col(df, False, "goals_header_fromifk"),
        "xG": _col(df, False, "xg_fromifk"),
                   "xG - Header": _col(df, False, "xg_header_fromifkbox"),
    }
    out = _ensure_cols(df, cols)
    out = out[(out.Shot>0)]
    out = out.sort_values(by="Shot", ascending=False).head(9)
    return out[["Player Name","Contacts","Contacts - Header",
                "Contacts (Lost in Play)","Contacts (Lost Out)",
                "Contacts (Success)","Shot","Shot - Header",
                "Shot (Blocked)","Shot - Header (Blocked)",
                "Shot (Miss)","Shot - Header (Miss)",
                "Shot (Stopped)","Shot - Header (Stopped)",
                "xG","xG - Header","Goal",
               "Goal - Header"]]

def _pk_throwins(df,t):
    cols = {
        "Player Name": "playerName",
        "All Events": _col(df, False, "actions_{}_fromthrowinbox".format(t)),
        "Success - Contact": _col(df, False, "actions_{}_succ_fromthrowinbox".format(t)),
        "Lost Out": _col(df, False, "actions_{}_lostout_fromthrowinbox".format(t)),
        "Lost in Play": _col(df, False, "actions_{}_lostinplay_fromthrowinbox".format(t)),
        "Success - Shot": _col(df, False, "shots_created_{}_fromthrowinbox".format(t)),
        "xG": _col(df, False, "xg_created_{}_fromthrowinbox".format(t)),
    }
    out = _ensure_cols(df, cols)
    out = out[out["All Events"]>0]
    out = out.sort_values(by="All Events",ascending=False)
    return out[["Player Name","All Events","Lost Out", "Lost in Play","Success - Contact","Success - Shot","xG"]]

def _pc_throwins(df):
    cols = {
        "Player Name": "playerName",
        "Contacts": _col(df, False, "actions_contacts_fromthrowinbox"),
        "Contacts - Header": _col(df, False, "actions_contacts_header_fromthrowinbox"),
        "Contacts (Lost in Play)": _col(df, False, "actions_contacts_lostinplay_fromthrowinbox"),
        "Contacts (Lost Out)": _col(df, False, "actions_contacts_lostout_fromthrowinbox"),
        "Contacts (Success)": _col(df, False, "actions_contacts_succ_fromthrowinbox"),
        "Shot": _col(df, False, "shots_fromthrowin"),
        "Shot - Header": _col(df, False, "shots_header_fromthrowin"),
        "Shot (Miss)": _col(df, False, "shots_miss_fromthrowin"),
          "Shot - Header (Miss)": _col(df, False, "shots_header_miss_fromthrowin"),
        "Shot (Blocked)": _col(df, False, "shots_blocked_fromthrowin"),
        "Shot - Header (Blocked)": _col(df, False, "shots_header_blocked_fromthrowin"),
        "Shot (Stopped)": _col(df, False, "shots_stopped_fromthrowin"),
        "Shot - Header (Stopped)": _col(df, False, "shots_header_stopped_fromthrowin"),
        "Goal": _col(df, False, "goals_fromthrowin"),
                     "Goal - Header": _col(df, False, "goals_header_fromthrowin"),
        "xG": _col(df, False, "xg_fromthrowin"),
                   "xG - Header": _col(df, False, "xg_header_fromthrowin"),
    }
    out = _ensure_cols(df, cols)
    out = out[(out["Contacts"]>0) | (out.Shot>0)]
    out = out.sort_values(by="Shot",ascending=False).head(9)
    return out[["Player Name","Contacts","Contacts - Header",
                "Contacts (Lost in Play)","Contacts (Lost Out)",
                "Contacts (Success)","Shot","Shot - Header",
                "Shot (Blocked)","Shot - Header (Blocked)",
                "Shot (Miss)","Shot - Header (Miss)",
                "Shot (Stopped)","Shot - Header (Stopped)",
                "xG","xG - Header","Goal",
               "Goal - Header"]]

def team_stats_detailed(df):
    import numpy as np
    import pandas as pd

    df["Rival"] = np.where(df.away_name==df.teamName, df.home_name, df.away_name)
    df = df[["Rival","localDate","field","team_formation_desc","changes_num"]]

    df.rename(columns={
        "Rival": "Against",
        "localDate": "Date",
        "field": "Field",
        "team_formation_desc": "Formation",
        "changes_num": "Substitutions"
    }, inplace=True)

    # 👉 Fuerza orden ascendente por fecha para que coincida con tu notebook
    if "Date" in df.columns:
        # Si Date viene como string, conviértelo antes para garantizar el orden temporal
        try:
            df["Date"] = pd.to_datetime(df["Date"])
        except Exception:
            pass
        df = df.sort_values(by="Date", ascending=True).reset_index(drop=True)

    # (Opcional) convierte numéricas a string si Word da guerra con formatos
    num_cols = ["Substitutions"]
    for c in num_cols:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: "" if pd.isna(x) else str(x))

    return df 


import numpy as np
import pandas as pd

def players_overview(df: pd.DataFrame, rival: str) -> pd.DataFrame:
    """
    Construye la tabla de overview de jugadores para el rival.
    - df debe ser el df de jugadores (df_players.csv).
    - Mantiene el orden de columnas EXACTO como en el notebook.
    - 'logo' se deja en blanco (no metemos imágenes en el Word).
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # POS = position / position2
    pos1 = df.get("position")
    pos2 = df.get("position2")
    df["POS"] = np.where(
        pos2.isna() if pos2 is not None else True,
        pos1,
        pos1.fillna("").astype(str) + "/" + pos2.fillna("").astype(str)
    )

    # Filtrar rival + ordenar por 'orden' (si no existe, no ordena)
    if "teamName" in df.columns:
        df = df[df["teamName"] == rival]
    if "orden" in df.columns:
        df = df.sort_values(by="orden", na_position="last")

    # Selección de columnas (si faltan, crearlas vacías)
    cols_source = [
        "shirtNo", "playerName", "POS", "age", "height",
        "corner_taker_sn", "ifk_taker_sn", "throwin_taker_sn", "dfk_taker_sn",
        "passes_sp", "passes_succ_sp", "shots_sp", "goals_sp", "xg_sp",
        "actions_fromcorner", "actions_succ_fromcorner",
        "actions_fromifkbox", "actions_succ_fromifkbox",
        "actions_fromthrowinbox", "actions_succ_fromthrowinbox",
        "shots_fromdfk"
    ]

    df = df[cols_source].rename(columns={
        "shirtNo":"No",
        "playerName":"Player",
        "POS":"Pos",
        "age":"Age",
        "height":"Height",
        "corner_taker_sn":"Corner Taker",
        "ifk_taker_sn":"IFK Taker",
        "throwin_taker_sn":"Throwin Taker",
        "dfk_taker_sn":"DFK Taker",
        "passes_sp":"SP",
        "passes_succ_sp":"SP Succ",
        "shots_sp":"SP Shots",
        "goals_sp":"SP Goals",
        "xg_sp":"SP xG",
        "actions_fromcorner":"Corners",
        "actions_succ_fromcorner":"Corners Succ",
        "actions_fromifkbox":"IFK Box",
        "actions_succ_fromifkbox":"IFK Box Succ",
        "actions_fromthrowinbox":"ThrowIns to Box",
        "actions_succ_fromthrowinbox":"ThrowIns to Box Succ",
        "shots_fromdfk":"DFK Shots"
    })

    # Asegurar tipos “amables” para que Word no dé guerra
    num_cols = ["No","Age","Height","SP","SP Succ","SP Shots","SP Goals","SP xG",
                "Corners","Corners Succ","IFK Box","IFK Box Succ",
                "ThrowIns to Box","ThrowIns to Box Succ","DFK Shots"]
    # --- Tipado de columnas ---
    # 1) columnas string básicas
    str_cols = ["Player", "Pos"]
    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str)

    # 2) columnas mixtas: convertir a int -> string -> limpiar "0"
    mixed_cols = ["No", "Corner Taker", "IFK Taker", "Throwin Taker", "DFK Taker"]
    for c in mixed_cols:
        if c in df.columns:
            # primero convertimos a int (NaN→0)
            df[c] = (
                pd.to_numeric(df[c], errors="coerce")
                .fillna(0)
                .astype(int)
                .astype(str)
                .replace("0", "")  # convertir "0" en blanco
            )

    # 3) columna float (2 decimales)
    if "SP xG" in df.columns:
        df["SP xG"] = (
            pd.to_numeric(df["SP xG"], errors="coerce")
            .fillna(0.0)
            .round(2)
            .astype(float)
        )

    # 4) columnas enteras (todas las demás numéricas)
    int_cols = [
        "Age", "Height",
        "SP", "SP Succ", "SP Shots", "SP Goals",
        "Corners", "Corners Succ",
        "IFK Box", "IFK Box Succ",
        "ThrowIns to Box", "ThrowIns to Box Succ",
        "DFK Shots",
    ]
    for c in int_cols:
        if c in df.columns:
            df[c] = (
                pd.to_numeric(df[c], errors="coerce")
                .fillna(0)
                .round()
                .astype("Int64")
            )

    # 5) mantener orden final coherente con la plantilla
    new_order = [
        "No", "Player", "Pos", "Age", "Height",
        "Corner Taker", "IFK Taker", "Throwin Taker", "DFK Taker",
        "SP", "SP Succ", "SP Shots", "SP Goals", "SP xG",
        "Corners", "Corners Succ",
        "IFK Box", "IFK Box Succ",
        "ThrowIns to Box", "ThrowIns to Box Succ",
        "DFK Shots"
    ]
    df = df[[c for c in new_order if c in df.columns]]

    return df
