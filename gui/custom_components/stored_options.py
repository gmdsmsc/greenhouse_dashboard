# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st

''' Provides a set of functions to create multiselect and selectbox widgets
    that remember previously selected values even if the available options change.'''

# Define a callback function to update session state
def change_cb():
    st.session_state.multiselect_values = st.session_state.multiselect_widget

def stored_multiselect(label, current_options, reset=False, **kwargs):
    ''' Makes a multiselect that remembers previously selected values
        even if the available options change. '''

    # Initialize session state for multiselect if it doesn't exist
    if "multiselect_values" not in st.session_state:
        st.session_state.multiselect_values = []
    elif reset:
        st.session_state.multiselect_values = []

    # Create a combined list of options (previously selected + current options)
    combined_options = list(set(st.session_state.multiselect_values + current_options))

    combined_cb = change_cb
    if 'on_change' in kwargs:
        def combined_cb():
            change_cb()
            kwargs['on_change']()
        kwargs.pop('on_change')

    # Create the multiselect with the combined options and previously selected values
    selected_values = st.multiselect(
        label,
        combined_options,
        default=st.session_state.multiselect_values,
        key="multiselect_widget",
        on_change=combined_cb, **kwargs)

    return selected_values

def stored_selectbox(label, current_options, reset=False, unique_key=None, **kwargs):
    ''' Makes a selectbox that remembers previously selected values
        even if the available options change. '''

    if unique_key is None:
        unique_key = 'selected_option'

    # Initialize session state
    if unique_key not in st.session_state:
        setattr(st.session_state, unique_key, None)
    if reset and getattr(st.session_state, unique_key) not in current_options:
            setattr(st.session_state, unique_key, None)

    # Merge previous selection with current options if needed
    all_options = list(set([getattr(st.session_state, unique_key)] + 
                    current_options if getattr(st.session_state, unique_key)
                    else current_options))

    # Second selectbox
    selected_option = st.selectbox(
        label,
        options=all_options,
        index=all_options.index(getattr(st.session_state, unique_key)) if getattr(st.session_state, unique_key) in all_options else 0)

    return selected_option


if __name__ == '__main__':

    # Define options for each key
    options_map = {
        "key1": ["opt1", "opt2", "opt3", "opt4"],
        "key2": ["opt4", "opt5", "opt6"]
    }
    # Create the selectbox for keys
    selected_key = st.selectbox("Select a key", ["key1", "key2"])
    # Get current options based on selected key
    current_options = options_map[selected_key]

    if st.button("Reset"):
        stored_selectbox("Select", current_options, reset=True)
    else:
        stored_selectbox("Select", current_options)
