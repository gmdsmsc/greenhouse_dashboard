# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
from sqlalchemy.exc import IntegrityError
from gui.menu import menu_nav

if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session

    st.title("Dataset Overview")

    dataset = menu_nav.get_current_selection()

    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    with col1:
        dataset_name = st.text_input("Dataset Name:", value=dataset.name)
    with col2:
        if st.button("Rename"):
            dataset.name = dataset_name
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                st.error("❌ A Dataset with this name already exists.")
            else:
                st.success("✅ Saved Successfully!")
                st.rerun()

    # Dataset start and end date
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Start DateTime:", value=dataset.start_datetime, disabled=True)
    with col2:
        st.text_input("End DateTime:", value=dataset.end_datetime, disabled=True)

    # Dataset notes
    notes = st.text_area(
        label="Enter Detailed Dataset Notes",
        value=dataset.notes,
        height=200
    )
    if st.button("Save Notes"):
        if dataset.notes != notes:
            dataset.notes = notes
            session.commit()
            st.write("✅ Saved Successfully!")


    if dataset.row_count(dataset.sensors) == 0:
        st.warning("❌ There is no data in this dataset. Check the data range of the source " \
        "data and any exclusions that may have been applied.")
