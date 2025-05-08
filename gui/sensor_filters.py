# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st

# Function to add a new filter
def add_filter(options, key_to_values):
    st.session_state.group_filters.append({"filter_type": "group_filter",
                                     "options": options, 
                                     "selected_key": options[0], 
                                     "selected_value": key_to_values[options[0]][0]})

# Function to delete a specific filter
def delete_filter(index):
    temp_filters = st.session_state.group_filters.copy()
    temp_filters.pop(index)
    st.session_state.group_filters = temp_filters

def make_filters(options, key_to_values):
    # Initialize session state
    if "group_filters" not in st.session_state:
        st.session_state.group_filters = []
    if 'to_be_deleted' not in st.session_state:
        st.session_state.to_be_deleted = None

    cols = st.columns([2, 2, 1])

    with st.expander("Sensor Filters"):
        with cols[0]:
            if st.button("Add Sensor Filter"):
                if options:
                    add_filter(options, key_to_values)
                else:
                    st.warning("No options available to add a filter.")

        with cols[1]:
            if st.button("Remove Last Filter"):
                num_filters = len(st.session_state.group_filters)
                if num_filters > 0:
                    last_filter_index = num_filters - 1
                    delete_filter(last_filter_index)

    # Display the filters
    for i, filter in enumerate(st.session_state.group_filters):
        cols = st.columns([3, 3], vertical_alignment="bottom")

        with cols[0]:
            # Selectbox for selecting a key
            filter["selected_key"] = st.selectbox(
                f"Filter Key", filter["options"], 
                index=filter["options"].index(filter["selected_key"]),
                key=f"key_{i}")

        with cols[1]:
            # Dropdown for selecting a value based on the selected key
            filter["selected_value"] = st.selectbox(
                f"Filter Value",
                key_to_values[filter["selected_key"]],
                index=0,
                key=f"value_{i}")


if __name__ == '__main__':
    
    options = ["key1", "key2", "key3"]
    # Define the mapping between keys and values
    key_to_values = {
        "key1": ["value1", "value2", "value3"],
        "key2": ["value4", "value5", "value6"],
        "key3": ["value7", "value8", "value9"]
    }
    make_filters(options, key_to_values)