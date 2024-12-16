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


def fetch_tourism_data():
    """
    Fetches tourism data. For demonstration, we use a sample dataset.
    """
    # Sample tourism data: number of tourists per month in Dubai
    tourism_data = {
        'month': ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05',
                  '2023-06', '2023-07', '2023-08', '2023-09', '2023-10',
                  '2023-11', '2023-12'],
        'tourists': [500000, 450000, 600000, 700000, 800000,
                     750000, 720000, 680000, 700000, 800000,
                     850000, 900000]
    }
    tourism_df = pd.DataFrame(tourism_data)
    tourism_df['month'] = pd.to_datetime(tourism_df['month'])
    return tourism_df

tourism_df = fetch_tourism_data()

# Merge weather data with tourism data based on month
weather_df['month'] = pd.to_datetime(weather_df['date']).dt.to_period('M').dt.to_timestamp()
combined_df = pd.merge(weather_df, tourism_df, on='month', how='left')


def store_data_sqlite(df, db_name='weather_tourism.db'):
    """
    Stores the DataFrame into an SQLite database.
    """
    engine = create_engine(f'sqlite:///{db_name}')
    df.to_sql('weather_tourism', con=engine, if_exists='replace', index=False)
    return engine

engine = store_data_sqlite(combined_df)


def create_dash_app(engine):
    """
    Creates and runs a Dash application to visualize the data.
    """
    # Initialize Dash app
    app = Dash(__name__)
    
    # Fetch data from SQLite
    query = "SELECT * FROM weather_tourism"
    df = pd.read_sql(query, engine)
    
    # Convert 'month' to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df['month']):
        df['month'] = pd.to_datetime(df['month'])
    
    # Layout of the Dash app
    app.layout = html.Div([
        html.H1("Dubai Weather and Tourism Data (2023)"),
        
        html.Div([
            html.Label("Select Temperature Type:"),
            dcc.Dropdown(
                id='temp_type',
                options=[
                    {'label': 'Max Temperature', 'value': 'temp_max'},
                    {'label': 'Min Temperature', 'value': 'temp_min'}
                ],
                value='temp_max'
            )
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '0 20'}),
        
        html.Div([
            html.Label("Select Month Range:"),
            dcc.RangeSlider(
                id='month_range',
                min=1,
                max=12,
                value=[1, 12],
                marks={i: pd.to_datetime(f'2023-{i:02d}-01').strftime('%b') for i in range(1,13)},
                step=1,
                allowCross=False
            )
        ], style={'width': '98%', 'padding': '20px 20px 20px 20px'}),
        
        dcc.Graph(id='temperature_graph'),
        
        dcc.Graph(id='tourism_graph')
    ])
    
    # Callback to update graphs based on user input
    @app.callback(
        [Output('temperature_graph', 'figure'),
         Output('tourism_graph', 'figure')],
        [Input('temp_type', 'value'),
         Input('month_range', 'value')]
    )
