# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
import app.db.model as db

@st.dialog("Image Upload", width='large')
def image_upload(session, trial):
    st.title("Image Gallery")
    # Drag-and-drop image upload
    uploaded_files = st.file_uploader(
        "Drop your images here or click to upload",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"])

    # Display images in a scrolling container
    if uploaded_files:
        for uploaded_file in reversed(uploaded_files):
            try:
                st.image(uploaded_file, caption="Image Caption")
                uploaded_file.valid = True
            # If the file is not showing a valid image for any reason, 
            # set an indicator for later uploading
            except:
                st.warning(f"{uploaded_file.name} is not a valid image file.")
                uploaded_file.valid = False

        if st.button("Submit"):
            with st.spinner("Processing..."):
                for uploaded_file in uploaded_files:
                    if uploaded_file.valid:
                        new_image = db.Image(name=uploaded_file.name, data=uploaded_file.read(), trial=trial)
                        session.add(new_image)
                session.commit()
                st.rerun()
