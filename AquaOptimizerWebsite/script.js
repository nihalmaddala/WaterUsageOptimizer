// script.js
//lying for fun
const API_KEY = "f93ee9efeaaa0f31307a3f03995e4a3a";

async function getWeather() {
  const zipInput = document.getElementById("location").value || "95340";

  // Step 1: Get lat/lon from zip
  const geoUrl = `https://api.openweathermap.org/geo/1.0/zip?zip=${zipInput},US&appid=${API_KEY}`;
  const geoResponse = await fetch(geoUrl);
  const geoData = await geoResponse.json();
  const lat = geoData.lat;
  const lon = geoData.lon;

  // Step 2: Get weather from OpenWeather
  const weatherUrl = `https://api.openweathermap.org/data/2.5/forecast?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`;
  try {
    const weatherResponse = await fetch(weatherUrl);
    const weatherData = await weatherResponse.json();
    displayForecast(weatherData);
  } catch (error) {
    console.error("Error fetching weather data:", error);
  }

  // Step 3: Get hourly soil moisture from Open-Meteo
  const soilUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&hourly=soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm&timezone=auto`;
  try {
    const soilResponse = await fetch(soilUrl);
    const soilData = await soilResponse.json();
    displayHourlySoilMoisture(soilData);
  } catch (error) {
    console.error("Error fetching soil moisture data:", error);
  }
}

function displayForecast(data) {
  const forecastGrid = document.getElementById("forecastGrid");
  forecastGrid.innerHTML = "";

  if (!data.list) {
    forecastGrid.innerHTML = "<p>⚠️ Unable to retrieve forecast. Check zip code.</p>";
    return;
  }

  for (let i = 0; i < data.list.length; i += 8) {
    const date = new Date(data.list[i].dt * 1000);
    const dayName = date.toLocaleDateString("en-US", { weekday: "short" });
    const formattedDate = date.toLocaleDateString();
    const temp = Math.round(data.list[i].main.temp * 10) / 10;
    const rain = data.list[i].rain?.["3h"] || 0;

    const card = document.createElement("div");
    card.className = "forecast-card";
    card.innerHTML = `
      <strong>${dayName}</strong><br>${formattedDate}<br>
      🌡️ ${temp}°C<br>
      🌧️ ${rain} mm
    `;
    forecastGrid.appendChild(card);
  }
}

function displayHourlySoilMoisture(data) {
  const container = document.querySelector(".container");
  let soilDiv = document.querySelector(".soil-moisture");

  if (!soilDiv) {
    soilDiv = document.createElement("div");
    soilDiv.className = "soil-moisture";
    soilDiv.innerHTML = `
      <h3>🌱 Soil Moisture (Hourly, Top Layers)</h3>
      <div id="soilData"></div>
    `;
    container.insertBefore(soilDiv, document.querySelector(".recommendation"));
  }

  const time = data.hourly?.time;
  const layer0 = data.hourly?.soil_moisture_0_to_1cm;
  const layer1 = data.hourly?.soil_moisture_1_to_3cm;
  const layer2 = data.hourly?.soil_moisture_3_to_9cm;
  const layer3 = data.hourly?.soil_moisture_9_to_27cm;

  const soilDataDiv = document.getElementById("soilData");

  if (!time || !layer0 || !layer0.length) {
    soilDataDiv.innerHTML = "⚠️ No soil moisture data available for this location.";
    return;
  }

  let output = "";
  for (let i = 0; i < time.length && i < 24 * 5; i += 24) {
    output += `<strong>${time[i].split("T")[0]}</strong><br>`;
    output += `0–1cm: ${layer0[i]?.toFixed(3)} m³/m³<br>`;
    output += `1–3cm: ${layer1[i]?.toFixed(3)} m³/m³<br>`;
    output += `3–9cm: ${layer2[i]?.toFixed(3)} m³/m³<br>`;
    output += `9–27cm: ${layer3[i]?.toFixed(3)} m³/m³<br><br>`;
  }

  soilDataDiv.innerHTML = output;
}
