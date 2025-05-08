# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import app.db.model as db
import streamlit as st
from gui.dialogs.deleter_dialog import check_delete
from gui.custom_components.paginated_data_editor import paginated_selectable_data_editor
from app.database_retriever import FullTableDatabaseRetriever
from app.backend import get_trial_by_name
from gui.menu import menu_nav


if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session

    st.title("Trial Selection")

    st.write("Select a Trial below to view its details or delete it." )
    st.write("Click 'New Trial' on the left menu to create a new Trial.")

    # Configure wide column widths for the name column
    column_config={"name": st.column_config.Column(),}
    
    # Make the data editor (table)
    grid_response = paginated_selectable_data_editor(
        FullTableDatabaseRetriever(session, db.Trial, options=['name', 'start_datetime', 'end_datetime', 'notes']), 
        column_config=column_config,
        hide_index=True)

    if grid_response:
        # Make the buttons
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("View Selected"):
                selected_rows = grid_response['selected_data']
                if selected_rows is not None:
                    trial = get_trial_by_name(session, selected_rows.iloc[0]['name'])
                    menu_nav.navigate_to(trial)
                    st.rerun()
        with col2:
            if st.button("Delete Selected"):
                selected_rows = grid_response['selected_data']
                if selected_rows is not None:
                    trial = get_trial_by_name(session, selected_rows.iloc[0]['name'])
                    check_delete(session, trial)

    st.write("**WARNING:**" \
    " Deleting a Trial will remove all associated data and files. " \
    "Please proceed with caution.")