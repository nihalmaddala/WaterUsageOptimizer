import pandas as pd
from sklearn.linear_model import LinearRegression
from weather_fetcher import get_weekly_forecast

# === Load and clean data ===
df = pd.read_csv("All_data_dwr.csv")
df.columns = df.columns.str.strip()
df = df.dropna(subset=["AW", "Total_Land1", "Crop"])

# === Save crop mapping and average land used per county+crop ===
county_crop_map = df.groupby("NAME")["Crop"].unique().to_dict()
county_crop_land = df.groupby(["NAME", "Crop"])["Total_Land1"].mean().to_dict()

# One-hot encode crops
df = pd.get_dummies(df, columns=["Crop"])

# Add placeholder weather values for training
df["avg_temp"] = 25
df["avg_humidity"] = 50
df["total_rain"] = 0

# Prepare training features
features = ["Total_Land1", "avg_temp", "avg_humidity", "total_rain"] + [col for col in df.columns if col.startswith("Crop_")]
X = df[features]
y = df["AW"]

# === Train model ===
model = LinearRegression()
model.fit(X, y)

# === Predict using real weather ===
counties = df["NAME"].unique()

for county in counties:
    forecast = get_weekly_forecast(county)
    if not forecast:
        print(f"[SKIP] Could not get forecast for {county}")
        continue

    crops = county_crop_map.get(county, [])
    for crop in crops:
        avg_land = county_crop_land.get((county, crop), 0)

        # Skip tiny land values (likely noise)
        if avg_land < 0.1:
            continue

        row = {
            "Total_Land1": avg_land,
            "avg_temp": forecast["avg_temp"],
            "avg_humidity": forecast["avg_humidity"],
            "total_rain": forecast["total_rain"]
        }

        # One-hot encode crops
        for col in [c for c in df.columns if c.startswith("Crop_")]:
            row[col] = 1 if col == f"Crop_{crop}" else 0

        # Predict
        pred_df = pd.DataFrame([row])
        predicted_aw = model.predict(pred_df)[0]

        print(f"[{county} - {crop}] ➤ Recommended AW: {predicted_aw:.2f} acre-feet for ~{avg_land:.3f} acres")
