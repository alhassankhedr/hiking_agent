import requests

def get_weather(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,precipitation_probability,weathercode"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching weather data: {e}")
        return {}
    except ValueError:
        print("Failed to decode weather data from response.")
        return {}

from datetime import datetime, date
import statistics

# WMO Weather interpretation codes
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

def get_todays_weather_summary(weather_data):
    """Processes hourly weather data to create a summary for today's daylight hours."""
    if not weather_data or "hourly" not in weather_data:
        return "Weather data is incomplete."

    hourly = weather_data["hourly"]
    required_keys = ["time", "temperature_2m", "precipitation_probability", "weathercode"]
    for key in required_keys:
        if key not in hourly or not hourly[key]:
            return f"Missing or empty weather data for '{key}'."

    times = hourly["time"]
    temperatures = hourly["temperature_2m"]
    precip_probs = hourly["precipitation_probability"]
    weather_codes = hourly["weathercode"]

    daylight_temps = []
    daylight_precip_probs = []
    daylight_codes = []

    today_str = date.today().isoformat()

    for i, dt_str in enumerate(times):
        try:
            dt_obj = datetime.fromisoformat(dt_str)
            # Filter for today between 8 AM and 5 PM (17:00)
            if dt_obj.date() == date.today() and 8 <= dt_obj.hour <= 17:
                daylight_temps.append(temperatures[i])
                daylight_precip_probs.append(precip_probs[i])
                daylight_codes.append(weather_codes[i])
        except (ValueError, IndexError):
            continue # Skip malformed data points

    if not daylight_temps:
        return "Could not get a weather summary for today's daylight hours."

    # Calculate summary statistics
    try:
        avg_temp = round(statistics.mean(daylight_temps))
        max_precip = max(daylight_precip_probs)
        most_common_code = statistics.mode(daylight_codes)
        weather_description = WMO_CODES.get(most_common_code, "unknown weather")
    except statistics.StatisticsError:
        return "Could not calculate weather statistics due to insufficient data."

    summary = f"Today's forecast: {weather_description}, with an average temperature of {avg_temp}°C and a maximum precipitation probability of {max_precip}%."
    return summary

if __name__ == '__main__':
    # Example usage
    latitude = 52.52
    longitude = 13.41
    weather_data = get_weather(latitude, longitude)
    summary = get_todays_weather_summary(weather_data)
    print(summary)
