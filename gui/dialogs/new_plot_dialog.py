# -*- coding: utf-8 -*-
"""
@author: Graham.Macleod
"""

import streamlit as st
import app.db.model as db
from gui.sensor_filters import make_filters
from gui.custom_components.stored_options import stored_multiselect, stored_selectbox

''' Provides a dialog for creating new plots. '''

def make_xy(dataset, project):
    x_axis, y_axis = select_sensors_xy(dataset, project)
    if x_axis and y_axis:
        sensor_names = [x_axis, y_axis]
        sensors = {sensor.get_display_name(): sensor for sensor in dataset.sensors}
        selected_sensors = [sensors[sensor_name] for sensor_name in sensor_names]       
        return {'x_axis': x_axis, 
                'y_axis': y_axis, 
                'plot_type': 'Scatter', 
                'plot_format': 'xy',
                'sensors': selected_sensors}
    return {}

def make_time(dataset, project):
    selected_sensors = select_sensors(dataset, project)
    return {'x_axis': 'datetime', 
            'y_axis': 'value', 
            'color': 'variable', 
            'plot_type': 'Line',
            'sensors': selected_sensors}

def make_groupy(dataset, project):
    x_axis, group_key = select_sensors_groupy(dataset, project)
    groups = [group for group in project.groups if group.key == group_key]
    selected_sensor_lists = [group.sensors for group in groups]
    selected_sensors = list(set([item for sublist in selected_sensor_lists for item in sublist]))
    selected_sensors += [sensor for sensor in dataset.sensors if sensor.get_display_name() == x_axis]
    return {'x_axis': x_axis, 
            'y_axis': group_key, 
            'color': 'value',
            'plot_type': 'Scatter', 
            'plot_format': 'groupy',
            'sensors': selected_sensors}

def make_occurrence(dataset, project):
    cols = st.columns(2)
    with cols[0]:
        lower_limit = st.number_input('Lower Limit',
                        min_value=1.0, 
                        max_value=9999.0, 
                        value=18.0, 
                        format="%.2f")
    with cols[1]:
        upper_limit = st.number_input('Upper Limit',
                        min_value=1.0, 
                        max_value=9999.0, 
                        value=24.0, 
                        format="%.2f")
    if lower_limit and upper_limit:
        return {'lower_limit': lower_limit, 
                'upper_limit': upper_limit,}
    return False


def make_detrend(dataset, project):
    cols = st.columns(2)
    with cols[0]:
        qty = st.number_input('Window',
                        min_value=1, 
                        max_value=1000, 
                        value=10, 
                        step=1)
    with cols[1]:
        units = {'seconds': 's', 'minutes': 'min', 'hours': 'h'}
        selected_units = st.selectbox('Unit of Time', 
                     units.keys())
        units = units[selected_units]
    if qty and units:
        return {'quantity': qty, 'detrend_units': units}
    return False

def make_dli(dataset, project):
    st.write("WARNING: Assumes units of µMol/m2/S")
    return False

def make_transmissibility(dataset, project):
    group_filters = st.session_state.group_filters
    sensor_filters = st.session_state.sensor_filters
    sensors_all = dataset.sensors
    sensors_all = {sensor.get_display_name(): sensor for sensor in sensors_all}
    sensors = dataset.get_filtered_sensors(project, group_filters, sensor_filters)
    sensors = {sensor.get_display_name(): sensor for sensor in sensors}
    sensor_name = st.selectbox("Select Reference", sensors)       
    if sensor_name:
        sensor = sensors_all[sensor_name]
        return {'reference_sensor': sensor,
                'filters': [{'filter_type': 'reference_filter', 
                'selected_key': 'name', 
                'selected_value': sensor_name}]}
    return False


def sensors_change():
    ''' if the available sensors change, resets the selected sensors '''
    try:
        st.session_state.multiselect_values = []
    except AttributeError:
        st.session_state.x_axis_selection = None
        st.session_state.y_axis_selection = None

def select_sensors(dataset, project):
    options, key_to_values = project.get_filter_options()
    make_filters(options, key_to_values)
    group_filters = st.session_state.group_filters
    sensor_filters = st.session_state.sensor_filters
    reference_filters = st.session_state.reference_filters
    sensors_all = dataset.sensors
    sensors_names_all = {sensor.get_display_name(): sensor for sensor in sensors_all}
    filtered_sensors = dataset.get_filtered_sensors(project, group_filters, sensor_filters, reference_filters)
    filtered_sensor_names = [sensor.get_display_name() for sensor in filtered_sensors]
    selected_sensor_names = stored_multiselect('Select Sensors', filtered_sensor_names)
    selected_sensors = [sensors_names_all.get(sensor_name) for sensor_name in selected_sensor_names]
    return [sensor for sensor in selected_sensors if sensor is not None]

