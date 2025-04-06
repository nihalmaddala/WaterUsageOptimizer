import pandas as pd
import requests
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Load and prepare model data
df = pd.read_csv("All_data_dwr.csv")
df = df.dropna(subset=["AW", "Total_Land1", "Crop"])
df = pd.get_dummies(df, columns=["Crop"])
df["avg_temp"] = 25
df["avg_humidity"] = 50
df["total_rain"] = 0

features = ["Total_Land1", "avg_temp", "avg_humidity", "total_rain"] + \
           [col for col in df.columns if col.startswith("Crop_")]
X = df[features]
y = df["AW"]
model = LinearRegression().fit(X, y)

# Constants
Kc = {
    "Tomato": 1.05, "Almond": 0.75, "Grape": 0.65, "Citrus": 0.8,
    "Lettuce": 1.0, "Corn": 0.95, "Spinach": 1.1
}
Roots = {
    "Tomato": 30, "Almond": 120, "Grape": 100, "Citrus": 100,
    "Lettuce": 20, "Corn": 80, "Spinach": 25
}
ET0 = [4.0, 4.2, 4.1, 4.3, 4.0]  # Fixed ET₀ values (mm/day)

API_KEY = "f93ee9efeaaa0f31307a3f03995e4a3a"  # 🔁 Replace with real key

@app.route("/get_plan", methods=["POST"])
def get_plan():
    try:
        print("✅ /get_plan received")
        data = request.json
        print("📥 Input:", data)

        crop = data["crop"]
        area = float(data["area"])
        zip_code = data["zip"]
        know_root = data["know_root"]
        root_depth = float(data.get("root_depth", 0))
        age = float(data.get("crop_age", 1))
        applied = float(data.get("applied", 0))
        rain_today = float(data.get("rain", 0)) if data.get("gauge") == "yes" else 0

        kc = Kc.get(crop, 1.0)
        root_cm = root_depth if know_root == "yes" else min(Roots[crop] * (age / 12), Roots[crop])
        root_m = root_cm / 100

        # Get location coordinates
        geo = requests.get(
            f"https://api.openweathermap.org/geo/1.0/zip?zip={zip_code},US&appid={API_KEY}"
        ).json()
        lat, lon = geo["lat"], geo["lon"]

        # Get weather forecast
        weather = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        ).json()
        tmax = weather["daily"]["temperature_2m_max"]
        tmin = weather["daily"]["temperature_2m_min"]
        rain = weather["daily"]["precipitation_sum"]

        avg_temp = sum([(a + b) / 2 for a, b in zip(tmax, tmin)]) / 5
        total_rain = sum(rain[:5])
        rain_input = [rain_today] + rain[1:5]

        # Predict AW
        row = {
            "Total_Land1": area,
            "avg_temp": avg_temp,
            "avg_humidity": 50,
            "total_rain": total_rain
        }
        for col in [c for c in df.columns if c.startswith("Crop_")]:
            row[col] = 1 if col == f"Crop_{crop}" else 0

        input_df = pd.DataFrame([row])
        pred_aw = model.predict(input_df)[0]
        aw_liters = pred_aw * 1233.5 * area  # acre-ft to liters (per hectare)

        # Build 5-day schedule
        today = datetime.now()
        day_labels = [(today + timedelta(days=i)).strftime("%A (%b %d)") for i in range(5)]

        schedule = []
        for i in range(5):
            etc = ET0[i] * kc
            eff_rain = rain_input[i] * 0.75
            net_mm = max(0, etc - eff_rain)
            base = (net_mm * area) - (applied if i == 0 else 0)
            liters = max(0, min(base, aw_liters / 5))
            schedule.append({
                "day": day_labels[i],
                "et0": round(ET0[i], 1),
                "etc": round(etc, 2),
                "rain": round(rain_input[i], 2),
                "liters": round(liters, 1)
            })

        # Summary text
        avg_liters = round(sum([d["liters"] for d in schedule]) / 5, 1)
        summary_text = (
            f"Based on your crop ({crop}) and ZIP code ({zip_code}), your estimated seasonal water need is "
            f"{round(pred_aw, 2)} acre-feet.\n\n"
            f"Apply about {avg_liters} liters per day over the next 5 days.\n"
            f"{'We used your provided root depth.' if know_root == 'yes' else f'We used crop age ({age} months) to estimate root depth.'}\n"
            f"{'Rainfall from your gauge was factored in.' if data.get('gauge') == 'yes' else 'Forecasted rainfall was used instead.'}\n\n"
            f"💧 This schedule is designed to minimize water use and reduce costs while keeping your crops healthy."
        )

        print("✅ Prediction complete.")
        return jsonify({
            "predicted_aw": round(pred_aw, 3),
            "schedule": schedule,
            "summary": summary_text
        })

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False)
