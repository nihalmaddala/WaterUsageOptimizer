// script.js

const API_KEY = "9f2a9ab6a750066ee02915fa779054c6";

async function getWeather() {
  const zipInput = document.getElementById("location").value || "95340";
  const url = `https://api.openweathermap.org/data/2.5/forecast?zip=${zipInput},US&appid=${API_KEY}&units=metric`;

  try {
    const response = await fetch(url);
    const data = await response.json();
    displayForecast(data);
  } catch (error) {
    console.error("Error fetching weather data:", error);
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
