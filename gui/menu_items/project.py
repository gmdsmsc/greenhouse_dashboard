# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import app.db.model as db
import streamlit as st
from gui.custom_components.paginated_data_editor import paginated_selectable_data_editor
from gui.dialogs.deleter_dialog import check_delete
from app.database_retriever import FullTableDatabaseRetriever
from app.backend import get_project_by_name
from gui.menu import menu_nav


if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session

    st.title("Project Selection")

    st.write("Select a Project below to view its details or delete it." )

    st.write("Click 'New Project' on the main menu to create a new Project.")
    # Configure the table
    column_config={"name": st.column_config.Column(width="large"),}
    
    grid_response = paginated_selectable_data_editor(
        FullTableDatabaseRetriever(session, db.Project, options=['name', 'notes']), 
        column_config=column_config,
        hide_index=True)

    if grid_response:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("View Selected"):
                selected_rows = grid_response['selected_data']
                if selected_rows is not None:
                    project = get_project_by_name(session, selected_rows.iloc[0]['name'])
                    menu_nav.navigate_to(project)
                    st.rerun()
        with col2:
            if st.button("Deleted Selected"):
                selected_rows = grid_response['selected_data']
                if selected_rows is not None:
                    project = get_project_by_name(session, selected_rows.iloc[0]['name'])
                    check_delete(session, project)