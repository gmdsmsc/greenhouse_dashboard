# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import app.db.model as db
from app.backend import unattached_keys, get_group_by_keyval, clone_group
import streamlit as st
from gui.custom_components.selectable_data_editor import selectable_data_editor
from gui.dialogs.deleter_dialog import check_delete
from sqlalchemy.exc import IntegrityError
from gui.menu import menu_nav


@st.dialog("Add new Key")
def new_key(existing_keys):
    options = ['Custom'] + existing_keys
    key = st.selectbox("Select a Key:", options)
    if key == 'Custom':
        key = st.text_input("Custom Key:")

    if st.button("Submit Key"):
        st.session_state.additional_key_vals.append(key)
        st.rerun()

@st.dialog("Copy Sensor Groups")
def clone_metadata(project):
    st.write('Copy sensor groups from another project.')
    session = st.session_state.db_session
    other_projects = session.query(db.Project).filter(db.Project.id != project.id).all()
    other_project_names = {p.name: p for p in other_projects}
    key = st.selectbox("Select a Project:", other_project_names)
    if key:
        if st.button("Confirm"):
            source_project = other_project_names[key]
            source_groups = {(group.key, group.value): group for group in source_project.groups}
            existing_groups = {(group.key, group.value): group for group in project.groups}
            new_group_keyvals = set(source_groups.keys()) - set(existing_groups.keys())
            new_groups = [source_groups[key] for key in new_group_keyvals]
            for group in new_groups:
                new_group = clone_group(group, project)
                new_group.project_id = project.id
                session.add(new_group)
            session.commit()
            st.rerun()



@st.cache_data
def get_key_vals(project_id):
    # Only happens if the project_id has changed
    project = menu_nav.get_current_selection()
    st.session_state.additional_key_vals = []
    df = project.get_group_display_df()
    return df['key'].unique().tolist()

def add_sidebar_menu(project, df, existing_key_vals):
    cols = st.sidebar.columns(2)
    with cols[0]:
        if st.button("Copy Groups"):
            clone_metadata(project)
    with cols[1]:
        if st.button("New Group Key"):
            new_key(unattached_keys(session, df['key'].unique().tolist()))
    
    key_vals = existing_key_vals + st.session_state.additional_key_vals
    key = st.sidebar.selectbox("Select Group Key:", key_vals)

    value = st.sidebar.text_input("Group Name:")
    
    available_sensor_names = project.get_unassigned_sensor_names(key)
    sensor_names = st.sidebar.multiselect("Select sensors:", available_sensor_names)
 
    if st.sidebar.button("Submit Group"):
        if not key:
            st.sidebar.error("Group Key cannot be empty.")
        elif not value:
            st.sidebar.error("Group Value cannot be empty.")
        elif sensor_names:
            existing_group = get_group_by_keyval(session, project, key, value)
            if existing_group:
                group = existing_group
                existing_sensor_names = group.get_sensor_names()
                sensor_names = list(set(existing_sensor_names) | set(sensor_names))
                group.set_sensor_names(session, sensor_names)
            else:
                # Create a new group
                group = db.Group(project_id=project.id, key=key, value=value)
                group.set_sensor_names(session, sensor_names)
                session.add(group)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                st.warning('Duplicate metadata grouping not allowed.')
            else:
                st.rerun()



if hasattr(st.session_state, 'db_session'):

    st.title("Metadata Grouping")

    session = st.session_state.db_session
    project = menu_nav.get_current_selection()
    
    if "sensors" not in st.session_state:
        st.session_state.sensors = project.get_sensors()
    if "additional_key_vals" not in st.session_state:
        st.session_state.additional_key_vals = []

    df = project.get_group_display_df()
    if df.empty:
        st.warning("Nothing here yet. Use the left menu to add new data.")
    else:
        placeholder = st.empty()
        grid_response = selectable_data_editor(
            placeholder,
            df,
            hide_index=True,
            disabled=['key', 'value', 'sensors'],
            )

        if grid_response:
                if st.button("Delete Selected"):
                    selected_rows = grid_response['selected_data']
                    if selected_rows is not None:
                        key = selected_rows.iloc[0]['key']
                        val = selected_rows.iloc[0]['value']
                        group = get_group_by_keyval(session, project, key, val)
                        res = check_delete(session, group)


    existing_key_vals = get_key_vals(project.id)
    add_sidebar_menu(project, df, existing_key_vals)

