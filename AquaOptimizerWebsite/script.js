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
  const weatherDiv = document.querySelector(".weather p");
  let output = "";

  if (!data.list) {
    weatherDiv.innerHTML = "⚠️ Unable to retrieve forecast. Check zip code.";
    return;
  }

  // Get forecast every 24 hours (8 intervals of 3 hours each)
  for (let i = 0; i < data.list.length; i += 8) {
    const date = new Date(data.list[i].dt * 1000).toLocaleDateString();
    const temp = data.list[i].main.temp;
    const rain = data.list[i].rain?.["3h"] || 0;

    output += `${date}: 🌡️ ${temp}°C | 🌧️ ${rain} mm<br>`;
  }

  weatherDiv.innerHTML = output;
}
