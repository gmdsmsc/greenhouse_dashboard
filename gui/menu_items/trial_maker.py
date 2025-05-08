# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 11:52:02 2025
@author: Phoebe.Sinclair
"""

import re
import streamlit as st
import app.db.model as db
from datetime import datetime
from gui.dialogs.file_importer_selection import importer_type_selection, run_selected_importer
import pandas as pd
from app.fetch_weather import fetch_weather_data  # Import the new fetch_weather.py module
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from sqlalchemy import select
from gui.file_uploader import run_file_attach, attach_files_to_trial
from gui.menu import menu_nav


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

def append_df(df_existing, df): # Function to append imported readings to existing readings
    if not df.empty:
        df = df.set_index('datetime').tz_convert('UTC').reset_index()
        df = df.rename(columns={'value': 'value_'}) # Rename if any columns are named value to avoid conflicts
        df_melted = df.melt(id_vars='datetime', var_name='variable', value_name='value').dropna(subset=['value'])
        if not df_melted.empty:
            if st.session_state.imported_readings is None:
                df_existing = df_melted
            else:
                df_existing = pd.concat([df_existing, df_melted], ignore_index=True)
    if df_existing is not None:
        return df_existing.drop_duplicates(subset=['datetime', 'variable'], keep='first')


@st.dialog("Open Meteo Weather Data", width="large")
def weather_dialog(lat, lon, start_date, end_date):
    if lat is None or lon is None:
        st.error("❌ Either the postcode is not valid or the Geocoder service is down. "
                    "Weather data retrieval will not be possible.")
    else:
        with st.spinner("Fetching weather data..."):
            try:
                weather_data = fetch_weather_data(lat, lon, start_date, end_date)
            except:
                weather_data = None
        if weather_data is not None:
            st.write("On pressing the **Confirm** button below, the weather data previewed" \
            " here will be added to the readings store, ready for import.")
            st.write('Preview:')
            st.dataframe(weather_data.head(20), hide_index=True)
            st.success("✅ Weather data fetched successfully!")

            if st.button("Confirm"):
                st.session_state.weather_data = weather_data
                st.rerun()
        else:
            st.error("❌ Failed to fetch weather data for an unexpected reason.")


# This should always find a database session but 
# will just display a blank screen if not in order
#  to fail (somewhat) gracefully
if hasattr(st.session_state, 'db_session'):
    session = st.session_state.db_session

    # Initialize session states
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "weather_data" not in st.session_state:
        st.session_state.weather_data = None
    if "imported_readings" not in st.session_state:
        st.session_state.imported_readings = None
    if "imported_file" not in st.session_state:
        st.session_state.imported_file = None
    if 'lat' not in st.session_state:
        st.session_state.lat = None
    if 'lon' not in st.session_state:
        st.session_state.lon = None
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = None

    st.title("Trial Setup")

    st.write("This page allows you to set up a new trial. " \
    "Please enter the trial name, postcode, and any notes you would like to add, then attach trial data readings and, optionally, imported weather data. ")
    st.write(
    "Please ensure that the name is descriptive and unique. ")
  
    ## Trial inputs
    trial_name = st.text_input("Enter the Trial Name", placeholder="e.g. Greenhouse Test A")
    postcode = st.text_input("Enter the Postcode", placeholder="e.g. BS60 1QY (UK)")
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
        placeholder="Write a detailed description of the trial...",
        height=200
    )

    st.write("Attach sensor readings to the trial here. " \
    "You can import readings from a file or fetch weather " \
    " data if the postcode has been validated and trial data covering"
    "a range of dates has been added.") 

    # Buttons to attach or clear readings
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Attach Readings"):
            importer_type_selection() # Call the utility for choosing how to import readings
    with col2:
        if st.button("Clear Readings"):
            st.session_state.imported_readings = None
            st.write("✅ Readings cleared.")

    with st.expander("Attach Files"):
        st.write("Attach any files you would like to associate with the trial here. " \
                "These files will be stored in the database and can be accessed later. " \
                "Please note that attaching large files may cause the database to exceed " \
                "the capacity of the server.")
        run_file_attach()

    # Checks if an importer has been selected and runs it
    run_selected_importer()

    # Create local variables for readability
    imported_readings = st.session_state.imported_readings
    imported_file = st.session_state.imported_file
    weather_data = st.session_state.weather_data
    # Pass the imported file to the readings store
    if imported_file is not None:
        st.session_state.imported_readings = append_df(imported_readings, imported_file)
        st.session_state.trial_start_datetime = st.session_state.imported_readings['datetime'].min().to_pydatetime()
        st.session_state.trial_end_datetime = st.session_state.imported_readings['datetime'].max().to_pydatetime()
        st.session_state.imported_file = None

    # Pass the weather data to the readings store
    if st.session_state.weather_data is not None:
        st.session_state.imported_readings = append_df(imported_readings, weather_data)
        st.session_state.weather_data = None

    # Check and display imported readings
    if st.session_state.imported_readings is None:
        st.warning("No valid readings have been attached and the trial cannot yet be submitted. " )
    else:

        df = st.session_state.imported_readings
        num_rows = df.shape[0]

        # Button to fetch weather data
        if st.button("Fetch Weather Data"):
            weather_dialog(st.session_state.lat, st.session_state.lon, st.session_state.trial_start_datetime, st.session_state.trial_end_datetime)

        # Makes a map of the readings/sensors metadata
        df = pd.DataFrame({'name': st.session_state.imported_readings['variable'].unique().copy()})
        df['display_name'] = None

        readings_map = st.data_editor(df.reset_index(drop=True), 
                            disabled=["variable"],
                            hide_index=True,)
        readings_map = readings_map.astype("string")
        non_nul_displaynames = readings_map['display_name'][readings_map['display_name'] != '']
        duplicate_names = non_nul_displaynames[non_nul_displaynames.duplicated()].unique()


        st.write(f"✅ {num_rows} readings ready for submission.")
        
        with st.expander("Truncate Readings"):
            st.write("Leave this as is unless readings have been attached "
            "with a date/time range that spans wider than the period of interest.")
            # Display options to truncate the trial data
            col1, col2 = st.columns([1, 1])
            with col1:
                trial_start_date = st.date_input("Trial Start Date", min_value=st.session_state.trial_start_datetime, max_value=st.session_state.trial_end_datetime, value=st.session_state.trial_start_datetime)
            with col2:
                trial_start_time = st.time_input("Start Time", value=st.session_state.trial_end_datetime)

            col1, col2 = st.columns([1, 1])
            with col1:
                trial_end_date = st.date_input("Trial End Date", min_value=st.session_state.trial_start_datetime, max_value=st.session_state.trial_end_datetime, value=st.session_state.trial_end_datetime)
            with col2:
                trial_end_time = st.time_input("End Time", value=st.session_state.trial_end_datetime)
            st.session_state.trial_start_datetime = datetime.combine(trial_start_date, trial_start_time)
            st.session_state.trial_end_datetime = datetime.combine(trial_end_date, trial_end_time)

        # Submit Trial Button
        if st.button("Submit"):
            with st.spinner("Submitting trial..."):
                if not trial_name:                    
                    st.error("❌ Please enter a **Trial Name**.")
                elif session.execute(select(db.Trial).where(db.Trial.name == trial_name)).one_or_none() is not None:
                    st.error("❌ A Trial with this name already exists.")
                elif not st.session_state.trial_start_datetime or not st.session_state.trial_end_datetime:
                    st.error("❌ Please select trial start and end date/times.")
                elif st.session_state.trial_end_datetime < st.session_state.trial_start_datetime:
                    st.error("❌ End date/time cannot be earlier than the trial start date/time.")
                elif not postcode:
                    st.error("❌ Please enter a **Postcode**.")
                elif len(duplicate_names) > 0:
                    duplicate_names_str = ','.join(duplicate_names.tolist())
                    st.warning(f'Duplicate sensor display names found: [{duplicate_names_str}]')
                else:
                    trial = db.Trial(name=trial_name, postcode=postcode, notes=notes)
                    try:
                        trial.dataframe = st.session_state.imported_readings
                    except (AssertionError, TypeError):
                        st.error("❌ Not all of the incoming readings were in the correct format. Please check the data and try again.")
                    else:
                        trial.readings_map = readings_map
                        attach_files_to_trial(trial, st.session_state.uploaded_files)
                        session.add(trial)
                        session.commit()
                        st.session_state.imported_readings = None
                        st.session_state.submitted = True
                        menu_nav.navigate_to(trial)
                        st.rerun()

