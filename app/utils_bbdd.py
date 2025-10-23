# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 01:39:23 2025

@author: aleex
"""

import pandas as pd
from sqlalchemy import create_engine
import json

def get_conn(ruta_config):
    with open('{}/config.json'.format(ruta_config), 'r') as file:
        config_data = json.load(file)
    engine = create_engine(f"mysql+mysqlconnector://{config_data["db_watford"]["user"]}:{config_data["db_watford"]["password"]}@{config_data["db_watford"]["host"]}:{config_data["db_watford"]["port"]}/{config_data["db_watford"]["database"]}")
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