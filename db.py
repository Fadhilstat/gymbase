import sqlite3
import pandas as pd
import streamlit as st
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gym_database.sqlite')

@st.cache_resource
def _get_conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA foreign_keys = ON")
    return c

def q(sql, params=()):
    """Run SELECT → return DataFrame"""
    return pd.read_sql_query(sql, _get_conn(), params=params)

def run(sql, params=()):
    """Run INSERT / UPDATE / DELETE"""
    conn = _get_conn()
    conn.execute(sql, params)
    conn.commit()

def db_exists():
    return os.path.exists(DB_PATH)