def select_sensors_xy(dataset, project):
    options, key_to_values = project.get_filter_options()
    make_filters(options, key_to_values)
    group_filters = st.session_state.group_filters
    sensor_filters = st.session_state.sensor_filters
    reference_filters = st.session_state.reference_filters
    sensors_all = dataset.sensors
    sensors_all = {sensor.get_display_name(): sensor for sensor in sensors_all}
    filtered_sensors = dataset.get_filtered_sensors(project, group_filters, sensor_filters, reference_filters)
    x_axis_sensors = [sensor.get_display_name() for sensor in filtered_sensors]
    x_axis = stored_selectbox('Select X-Axis', x_axis_sensors, unique_key='x_axis_selection')
    y_axis_sensors = [sensor.get_display_name() for sensor in filtered_sensors if sensor.get_display_name() != x_axis]
    y_axis = stored_selectbox('Select Y-Axis', y_axis_sensors, unique_key='y_axis_selection')
    return x_axis, y_axis

def select_sensors_groupy(dataset, project):
    options, key_to_values = project.get_filter_options()
    make_filters(options, key_to_values)
    group_filters = st.session_state.group_filters
    sensor_filters = st.session_state.sensor_filters
    reference_filters = st.session_state.reference_filters
    sensors_all = dataset.sensors
    sensors_all = {sensor.get_display_name(): sensor for sensor in sensors_all}
    filtered_sensors = dataset.get_filtered_sensors(project, group_filters, sensor_filters, reference_filters)
    x_axis_sensors = [sensor.get_display_name() for sensor in filtered_sensors]
    x_axis = stored_selectbox('Select X-Axis', x_axis_sensors, unique_key='x_axis_selection')
    unique_keys = list(set([group.key for group in project.groups]))
    key = st.selectbox('Select Y-Axis Key', unique_keys)   
    return x_axis, key

@st.dialog("Add new Plot")
def new_plot(session, project):

    datasets = {dataset.name:dataset for dataset in project.datasets}
    dataset_name = st.selectbox("Select a Dataset:", datasets.keys(), on_change=sensors_change)
    if not dataset_name:
        st.warning("Please add a dataset to the project to continue.")
    else:
        dataset = datasets[dataset_name]

        transformations = {'None': '',
                        'DLI (PAR type only)': 'dli', 
                        'Transmissibility (PAR type only)': 'tx',
                        'Detrend (remove mean)': 'detrend',
                        'Occurrence Count': 'occurrence_count',
                        'Running Mean': 'running_mean',}
        # Select a transformation of the data
        selected_transformation_name = st.selectbox('Transformation', transformations.keys(),
                                    on_change=sensors_change)# , 'Max', 'Mean', 'Occurrence Count']) TODO: Restore
        transformation = transformations.get(selected_transformation_name, '')

        if 'sensor_filters' not in st.session_state:
            st.session_state['sensor_filters'] = []    
        # Add PAR filter as a sensor filter if applicable
        if transformation in ['dli', 'tx']:
            st.session_state.sensor_filters = [{'filter_type': 'group_filter',
                                                'selected_key': 'type', 
                                                'selected_value': 'PAR'}]
        else:
            st.session_state.sensor_filters = []

        if 'reference_filters' not in st.session_state:
            st.session_state['reference_filters'] = []

        transformation_options = {
        'dli': make_dli,
        'tx': make_transmissibility, 
        'detrend': make_detrend,
        'occurrence_count': make_occurrence,
        'running_mean': make_detrend}
        func = transformation_options.get(transformation)
        res = None
        if func is not None:
            res = func(dataset, project)
            if res and 'filters' in res:
                st.session_state.reference_filters = res['filters']
                res.pop('filters')
            else:
                st.session_state.reference_filters = []

        # Select plot type
        xaxis_type = st.selectbox('Select Plot Type', ['Time', 'XY', 'GroupY'])

        opts = {'XY': make_xy, 'GroupY': make_groupy, 'Time': make_time}
        kwargs = opts[xaxis_type](dataset, project)
        if res is not None and res is not False:
            kwargs = {**kwargs, **res}
        if transformation:
            kwargs['preprocess'] = transformation

        if st.button("Make Plot"):
            vis = db.Visualisation(project_id=project.id, dataset_id=dataset.id, **kwargs)
            session.add(vis)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                st.warning(e.orig)
            else:
                st.rerun()