from ..services.weather_service import WeatherService
from typing import Dict, Any
from google.adk.tools.tool_context import ToolContext
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


weather_service = WeatherService(api_key=os.environ.get("WEATHER_API_KEY"))


async def get_weather_forecast(
        location: str,
        days: int = 5,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Fetch weather forecast (raw data) for the agent to process.

    Args:
        location (str): Location for weather forecast
        days (int): Number of days for forecast (1-10)
        tool_context (ToolContext): Optional session context

    Returns:
        Dict: Raw forecast data
    """
    if days < 1 or days > 10:
        return {"status": "error", "message": "Forecast days must be between 1 and 10"}

    forecast_data = await weather_service.get_forecast(location, days)

    # Optionally store in session state
    if tool_context and forecast_data.get("status") == "success":
        tool_context.state["last_weather_location"] = location
        tool_context.state["last_weather_forecast"] = forecast_data

    return forecast_data


async def get_current_weather(
        location: str,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Fetch current weather (raw data) for the agent to process.

    Args:
        location (str): Location for current weather
        tool_context (ToolContext): Optional session context

    Returns:
        Dict: Raw current weather data
    """
    weather_data = await weather_service.get_current_weather(location)

    # Optionally store in session state
    if tool_context and weather_data.get("status") == "success":
        tool_context.state["last_weather_location"] = location
        tool_context.state["last_current_weather"] = weather_data

    return weather_data
