# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
import pandas as pd
from gui.custom_components.selectable_data_editor import selectable_data_editor

''' Creates a streamlit table that paginates a database table. '''


def paginated_selectable_data_editor(retriever, *pargs, **kwargs):
    if retriever.get_row_count() == 0:
        st.warning("Nothing here yet. Use the left menu to add new data.")
        return None
    else:
        # Bottom menu
        top_menu = st.columns(3)
        with top_menu[0]:
            sort = st.radio("Sort Data", options=["Yes", "No"], horizontal=1, index=1)
        if sort == "Yes":
            with top_menu[1]:
                sort_field = st.selectbox("Sort By", options=retriever.get_options())
            with top_menu[2]:
                sort_direction = st.radio("Direction", options=["⬆️", "⬇️"], horizontal=True)
            retriever.set_sort_fields(by=sort_field, ascending=sort_direction == "⬆️")

        # Placeholder for table
        placeholder = st.container()

        # Bottom menu
        bottom_menu = st.columns((1, 1, 1), vertical_alignment="bottom")
        with bottom_menu[2]:
            batch_size = st.selectbox("Page Size", options=[25, 50, 100])
        with bottom_menu[0]:
            num_pages = retriever.get_num_pages(batch_size)
            current_page = st.number_input("Page", min_value=1, max_value=num_pages, step=1)
        with bottom_menu[1]:
            st.markdown(f"Page **{current_page}** of **{num_pages}** ")

        # display the current page
        df = retriever.get_page(current_page, batch_size)
        res = selectable_data_editor(placeholder, df, 
                                    *pargs, **kwargs)
        return res

if __name__ == '__main__':
    from app.dataframe_retriever import DataFrameRetriever
    file_path = st.file_uploader("Select CSV file to upload", type=["csv"])
    if file_path:
        df = pd.read_csv(file_path)
        selected_row = selectable_data_editor(DataFrameRetriever(df), hide_index=True)
        print(selected_row)
