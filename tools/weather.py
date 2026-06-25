import urllib.request
import urllib.parse
import json
from typing import Optional


def get_weather(location: str) -> Optional[str]:
    """
    Get current weather + today's forecast for any location in the world.
    Uses the free Open-Meteo API (no key required).
    Returns a formatted string or None if the location can't be found / data fails.
    """
    try:
        geo_params = urllib.parse.urlencode({
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        })
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?{geo_params}"

        with urllib.request.urlopen(geo_url, timeout=6) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))

        if not geo_data.get("results"):
            return None

        result = geo_data["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        name = result.get("name", location)
        country = result.get("country", "")

        current_vars = "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
        daily_vars = "temperature_2m_max,temperature_2m_min,weather_code"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": current_vars,
            "daily": daily_vars,
            "timezone": "auto"
        }
        weather_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(weather_params)

        with urllib.request.urlopen(weather_url, timeout=6) as resp:
            weather_data = json.loads(resp.read().decode("utf-8"))

        current = weather_data.get("current", {})
        daily = weather_data.get("daily", {})

        wmo_desc = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
            55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
            80: "Rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }

        current_code = current.get("weather_code", -1)
        current_desc = wmo_desc.get(current_code, "Unknown")
        daily_code = daily.get("weather_code", [None])[0]
        daily_desc = wmo_desc.get(daily_code, "Unknown") if daily_code else "Unknown"

        temp_now = current.get("temperature_2m", "?")
        apparent = current.get("apparent_temperature", "?")
        humidity = current.get("relative_humidity_2m", "?")
        wind = current.get("wind_speed_10m", "?")
        high = daily.get("temperature_2m_max", [None])[0]
        low = daily.get("temperature_2m_min", [None])[0]

        weather_text = (
            f"Current weather in {name}, {country}:\n"
            f"- Temperature: {temp_now}°C (feels like {apparent}°C)\n"
            f"- Conditions: {current_desc}\n"
            f"- Humidity: {humidity}%\n"
            f"- Wind speed: {wind} km/h\n"
        )
        if high is not None and low is not None:
            weather_text += f"Today's forecast: High {high}°C, Low {low}°C, {daily_desc}."

        return weather_text

    except Exception as e:
        print(f"[WEATHER ERROR] {e}")
        return None