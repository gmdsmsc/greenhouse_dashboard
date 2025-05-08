# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
import app.db.model as db

def run_file_attach():

    # Streamlit file uploader allows multiple files to be uploaded
    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)
    st.session_state.uploaded_files = uploaded_files

    if uploaded_files:
        st.write(f"✅ {len(uploaded_files)} file(s) ready for upload:")
        
        # Iterate over the uploaded files
        for uploaded_file in uploaded_files:

            # Display file metadata
            st.write({
                "filename": uploaded_file.name,
                "filetype": uploaded_file.type,
                "filesize": uploaded_file.size
            })

def attach_files_to_trial(trial, uploaded_files):
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file = db.File(name=uploaded_file.name, 
                            data=uploaded_file.getvalue(), 
                            mime=uploaded_file.type)
            trial.files.append(file)
