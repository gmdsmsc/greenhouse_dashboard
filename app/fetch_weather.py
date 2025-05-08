# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 11:52:02 2025
@author: Phoebe.Sinclair
"""

import requests_cache
import openmeteo_requests 
import pandas as pd

''' Fetches weather data from the Open Meteo API and caches the responses.
    The data is returned as a pandas DataFrame.'''

# Create a cache session to store the responses for Open Meteo API calls
cache_session = requests_cache.CachedSession('cache/openmeteo_cache', expire_after=3600)

def fetch_weather_data(latitude, longitude, start_date, end_date):
    # Initialize the weather client with the cache session
    openmeteo = openmeteo_requests.Client(session=cache_session)
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "hourly": "temperature_2m,cloud_cover,precipitation,shortwave_radiation,sunshine_duration,weather_code",
    }

    # Fetch the data from the API
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()
    
    start_datetime = pd.to_datetime(hourly.Time(), unit="s", utc=True)
    end_datetime = pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True)
    
    # Return the weather data as a pandas DataFrame
    return pd.DataFrame({
        "datetime": pd.to_datetime(pd.date_range(
            start=start_datetime,
            end=end_datetime,
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )),
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "cloud_cover": hourly.Variables(1).ValuesAsNumpy(),
        "precipitation": hourly.Variables(2).ValuesAsNumpy(),
        "shortwave_radiation": hourly.Variables(3).ValuesAsNumpy(),
        "sunshine_duration": hourly.Variables(4).ValuesAsNumpy(),
        "weather_code": hourly.Variables(5).ValuesAsNumpy()
    })