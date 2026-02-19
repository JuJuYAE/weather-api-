from datetime import time


def is_playable_weather(row) -> bool:
    return (
        row["rain"] <= 0.5 and
        row["precipitation_probability"] < 60 and
        row["wind_speed_10m"] < 25 and
        row["wind_gusts_10m"] < 45 and
        row["apparent_temperature"] > 0 and
        row["weather_code"] < 61
    )


def playable_conditions(row) -> bool:
    t = row["date"].time()
    dow = row["date"].day_of_week  # Mon=0 ... Sun=6

    if dow in [0, 1, 2, 3, 4]:  # weekdays
        if t == time(19, 0):
            return is_playable_weather(row)

    if dow in [5, 6]:  # weekend
        if time(10, 0) <= t <= time(15, 0):
            return is_playable_weather(row)

    return False


# ---------- 1) Playability + scoring ----------

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def playability_label(row) -> str:
    # "maybe" band
    if row["rain"] > 0.1:
        return "maybe"
    if row["precipitation_probability"] >= 30:
        return "maybe"
    if row["wind_speed_10m"] >= 18:
        return "maybe"
    if row["wind_gusts_10m"] >= 35:
        return "maybe"
    if row["apparent_temperature"] < 3:
        return "maybe"
    if row["weather_code"] >= 51:  # drizzle family
        return "maybe"

    return "playable"


def session_score(row) -> int:
    """
    0–100 "tennis vibes" score.
    Warmer, drier, less wind/gusts => higher.
    """
    # temp: 0°C meh, 10°C great, 15°C max
    temp = _clamp((row["apparent_temperature"] - 0) / 15, 0, 1)

    # precip prob: 0% best, 60% bad
    pop = 1 - _clamp(row["precipitation_probability"] / 60, 0, 1)

    # wind: 0 best, 25 bad
    wind = 1 - _clamp(row["wind_speed_10m"] / 25, 0, 1)

    # gusts: 0 best, 45 bad
    gust = 1 - _clamp(row["wind_gusts_10m"] / 45, 0, 1)

    # penalties
    rain_penalty = _clamp(row["rain"] / 1.0, 0, 1) if row["rain"] > 0 else 0

    wc = int(row["weather_code"])
    code_penalty = 0
    if 51 <= wc <= 57:
        code_penalty = 0.15
    elif wc >= 61:
        code_penalty = 0.60

    raw = (
        0.30 * temp +
        0.40 * pop +
        0.20 * wind +
        0.10 * gust
    )

    raw = raw - 0.45 * rain_penalty - code_penalty
    return int(round(100 * _clamp(raw, 0, 1)))
