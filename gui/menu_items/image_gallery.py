# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
from gui.image_upload import image_upload
from gui.menu import menu_nav


@st.dialog("Image Delete")
def delete_image(session, images):
    indexed_filenames = [f"{index + 1}: {image.name}" for index, image in enumerate(images)]
    selected = st.selectbox("Select an image to delete", indexed_filenames)
    index, _ = selected.split(": ", 1)
    image = images[int(index) - 1]

    if st.button("Confirm"):
        session.delete(image)
        session.commit()
        st.rerun()

if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session
    trial = menu_nav.get_current_selection()

    st.write("Press the Upload Images button on the sidebar to add new images.")


    images = trial.images
    if images:
        for image in images:
            st.image(image.image(), caption=image.name)             
        if st.sidebar.button("Delete Image"):
            delete_image(session, images)
    else:
        st.warning("The trial has no images yet.")
    
    if st.sidebar.button("Upload Images"):
        image_upload(session, trial)