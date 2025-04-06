import pandas as pd
import requests
import os
from sklearn.linear_model import LinearRegression
import warnings
import urllib.parse

# Optional: suppress SSL warning on Mac
warnings.filterwarnings("ignore", category=UserWarning)

# === Load and clean historical data ===
df = pd.read_csv("All_data_dwr.csv")
df.columns = df.columns.str.strip()
df = df.dropna(subset=["AW", "Total_Land1", "Crop"])

# === Crop mappings and average land ===
county_crop_map = df.groupby("NAME")["Crop"].unique().to_dict()
county_crop_land = df.groupby(["NAME", "Crop"])["Total_Land1"].mean().to_dict()

# === One-hot encode crops ===
df = pd.get_dummies(df, columns=["Crop"])

# === Add dummy weather & soil features ===
df["avg_temp"] = 25
df["avg_humidity"] = 50
df["total_rain"] = 0
df["soil_moisture"] = 0.4

# === Feature prep ===
features = ["Total_Land1", "avg_temp", "avg_humidity", "total_rain", "soil_moisture"] + \
           [col for col in df.columns if col.startswith("Crop_")]
X = df[features]
y = df["AW"]

# === Train model ===
model = LinearRegression()
model.fit(X, y)

# === Function: Get 7-day weather + soil from Open-Meteo ===
def get_weather_and_soil(city):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&country=US&count=1"
    geo_res = requests.get(geo_url).json()

    print(f"[DEBUG] Geocoding URL: {geo_url}")
    print(f"[DEBUG] Geocoding response: {geo_res}")

    if not geo_res.get("results"):
        print(f"[SKIP] Geocoding failed for city {city}")
        return None

    lat = geo_res["results"][0]["latitude"]
    lon = geo_res["results"][0]["longitude"]

    # Removed soil_moisture_0_10cm_mean to avoid breaking the request
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&timezone=America/Los_Angeles"
    )

    print(f"[DEBUG] Weather URL: {weather_url}")
    weather_res = requests.get(weather_url).json()
    print(f"[DEBUG] Weather response: {weather_res}")

    daily = weather_res.get("daily", {})
    if not daily:
        print(f"[SKIP] Weather forecast missing for city {city}")
        return None

    temps = [(tmin + tmax) / 2 for tmin, tmax in zip(daily["temperature_2m_min"], daily["temperature_2m_max"])]
    avg_temp = sum(temps[:7]) / 7
    total_rain = sum(daily["precipitation_sum"][:7])
    avg_soil_moisture = 0.35  # Still simulate this part

    return {
        "avg_temp": avg_temp,
        "avg_humidity": 50,
        "total_rain": total_rain,
        "soil_moisture": avg_soil_moisture
    }


# === Function: Process Farmer Input and Compare ===
def process_farmer_data(farmer_csv):
    farmer_df = pd.read_csv(farmer_csv)
    farmer_df.columns = farmer_df.columns.str.strip().str.title()

    crop_columns = [col for col in df.columns if col.startswith("Crop_")]
    results = []

    for _, row in farmer_df.iterrows():
        crop = row.get("Crop")
        city = row.get("City")
        year = row.get("Year")
        total_water = row.get("Total_Water")
        total_land = row.get("Total_Land")

        if not all([crop, city, total_water, total_land]):
            print(f"[SKIP] Missing data in row: {row}")
            continue

        actual_aw = total_water / total_land
        forecast = get_weather_and_soil(city)

        if not forecast:
            print(f"[SKIP] Could not fetch data for city {city}")
            continue

        input_row = {
            "Total_Land1": total_land,
            "avg_temp": forecast["avg_temp"],
            "avg_humidity": forecast["avg_humidity"],
            "total_rain": forecast["total_rain"],
            "soil_moisture": forecast["soil_moisture"]
        }

        for col in crop_columns:
            input_row[col] = 1 if col == f"Crop_{crop}" else 0

        input_df = pd.DataFrame([input_row])
        predicted_aw = model.predict(input_df)[0]

        error = actual_aw - predicted_aw
        adjusted_aw = predicted_aw + 0.2 * error

        results.append({
            "Crop": crop,
            "City": city,
            "Year": year,
            "Actual_AW": actual_aw,
            "Predicted_AW": predicted_aw,
            "Adjusted_AW": adjusted_aw,
            "Rainfall": forecast["total_rain"],
            "Soil_Moisture": forecast["soil_moisture"]
        })

    result_df = pd.DataFrame(results)
    result_df.to_csv("adjusted_aw_output.csv", index=False)
    print("✅ Saved: adjusted_aw_output.csv")
#holymoly guacomoly
# === Run the prediction pipeline ===
process_farmer_data("farmer_input.csv")
