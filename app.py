from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from meteostat import Point, Daily, Hourly
import pandas as pd
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

def safe_float(value, default=None):
    """Safely convert value to float, handling NaN and None"""
    if value is None or pd.isna(value) or math.isnan(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def log_weather_data(weather_data):
    """Helper function to log weather data"""
    if 'error' in weather_data:
        print(f"❌ Weather error: {weather_data['error']}")
        return
    
    current = weather_data['current']
    print("🌤️ CURRENT WEATHER:")
    print(f"   Temperature: {current.get('temperature', 'N/A')}°C")
    print(f"   Dew Point: {current.get('dew_point', 'N/A')}°C")
    print(f"   Humidity: {current.get('humidity', 'N/A')}%")
    print(f"   Cloud Cover: {current.get('cloud_cover', 'N/A')}%")
    print(f"   Wind Speed: {current.get('wind_speed', 'N/A')} km/h")
    print(f"   Pressure: {current.get('pressure', 'N/A')} hPa")
    print(f"   Precipitation: {current.get('precipitation', 'N/A')} mm")

def get_weather_data():
    """
    Fetch current and 5-day forecast weather data using Meteostat
    Returns: Dictionary with current weather and 5-day forecast
    """
    global weather_cache, weather_last_updated
    
    # Check if cache is still valid
    if weather_cache and weather_last_updated:
        if (datetime.now() - weather_last_updated).total_seconds() < CACHE_DURATION:
            print("🌤️ Using cached weather data")
            return weather_cache
    
    try:
        print("🌤️ Fetching fresh weather data from Meteostat...")
        
        # Set your location coordinates (latitude, longitude)
        # Example: New York City coordinates
        location = Point(28.336485,79.402418 )
        
        # Get current date and time
        now = datetime.now()
        start = now - timedelta(days=1)  # Get data from yesterday to today
        end = now + timedelta(days=6)    # Get data for next 5 days
        
        # Get hourly data for current conditions
        hourly_data = Hourly(location, start, end)
        hourly_df = hourly_data.fetch()
        
        # Get daily data for forecast
        daily_data = Daily(location, start, end)
        daily_df = daily_data.fetch()
        
        # Check if dataframes are empty
        if hourly_df.empty or daily_df.empty:
            return {'error': 'No weather data available from Meteostat'}
        
        # Extract current weather (most recent hour)
        current_hour = hourly_df.iloc[-1]
        
        # Prepare current weather data with safe float conversion
        current_weather = {
            'temperature': safe_float(current_hour.get('temp')),
            'dew_point': safe_float(current_hour.get('dwpt')),
            'humidity': safe_float(current_hour.get('rhum')),
            'cloud_cover': safe_float(current_hour.get('coco')),
            'wind_speed': safe_float(current_hour.get('wspd')),
            'wind_direction': safe_float(current_hour.get('wdir')),
            'pressure': safe_float(current_hour.get('pres')),
            'precipitation': safe_float(current_hour.get('prcp')),
            'timestamp': current_hour.name.isoformat() if hasattr(current_hour.name, 'isoformat') else str(current_hour.name)
        }
        
        # Prepare 5-day forecast with safe float conversion
        forecast = []
        for i in range(1, 6):  # Next 5 days
            forecast_date = now.date() + timedelta(days=i)
            if forecast_date in daily_df.index:
                day_data = daily_df.loc[forecast_date]
                forecast.append({
                    'date': forecast_date.isoformat(),
                    'temperature_avg': safe_float(day_data.get('tavg')),
                    'temperature_min': safe_float(day_data.get('tmin')),
                    'temperature_max': safe_float(day_data.get('tmax')),
                    'precipitation': safe_float(day_data.get('prcp')),
                    'wind_speed_avg': safe_float(day_data.get('wspd')),
                    'pressure_avg': safe_float(day_data.get('pres'))
                })
            else:
                # Add placeholder for missing forecast days
                forecast.append({
                    'date': forecast_date.isoformat(),
                    'temperature_avg': None,
                    'temperature_min': None,
                    'temperature_max': None,
                    'precipitation': None,
                    'wind_speed_avg': None,
                    'pressure_avg': None
                })
        
        weather_data = {
            'current': current_weather,
            'forecast': forecast,
            'location': {'lat': 28.336485, 'lon': 79.402418, 'name': 'Bareilly'},
            'last_updated': datetime.now().isoformat()
        }
        
        # Update cache
        weather_cache = weather_data
        weather_last_updated = datetime.now()
        
        return weather_data
        
    except Exception as e:
        print(f"❌ Error fetching weather data: {str(e)}")
        return {'error': str(e)}

@app.route('/esp32-data', methods=['POST'])
def receive_data():
    global box_temp, frequency, power_factor, voltage, current, power, energy
    global solar_voltage, solar_current, solar_power, battery_percentage
    global light_intensity, battery_voltage

    try:
        data = request.get_json()

        # Extract values into separate variables
        box_temp = data.get("BoxTemperature")
        frequency = data.get("Frequency")
        power_factor = data.get("PowerFactor")
        voltage = data.get("Voltage")
        current = data.get("Current")
        power = data.get("Power")
        energy = data.get("Energy")
        solar_voltage = data.get("SolarVoltage")
        solar_current = data.get("solarCurrent")
        solar_power = data.get("solarPower")
        battery_percentage = data.get("batteryPercentage")
        light_intensity = data.get("lightIntensity")
        battery_voltage = data.get("batteryVoltage")

        # Debug print
        print("📩 Data received from ESP32:")
        print(f"Box Temp: {box_temp} °C")
        print(f"Voltage: {voltage} V")
        print(f"Current: {current} A")
        print(f"Power: {power} W")
        print(f"Energy: {energy} Wh")
        print(f"Frequency: {frequency} Hz")
        print(f"Power Factor: {power_factor}")
        print(f"Solar: {solar_voltage} V, {solar_current} mA, {solar_power} mW")
        print(f"Battery: {battery_voltage} V, {battery_percentage} %")
        print(f"Light Intensity: {light_intensity} Lux")

        # 🔥 AUTO-FETCH WEATHER DATA WHEN ESP32 SENDS DATA
        print("\n🌤️ Auto-fetching weather data...")
        weather_data = get_weather_data()
        
        if 'error' in weather_data:
            print(f"❌ Weather fetch failed: {weather_data['error']}")
        else:
            current_weather = weather_data['current']
            print("✅ Current Weather:")
            print(f"   Temperature: {current_weather.get('temperature', 'N/A')}°C")
            print(f"   Humidity: {current_weather.get('humidity', 'N/A')}%")
            print(f"   Wind Speed: {current_weather.get('wind_speed', 'N/A')} km/h")
            print(f"   Cloud Cover: {current_weather.get('cloud_cover', 'N/A')}%")
        
        print("----------------------------------------")

        return jsonify({"status": "success", "message": "Data received"})

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/weather', methods=['GET'])
def get_weather():
    """
    Endpoint to get current weather and 5-day forecast
    """
    try:
        weather_data = get_weather_data()
        
        print("\n🌤️ Weather Information Retrieved:")
        print("=" * 50)
        
        if 'error' in weather_data:
            print(f"Error: {weather_data['error']}")
            return jsonify(weather_data), 500
        
        # Use the helper function
        log_weather_data(weather_data)
        
        # Print forecast
        print("\n5-DAY FORECAST:")
        for i, day in enumerate(weather_data['forecast'], 1):
            print(f"Day {i} ({day['date']}):")
            print(f"  Avg Temp: {day.get('temperature_avg', 'N/A')}°C")
            print(f"  Min Temp: {day.get('temperature_min', 'N/A')}°C")
            print(f"  Max Temp: {day.get('temperature_max', 'N/A')}°C")
            print(f"  Precipitation: {day.get('precipitation', 'N/A')} mm")
            print(f"  Wind Speed: {day.get('wind_speed_avg', 'N/A')} km/h")
        
        print(f"\nLocation: {weather_data['location']['name']}")
        print(f"Last Updated: {weather_data['last_updated']}")
        print("=" * 50)
        
        return jsonify(weather_data)
        
    except Exception as e:
        error_msg = f"Error retrieving weather data: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/combined-data', methods=['GET'])
def get_combined_data():
    """
    Endpoint to get both ESP32 data and weather data
    """
    try:
        # Get ESP32 data
        esp32_data = {
            'box_temperature': box_temp,
            'voltage': voltage,
            'current': current,
            'power': power,
            'energy': energy,
            'frequency': frequency,
            'power_factor': power_factor,
            'solar_voltage': solar_voltage,
            'solar_current': solar_current,
            'solar_power': solar_power,
            'battery_percentage': battery_percentage,
            'battery_voltage': battery_voltage,
            'light_intensity': light_intensity
        }
        
        # Get weather data
        weather_data = get_weather_data()
        
        combined_data = {
            'esp32_data': esp32_data,
            'weather_data': weather_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(combined_data)
        
    except Exception as e:
        error_msg = f"Error retrieving combined data: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/')
def home():
    return """
    ESP32 API is running. 🚀<br>
    Endpoints:<br>
    - POST /esp32-data (Receive ESP32 data)<br>
    - GET /weather (Get weather data)<br>
    - GET /combined-data (Get both ESP32 and weather data)
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
