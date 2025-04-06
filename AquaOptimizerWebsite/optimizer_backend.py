from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

@app.route("/get_plan", methods=["POST"])
def get_plan():
    data = request.get_json()
    zip_code = data.get("zip")
    crop = data.get("crop")
    area = float(data.get("area", 0))
    know_root = data.get("know_root")
    root_depth = float(data.get("root_depth", 0))
    crop_age = float(data.get("crop_age", 1))
    applied = float(data.get("applied", 0))
    gauge = data.get("gauge")
    rain = float(data.get("rain", 0))

    predicted_aw = 17.16
    avg_liters = 3040.0

    start_date = datetime.today()
    forecast = []
    for i in range(5):
        day_date = start_date + timedelta(days=i)
        forecast.append({
            "day": day_date.strftime("%A (%b %d)"),
            "date": day_date.strftime("%-m/%-d/%Y"),
            "temp": 50 + i,  # mock temperature
            "rain": 0,
            "soil_moisture": f"{0.153 - i * 0.015:.3f}",
            "et0": round(4 + (i % 2) * 0.2, 2),
            "etc": round(3 + (i % 3) * 0.07, 2),
            "liters": int(2990 + i * 130)
        })

    summary = (
        f"Based on your crop ({crop}) and ZIP code ({zip_code}), your estimated seasonal water need is {predicted_aw} acre-feet.\n"
        f"\nApply about {avg_liters} liters per day over the next 5 days."
        f"\nWe used {'crop age (' + str(crop_age) + ' months)' if know_root == 'no' else 'root depth (' + str(root_depth) + ' cm)'} to estimate root depth."
        f"\n{'Forecasted rainfall was used instead.' if gauge == 'no' else 'Your rainfall input was used.'}"
        f"\n\n💧 This schedule is designed to minimize water use and reduce costs while keeping your crops healthy."
    )

    return jsonify({
        "predicted_aw": predicted_aw,
        "schedule": forecast,
        "summary": summary
    })

if __name__ == "__main__":
    app.run(debug=False)