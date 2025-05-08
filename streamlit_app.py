# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gui.menu import make_table
from app.db.settings import DATABASE_URL


@st.cache_resource
def get_session(db_path):
    engine = create_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()

# Initialize session state variables
if 'db_session' not in st.session_state:
    session = get_session(DATABASE_URL)
    st.session_state.db_session = session

make_table()
