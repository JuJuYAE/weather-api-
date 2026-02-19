import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from helpers import playable_conditions, tennis_telegram_summary


load_dotenv()

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)


CHAT_ID = os.getenv("CHAT_ID")  
NEWHAM_LAT = float(os.getenv("NEWHAM_LAT"))
NEWHAM_LON = float(os.getenv("NEWHAM_LON"))


url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": NEWHAM_LAT,
	"longitude":NEWHAM_LON,
	"daily": ["sunrise", "sunset"],
	"hourly": ["temperature_2m", "apparent_temperature", "precipitation_probability", "rain", "weather_code", "wind_speed_10m", "wind_gusts_10m"],
    "forecast_days": 14,
	"timezone": "auto",
}
responses = openmeteo.weather_api(url, params=params)
response = responses[0]


# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_apparent_temperature = hourly.Variables(1).ValuesAsNumpy()
hourly_precipitation_probability = hourly.Variables(2).ValuesAsNumpy()
hourly_rain = hourly.Variables(3).ValuesAsNumpy()
hourly_weather_code = hourly.Variables(4).ValuesAsNumpy()
hourly_wind_speed_10m = hourly.Variables(5).ValuesAsNumpy()
hourly_wind_gusts_10m = hourly.Variables(6).ValuesAsNumpy()



hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	end =  pd.to_datetime(hourly.TimeEnd() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["apparent_temperature"] = hourly_apparent_temperature
hourly_data["precipitation_probability"] = hourly_precipitation_probability
hourly_data["rain"] = hourly_rain
hourly_data["weather_code"] = hourly_weather_code
hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
hourly_data["wind_gusts_10m"] = hourly_wind_gusts_10m

hourly_dataframe = pd.DataFrame(data = hourly_data)

playable_filter = hourly_dataframe.apply(playable_conditions, axis = 1)

playable_times = hourly_dataframe[playable_filter]


summary_text = tennis_telegram_summary(playable_times)   # df_playable = your filtered dataframe




async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("Missing TELEGRAM_TOKEN environment variable")

    bot = Bot(token=token)

    summary_text = tennis_telegram_summary(playable_times)

    await bot.send_message(
        chat_id=CHAT_ID,
        text=summary_text,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )

if __name__ == "__main__":
    asyncio.run(main())
