"""Stacks the scored zone x hour panel with calendar features and weather,
producing the single modelling-ready features table. Drops all raw counts
and per-mode normalized columns before returning, so the trained model can
never trivially reconstruct its own target from a leftover intermediate
column.
"""

import holidays
import pandas as pd

import config
from weather import historical

# Open-Meteo's own field name differs from the model-facing feature name;
# the other three (apparent_temperature/precipitation/snowfall) already
# match config.FEATURE_COLUMNS as fetched.
WEATHER_RENAME = {"temperature_2m": "temperature"}


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df[config.COL_HOUR].dt.hour
    df["day_of_week"] = df[config.COL_HOUR].dt.dayofweek
    df["month"] = df[config.COL_HOUR].dt.month

    # `years=` must be passed explicitly: the holidays library populates its
    # internal date set lazily, only on a direct `in`/`.get()` lookup for a
    # given year. Series.isin() never performs that lookup, so isin() against
    # a freshly-constructed, never-queried HolidayBase silently returns False
    # for every date, even genuine holidays - verified directly: a fresh
    # object gave is_holiday=False for Memorial Day 2026 until an unrelated
    # single-date lookup happened to populate that year first.
    years = df[config.COL_HOUR].dt.year.unique().tolist()
    holiday_dates = holidays.country_holidays(
        config.HOLIDAY_COUNTRY, subdiv=config.HOLIDAY_SUBDIVISION, years=years
    )
    df["is_holiday"] = df[config.COL_HOUR].dt.date.isin(holiday_dates)
    return df


def add_weather_features(df: pd.DataFrame, weather: pd.DataFrame | None = None) -> pd.DataFrame:
    if weather is None:
        weather = historical.get_full_history()
    weather = weather.rename(columns=WEATHER_RENAME)
    return df.merge(weather, on=config.COL_HOUR, how="left")


def build_features(scored_panel: pd.DataFrame) -> pd.DataFrame:
    df = add_calendar_features(scored_panel)
    df = add_weather_features(df)

    non_zone_features = [c for c in config.FEATURE_COLUMNS if c != config.COL_ZONE]
    keep = [config.COL_ZONE, config.COL_HOUR, "busyness_score"] + non_zone_features
    return df[keep]
