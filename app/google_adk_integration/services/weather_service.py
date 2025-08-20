import httpx
from typing import Dict, Any
import logging
import asyncio

logger = logging.getLogger(__name__)


class WeatherService:
    """Real-time weather service integration using OpenWeatherMap API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.timeout = 10.0

    async def get_current_weather(self, location: str) -> Dict[str, Any]:
        """Fetch current weather for a given location"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'q': location,
                    'appid': self.api_key,
                    'units': 'metric'
                }
                response = await client.get(f"{self.base_url}/weather", params=params)
                response.raise_for_status()
                data = response.json()
                return self._format_current_weather(data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather for {location}: {e.response.text}")
            return {"status": "error", "message": "Failed to fetch current weather"}
        except Exception as e:
            logger.error(f"Error fetching weather for {location}: {e}")
            return {"status": "error", "message": "Failed to fetch current weather"}

    async def get_forecast(self, location: str, days: int = 5) -> Dict[str, Any]:
        """Fetch weather forecast for the next `days` days"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'q': location,
                    'appid': self.api_key,
                    'units': 'metric',
                    'cnt': min(days * 8, 40)  # OpenWeatherMap returns up to 40 intervals
                }
                response = await client.get(f"{self.base_url}/forecast", params=params)
                response.raise_for_status()
                data = response.json()
                return self._format_forecast(data, days)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching forecast for {location}: {e.response.text}")
            return {"status": "error", "message": "Failed to fetch weather forecast"}
        except Exception as e:
            logger.error(f"Error fetching forecast for {location}: {e}")
            return {"status": "error", "message": "Failed to fetch weather forecast"}

    def _format_current_weather(self, data: Dict) -> Dict[str, Any]:
        try:
            temp = round(data["main"]["temp"])
            humidity = data["main"]["humidity"]
            condition = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"]

            return {
                "status": "success",
                "location": data["name"],
                "country": data["sys"]["country"],
                "current": {
                    "temperature": temp,
                    "humidity": humidity,
                    "condition": condition,
                    "wind_speed": wind_speed,
                    "wind_direction": data["wind"].get("deg", 0),
                    "feels_like": round(data["main"]["feels_like"]),
                    "pressure": data["main"]["pressure"],
                    "icon": data["weather"][0]["icon"]
                },
                "farming_advice": self._generate_farming_advice(data)
            }
        except Exception as e:
            logger.error(f"Error formatting current weather data: {e}")
            return {"status": "error", "message": "Failed to format weather data"}

    def _format_forecast(self, data: Dict, days: int) -> Dict[str, Any]:
        try:
            forecasts = []
            current_date = None
            daily_data = {}

            for item in data["list"]:
                date = item["dt_txt"].split()[0]

                if date != current_date:
                    if current_date and daily_data:
                        forecasts.append(daily_data)

                    current_date = date
                    daily_data = {
                        "date": date,
                        "temp_max": item["main"]["temp_max"],
                        "temp_min": item["main"]["temp_min"],
                        "humidity": item["main"]["humidity"],
                        "condition": item["weather"][0]["description"],
                        "rain_chance": item.get("pop", 0) * 100,
                        "wind_speed": item["wind"]["speed"]
                    }
                else:
                    daily_data["temp_max"] = max(daily_data["temp_max"], item["main"]["temp_max"])
                    daily_data["temp_min"] = min(daily_data["temp_min"], item["main"]["temp_min"])
                    daily_data["rain_chance"] = max(daily_data["rain_chance"], item.get("pop", 0) * 100)

            if daily_data:
                forecasts.append(daily_data)

            return {
                "status": "success",
                "location": data["city"]["name"],
                "forecast": forecasts[:days],
                "farming_advice": self._generate_forecast_advice(forecasts[:days])
            }
        except Exception as e:
            logger.error(f"Error formatting forecast data: {e}")
            return {"status": "error", "message": "Failed to format forecast data"}

    def _generate_farming_advice(self, weather_data: Dict) -> str:
        temp = weather_data["main"]["temp"]
        humidity = weather_data["main"]["humidity"]
        condition = weather_data["weather"][0]["main"].lower()
        advice = []

        if "rain" in condition:
            advice.append("Heavy rain expected - ensure proper field drainage")
        if temp > 35:
            advice.append("High temperature - increase irrigation")
        if temp < 10:
            advice.append("Cold weather - protect crops from frost")
        if humidity > 80:
            advice.append("High humidity - monitor for fungal diseases")
        if humidity < 30:
            advice.append("Low humidity - ensure soil moisture")

        return " | ".join(advice) if advice else "Monitor crop conditions regularly"

    def _generate_forecast_advice(self, forecast: list) -> str:
        rain_days = sum(1 for day in forecast if day["rain_chance"] > 50)
        avg_temp = sum(day["temp_max"] for day in forecast) / len(forecast)
        advice = []

        if rain_days >= 3:
            advice.append("Multiple rainy days ahead - plan field activities accordingly")
        elif rain_days == 0:
            advice.append("Dry spell expected - ensure irrigation planning")
        if avg_temp > 30:
            advice.append("Hot weather ahead - monitor crop stress")
        elif avg_temp < 15:
            advice.append("Cool weather - adjust planting schedules")

        return " | ".join(advice) if advice else "Plan farming activities based on weather"



if __name__ == "__main__":
    import os
    async def main():
        service = WeatherService(api_key=os.environ.get("WEATHER_API_KEY"))
        location = "Mumbai"

        print("Fetching current weather...")
        current = await service.get_current_weather(location)
        print(current)

        print("\nFetching 5-day forecast...")
        forecast = await service.get_forecast(location, days=5)
        print(forecast)

    asyncio.run(main())
