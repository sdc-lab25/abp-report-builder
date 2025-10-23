# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 00:19:17 2025

@author: aleex
"""

import pandas as pd
import numpy as np
from functools import reduce


def get_gk_events(event_data,player_data,dim_team):
    ev=event_data[(event_data.type_value.isin([1,13,14,15,16]))]
    player_data=pd.merge(player_data,dim_team[['teamId','teamName']],how='left',on="teamId")
    try:
        player_data['teamName']=player_data.teamName_y
    except:
        pass
    evs = pd.merge(ev,player_data[["matchId","teamName","keeperId","subbedInExpandedMinute"]],
                  left_on=["matchId","oppositionTeamName"],right_on=["matchId","teamName"])
    #evs = pd.merge(evs,match_data[["matchId","season"]],on="matchId",how='left')  
    evs = evs[evs.minute<evs.subbedInExpandedMinute]  
    evs['ps_xG'] = np.where((evs.type_value.isin([15,16])) & (evs.value_Blocked==1) ,0,evs.ps_xG)
    evs['isPass'] =np.where(evs.type_value==1,1,0)    
    evs['isShot'] =np.where(evs.type_value.isin([13,14,15,16]),1,0)  
    evs['isGoal'] =np.where(evs.type_value.isin([16]),1,0)     
    evs['isIntervention'] =np.where(evs.type_value.isin([1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 41, 42, 50, 52, 54,61]),1,0)
    evs['isIntervention_finalthird'] = np.where((evs['isIntervention']==1) & (evs.tercio_id==3),1,0)
    evs['isIntervention_box'] = np.where((evs['isIntervention']==1) & (evs.x>=83) & ((evs.y>=21.1) | (evs.y<=78.9)),1,0)            
    ev_group = evs.groupby(by=["keeperId","matchId"],as_index=False)[["value_Cross","ps_xG","xG","isShot","isGoal","isIntervention","isIntervention_finalthird","isIntervention_box"]].sum()
    ev_sotgoalside = evs[(evs.type_value.isin([15,16])) & ((evs.value_Blocked!=1) | (evs.value_Blocked.isna()==True)) & (evs.isShot==1) & ((evs.value_HighLeft==1) | (evs.value_LowRight==1) | (evs.value_HighRight==1) | (evs.value_LowLeft==1) )].groupby(by=["keeperId","matchId"],as_index=False).id.count()
    ev_sotgoalside.rename({"id":"opp_sotgoalside"},inplace=True,axis=1)
    ev_savegoalside = evs[(evs.type_value.isin([15,16])) & ((evs.value_Blocked!=1) | (evs.value_Blocked.isna()==True)) & (evs.type_value==15) & ((evs.value_HighLeft==1) | (evs.value_LowRight==1) | (evs.value_HighRight==1) | (evs.value_LowLeft==1) )].groupby(by=["keeperId","matchId"],as_index=False).id.count()
    ev_savegoalside.rename({"id":"save_goalside"},inplace=True,axis=1)
    ev_sotcc = evs[(evs.type_value.isin([15,16])) & ((evs.value_Blocked!=1) | (evs.value_Blocked.isna()==True)) & (evs.isShot==1) & (evs.value_BigChance==1)].groupby(by=["keeperId","matchId"],as_index=False).id.count()
    ev_sotcc.rename({"id":"opp_sotcc"},inplace=True,axis=1)
    ev_savecc = evs[(evs.type_value.isin([15,16])) & ((evs.value_Blocked!=1) | (evs.value_Blocked.isna()==True)) & (evs.type_value==15) & (evs.value_BigChance==1)].groupby(by=["keeperId","matchId"],as_index=False).id.count()
    ev_savecc.rename({"id":"save_cc"},inplace=True,axis=1)
    ev_sotboxdanger = evs[(evs.type_value.isin([15,16])) & ((evs.value_Blocked!=1) | (evs.value_Blocked.isna()==True)) & (evs.isShot==1) & ((evs.value_BoxCentre==1) | (evs.value_SmallBoxLeft==1) | (evs.value_SmallBoxRight==1) | (evs.value_SmallBoxCentre==1) )].groupby(by=["keeperId","matchId"],as_index=False).id.count()
    ev_sotboxdanger.rename({"id":"opp_sotboxdanger"},inplace=True,axis=1)
    ev_saveboxdanger = evs[(evs.type_value.isin([15,16])) & ((evs.value_Blocked!=1) | (evs.value_Blocked.isna()==True)) & (evs.type_value==15) & ((evs.value_BoxCentre==1) | (evs.value_SmallBoxLeft==1) | (evs.value_SmallBoxRight==1) | (evs.value_SmallBoxCentre==1) )].groupby(by=["keeperId","matchId"],as_index=False).id.count()
    ev_saveboxdanger.rename({"id":"save_boxdanger"},inplace=True,axis=1)
    ev_sot = evs[(evs.type_value.isin([15,16])) & ((evs.value_Blocked!=1) | (evs.value_Blocked.isna()==True)) ].groupby(by=["keeperId","matchId"],as_index=False).id.count()
    ev_sot.rename({"id":"opp_sot"},inplace=True,axis=1)
    ev_sotoneonone = evs[(evs.type_value.isin([15,16])) & ((evs.value_Blocked!=1) | (evs.value_Blocked.isna()==True)) & (evs.isShot==1) & ((evs.qualifiers.str.contains("'qualifierId': 89}")) | (evs["qualifiers"].apply(lambda x: "'qualifierId': 89}".replace("qualifierId", "value").replace("}", ".") not in x)))].groupby(by=["keeperId","matchId"],as_index=False).id.count()
    ev_sotoneonone.rename({"id":"opp_sotboxdanger"},inplace=True,axis=1)
    ev_saveoneonone = evs[(evs.type_value.isin([15,16])) & ((evs.value_Blocked!=1) | (evs.value_Blocked.isna()==True)) & (evs.type_value==15) & ((evs["qualifiers"].apply(lambda x: "'qualifierId': 89}".replace("qualifierId", "value").replace("}", ".") not in x)))].groupby(by=["keeperId","matchId"],as_index=False).id.count()
    ev_saveoneonone.rename({"id":"saves_oneonone"},inplace=True,axis=1)
    
    ev_group.rename({"value_Cross":"opp_cross","isShot":"opp_shot","xG":"opp_xG","ps_xG":"opp_psxG","isGoal":"opp_goal",
                     "isIntervention":"op_ob_interventions","isIntervention_finalthird":"op_ob_interventions_finalthird",
                     "isIntervention_box":"op_ob_interventions_box"},inplace=True,axis=1)
    ev_group = pd.merge(ev_group,ev_sot,how="left",on=["keeperId","matchId"])
    
    ev_group = pd.merge(ev_group,ev_sotgoalside,how="left",on=["keeperId","matchId"])
    ev_group = pd.merge(ev_group,ev_savegoalside,how="left",on=["keeperId","matchId"])
    ev_group = pd.merge(ev_group,ev_sotcc,how="left",on=["keeperId","matchId"])
    ev_group = pd.merge(ev_group,ev_savecc,how="left",on=["keeperId","matchId"])
    ev_group = pd.merge(ev_group,ev_sotboxdanger,how="left",on=["keeperId","matchId"])
    ev_group = pd.merge(ev_group,ev_saveboxdanger,how="left",on=["keeperId","matchId"])
    ev_group = pd.merge(ev_group,ev_saveoneonone,how="left",on=["keeperId","matchId"])
    
    ev_group.rename({"keeperId":"playerId"},axis=1,inplace=True)
    ev_group = ev_group.fillna(0)
    return ev_group


def get_pu_claims(events_gk):
    pu_claims=pd.DataFrame()
    pus=events_gk[((events_gk['type_displayName'].isin(["Claim","Punch"])) & (events_gk['outcomeType_value']!=1)) | (events_gk['type_displayName'].isin(["KeeperPickup","Keeper pick-up"]))]
    for m in pus.matchId.unique():
        match = pus[pus.matchId==m]
        cn= match[(match['type_displayName'].isin(["Claim","Punch"])) & (match['outcomeType_value']!=1)]
        puck = match[(match['type_displayName'].isin(["KeeperPickup","Keeper pick-up"]))]
        for i,j in cn.iterrows():
            p=puck[(puck.time_seconds>=j['time_seconds']) & (puck.time_seconds<=j['time_seconds']+5)]
            p['seconds_after'] = p.time_seconds-j['time_seconds']
            p['claim_id'] = j['id']
            if p.shape[0]>0:
                pu_claims=pd.concat([pu_claims,p])
    return pu_claims


def add_auxiliary_columns(df):
    """
    Añade columnas auxiliares necesarias para los filtros.
    """
    df = df.reset_index(drop=True)
    df['qualifiers'] = df['qualifiers'].astype(str)
    cols_to_init = [
        "progressive_pass",
        "progressive_carry",
        "open_pass",
        "final_third_pass",
        "claim_safe",
        "value_Length_alt"
    ]
    for col in cols_to_init:
        df[col] = False
    gpu = get_pu_claims(df)
    # --- Progressive Pass ---
    df["progressive_pass"] = ((df['type_displayName']=="Pass") &
                      (df.endX>df.x) &
                      (((df.endX-df.x)*105/100 > 30) & (df.endX<50)
                       | ((df.endX-df.x)*105/100 > 15) & (df.endX>50) & (df.x<=50)
                       | ((df.endX-df.x)*105/100 > 10) & (df.endX>50) & (df.x>=50)
                       ))
    df["progressive_carry"] = ((df['type_value']==101) &
                      ((df.endX-df.x)>=5))
                     
    # --- Open Play Pass ---
    df["open_pass"] = (
        (df["type_displayName"] == "Pass") &
        ((~df.qualifiers.str.contains("'qualifierId': 5}")) & ((df["qualifiers"].apply(lambda x: "'qualifierId': 5}".replace("qualifierId", "value").replace("}", ".") not in x)))) &
        ((~df.qualifiers.str.contains("'qualifierId': 6}")) & ((df["qualifiers"].apply(lambda x: "'qualifierId': 6}".replace("qualifierId", "value").replace("}", ".") not in x)))) &
        (df.value_Chipped==1) & (df.endX>df.x) & (df.y>21.1) & (df.y<=78.9) &
        ((~df.qualifiers.str.contains("'qualifierId': 107}")) & ((df["qualifiers"].apply(lambda x: "'qualifierId': 107}".replace("qualifierId", "value").replace("}", ".") not in x)))) & 
        (df.endX<=50) & (df.endX>17) & ((df.endY<21.1) | (df.endY>78.9))
    )

    # --- Final Third Pass ---
    df["final_third_pass"] = (
        (df["type_displayName"] == "Pass") &
        (df["endX"] >= 66.6) & (df.x<66.6)  # Consideramos final third como último tercio
    )
    if gpu.shape[0]>0:
    # --- Safe Claim ---
        df["claim_safe"] = ((
            (df["type_displayName"].isin(["Claim", "Punch"])) &
            (df["outcomeType_value"] != 1)  # Exitoso
            & (df.id.isin(gpu.claim_id.unique())))
            | ((df["type_displayName"].isin(["Punch"])) & (df["outcomeType_value"] == 1))
        )

    # --- Alternativa para pases: calcular longitud alternativa (positivo/negativo) ---
    df["value_Length_alt"] = df.apply(
        lambda x: -x["value_Length"] if x["x"] > x["endX"] else x["value_Length"],
        axis=1
    )
    #df.replace({False:0,True:1},inplace=True)
    return df

def calcular_kpis_carries(df):
    # Asegurarse de que ciertas columnas están en el formato correcto
    df['progressive_carry'] = df['progressive_carry'].astype(bool)

    # Columnas con condiciones
    df['carry_box'] = (
        (df['type_displayName'].isin(['Carry'])) &
        (df['endX'] >= 83) &
        (df['endY'] >= 21.1) & (df['endY'] <= 78.9)
    )

    df['carry_succ_box'] = (
        (df['type_displayName'].isin(['Carry'])) &
        (df['outcomeType_value'] == 1) &
        (df['endX'] >= 83) &
        (df['endY'] >= 21.1) & (df['endY'] <= 78.9)
    )

    df['carry_prog'] = (df['progressive_carry'] == True)

    df['carries'] = df['type_displayName'].isin(['Carry'])

    df['carries_finalthird'] = (
        df['type_displayName'].isin(['Carry']) &
        (df['tercio_id'] == 3)
    )

    df['carries_ext'] = (
        df['type_displayName'].isin(['Carry']) &
        (df['carril_id'] == 'EXT')
    )

    # Agrupar y contar cada métrica
    kpis = df.groupby(['playerId', 'season', 'playerName'])[
        ['carry_box', 'carry_succ_box', 'carry_prog', 'carries', 'carries_finalthird', 'carries_ext']
    ].sum().reset_index()

    return kpis

def transform_events_agg(event_data, series_config,gr_cols):
    
    results = {}
    
    
    for name, config in series_config.items():
            df_filtered = event_data.copy()
            
            if "filters" in config:
                for f in config["filters"]:
                    if "or" in f:
                        op_map = {
                            "==": lambda col, val: col == val,
                            "!=": lambda col, val: col != val,
                            ">": lambda col, val: col > val,
                            ">=": lambda col, val: col >= val,
                            "<": lambda col, val: col < val,
                            "<=": lambda col, val: col <= val,
                            "in": lambda col, val: col.isin(val),
                            "contains": lambda col, val: col.str.contains(val, na=False),
                            "ncontains": lambda col, val: ~col.str.contains(val, na=False)
                        }

                        or_conditions = []
                        for cond in f["or"]:
                            col, op, val = cond["column"], cond["op"], cond["value"]
                            if op in op_map:
                                or_conditions.append(op_map[op](df_filtered[col], val))
                        
                        if or_conditions:
                            df_filtered = df_filtered[pd.concat(or_conditions, axis=1).any(axis=1)]
                    else:
                        col, op, val = f["column"], f["op"], f["value"]
                        if op == "==":
                            df_filtered = df_filtered[df_filtered[col] == val]
                        elif op == "!=":
                            df_filtered = df_filtered[df_filtered[col] != val]
                        elif op == ">":
                            df_filtered = df_filtered[df_filtered[col] > val]
                        elif op == ">=":
                            df_filtered = df_filtered[df_filtered[col] >= val]
                        elif op == "<":
                            df_filtered = df_filtered[df_filtered[col] < val]
                        elif op == "<=":
                            df_filtered = df_filtered[df_filtered[col] <= val]
                        elif op == "in":
                            df_filtered = df_filtered[df_filtered[col].isin(val)]
                        elif op == "contains":
                            df_filtered = df_filtered[(df_filtered[col].str.contains(val,regex=False)) | (df_filtered[col].str.contains(val.replace("}", "."),regex=False)) ]
                        elif op == "ncontains":
                            df_filtered = df_filtered[(~df_filtered[col].str.contains(val,regex=False)) & (~df_filtered[col].str.contains(val.replace("}", "."),regex=False)) ]
            if "aggregation" in config:
                agg_col = config["aggregation"]["agg_column"]
                grouped = df_filtered.groupby(by=gr_cols, as_index=False)[agg_col].sum()
                
                if config["aggregation"].get("convert_meters", False): 
                    grouped[agg_col] = grouped[agg_col] * 0.9144
            else:
                grouped = df_filtered.groupby(by=gr_cols, as_index=False).type_displayName.count()
            
            grouped.columns = gr_cols+[name]
            results[name] = grouped
        
    dfs = [df for df in list(results.values()) if not df.empty]
    final_df = reduce(lambda left, right: pd.merge(left, right, on=gr_cols, how="outer"), dfs)   
    
    
    
    
    ni = [i for i in series_config if i not in final_df.columns]
    if len(ni)>0:
        for i in ni:
            final_df[i]=0
    final_df = final_df.fillna(0)
    return final_df

def calcula_medidas_compuestas(dd):
    dd["goals_fromcorner_pct"] = (dd["goals_fromcorner"] / dd["actions_fromcorner"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["xg_fromcorner_pct"] = (dd["xg_fromcorner"] / dd["shots_fromcorner"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["shots_fromcorner_pct"] = (dd["shots_fromcorner"] / dd["actions_fromcorner"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["actions_succ_fromcorner_pct"] = (dd["actions_succ_fromcorner"] / dd["actions_fromcorner"]).replace([np.inf, -np.inf], 0).fillna(0)
    
    dd["goals_fromdfk_pct"] = (dd["goals_fromdfk"] / dd["shots_fromdfk"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["xg_fromdfk_pct"] = (dd["xg_fromdfk"] / dd["shots_fromdfk"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["shots_dfk_pct"] = (dd["shots_succ_fromdfk"] / dd["shots_fromdfk"]).replace([np.inf, -np.inf], 0).fillna(0)

    dd["goals_fromifkbox_pct"] = (dd["goals_fromifkbox"] / dd["shots_fromifkbox"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["xg_fromifkbox_pct"] = (dd["xg_fromifkbox"] / dd["shots_fromifkbox"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["shots_fromifkbox_pct"] = (dd["shots_fromifkbox"] / dd["actions_fromifkbox"]).replace([np.inf, -np.inf], 0).fillna(0)
    
    dd["goals_fromifk_pct"] = (dd["goals_fromifk"] / dd["actions_fromifkbox"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["xg_fromifk_pct"] = (dd["xg_fromifk"] / dd["shots_fromifk"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["shots_fromifk_pct"] = (dd["shots_fromifk"] / dd["actions_fromifkbox"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["actions_succ_fromifkbox_pct"] = (dd["actions_succ_fromifkbox"] / dd["actions_fromifkbox"]).replace([np.inf, -np.inf], 0).fillna(0)

    dd["goals_fromthrowin_pct"] = (dd["goals_fromthrowin"] / dd["actions_fromthrowinbox"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["xg_fromthrowin_pct"] = (dd["xg_fromthrowin"] / dd["shots_fromthrowin"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["shots_fromthrowin_pct"] = (dd["shots_fromthrowin"] / dd["actions_fromthrowinbox"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["actions_succ_fromthrowinbox_pct"] = (dd["actions_succ_fromthrowinbox"] / dd["actions_fromthrowinbox"]).replace([np.inf, -np.inf], 0).fillna(0)
    
    
    # Porcentajes y ratios con protección contra división por cero
    dd["actions_sp"] = dd["passes_sp"] + dd["shots_fromdfk"]
    dd["actions_succ_sp"] = dd["passes_succ_sp"] + dd["shots_fromdfk"]
    dd["actions_succ_sp_pct"] = (dd["actions_succ_sp"] / dd["actions_sp"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["goals_sp_pct"] = (dd["goals_sp"] / dd["actions_sp"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["shots_sp_pct"] = (dd["shots_sp"] / dd["actions_sp"]).replace([np.inf, -np.inf], 0).fillna(0)
    dd["xg_sp_pct"] = (dd["xg_sp"] / dd["actions_sp"]).replace([np.inf, -np.inf], 0).fillna(0)
    
    dd["actions_1p_fromcorner"] = dd.actions_right_1p_fromcorner + dd.actions_left_1p_fromcorner
    dd["actions_2p_fromcorner"] = dd.actions_right_2p_fromcorner + dd.actions_left_2p_fromcorner
    dd["actions_pfoot_fromcorner"] = dd.actions_right_pfoot_fromcorner + dd.actions_left_pfoot_fromcorner
    dd["actions_ofoot_fromcorner"] = dd.actions_right_ofoot_fromcorner + dd.actions_left_ofoot_fromcorner
    dd["actions_toolong_fromcorner"] = dd.actions_right_toolong_fromcorner + dd.actions_left_toolong_fromcorner
    dd["actions_near_fromcorner"] = dd.actions_right_near_fromcorner + dd.actions_left_near_fromcorner
    dd["shots_created_fromcorner"] = dd["shots_created_left_fromcorner"] + dd["shots_created_right_fromcorner"]
    dd["xg_created_fromcorner"] = dd["xg_created_left_fromcorner"] + dd["xg_created_right_fromcorner"]
    
    dd["actions_lat_fromifkbox"] = dd.actions_right_fromifkbox + dd.actions_left_fromifkbox
    dd["actions_other_fromifk"] = dd.actions_fromifk - dd.actions_fromifkbox
    dd["actions_1p_fromifkbox"] = dd.actions_right_1p_fromifkbox + dd.actions_left_1p_fromifkbox
    dd["actions_2p_fromifkbox"] = dd.actions_right_2p_fromifkbox + dd.actions_left_2p_fromifkbox
    dd["actions_pfoot_fromifkbox"] = dd.actions_right_pfoot_fromifkbox + dd.actions_left_pfoot_fromifkbox
    dd["actions_ofoot_fromifkbox"] = dd.actions_right_ofoot_fromifkbox + dd.actions_left_ofoot_fromifkbox
    
    dd["actions_1p_fromthrowinbox"] = dd.actions_right_1p_fromthrowinbox + dd.actions_left_1p_fromthrowinbox
    dd["actions_2p_fromthrowinbox"] = dd.actions_right_2p_fromthrowinbox + dd.actions_left_2p_fromthrowinbox
    return dd


def calcula_secuencia_xg(df, col_xg,col_tiro):
    """
    Para cada fila del DataFrame, asigna en 'col_xg_secuencia' el xG de la primera acción de tiro siguiente 
    (type_value en [13,14,15,16]) en el mismo partido y periodo, y con tiempo posterior.
    
    Args:
        df: DataFrame de entrada
        col_xg: columna que contiene xG
        tipo_tiro_col: columna que indica tipo de acción
        tiros: lista de valores que definen un tiro
        
    Returns:
        df con nueva columna 'col_xg_secuencia'
    """
    
    df = df.sort_values(by=['matchId','period_value','time_seconds'],ascending=True).reset_index(drop=True)
    df[col_xg] = np.nan
    
    # Índices de todas las acciones de tiro
    indices_pretiros = df.index[df[col_tiro]==1].to_list()
    indices_tiros = df.index[df["type_value"].isin([13,14,15,16])].to_list()
    


    
    for i in indices_pretiros:
        candidatos = [p for p in indices_tiros if p > i]
        if len(candidatos)>0:
            
            siguiente_idx = min(candidatos)
                    # Comprobamos mismo match, mismo periodo y tiempo mayor o igual
            if (df.at[siguiente_idx, 'matchId'] == df.at[i, 'matchId'] and
                        df.at[siguiente_idx, 'period_value'] == df.at[i, 'period_value'] and
                        df.at[siguiente_idx, 'time_seconds'] >= df.at[i, 'time_seconds']):
                        df.at[i, col_xg] = df.at[siguiente_idx, "xG"]
    
    return df
    
def calcula_secuencia_shotproc(df, col_sec,col_tiro):
    """
    Para cada fila del DataFrame, asigna en 'col_xg_secuencia' el xG de la primera acción de tiro siguiente 
    (type_value en [13,14,15,16]) en el mismo partido y periodo, y con tiempo posterior.
    
    Args:
        df: DataFrame de entrada
        col_xg: columna que contiene xG
        tipo_tiro_col: columna que indica tipo de acción
        tiros: lista de valores que definen un tiro
        
    Returns:
        df con nueva columna 'col_xg_secuencia'
    """
    col_shots = col_sec.replace("_left_","_").replace("_right_","_").replace("_short_","_").replace("_long_","_").replace("__","_")
    col_abp = col_tiro.split("_")[0]+ "_" + col_tiro.split("_")[-1]
    df = df.sort_values(by=['matchId','period_value','time_seconds'],ascending=True).reset_index(drop=True)
    
        
    # Índices de todas las acciones de tiro
    indices_pretiros = df.index[df[col_abp]==1].to_list()
    indices_tiros = df.index[df[col_shots] ==1].to_list()
        
    
        
    # Inicializamos la columna
    df[col_sec] = np.nan
        
    for i in indices_tiros:
        candidatos = [p for p in indices_pretiros if p < i]
        if len(candidatos)>0:
            siguiente_idx = max(candidatos)
            if (df.at[siguiente_idx, 'matchId'] == df.at[i, 'matchId'] and
                df.at[siguiente_idx, 'period_value'] == df.at[i, 'period_value'] and
                df.at[siguiente_idx, 'time_seconds'] <= df.at[i, 'time_seconds'] and
                df.at[siguiente_idx, col_tiro] == 1):
                             
                    df.at[i, col_sec] = df.at[i, col_shots]
    
    return df



def calcula_secuencia_contacts(df, col_tiro):
    """
    Para cada fila del DataFrame, asigna en 'col_xg_secuencia' el xG de la primera acción de tiro siguiente 
    (type_value en [13,14,15,16]) en el mismo partido y periodo, y con tiempo posterior.
    
    Args:
        df: DataFrame de entrada
        col_xg: columna que contiene xG
        tipo_tiro_col: columna que indica tipo de acción
        tiros: lista de valores que definen un tiro
        
    Returns:
        df con nueva columna 'col_xg_secuencia'
    """

    df = df.sort_values(by=['matchId','period_value','time_seconds'],ascending=True).reset_index(drop=True)
    
        
    indices_tiros = df.index[df[col_tiro] ==1].to_list()
    col_abp = col_tiro.split("_")[-1]    
    df["actions_contacts_{}".format(col_abp)] = np.nan
    df["actions_contacts_header_{}".format(col_abp)] = np.nan
    df["actions_contacts_header_succ_{}".format(col_abp)] = np.nan
    df["actions_contacts_header_lostinplay_{}".format(col_abp)] = np.nan
    df["actions_contacts_header_lostout_{}".format(col_abp)] = np.nan
    df["actions_contacts_header_kp_{}".format(col_abp)] = np.nan
    df["actions_contacts_succ_{}".format(col_abp)] = np.nan
    df["actions_contacts_lostinplay_{}".format(col_abp)] = np.nan
    df["actions_contacts_lostout_{}".format(col_abp)] = np.nan
    df["actions_contacts_kp_{}".format(col_abp)] = np.nan
        
    for i in indices_tiros:
        df_i = df[(df.playerId==df[df.index==i].pase_receptor_id.values[0]) & (df.time_seconds>=df[df.index==i].time_seconds.values[0]) & (df.matchId==df[df.index==i].matchId.values[0]) & (df.period_value==df[df.index==i].period_value.values[0])].head(1)
        if df_i.shape[0]>0:
            qualifier = df_i.qualifiers.astype(str).values[0]
            idx = df_i.index[0]
            
            df.at[idx, "actions_contacts_{}".format(col_abp)] = 1
            
            if "'qualifierId': 15}" in qualifier or "'qualifierId': 15." in qualifier:
                df.at[idx, "actions_contacts_header_{}".format(col_abp)] = 1
                if df_i.outcomeType_value.values[0]==1:
                    df.at[idx, "actions_contacts_header_succ_{}".format(col_abp)] = 1
                if df_i.outcomeType_value.values[0]==0:
                    df.at[idx, "actions_contacts_header_lostinplay_{}".format(col_abp)] = 1
                if "'qualifierId': 167}" in qualifier or "'qualifierId': 167." in qualifier:
                    df.at[idx, "actions_contacts_header_lostout_{}".format(col_abp)] = 1
                if df_i.outcomeType_value.values[0]==1 and ( "'qualifierId': 210}" in qualifier or "'qualifierId': 210." in qualifier):
                    df.at[idx, "actions_contacts_header_kp_{}".format(col_abp)] = 1
            else:
                if df_i.outcomeType_value.values[0]==1:
                    df.at[idx, "actions_contacts_succ_{}".format(col_abp)] = 1
                if df_i.outcomeType_value.values[0]==0:
                    df.at[idx, "actions_contacts_lostinplay_{}".format(col_abp)] = 1
                if "'qualifierId': 167}" in qualifier or "'qualifierId': 167." in qualifier:
                    df.at[idx, "actions_contacts_lostout_{}".format(col_abp)] = 1
                if df_i.outcomeType_value.values[0]==1 and ( "'qualifierId': 210}" in qualifier or "'qualifierId': 210." in qualifier):
                    df.at[idx, "actions_contacts_kp_{}".format(col_abp)] = 1
        
    return df
    

def calcula_medidas_secuencia(df,medidas):
    for medida in medidas:
        func=medidas[medida]['funcion_calculo']
        origen = medidas[medida]['columna_origen']
        if func=="secuencia_xg":
            df=calcula_secuencia_xg(df,medida,origen)
        if func=="secuencia_shotproc":
            df=calcula_secuencia_shotproc(df,medida,origen)
        if func=="secuencia_contacts":
            df=calcula_secuencia_contacts(df, origen)
        
    return df