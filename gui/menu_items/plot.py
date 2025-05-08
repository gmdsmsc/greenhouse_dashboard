# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import app.db.model as db
import streamlit as st
from gui.dialogs.new_plot_dialog import new_plot
from gui.menu import menu_nav


@st.cache_resource
def load_plot():
    import plotly.graph_objects as go
    return go.Figure()

def new_notepad(session, project):
    text = db.TextNote(text="New Note", project_id=project.id)  
    session.add(text)
    session.commit()
    st.rerun()

@st.dialog("Delete Item")
def delete_item(session, project):
    items = {item.get_title(i + 1): item for i, item in enumerate(project.contents)}
    item_name = st.selectbox("Select Item to Delete", items.keys())
    item = items[item_name]
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button('Confirm'):
            item.project.contents.remove(item)
            session.commit()
            st.rerun()
    with col2:
        if st.button('Cancel'):
            st.rerun()


@st.dialog("Output CSV")
def output_csv(session, project):
    items = {item.get_title(i + 1): item for i, item in enumerate(project.contents) if item.content_table == 'visualisation'}
    item_name = st.selectbox("Select Item to Delete", items.keys())
    if item_name is None:
        st.warning("Please add a dataset to the project to continue.")
    else:
        item = items[item_name]
        df = item.get_df_for_csv()
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Data", data=csv, file_name=f"output.csv", mime="text/csv")

def get_small_columns(df):
    columns = df.columns
    for column in columns:
        u_count = df[column].nunique()
        if u_count < 50:
            yield column

def get_float_or_date_columns(df):
    columns = df.columns
    for column in columns:
        if (df[column].dtype in ['float32', 'float64', 'datetime64[ns]']):
            yield column


def get_float_columns(df):
    columns = df.columns
    for column in columns:
        if (df[column].dtype in ['float32', 'float64']):
            yield column

def cache_sqla_renderable(obj, force_refresh=False):
    if "cached_ids" not in st.session_state:
        st.session_state.cached_ids = {}
    key = (obj.__class__.__name__, obj.id)
    if key not in st.session_state.cached_ids or force_refresh:
        st.session_state.cached_ids[key] = obj.render()
    return st.session_state.cached_ids[key]


if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session
    project = menu_nav.get_current_selection()

    for i, item in enumerate(project.contents):
        title = item.get_title(i + 1)

        rendered_item = cache_sqla_renderable(item)
        if type(rendered_item) == str:
            updated_text = st.text_area(title, rendered_item, key=f"text_{i + 1}")
            if item.text != updated_text:
                item.text = updated_text
                rendered_item = cache_sqla_renderable(item, force_refresh=True)
                session.commit()
        else:
            rendered_item.update_layout(title=title)
            st.plotly_chart(rendered_item, key=f"plot_{i + 1}")


    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        # Create a button to open the modal
        if st.button("New Plot"):
            new_plot(session, project)      
    with col2:
        if st.button("New Notepad"):
            new_notepad(session, project)
    with col3:
        if st.button("Delete Item"):
            delete_item(session, project)
    
    if st.sidebar.button("Output CSV"):
        output_csv(session, project)


