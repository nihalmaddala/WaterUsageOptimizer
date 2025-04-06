import pandas as pd
import requests
import openmeteo_requests
import requests_cache
from retry_requests import retry
import os
from dotenv import load_dotenv
import warnings
from sklearn.linear_model import LinearRegression

warnings.filterwarnings("ignore", category=UserWarning)
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Setup Open-Meteo client
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# === Helper functions ===
def get_lat_lon(city):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&country=US&count=1"
    res = requests.get(geo_url).json()
    if res.get("results"):
        lat = res["results"][0]["latitude"]
        lon = res["results"][0]["longitude"]
        return lat, lon
    return None, None

def train_model():
    df = pd.read_csv("All_data_dwr.csv")
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["AW", "Total_Land1", "Crop"])
    df = pd.get_dummies(df, columns=["Crop"])
    df["avg_temp"] = 68
    df["total_rain"] = 0
    df["soil_moisture"] = 0.2
    features = ["total_rain", "avg_temp", "soil_moisture"]
    X = df[features]
    y = df["AW"]
    model = LinearRegression().fit(X, y)
    return model

def get_forecast_with_soil(city):
    lat, lon = get_lat_lon(city)
    if not lat or not lon:
        print(f"[SKIP] Could not geocode {city}")
        return None

    # === OpenWeather for rainfall ===
    ow_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,current,alerts&appid={API_KEY}&units=metric"
    ow_data = requests.get(ow_url).json()
    rain_by_day = [day.get("rain", 0) for day in ow_data.get("daily", [])[:7]]

    # === Open-Meteo for soil and temperature ===
    om_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "hourly": ["soil_moisture_0_to_1cm"],
        "temperature_unit": "fahrenheit",
        "timezone": "auto"
    }

    responses = openmeteo.weather_api(om_url, params=params)
    response = responses[0]

    # Daily temp
    daily = response.Daily()
    temps_max = daily.Variables(0).ValuesAsNumpy()
    temps_min = daily.Variables(1).ValuesAsNumpy()
    dates = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()), inclusive="left"
    ).date
    avg_temps = [(temps_max[i] + temps_min[i]) / 2 for i in range(len(temps_max))]

    # Hourly soil moisture
    hourly = response.Hourly()
    soil = hourly.Variables(0).ValuesAsNumpy()
    soil_avg_per_day = [soil[i*24:(i+1)*24].mean() for i in range(min(7, len(dates)))]

    return {
        "dates": dates,
        "temps": avg_temps,
        "soils": soil_avg_per_day,
        "rain": rain_by_day
    }

def predict_daily_aw(csv_file):
    df = pd.read_csv(csv_file)
    model = train_model()
    results = []

    for _, row in df.iterrows():
        crop = row["Crop"]
        city = row["City"]

        forecast = get_forecast_with_soil(city)
        if not forecast:
            continue

        for i in range(min(7, len(forecast["dates"]))):
            X_input = pd.DataFrame([{
                "total_rain": forecast["rain"][i] if i < len(forecast["rain"]) else 0,
                "avg_temp": forecast["temps"][i],
                "soil_moisture": forecast["soils"][i]
            }])
            pred_aw = model.predict(X_input)[0]

            results.append({
                "Crop": crop,
                "City": city,
                "Date": forecast["dates"][i],
                "Predicted_AW_Day": round(pred_aw, 3),
                "Rainfall_mm": forecast["rain"][i] if i < len(forecast["rain"]) else 0,
                "Temperature_F": forecast["temps"][i],
                "Soil_Moisture": round(forecast["soils"][i], 3)
            })

    pd.DataFrame(results).to_csv("daily_aw_schedule.csv", index=False)
    print("✅ Saved: daily_aw_schedule.csv")

# === Run ===
predict_daily_aw("farmer_input.csv")
