# config.py
import os
from datetime import timedelta

class Config:
    # Server configuration
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True
    
    # Weather configuration
    LATITUDE = 28.336485  # Replace with your actual latitude
    LONGITUDE = 79.402418  # Replace with your actual longitude
    LOCATION_NAME = "Bareilly,Uttar pradesh,India"  # Replace with your location name
    
    # Cache configuration
    WEATHER_CACHE_DURATION = 3600  # 1 hour in seconds
    WEATHER_CACHE_ENABLED = True
    
    # ESP32 data validation (optional)
    MIN_VOLTAGE = 0
    MAX_VOLTAGE = 250
    MIN_TEMPERATURE = -40
    MAX_TEMPERATURE = 100
