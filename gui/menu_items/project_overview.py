# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
from sqlalchemy.exc import IntegrityError
from gui.menu import menu_nav


if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session

    st.title("Project Overview")

    project = menu_nav.get_current_selection()

    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    with col1:
        dataset_name = st.text_input("Project Name:", value=project.name)
    with col2:
        if st.button("Rename"):
            project.name = dataset_name
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                st.error("❌ A Project with this name already exists.")
            else:
                st.success("✅ Saved Successfully!")
                st.rerun()

    # Project notes
    notes = st.text_area(
        label="Enter Detailed Project Notes",
        value=project.notes,
        height=200
    )
    if st.button("Save Notes"):
        if project.notes != notes:
            project.notes = notes
            session.commit()
            st.write("✅ Saved Successfully!")
