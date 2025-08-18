from ..tools.weather_tools import get_weather_forecast, get_current_weather
from google.adk.agents import Agent

def create_weather_agent() -> Agent:
    """
    Create a specialized agent for weather and climate advice.
    The agent receives raw weather data and generates farming recommendations dynamically.
    """

    instruction_text = """
    You are WeatherWise, an expert agricultural meteorologist.

    Your responsibilities:
    1. Receive raw weather data (current conditions and forecasts) from tools.
    2. Analyze the data in the context of the user's crops, location, and experience level.
    3. Generate actionable farming advice:
       • Irrigation scheduling
       • Pest and disease management
       • Crop operations (planting, spraying, harvesting)
       • Warnings for extreme weather (heat, frost, rain)
    4. Present advice in clear, simple language that farmers can follow.
    5. Adapt advice for multiple crops, and integrate multi-domain factors if relevant.
    """

    return Agent(
        name="weather_specialist",
        model="gemini-2.0-flash",
        description="Expert in agricultural meteorology and weather-based farming recommendations",
        instruction=instruction_text,
        tools=[get_weather_forecast, get_current_weather],
        output_key="last_weather_advice"
    )
