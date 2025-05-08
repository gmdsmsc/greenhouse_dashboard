# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 11:52:02 2025
@author: Phoebe.Sinclair
"""

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import openmeteo_requests
import requests_cache
from retry_requests import retry


# Setup Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Function to get coordinates from postcode 
def get_coordinates(postcode):
    geolocator = Nominatim(user_agent="streamlit-geocoder")
    try:
        location = geolocator.geocode(postcode)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        return None, None

# Function to fetch weather data from Open-Meteo API
def fetch_weather_data(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,cloud_cover,precipitation,shortwave_radiation,sunshine_duration,weather_code",
        "timezone": "auto"
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Process hourly weather data
    hourly = response.Hourly()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "cloud_cover": hourly.Variables(1).ValuesAsNumpy(),
        "precipitation": hourly.Variables(2).ValuesAsNumpy(),
        "shortwave_radiation": hourly.Variables(3).ValuesAsNumpy(),
        "sunshine_duration": hourly.Variables(4).ValuesAsNumpy(),
        "weather_code": hourly.Variables(5).ValuesAsNumpy()
    }

    return pd.DataFrame(data=hourly_data)