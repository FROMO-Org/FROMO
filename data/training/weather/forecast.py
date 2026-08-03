"""Live Open-Meteo forecast fetch for the daily production job, using the
same coordinate from config.py as historical.py - closing the legacy
mismatch where training and live inference silently used two different
points.
"""

import pandas as pd
import requests

import config


def fetch_forecast(days: int = 2) -> pd.DataFrame:
    """Hourly weather forecast at the pipeline's single configured
    coordinate, via Open-Meteo's forecast API. `days` includes today."""
    params = {
        "latitude": config.WEATHER_LATITUDE,
        "longitude": config.WEATHER_LONGITUDE,
        "hourly": ",".join(config.WEATHER_HOURLY_FIELDS),
        "timezone": config.WEATHER_TIMEZONE,
        "forecast_days": days,
    }
    response = requests.get(config.WEATHER_FORECAST_URL, params=params, timeout=60)
    response.raise_for_status()
    hourly = response.json()["hourly"]
    df = pd.DataFrame(hourly)
    df[config.COL_HOUR] = pd.to_datetime(df["time"])
    return df.drop(columns="time")


def get_tomorrow_local_range() -> tuple[pd.Timestamp, pd.Timestamp]:
    """[start, end] hourly timestamps for tomorrow in the configured local
    timezone - shared with modeling/predict.py so the prediction grid and
    the fetched weather always refer to the exact same 24 hours."""
    today_local = pd.Timestamp.now(tz=config.WEATHER_TIMEZONE).normalize().tz_localize(None)
    start = today_local + pd.Timedelta(days=1)
    end = start + pd.Timedelta(hours=23)
    return start, end


def fetch_tomorrow() -> pd.DataFrame:
    """The 24 hourly rows for tomorrow (in the configured local timezone) -
    the specific slice the daily production job predicts for."""
    forecast = fetch_forecast(days=2)
    start, end = get_tomorrow_local_range()
    mask = forecast[config.COL_HOUR].between(start, end)
    return forecast.loc[mask].reset_index(drop=True)
