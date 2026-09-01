#!/usr/bin/env python
# execution/fetch_imd_weather.py

import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import time

# ========================================
# CONFIGURATION
# ========================================
EXISTING_DATA_PATH = "data/enriched_with_driver.csv"
OUTPUT_PATH = "data/enriched_with_weather.csv"
WEATHER_CACHE_PATH = "data/weather_cache_imd.csv"

# IMD API Configuration
IMD_API_BASE = "https://api.imd.gov.in/api/v1"
PUNE_STATION_ID = 43063  # Shivajinagar, Pune

# ========================================
# FUNCTIONS
# ========================================

def fetch_current_weather(station_id):
    """
    Fetch current weather data from IMD API for a given station ID.
    Returns a dictionary with weather fields.
    """
    url = f"{IMD_API_BASE}/current_wx"
    params = {"id": station_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # The API might return a list or a single object
        if isinstance(data, list):
            # If it's a list, take the first item (should be the station)
            if len(data) > 0:
                return data[0]
            else:
                print("Empty response from IMD API.")
                return None
        elif isinstance(data, dict):
            return data
        else:
            print(f"Unexpected response format: {type(data)}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def parse_weather_response(weather_data):
    """
    Parse the IMD API response into a structured dictionary.
    Converts UTC time to IST and extracts date.
    """
    if not weather_data:
        return None
    
    # Extract fields
    date_str = weather_data.get('Date of Observation')  # Format: YYYY-mm-dd
    time_utc_str = weather_data.get('Time of Observation')  # Format: HH:MM:SS (UTC)
    
    if not date_str or not time_utc_str:
        print("Missing date or time in weather response.")
        return None
    
    # Combine date and UTC time
    dt_utc = datetime.strptime(f"{date_str} {time_utc_str}", "%Y-%m-%d %H:%M:%S")
    
    # Convert UTC to IST (UTC+5:30)
    dt_ist = dt_utc + timedelta(hours=5, minutes=30)
    
    return {
        'date': dt_ist.date(),
        'hour': dt_ist.hour,
        'station_id': weather_data.get('Station Id'),
        'station': weather_data.get('Station'),
        'mslp': weather_data.get('M.S.L.P'),          # hPa
        'wind_direction': weather_data.get('Wind Direction'),
        'wind_speed': weather_data.get('Wind Speed'),  # KMPH
        'temperature': weather_data.get('Temperature'), # deg C
        'weather_code': weather_data.get('Weather Code'),
        'nebulosity': weather_data.get('Nebulosity'),   # 0-8
        'humidity': weather_data.get('Humidity'),       # %
        'rainfall_24h': weather_data.get('Last 24 hrs Rainfall')  # mm
    }

def fetch_and_cache_weather(station_id, cache_path):
    """
    Fetch current weather, cache it, and return as DataFrame.
    """
    print(f"Fetching weather for station {station_id}...")
    raw_data = fetch_current_weather(station_id)
    
    if not raw_data:
        print("No weather data received.")
        return pd.DataFrame()
    
    parsed = parse_weather_response(raw_data)
    if not parsed:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame([parsed])
    
    # Load existing cache if any
    if os.path.exists(cache_path):
        cache_df = pd.read_csv(cache_path)
        cache_df['date'] = pd.to_datetime(cache_df['date']).dt.date
        # Append new data (avoid duplicates by date)
        new_date = parsed['date']
        if new_date not in cache_df['date'].values:
            cache_df = pd.concat([cache_df, df], ignore_index=True)
        else:
            # Update existing record for that date
            cache_df = cache_df[cache_df['date'] != new_date]
            cache_df = pd.concat([cache_df, df], ignore_index=True)
        cache_df.to_csv(cache_path, index=False)
        print(f"Updated cache at {cache_path}")
        return cache_df
    else:
        df.to_csv(cache_path, index=False)
        print(f"Created cache at {cache_path}")
        return df

def load_cached_weather(cache_path):
    """Load cached weather data."""
    if os.path.exists(cache_path):
        df = pd.read_csv(cache_path)
        df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    return pd.DataFrame()

def merge_weather(main_df, weather_df):
    """Merge weather data into main dataset on (date, hour)."""
    main = main_df.copy()
    main['date'] = pd.to_datetime(main['date']).dt.date
    
    # Merge on date and hour
    merged = main.merge(weather_df, on=['date', 'hour'], how='left')
    
    # Fill missing weather with the most recent available (forward fill per date)
    # This is a simple approach – you can refine it
    for col in ['temperature', 'humidity', 'wind_speed', 'mslp', 'rainfall_24h']:
        if col in merged.columns:
            merged[col] = merged.groupby('date')[col].ffill()
    
    return merged

# ========================================
# MAIN
# ========================================

def main():
    print("Loading enriched dataset...")
    main_df = pd.read_csv(EXISTING_DATA_PATH)
    print(f"Loaded {len(main_df)} rows.")

    # Fetch current weather and update cache
    weather_df = fetch_and_cache_weather(PUNE_STATION_ID, WEATHER_CACHE_PATH)
    
    if weather_df.empty:
        print("No weather data available. Exiting.")
        return
    
    # Load full cache
    full_weather = load_cached_weather(WEATHER_CACHE_PATH)
    print(f"Loaded {len(full_weather)} cached weather records.")

    # Merge weather into main dataset
    merged = merge_weather(main_df, full_weather)
    
    # Report coverage
    weather_coverage = merged['temperature'].notna().sum()
    print(f"Merged dataset has {len(merged)} rows.")
    print(f"Rows with weather data: {weather_coverage} ({weather_coverage/len(merged)*100:.1f}%)")

    # Save final dataset
    merged.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved enriched dataset to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()