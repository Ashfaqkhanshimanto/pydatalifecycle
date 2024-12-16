import requests
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import datetime


def fetch_weather_data(latitude, longitude, start_date, end_date):
    """
    Fetches historical weather data from Open-Meteo API.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': end_date,
        'daily': ['temperature_2m_max', 'temperature_2m_min', 'precipitation_sum'],
        'timezone': 'auto'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # Raise an error for bad status
    data = response.json()
    
    weather_df = pd.DataFrame({
        'date': data['daily']['time'],
        'temp_max': data['daily']['temperature_2m_max'],
        'temp_min': data['daily']['temperature_2m_min'],
        'precipitation': data['daily']['precipitation_sum']
    })
    return weather_df

# Example: Fetch data for Dubai from Jan 1, 2023 to Dec 31, 2023
weather_df = fetch_weather_data(
    latitude=25.2048,
    longitude=55.2708,
    start_date='2023-01-01',
    end_date='2023-12-31'
)
