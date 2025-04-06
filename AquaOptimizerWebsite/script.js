// === Crop moisture data logic ===

function populateCropDropdown(data) {
  const cropSelect = document.getElementById("crop");
  data.forEach(crop => {
    const option = document.createElement("option");
    option.value = crop.cropname;
    option.textContent = crop.cropname;
    cropSelect.appendChild(option);
  });
}
populateCropDropdown(cropMoistureData);

function getCropTooltip(cropName) {
  const match = cropMoistureData.find(c => c.cropname === cropName);
  return match ? match.description : "Soil moisture guidance not available.";
}

function formatRange(cropName) {
  const match = cropMoistureData.find(c => c.cropname === cropName);
  return match ? `${parseFloat(match.low).toFixed(2)}–${parseFloat(match.high).toFixed(2)} m³/m³` : "N/A";
}

function isMoistureIdeal(cropName, value) {
  const match = cropMoistureData.find(c => c.cropname === cropName);
  if (!match) return null;
  const min = parseFloat(match.low);
  const max = parseFloat(match.high);
  return value >= min && value <= max;
}

function getMoistureMessage(cropName, value) {
  const match = cropMoistureData.find(c => c.cropname === cropName);
  if (!match) return "";
  const min = parseFloat(match.low);
  const max = parseFloat(match.high);
  if (value < min) return "⚠️ Too Dry";
  if (value > max) return "⚠️ Too Wet";
  return "✅ Optimal";
}

// === Weather & Soil Logic ===

const API_KEY = "f93ee9efeaaa0f31307a3f03995e4a3a"; // Replace with your actual API key

async function getWeather() {
  document.querySelector('.recommendation').classList.remove("show");
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
    const date = dateObj.toLocaleDateString("en-CA");
    const celsius = weatherData.list[i].main.temp;
const fahrenheit = Math.round((celsius * 9) / 5 + 32);
    const rain = weatherData.list[i].rain?.["3h"] || 0;

    let avgSoil = "N/A";
    let idealStatus = "";
    let avgFloat = null;
    const crop = document.getElementById("crop").value;

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

    const moistureStatusText = (avgFloat !== null && crop)
      ? getMoistureMessage(crop, avgFloat)
      : "";

    const card = document.createElement("div");
    card.className = "forecast-card";
    card.innerHTML = `
      <strong>${day}</strong><br>${dateObj.toLocaleDateString()}<br>
      🌡️ ${fahrenheit}°F<br>
      🌧️ ${rain} mm
      <div class="soil">
        <span style="display: block; font-size: 0.85rem; color: #555;">
          Soil Moisture 
          <span title="${getCropTooltip(crop)} (Ideal: ${formatRange(crop)})">ℹ️</span>
        </span>
        🌱 ${avgSoil}${idealStatus}<br>
        <span class="moisture-status">${moistureStatusText}</span>
      </div>
    `;
    forecastGrid.appendChild(card);
  }
  document.querySelector('.recommendation').classList.add("show");
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("location").value = "95340";
  getWeather();
});


