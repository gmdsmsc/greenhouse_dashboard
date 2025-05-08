# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 11:52:02 2025
@author: roman
"""
import streamlit as st
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
from gui.menu import menu_nav


def cache_plot(dataset, sensors, force_refresh=False):
    if "cache_exclusion_plot" not in st.session_state:
        st.session_state.cache_exclusion_plot = (None, None, None)
    sensor_names = tuple(sensor.get_display_name() for sensor in sensors)
    if dataset.id != st.session_state.cache_exclusion_plot[0] or \
         st.session_state.cache_exclusion_plot[1] != sensor_names or \
          force_refresh:
        df = dataset.trial.get_dataframe(sensors)
        fig = None
        if not df.empty:
            fig = px.line(df, x='datetime', y='value', color='variable')
            x_min, y_min = df['datetime'].min(), df['value'].min()
            markerPoint = go.Scatter(x=[x_min], y=[y_min], mode='lines+markers', showlegend=False, opacity=0)
            fig.add_trace(markerPoint)
            #Plot creation and Exclusion Selection:
            fig.update_layout(
                dragmode='select',
                selectdirection='h',
                modebar_remove=['lasso2d']
            )
        st.session_state.cache_exclusion_plot = (dataset.id, sensor_names, fig)
    return st.session_state.cache_exclusion_plot[2]

@st.dialog("Select New Exclusions", width='large')
def select_new_time_periods(dataset):

    st.title(f"Trial: {dataset.trial.name}")

    sensors = dataset.sensors
    sensor_display_names = {sensor.get_display_name(): sensor for sensor in sensors}

    with st.form("select_sensors"):
        selected_display_names = st.multiselect("Select sensors:", sensor_display_names.keys())
        selected_sensors = [sensor_display_names[selected_display_name] for 
                            selected_display_name in selected_display_names]
        if st.form_submit_button("Submit"):
            st.session_state.selected_sensors = selected_sensors

    if st.session_state.selected_sensors is not None:
        st.session_state.fig = cache_plot(dataset, st.session_state.selected_sensors)
        
        if st.session_state.fig is None:
            st.warning("No data available for the selected sensors.")
        else:
            with st.expander("Plot Usage Hints:"):
                st.write("1. Choose the Box Select option in the menu and drag horizontally to highlight exclusion time periods.")
                st.write("2. Hold shift to add multiple exclusion time periods.")
                st.write("3. Click the the middle of a highlighted region to drag its location.")
            st.session_state.selectionScreen = st.plotly_chart(
                st.session_state.fig,
                use_container_width=True,
                key="datetime",
                on_select="rerun"
            )

        if st.button('Add'):
            if st.session_state.selectionScreen is not None and st.session_state.selectionScreen["selection"]["box"]:
                #TODO: Try to get the sensors from the visible sensors on the plot instead
                display_names = [sensor.get_display_name() for sensor in st.session_state.selected_sensors]
                for selects in st.session_state.selectionScreen["selection"]["box"]:
                    x0, x1 = pd.to_datetime(selects["x"][0]), pd.to_datetime(selects["x"][1])
                    new_selects = pd.DataFrame({'id': [None],
                                                'start_datetime': [x0], 
                                                'end_datetime': [x1], 
                                                'sensors':[display_names],
                                                'view': True})
                    if st.session_state.stored_selections is None or st.session_state.stored_selections.empty:
                        st.session_state.stored_selections = new_selects
                    else:
                        dataframes = [st.session_state.stored_selections, new_selects]
                        st.session_state.stored_selections = pd.concat(dataframes, ignore_index=True)
                st.write('Success')
        if st.button('Finish'):
            st.rerun()


def cache_dataset_stored_selections(dataset, force_refresh=False):
    if "cached_dataset" not in st.session_state:
        st.session_state.cached_dataset = None
    if dataset.id != st.session_state.cached_dataset or force_refresh:
        df = dataset.get_exclusions_df(view_col=True)
        df['start_datetime'] = pd.to_datetime(df['start_datetime'])
        df['id'] = df['id'].astype('Int64') # Needs to be nullable int
        st.session_state.cached_dataset = dataset.id
        st.session_state.stored_selections = df

if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session
    dataset = menu_nav.get_current_selection()
    min_value = dataset.start_datetime
    max_value = dataset.end_datetime

    #Initializing stored variables
    if 'selected_sensors' not in st.session_state:
        st.session_state.selected_sensors = None

    if 'fig' not in st.session_state:
        st.session_state.fig = None

    if 'stored_selections' not in st.session_state:
        st.session_state.stored_selections = None

    # If the dataset changes, reset the stored selections
    cache_dataset_stored_selections(dataset)

    #User editable dataframe
    st.subheader("Excluded Time Periods")
    st.write("Click 'Add New Exclusion' on the left menu to add a new exclusion.")
    
    if st.sidebar.button("Add New Exclusion"):
        select_new_time_periods(dataset)


    if st.session_state.stored_selections is None or st.session_state.stored_selections.empty:
        st.warning("No exclusions have been selected yet.")
    else:
        df = st.session_state.stored_selections
        cols = st.columns(3)
        with cols[0]:
            if st.button("Select All"):
                df['view'] = True
        with cols[1]:
            if st.button("Select None"):
                df['view'] = False
        st.session_state.stored_selections = df

        stored_selections = st.data_editor(st.session_state.stored_selections, 
                                num_rows="dynamic", 
                                column_config={
                                    "start_datetime": st.column_config.DatetimeColumn(
                                        "start_datetime",
                                            min_value=min_value,
                                            max_value=max_value,
                                            format="yyyy-MM-DD HH:mm:ss",step=60,),
                                        "end_datetime": st.column_config.DatetimeColumn(
                                        "end_datetime",
                                            min_value=min_value,
                                            max_value=max_value,
                                            format="yyyy-MM-DD HH:mm:ss",step=60,),
                                        "sensors": st.column_config.ListColumn(
                                            "sensors",
                                            width="medium",
                                        ),
                                    },
                                    )
        
        st.write("WARNING: New exclusions shown here may not be saved. Click the Save Changes button and"\
                " ensure an id number has been assigned to each exclusion." )
        placeholder = st.empty()

        trial_sensors = {sensor.get_display_name(): sensor for sensor in dataset.sensors}
        df = stored_selections[stored_selections['view'] == True]
        sensor_name_list = df['sensors'].explode().dropna().unique()
        selected_sensors = [trial_sensors[sensor_name] for sensor_name in sensor_name_list]
        start_stops = list(zip(df['start_datetime'], df['end_datetime']))

        df = dataset.trial.get_dataframe(selected_sensors)
        if df is not None:
            fig = px.line(df, x='datetime', y='value', color='variable')
            y_min, y_max = df['value'].min(), df['value'].max()
            for start, stop in start_stops:     
                fig.add_shape(
                type="rect",
                x0=start, x1=stop, y0=y_min, y1=y_max,
                fillcolor="LightSkyBlue",
                opacity=0.5,
                layer="below",
                line_width=0,
                )
            st.plotly_chart(fig)

        if placeholder.button('Save Changes'):
            dataset.set_exclusions_df(stored_selections)

            try:
                session.commit()
            except Exception as e:
                print(e)
                session.rollback()
                st.warning("At least one exclusion region was invalid and changes were not saved. Please check and try again.")
            else:
                cache_dataset_stored_selections(dataset, force_refresh=True)
                st.rerun()
