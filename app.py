from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import requests
import math

app = Flask(__name__)

# Global variables for ESP32 data
box_temp = None
frequency = None
power_factor = None
voltage = None
current = None
power = None
energy = None
solar_voltage = None
solar_current = None
solar_power = None
battery_percentage = None
light_intensity = None
battery_voltage = None

# Weather data cache
weather_cache = None
weather_last_updated = None
CACHE_DURATION = 3600  # Cache weather data for 1 hour

# Bareilly, Uttar Pradesh, India coordinates
BAREILLY_LAT = 28.3640
BAREILLY_LON = 79.4151

# Open-Meteo API (NO API KEY REQUIRED - global coverage)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def get_weather_data():
    """
    Fetch current and 7-day forecast weather data using Open-Meteo
    Returns: Dictionary with current weather and forecast
    """
    global weather_cache, weather_last_updated
    
    # Check if cache is still valid
    if weather_cache and weather_last_updated:
        if (datetime.now() - weather_last_updated).total_seconds() < CACHE_DURATION:
            print("🌤️ Using cached weather data")
            return weather_cache
    
    try:
        print("🌤️ Fetching fresh weather data from Open-Meteo...")
        print(f"📍 Location: Bareilly, India ({BAREILLY_LAT}, {BAREILLY_LON})")
        
        # Open-Meteo API parameters
        params = {
            'latitude': BAREILLY_LAT,
            'longitude': BAREILLY_LON,
            'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m',
            'hourly': 'temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,cloud_cover,wind_speed_10m',
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,weather_code',
            'timezone': 'auto',
            'forecast_days': 7
        }
        
        # Make API request
        response = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract current weather
        current = data.get('current', {})
        current_weather = {
            'temperature': current.get('temperature_2m'),
            'feels_like': current.get('apparent_temperature'),
            'humidity': current.get('relative_humidity_2m'),
            'cloud_cover': current.get('cloud_cover'),
            'wind_speed': current.get('wind_speed_10m'),
            'wind_direction': current.get('wind_direction_10m'),
            'precipitation': current.get('precipitation'),
            'rain': current.get('rain'),
            'weather_code': current.get('weather_code'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract daily forecast (next 5 days)
        forecast = []
        daily_data = data.get('daily', {})
        times = daily_data.get('time', [])
        
        for i in range(min(5, len(times))):  # Next 5 days
            forecast.append({
                'date': times[i],
                'temperature_max': daily_data.get('temperature_2m_max', [])[i] if i < len(daily_data.get('temperature_2m_max', [])) else None,
                'temperature_min': daily_data.get('temperature_2m_min', [])[i] if i < len(daily_data.get('temperature_2m_min', [])) else None,
                'precipitation': daily_data.get('precipitation_sum', [])[i] if i < len(daily_data.get('precipitation_sum', [])) else None,
                'rain': daily_data.get('rain_sum', [])[i] if i < len(daily_data.get('rain_sum', [])) else None,
                'weather_code': daily_data.get('weather_code', [])[i] if i < len(daily_data.get('weather_code', [])) else None
            })
        
        weather_data = {
            'current': current_weather,
            'forecast': forecast,
            'location': {'lat': BAREILLY_LAT, 'lon': BAREILLY_LON, 'name': 'Bareilly, India'},
            'last_updated': datetime.now().isoformat(),
            'source': 'open-meteo'
        }
        
        # Update cache
        weather_cache = weather_data
        weather_last_updated = datetime.now()
        
        print("✅ Weather data fetched successfully from Open-Meteo!")
        return weather_data
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Open-Meteo API error: {str(e)}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}
    except Exception as e:
        error_msg = f"Error processing weather data: {str(e)}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}

def log_weather_data(weather_data):
    """Helper function to log weather data"""
    if 'error' in weather_data:
        print(f"❌ Weather error: {weather_data['error']}")
        return
    
    current = weather_data['current']
    print("🌤️ CURRENT WEATHER:")
    print(f"   Temperature: {current.get('temperature', 'N/A')}°C")
    print(f"   Feels like: {current.get('feels_like', 'N/A')}°C")
    print(f"   Humidity: {current.get('humidity', 'N/A')}%")
    print(f"   Cloud Cover: {current.get('cloud_cover', 'N/A')}%")
    print(f"   Wind Speed: {current.get('wind_speed', 'N/A')} km/h")
    print(f"   Precipitation: {current.get('precipitation', 'N/A')} mm")
    print(f"   Rain: {current.get('rain', 'N/A')} mm")

# ... [KEEP ALL YOUR EXISTING ROUTES UNCHANGED] ...
# /esp32-data, /weather, /combined-data, /test-meteo, / all remain the same

@app.route('/test-open-meteo', methods=['GET'])
def test_open_meteo():
    """
    Test endpoint to check Open-Meteo API
    """
    try:
        print("🧪 Testing Open-Meteo API for Bareilly...")
        weather_data = get_weather_data()
        
        if 'error' in weather_data:
            return jsonify({"success": False, "error": weather_data['error']})
        
        return jsonify({
            "success": True,
            "has_data": True,
            "current_temperature": weather_data['current'].get('temperature'),
            "location": weather_data['location'],
            "source": weather_data.get('source', 'open-meteo')
        })
        
    except Exception as e:
        error_msg = f"Open-Meteo test failed: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"success": False, "error": error_msg})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
