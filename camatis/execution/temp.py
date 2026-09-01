import requests

# Endpoint to get all stations
url = "https://api.imd.gov.in/station/all"  # Base URL may vary, check documentation

try:
    response = requests.get(url)
    response.raise_for_status()
    stations = response.json()
    
    for station in stations.get('result', []):
        if 'pune' in station.get('jurisdiction', '').lower():
            print(f"Station found: {station}")
            # Example output: {'jurisdiction': 'Pune', 'region': 'Maharashtra', 'station': 'Shivajinagar', 'stationId': 43063}
except requests.exceptions.RequestException as e:
    print(f"Error fetching station data: {e}")