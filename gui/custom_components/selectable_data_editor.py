# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st

''' Creates a streamlit data_editor with selectable rows. '''

@st.cache_resource
def add_selection_column(df):
    # Check if the selection column already exists
    if 'Select' not in df.columns:
        df.insert(0, 'Select', False)
    return df

def selectable_data_editor(placeholder, df, *pargs, column_config=None, **kwargs):
    # Initialize selection column if not already in session state

    if "df_with_selection" not in st.session_state:
        st.session_state.df_with_selection = add_selection_column(df)
    elif not st.session_state.df_with_selection.drop(columns=["Select"]).equals(df):
        st.session_state.df_with_selection = add_selection_column(df)

    # Function to handle selection changes
    def on_change():
        # Get the edited data from session state
        edited_rows = st.session_state.editor_key.get("edited_rows", {})
        # Create a new dataframe with all selections set to False
        new_df = st.session_state.df_with_selection.copy()
        new_df["Select"] = False
        # Find the last row that was selected and set only that one to True
        last_selected_row = None
        for row_idx, edits in edited_rows.items():
            if "Select" in edits and edits["Select"] == True:
                last_selected_row = int(row_idx)
        # If a row was selected, update the dataframe
        if last_selected_row is not None:
            new_df.loc[last_selected_row, "Select"] = True
        # Update session state
        st.session_state.df_with_selection = new_df

    # Make selection column checkbox and disable all columns except the selection column   
    column_config1 = {col: {"disabled": True} for col in df.columns if col != "Column 1"}
    column_config2 = {"Select": st.column_config.CheckboxColumn("Select"),}
    column_config_combined = {**column_config1, **column_config2}

    if column_config is not None:
        column_config_combined = {**column_config, **column_config}

    # Display the data editor with the selection column
    editor = placeholder.data_editor(
        st.session_state.df_with_selection, *pargs,
        key="editor_key",
        on_change=on_change,
        column_config=column_config_combined,
        use_container_width=True,
        **kwargs
    )

    if editor["Select"].sum() == 1:
        grid_response = {}
        df = st.session_state.df_with_selection
        grid_response['selected_data'] = df.loc[df["Select"]].drop(columns=["Select"])
        return grid_response
    return False



