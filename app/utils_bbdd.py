# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 01:39:23 2025

@author: aleex
"""

import pandas as pd
from sqlalchemy import create_engine
import json

def get_conn(ruta_config):
    user = st.secrets["db_watford"]["user"]
    password = st.secrets["db_watford"]["password"]
    host = st.secrets["db_watford"]["host"]
    port = st.secrets["db_watford"]["port"]
    database = st.secrets["db_watford"]["database"]
    #user = os.environ.get("DB_WATFORD__USER")
    #password = os.environ.get("DB_WATFORD__PASSWORD")
    #host = os.environ.get("DB_WATFORD__HOST")
    #port = os.environ.get("DB_WATFORD__PORT")
    #database = os.environ.get("DB_WATFORD__DATABASE")
    engine = create_engine(
        f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    )
    return engine

def clean_df(df):
    for i in df.columns:
        if "name" not in i.lower() and "id" not in i.lower():
            df[i] = df[i].apply(lambda x: x.replace(",",".") if isinstance(x, str) else x)

    df = df.apply(pd.to_numeric, errors='ignore')
    for i in df.columns:
        if "top" in i:
            df[i]=df[i].fillna(0)
    return df