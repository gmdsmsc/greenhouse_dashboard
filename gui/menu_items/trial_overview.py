# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 11:52:02 2025
@author: Phoebe.Sinclair
"""

import re
import streamlit as st
from gui.file_uploader import attach_files_to_trial
from gui.dialogs.deleter_dialog import check_delete
from sqlalchemy import select
import app.db.model as db
from sqlalchemy.exc import IntegrityError
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from gui.menu import menu_nav


@st.cache_data
def add_selection_column(df):
    # Check if the selection column already exists
    if 'Download' not in df.columns:
        df['Download'] = "Download"
    return df

@st.dialog("Upload FIles")
def add_files():
    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)
    if st.button("Submit"):
        if uploaded_files:
            attach_files_to_trial(trial, uploaded_files)
            session.commit()
            st.rerun()

@st.cache_resource
def get_coordinates(postcode):
    # Geocoding function
    geolocator = Nominatim(user_agent="streamlit-geocoder")
    try:
        location = geolocator.geocode(postcode)
        if location:
            return location.latitude, location.longitude
    except (GeocoderTimedOut, GeocoderUnavailable):
        pass
    return None, None

def get_metadata(session, type):
    qry = select(db.Metadata.value).where(db.Metadata.key == type).order_by(db.Metadata.value).distinct()
    return session.execute(qry).scalars().all()

if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session

    st.title("Trial Overview")

    if 'uploaded_files_overview' not in st.session_state:
        st.session_state.uploaded_files_overview = None

    trial = menu_nav.get_current_selection()


    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    with col1:
        trial_name = st.text_input("Trial Name:", value=trial.name)
    with col2:
        if st.button("Rename"):
            trial.name = trial_name
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                st.error("❌ A Project with this name already exists.")
            else:
                st.success("✅ Saved Successfully!")
                st.rerun()

    # Trial start and end date
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Start DateTime:", value=trial.start_datetime, disabled=True)
    with col2:
        st.text_input("End DateTime:", value=trial.end_datetime, disabled=True)


    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    with col1:
        postcode = st.text_input("Postcode", value=trial.postcode)
    with col2:
        if st.button("Change"):
            trial.postcode = postcode
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                st.error("❌ Failed to update postcode.")
            else:
                st.success("✅ Saved Successfully!")
                st.rerun()

    st.session_state.lat, st.session_state.lon = get_coordinates(postcode)

    # Check the postcode validity with regex
    if postcode is not None and postcode != '':
        pattern = r"^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$"
        validity = bool(re.match(pattern, postcode.upper()))
        if not validity or st.session_state.lat is None or st.session_state.lon is None:
            st.error("❌ Either the postcode is not valid or the Geocoder service is down. "
                        "Weather data retrieval will not be possible."
                        " Please check and try again.")
        else:
            st.write("✅ Postcode detected at Latitude {lat}, Longitude {long}.".format(lat=st.session_state.lat, long=st.session_state.lon))
            st.map({"lat": [st.session_state.lat], "lon": [st.session_state.lon]})

    # Trial notes
    notes = st.text_area(
        label="Enter Detailed Trial Notes",
        value=trial.notes,
        height=200
    )
    if st.button("Save Notes"):
        if trial.notes != notes:
            trial.notes = notes
            session.commit()
            st.write("✅ Saved Successfully!")

    st.title("Attached Files")
    col1, col2, col3 = st.columns([3, 1, 1], vertical_alignment="bottom")
    with col1:
        selected = st.selectbox("Files", options=[f"{i}: {file.name}" for i, file in enumerate(trial.files)])
        if selected:
            index = int(selected.split(":")[0])
            selected_file = trial.files[index]
        else:
            selected_file = None
    with col2:
        if selected_file:
            st.download_button("📥 Download", 
                               data=selected_file.data, 
                               file_name=selected_file.name, 
                               mime=selected_file.mime)
    with col3:
        if selected_file:
            if st.button("Delete"):
                check_delete(session, selected_file)

    if st.button("Add Files"):
        add_files()   


    st.title("Sensors")

    df = trial.get_stored_readings_map_df()

    readings_map = st.data_editor(df.reset_index(drop=True), 
                        disabled=["variable"],
                        hide_index=True,)

    readings_map = readings_map.astype("string")

    if st.button("Save"):

        non_nul_displaynames = readings_map['display_name'][readings_map['display_name'] != '']
        duplicate_names = non_nul_displaynames[non_nul_displaynames.duplicated()].unique()
        if len(duplicate_names) > 0:
            duplicate_names_str = ','.join(duplicate_names.tolist())
            st.warning(f'Duplicate sensor display names found: [{duplicate_names_str}]')
        else:
            trial.readings_map = readings_map
            trial.apply_readings_map()
            session.commit()
            st.write("✅ Saved Successfully!")
