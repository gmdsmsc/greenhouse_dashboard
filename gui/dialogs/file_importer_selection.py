# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
from gui.csv_importer import run_csv_importer
from gui.file_importer import uploader_modal

''' Provides a dialog for selecting the type of file importer to use. '''

@st.dialog("Attach Sensor Readings")
def importer_type_selection():

    attach_mode = st.selectbox(
        "Select Sensor Readings",
        options=["importer (manual)", "importer (auto-detect)"],)
    
    if st.button("Confirm"):
        if attach_mode == "importer (manual)":
            st.session_state.reader_dialog = run_csv_importer
        else:
            st.session_state.reader_dialog = uploader_modal
        st.rerun()

def run_selected_importer():
    if "reader_dialog" not in st.session_state:
        st.session_state.reader_dialog = None
    if st.session_state.reader_dialog:
        reader_dialog = st.session_state.reader_dialog
        st.session_state.reader_dialog = None
        reader_dialog()
