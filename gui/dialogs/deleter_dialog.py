# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
from sqlalchemy.exc import IntegrityError

''' Provides a dialog for confirming deletion of an item. '''

@st.dialog("Are you sure?")
def check_delete(session, item):
    warning = st.warning("This will permanently delete the item and its stored data. Are you sure you wish to proceed?")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Confirm"):
            with st.spinner("Deleting..."):
                session.delete(item)
                try:
                    session.commit()
                    st.rerun()
                except IntegrityError:
                    session.rollback()
                    warning.warning("Could not delete this item as it is contains data. Please remove all data before deleting.")
    with col2:
        if st.button("Cancel"):
            st.rerun()