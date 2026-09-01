#!/usr/bin/env python
# execution/fetch_weather_openmeteo.py

import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# ========================================
# CONFIGURATION
# ========================================
EXISTING_DATA_PATH = "data/enriched_with_driver.csv"
OUTPUT_PATH = "data/enriched_with_weather.csv"
WEATHER_CACHE_PATH = "data/weather_cache_openmeteo.csv"

LAT = 18.5204
LON = 73.8567

# ========================================
# FUNCTIONS
# ========================================

def fetch_weather_for_date_range(start_date, end_date):
    """
    Fetch historical daily weather data from Open-Meteo Archive API.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "rain_sum",
            "snowfall_sum",
            "wind_speed_10m_max",
            "wind_gusts_10m_max"
        ],
        "timezone": "Asia/Kolkata",
        "format": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'daily' not in data:
            print("No 'daily' key in response.")
            return pd.DataFrame()
        daily = data['daily']
        # Ensure time is a list of strings; convert to datetime
        time_series = pd.to_datetime(daily['time'])
        # Extract date part
        dates = time_series.date  # This returns an array of datetime.date objects
        df = pd.DataFrame({
            'date': dates,
            'temp_max': daily['temperature_2m_max'],
            'temp_min': daily['temperature_2m_min'],
            'precipitation': daily['precipitation_sum'],
            'rain': daily['rain_sum'],
            'snowfall': daily['snowfall_sum'],
            'wind_speed_max': daily['wind_speed_10m_max'],
            'wind_gust_max': daily['wind_gusts_10m_max']
        })
        return df
    except Exception as e:
        print(f"Error fetching historical weather: {e}")
        return pd.DataFrame()

def fetch_forecast(days=7):
    """
    Fetch weather forecast for the next N days from Open-Meteo Forecast API.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "rain_sum",
            "snowfall_sum",
            "wind_speed_10m_max",
            "wind_gusts_10m_max"
        ],
        "forecast_days": days,
        "timezone": "Asia/Kolkata",
        "format": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'daily' not in data:
            return pd.DataFrame()
        daily = data['daily']
        time_series = pd.to_datetime(daily['time'])
        dates = time_series.date
        df = pd.DataFrame({
            'date': dates,
            'temp_max': daily['temperature_2m_max'],
            'temp_min': daily['temperature_2m_min'],
            'precipitation': daily['precipitation_sum'],
            'rain': daily['rain_sum'],
            'snowfall': daily['snowfall_sum'],
            'wind_speed_max': daily['wind_speed_10m_max'],
            'wind_gust_max': daily['wind_gusts_10m_max']
        })
        return df
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return pd.DataFrame()

def load_cached_weather():
    """Load cached weather data."""
    if os.path.exists(WEATHER_CACHE_PATH):
        df = pd.read_csv(WEATHER_CACHE_PATH)
        df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    return pd.DataFrame()

def save_cache(df):
    df.to_csv(WEATHER_CACHE_PATH, index=False)
    print(f"Cache saved with {len(df)} rows.")

def merge_weather(main_df, weather_df):
    """Merge daily weather data into main dataset on date."""
    main = main_df.copy()
    main['date'] = pd.to_datetime(main['date']).dt.date
    # Ensure weather_df date column is date object
    weather_df['date'] = pd.to_datetime(weather_df['date']).dt.date
    merged = main.merge(weather_df, on='date', how='left')
    return merged

# ========================================
# MAIN
# ========================================

def main():
    print("Loading enriched dataset...")
    main_df = pd.read_csv(EXISTING_DATA_PATH)
    print(f"Loaded {len(main_df)} rows.")

    # Determine date range needed
    main_df['date'] = pd.to_datetime(main_df['date']).dt.date
    min_date = main_df['date'].min()
    max_date = main_df['date'].max()
    today = datetime.now().date()
    print(f"Date range in dataset: {min_date} to {max_date}")

    # Load cache
    weather_df = load_cached_weather()
    existing_dates = set(weather_df['date'].unique()) if not weather_df.empty else set()
    needed_dates = set(main_df['date'].unique()) - existing_dates
    print(f"Need weather for {len(needed_dates)} dates.")

    # Separate historical and future
    historical = {d for d in needed_dates if d < today}
    future = {d for d in needed_dates if d >= today}

    # Fetch historical
    if historical:
        start = min(historical)
        end = max(historical)
        print(f"Fetching historical weather {start} to {end}...")
        hist_df = fetch_weather_for_date_range(start, end)
        if not hist_df.empty:
            weather_df = pd.concat([weather_df, hist_df], ignore_index=True)
            print(f"Added {len(hist_df)} historical days.")
        else:
            print("No historical data returned.")

    # Fetch forecast
    if future:
        forecast_days = 7
        print(f"Fetching {forecast_days}-day forecast...")
        fc_df = fetch_forecast(days=forecast_days)
        if not fc_df.empty:
            fc_df = fc_df[fc_df['date'].isin(future)]
            weather_df = pd.concat([weather_df, fc_df], ignore_index=True)
            print(f"Added {len(fc_df)} forecast days.")
        else:
            print("No forecast data returned.")

    if weather_df.empty:
        print("No weather data fetched. Exiting.")
        return

    # Save cache
    save_cache(weather_df)

    # Merge into main
    merged = merge_weather(main_df, weather_df)
    weather_coverage = merged['temp_max'].notna().sum()
    print(f"Merged dataset has {len(merged)} rows.")
    print(f"Rows with weather data: {weather_coverage} ({weather_coverage/len(merged)*100:.1f}%)")

    merged.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()