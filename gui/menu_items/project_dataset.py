# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import app.db.model as db
from app.backend import load_table
from sqlalchemy import select
import streamlit as st
from gui.custom_components.paginated_data_editor import paginated_selectable_data_editor
from app.database_retriever import DatabaseRetriever
from app.backend import get_dataset_by_name, clone_dataset, remove_dataset_from_project
from gui.menu import menu_nav

@st.dialog("Copy Dataset")
def copy_dataset(project):
    datasets_all = project.datasets
    dataset_names = {dataset.name: dataset for dataset in datasets_all}
    selected_dataset_name = st.selectbox("Select Dataset to copy from.", options=dataset_names.keys())
    if selected_dataset_name is not None:
        source_dataset = dataset_names[selected_dataset_name]
        if st.button("Confirm"):
            with st.spinner("Copying Dataset..."):
                new_dataset = clone_dataset(source_dataset)
                project.datasets.append(new_dataset)
                session.commit()
                st.rerun()

@st.dialog("Add Dataset")
def add_dataset(project):
    datasets_all = load_table(session, db.Dataset)
    if len(datasets_all) == 0:
        st.error("No datasets available. Please create a trial first.")
    else:
        new_datasets = [dataset for dataset in datasets_all if dataset not in project.datasets]
        datasets = {dataset.name: dataset for dataset in new_datasets}
        dataset_name = st.selectbox("Choose a dataset:", datasets.keys())
        if dataset_name is not None:
            dataset = datasets[dataset_name]
            if st.button("Confirm"):
                with st.spinner("Adding Dataset..."):
                    project.datasets.append(dataset)
                    session.commit()
                    st.rerun()


if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session
    project = menu_nav.get_current_selection()

    st.title("Project Dataset Selection")

    st.write("Select a Dataset to view its details or delete it." )

    qry = select(db.Dataset).join(db.Dataset.projects).filter(db.Project.id.in_([project.id])).order_by(db.Dataset.name)

    grid_response = paginated_selectable_data_editor(
        DatabaseRetriever(session, qry, options=['name', 'start_datetime', 'end_datetime', 'trial_name', 'notes']), 
        hide_index=True)


    if grid_response:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("View Selected"):
                selected_rows = grid_response['selected_data']
                if selected_rows is not None:
                    dataset = get_dataset_by_name(session, selected_rows.iloc[0]['name'])
                    menu_nav.navigate_to(dataset)
                    st.rerun()
        with col2:
            if st.button("Remove Selected"):
                selected_rows = grid_response['selected_data']
                if selected_rows is not None:
                    dataset = get_dataset_by_name(session, selected_rows.iloc[0]['name'])
                    res = remove_dataset_from_project(project, dataset)
                    st.rerun()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Copy Dataset"):
            copy_dataset(project)
    with col2:
        if st.button("Add Dataset"):
            add_dataset(project)
