# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import plotly.express as px
import streamlit as st
from gui.menu import menu_nav

if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session

    trial = menu_nav.get_current_selection()

    st.title(f"Trial: {trial.name}")

    st.write("Time data for the trial is shown below. " \
             "Please select the sensors to plot data.")


    sensors = trial.sensors
    sensors_names = {sensor.get_display_name(): sensor for sensor in sensors}
    with st.form("select_sensors"):
        selected_sensor_names = st.multiselect("Select sensors:", sensors_names.keys())
        selected_sensors = [sensors_names[name] for name in selected_sensor_names]

        submit_button = st.form_submit_button("Submit")

    if submit_button:

        with st.expander("Plot Usage Hints:"):
            st.write("1. Double click to reset zoom.")
            st.write("2. Drag in a straight line to zoom in time.")
            st.write("3. Drag diagonally to zoom in on a square.")
            st.write("4. Click on the legend to hide/show a sensor.")

        df = trial.get_dataframe(selected_sensors)
        fig = px.line(df, x='datetime', y='value', color='variable')
        st.plotly_chart(fig)
