"""Does a known, obtainable event signal (Madison Square Garden sports
events) contain information about busyness_score that the current feature
set (hour/day_of_week/month/is_holiday/weather/zone) does NOT already
capture? A concrete, measured answer, not an assumption - this is the
evidence for or against spending effort building an events feature.

Method: MSG is entirely inside zone 186 (Penn Station/Madison Sq West).
For every hour in that zone's full history, compute deviation-from-norm
(actual busyness_score minus the production norm_table lookup - a
descriptive measure, not a leakage-safe training target, since nothing
here is used to train anything). Compare mean deviation on event hours vs
non-event hours - then repeat the comparison RESTRICTED to the same
hour-of-day range MSG events occur in (evening, 19-22h), which isolates
the incremental effect of "an event is happening" from the already-known
"it's evening" effect. A control zone with no MSG events is run through
the identical comparison as a falsification check: if the control zone
shows the same evening-vs-event-hour gap, the effect isn't really about
events.
"""

import pandas as pd
from scipy.stats import ttest_ind

import config

MSG_EVENTS_PATH = config.LEGACY_DIR / "events" / "msg_events" / "sports_msg_events.csv"
MSG_ZONE = 186  # Penn Station/Madison Sq West
CONTROL_ZONE = 100  # Garment District - adjacent, no venue, similar commercial character
EVENT_HOUR_RANGE = range(19, 23)  # MSG events observed to start 19:00-20:00, run ~2h


def load_deviation(zone_id: int) -> pd.DataFrame:
    features = pd.read_csv(config.FEATURES_PATH, parse_dates=[config.COL_HOUR])
    norm_table = pd.read_csv(config.NORM_TABLE_PATH)
    zone_df = features.loc[features[config.COL_ZONE] == zone_id].merge(
        norm_table, on=[config.COL_ZONE, "day_of_week", "hour"], how="left"
    )
    zone_df["deviation"] = zone_df["busyness_score"] - zone_df["norm_value"]
    return zone_df


def flag_event_hours(zone_df: pd.DataFrame) -> pd.Series:
    """The same real MSG event timestamps, applied regardless of which
    zone's deviation series is passed in - this is what makes the control
    zone comparison meaningful (same city-wide moments, different place)."""
    events = pd.read_csv(MSG_EVENTS_PATH, parse_dates=["start_datetime", "end_datetime"])
    is_event = pd.Series(False, index=zone_df.index)
    hours = zone_df[config.COL_HOUR]
    for _, ev in events.iterrows():
        is_event |= hours.between(ev["start_datetime"].floor("h"), ev["end_datetime"].ceil("h"))
    return is_event


def compare(zone_id: int, label: str) -> None:
    zone_df = load_deviation(zone_id)
    zone_df["is_event"] = flag_event_hours(zone_df)

    overall_std = zone_df["deviation"].std()
    print(f"--- {label} (zone {zone_id}) ---")
    print(f"  overall deviation std: {overall_std:.4f}")

    non_event = zone_df.loc[~zone_df["is_event"], "deviation"]
    event = zone_df.loc[zone_df["is_event"], "deviation"]
    print(
        f"  ALL HOURS: non-event mean={non_event.mean():.4f} (n={len(non_event)}), "
        f"event mean={event.mean():.4f} (n={len(event)}), "
        f"gap={event.mean() - non_event.mean():.4f} "
        f"({(event.mean() - non_event.mean()) / overall_std:.2f} std devs)"
    )

    evening = zone_df.loc[zone_df["hour"].isin(EVENT_HOUR_RANGE)]
    non_event_evening = evening.loc[~evening["is_event"], "deviation"]
    event_evening = evening.loc[evening["is_event"], "deviation"]
    if len(event_evening) > 0:
        gap = event_evening.mean() - non_event_evening.mean()
        t_stat, p_value = ttest_ind(event_evening, non_event_evening, equal_var=False)
        print(
            f"  EVENING HOURS ONLY (hour in {list(EVENT_HOUR_RANGE)}): "
            f"non-event mean={non_event_evening.mean():.4f} (n={len(non_event_evening)}), "
            f"event mean={event_evening.mean():.4f} (n={len(event_evening)}), "
            f"gap={gap:.4f} ({gap / overall_std:.2f} std devs), "
            f"Welch's t={t_stat:.2f}, p={p_value:.2e}"
        )
    print()


if __name__ == "__main__":
    compare(MSG_ZONE, "MSG zone")
    compare(CONTROL_ZONE, "Control zone (no venue)")
