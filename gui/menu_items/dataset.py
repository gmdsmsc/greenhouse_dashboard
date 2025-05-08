# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import app.db.model as db
from app.backend import load_table
from sqlalchemy import select
import streamlit as st
from gui.dialogs.deleter_dialog import check_delete
from gui.custom_components.paginated_data_editor import paginated_selectable_data_editor
from app.database_retriever import DatabaseRetriever
from app.backend import get_dataset_by_name, clone_dataset
from gui.menu import menu_nav


@st.dialog("Copy Dataset")
def copy_dataset():
    datasets_all = load_table(session, db.Dataset)
    dataset_names = {dataset.name: dataset for dataset in datasets_all}
    selected_dataset_name = st.selectbox("Select Dataset to copy from.", options=dataset_names.keys())
    if selected_dataset_name is not None:
        source_dataset = dataset_names[selected_dataset_name]
        if st.button("Confirm"):
            with st.spinner("Copying Dataset..."):
                new_dataset = clone_dataset(source_dataset)
                session.add(new_dataset)
                session.commit()
                st.rerun()


if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session

    st.title("Dataset Selection")

    st.write("Select a Dataset to view its details or delete it." )

    trials = load_table(session, db.Trial)
    trial_names = {trial.name: trial for trial in trials}
    options = [None] + list(trial_names.keys())
    selected_trial_name = st.selectbox("Filter by Trial", options=options)
    if selected_trial_name is not None:
        trial = trial_names[selected_trial_name]
        qry = select(db.Dataset).where(db.Dataset.trial_id == trial.id).order_by(db.Dataset.name)
    else:
        qry = select(db.Dataset).order_by(db.Dataset.name)

    

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
            if st.button("Deleted Selected"):
                selected_rows = grid_response['selected_data']
                if selected_rows is not None:
                    dataset = get_dataset_by_name(session, selected_rows.iloc[0]['name'])
                    res = check_delete(session, dataset)

    if st.sidebar.button("Copy Dataset"):
        copy_dataset()

