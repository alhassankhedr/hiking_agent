import requests

def get_weather(latitude, longitude):
    """
    Fetches hourly weather forecast data from the Open-Meteo API.

    Retrieves temperature, precipitation probability, and weather codes
    for the specified location. The API provides hourly forecasts for
    the next several days.

    Args:
        latitude (float): The latitude coordinate (-90 to 90).
        longitude (float): The longitude coordinate (-180 to 180).

    Returns:
        dict or None: A dictionary containing the API response with weather data.
            The response includes 'hourly' key with 'time', 'temperature_2m',
            'precipitation_probability', and 'weathercode' arrays.
            Returns None if coordinates are invalid or if the API request fails.

    Raises:
        No exceptions are raised. All errors are caught and None is returned.
    """
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return None
    except (ValueError, TypeError):
        return None
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,precipitation_probability,weathercode"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching weather data: {e}")
        return None

from datetime import datetime, date
import statistics

# WMO Weather interpretation codes (World Meteorological Organization)
# Maps numeric weather codes to human-readable descriptions
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
    """
    Processes hourly weather data to create a concise summary for today's daylight hours.

    Filters weather data for today between 8 AM and 5 PM, calculates average
    temperature, maximum precipitation probability, and determines the most
    common weather condition. Returns a formatted string summary.

    Args:
        weather_data (dict): The raw weather data from the Open-Meteo API.
            Expected to contain a 'hourly' key with 'time', 'temperature_2m',
            'precipitation_probability', and 'weathercode' arrays.

    Returns:
        str: A human-readable summary string describing today's weather forecast
            during daylight hours (8 AM - 5 PM). Includes weather description,
            average temperature in Celsius, and maximum precipitation probability.
            Returns an error message string if data is unavailable or invalid.

    Example:
        >>> weather_data = {'hourly': {'time': [...], 'temperature_2m': [...]}}
        >>> summary = get_todays_weather_summary(weather_data)
        >>> print(summary)
        "Today's forecast: Partly cloudy, with an average temperature of 22°C
         and a maximum precipitation probability of 15%."
    """
    if not weather_data or not isinstance(weather_data, dict):
        return "Could not get a weather summary for today's daylight hours."
    
    try:
        hourly = weather_data.get("hourly", {})
        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        precip_probs = hourly.get("precipitation_probability", [])
        weather_codes = hourly.get("weathercode", [])

        daylight_temps = []
        daylight_precip_probs = []
        daylight_codes = []
        today = date.today()

        for i, dt_str in enumerate(times):
            try:
                if isinstance(dt_str, str):
                    dt_obj = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                    if dt_obj.date() == today and 8 <= dt_obj.hour <= 17:
                        if i < len(temperatures) and temperatures[i] is not None:
                            daylight_temps.append(temperatures[i])
                        if i < len(precip_probs) and precip_probs[i] is not None:
                            daylight_precip_probs.append(precip_probs[i])
                        if i < len(weather_codes) and weather_codes[i] is not None:
                            daylight_codes.append(weather_codes[i])
            except (ValueError, IndexError):
                continue

        if not daylight_temps:
            return "Could not get a weather summary for today's daylight hours."

        avg_temp = round(statistics.mean(daylight_temps))
        max_precip = max(daylight_precip_probs) if daylight_precip_probs else 0
        try:
            most_common_code = statistics.mode(daylight_codes)
        except statistics.StatisticsError:
            most_common_code = daylight_codes[0] if daylight_codes else 0
        weather_description = WMO_CODES.get(most_common_code, "unknown weather")

        return f"Today's forecast: {weather_description}, with an average temperature of {avg_temp}°C and a maximum precipitation probability of {max_precip}%."
    except Exception:
        return "Could not get a weather summary for today's daylight hours."

if __name__ == '__main__':
    # Example usage
    latitude = 52.52
    longitude = 13.41
    weather_data = get_weather(latitude, longitude)
    summary = get_todays_weather_summary(weather_data)
    print(summary)
