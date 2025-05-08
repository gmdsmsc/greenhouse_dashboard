# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st

''' Retrieves the database connection details from Streamlit secrets.'''

host = st.secrets["DB_HOST"]
user = st.secrets["DB_USER"]
password = st.secrets["DB_PASS"]
port = st.secrets["DB_PORT"]
dialect = st.secrets["DB_DIALECT"]
db_name = st.secrets["DB_NAME"]
DATABASE_URL = f"{dialect}://{user}:{password}@{host}:{port}/{db_name}"
