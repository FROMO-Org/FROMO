"""Historical Open-Meteo fetch for the training feature set, using the
single coordinate defined in config.py - the same coordinate forecast.py
uses for live inference, so training and production can never silently
diverge the way the legacy pipeline's two different coordinates did.

The result is cached to disk (config.WEATHER_HISTORICAL_CACHE_PATH) rather
than re-fetched on every pipeline run: Open-Meteo's historical archive is a
reanalysis product that can itself be revised after publication, so a later
re-run should only pick up different weather values if a re-fetch is
explicitly requested, not silently on every invocation.
"""

import logging

import pandas as pd
import requests

import config

logger = logging.getLogger(__name__)


def fetch_historical(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Hourly weather for [start, end] at the pipeline's single configured
    coordinate, via Open-Meteo's historical archive API."""
    params = {
        "latitude": config.WEATHER_LATITUDE,
        "longitude": config.WEATHER_LONGITUDE,
        "start_date": start.date().isoformat(),
        "end_date": end.date().isoformat(),
        "hourly": ",".join(config.WEATHER_HOURLY_FIELDS),
        "timezone": config.WEATHER_TIMEZONE,
    }
    response = requests.get(config.WEATHER_ARCHIVE_URL, params=params, timeout=60)
    response.raise_for_status()
    hourly = response.json()["hourly"]
    df = pd.DataFrame(hourly)
    df[config.COL_HOUR] = pd.to_datetime(df["time"])
    return df.drop(columns="time")


def get_full_history(force_refetch: bool = False) -> pd.DataFrame:
    if not force_refetch and config.WEATHER_HISTORICAL_CACHE_PATH.exists():
        df = pd.read_csv(config.WEATHER_HISTORICAL_CACHE_PATH)
        df[config.COL_HOUR] = pd.to_datetime(df[config.COL_HOUR])
        return df

    start, end = config.get_full_date_range()
    df = fetch_historical(start, end)
    config.WEATHER_HISTORICAL_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.WEATHER_HISTORICAL_CACHE_PATH, index=False)
    logger.info("Fetched and cached %d hours of historical weather", len(df))
    return df
