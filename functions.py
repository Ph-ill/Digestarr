import os
import requests
from datetime import timezone, datetime

def add_leading_zero_if_single_digit(s):
    if isinstance(s, str) and s.isdigit() and len(s) == 1:
        return '0' + s
    return s

def generate_emojis_from_text(text, api_key, model="mistral-large-latest", num_emojis=3):
    try:
        from mistralai import Mistral
        client = Mistral(api_key=api_key)
        prompt = f"Generate {num_emojis} emojis for the following text: {text}, output nothing other than the emojis"
        chat_response = client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        emoji_string = chat_response.choices[0].message.content.strip()
        return emoji_string
    except Exception as e:
        return f"Error occurred: {e}"

def format_air_time(air_date_utc):
    if isinstance(air_date_utc, datetime):
        dt = air_date_utc
    else:
        try:
            dt = datetime.fromisoformat(air_date_utc)
        except Exception:
            return str(air_date_utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local_dt = dt.astimezone()
    return local_dt.strftime('%I:%M %p')

def get_weather_forecast_by_coords(latitude, longitude):
    """
    Retrieve and format the daily weather forecast based on latitude and longitude.
    Returns a tuple: (condition, temperature_str)
    """
    url = "https://api.open-meteo.com/v1/forecast"
    # Read temperature unit from environment; default to 'celsius'
    temp_unit = os.getenv("WEATHER_TEMP_UNIT", "celsius").lower()
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weathercode,temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "temperature_unit": temp_unit
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        daily = data.get("daily", {})
        if daily:
            weather_code = daily.get("weathercode", [None])[0]
            temp_max = daily.get("temperature_2m_max", [None])[0]
            temp_min = daily.get("temperature_2m_min", [None])[0]
            weather_descriptions = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Fog",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                56: "Light freezing drizzle",
                57: "Dense freezing drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                66: "Light freezing rain",
                67: "Heavy freezing rain",
                71: "Slight snow fall",
                73: "Moderate snow fall",
                75: "Heavy snow fall",
                77: "Snow grains",
                80: "Slight rain showers",
                81: "Moderate rain showers",
                82: "Violent rain showers",
                85: "Slight snow showers",
                86: "Heavy snow showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail",
                99: "Thunderstorm with heavy hail"
            }
            condition = weather_descriptions.get(weather_code, "Unknown")
            # Build temperature string with appropriate unit symbol
            unit_symbol = "°C" if temp_unit == "celsius" else "°F"
            temperature_str = f"High: {temp_max}{unit_symbol}, Low: {temp_min}{unit_symbol}"
            return condition, temperature_str
        else:
            return "Weather data unavailable", ""
    except Exception as e:
        print("Weather API error:", e)
        return "Weather data error", ""
