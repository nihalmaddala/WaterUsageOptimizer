const API_KEY = "f93ee9efeaaa0f31307a3f03995e4a3a";

// Tooltip text for each crop
const cropTooltips = {
  tomato: "Tomatoes need consistent moisture. Low soil moisture can lead to cracking and poor fruit quality.",
  almond: "Almonds are drought-tolerant but need regular moisture during nut development.",
  grape: "Grapes benefit from drier soil to concentrate flavor, but need watering during flowering and fruit set."
};

// Ideal soil moisture ranges (m³/m³)
const cropMoistureRanges = {
  tomato: { min: 0.20, max: 0.30 },
  almond: { min: 0.15, max: 0.25 },
  grape:  { min: 0.10, max: 0.20 }
};

// Get tooltip based on selected crop
function getCropTooltip() {
  const cropSelect = document.getElementById("crop");
  const cropValue = cropSelect.value;
  return cropTooltips[cropValue] || "Soil moisture helps determine how much irrigation is needed.";
}

// Check if soil moisture is ideal for the selected crop
function isMoistureIdeal(crop, value) {
  const range = cropMoistureRanges[crop];
  if (!range) return null;
  return value >= range.min && value <= range.max;
}

// Format the ideal moisture range as a string
function formatRange(crop) {
  const range = cropMoistureRanges[crop];
  if (!range) return "N/A";
  return `${range.min.toFixed(2)}–${range.max.toFixed(2)} m³/m³`;
}

// Return user-friendly moisture status message
function getMoistureMessage(crop, value) {
  const range = cropMoistureRanges[crop];
  if (!range) return "";
  if (value < range.min) return "⚠️ Too Dry";
  if (value > range.max) return "⚠️ Too Wet";
  return "✅ Optimal";
}

// Main function to fetch and display weather + soil
async function getWeather() {
  const zipInput = document.getElementById("location").value || "95340";

  const geoUrl = `https://api.openweathermap.org/geo/1.0/zip?zip=${zipInput},US&appid=${API_KEY}`;
  const geoResponse = await fetch(geoUrl);
  const geoData = await geoResponse.json();
  const lat = geoData.lat;
  const lon = geoData.lon;

  const [weatherRes, soilRes] = await Promise.all([
    fetch(`https://api.openweathermap.org/data/2.5/forecast?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`),
    fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&hourly=soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm&timezone=auto`)
  ]);

  const weatherData = await weatherRes.json();
  const soilData = await soilRes.json();

  displayForecastWithSoil(weatherData, soilData);
}

// Display combined forecast + soil data
function displayForecastWithSoil(weatherData, soilData) {
  const forecastGrid = document.getElementById("forecastGrid");
  forecastGrid.innerHTML = "";

  const time = soilData.hourly?.time;
  const layer0 = soilData.hourly?.soil_moisture_0_to_1cm;
  const layer1 = soilData.hourly?.soil_moisture_1_to_3cm;
  const layer2 = soilData.hourly?.soil_moisture_3_to_9cm;

  for (let i = 0; i < weatherData.list.length && i / 8 < 5; i += 8) {
    const dateObj = new Date(weatherData.list[i].dt * 1000);
    const day = dateObj.toLocaleDateString("en-US", { weekday: "short" });
    const date = dateObj.toLocaleDateString("en-CA"); // YYYY-MM-DD
    const temp = Math.round(weatherData.list[i].main.temp * 10) / 10;
    const rain = weatherData.list[i].rain?.["3h"] || 0;

    let avgSoil = "N/A";
    let idealStatus = "";
    let avgFloat = null;
    const cropSelect = document.getElementById("crop");
    const crop = cropSelect.value;

    if (time) {
      const matchIndex = time.findIndex(t => t.startsWith(date));
      if (matchIndex !== -1) {
        const sm0 = layer0[matchIndex] || 0;
        const sm1 = layer1[matchIndex] || 0;
        const sm2 = layer2[matchIndex] || 0;
        avgFloat = (sm0 + sm1 + sm2) / 3;
        avgSoil = avgFloat.toFixed(3) + " m³/m³";

        const isIdeal = isMoistureIdeal(crop, avgFloat);
        idealStatus = isIdeal === null ? "" : (isIdeal ? " ✅" : " ❌");
      }
    }

    const moistureRangeText = crop ? `Ideal: ${formatRange(crop)}` : "";
    const moistureStatusText = (avgFloat !== null && crop)
      ? getMoistureMessage(crop, avgFloat)
      : "";

    const card = document.createElement("div");
    card.className = "forecast-card";
    card.innerHTML = `
      <strong>${day}</strong><br>${dateObj.toLocaleDateString()}<br>
      🌡️ ${temp}°C<br>
      🌧️ ${rain} mm
      <div class="soil">
        <span style="display: block; font-size: 0.85rem; color: #555;">
  Soil Moisture 
  <span title="${getCropTooltip()} (Ideal: ${formatRange(crop)})">ℹ️</span>
</span>
        🌱 ${avgSoil}${idealStatus}<br>
        
        <span class="moisture-status">${moistureStatusText}</span>
      </div>
    `;
    forecastGrid.appendChild(card);
  }
}
