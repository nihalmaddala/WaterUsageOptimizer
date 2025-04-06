import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weekly_forecast(city):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city},CA,US&limit=1&appid={API_KEY}"
    geo = requests.get(geo_url).json()
    if not geo:
        return None
    lat, lon = geo[0]["lat"], geo[0]["lon"]

    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,current,alerts&appid={API_KEY}&units=metric"
    res = requests.get(url).json()

    daily = res.get("daily", [])
    avg_temp = sum(day["temp"]["day"] for day in daily[:7]) / 7
    avg_humidity = sum(day["humidity"] for day in daily[:7]) / 7
    total_rain = sum(day.get("rain", 0) for day in daily[:7])

    return {
        "avg_temp": avg_temp,
        "avg_humidity": avg_humidity,
        "total_rain": total_rain
    }