import pandas as pd

from .playability import playability_label, session_score


# ---------- 2) Emojis + formatting ----------

def sky_emoji(weather_code: int) -> str:
    wc = int(weather_code)
    if wc in (0, 1):
        return "☀️"
    if wc == 2:
        return "🌤️"
    if wc == 3:
        return "☁️"
    if wc in (45, 48):
        return "😶‍🌫️"
    if 51 <= wc <= 57:
        return "🌦️"   # drizzle
    if 61 <= wc <= 67:
        return "🌧️"    # rain
    if 71 <= wc <= 77:
        return "❄️"    # snow
    if 95 <= wc <= 99:
        return "⛈️"    # thunderstorm
    return "🌥️"


def status_emoji(label: str, score: int, is_best: bool) -> str:
    if is_best:
        return "🔥"
    if label == "playable":
        return "✅"
    if label == "maybe":
        return "⚠️"
    return "❌"


def add_wind_emoji(wind_speed: float, gusts: float) -> str:
    return "💨" if (wind_speed >= 18 or gusts >= 40) else ""


def add_rain_emoji(rain: float, pop: float, weather_code: int) -> str:
    if rain > 0.1:
        return "🌧️"
    if pop >= 30 or (51 <= int(weather_code) <= 57):
        return "🌦️"
    return ""


# ---------- 3) Merge consecutive hours into "windows" ----------

def build_windows(df: pd.DataFrame, tz: str = "Europe/London") -> pd.DataFrame:
    """
    Converts hourly rows into windows per calendar date by merging consecutive hours.
    Window score = max session score within the window (and uses that row as the representative row).
    """
    dfx = df.copy()

    # Ensure datetime and timezone
    dfx["date"] = pd.to_datetime(dfx["date"], utc=True, errors="coerce")
    if tz:
        dfx["date"] = dfx["date"].dt.tz_convert(tz)

    dfx = dfx.sort_values("date").reset_index(drop=True)

    # compute label+score per row
    dfx["label"] = dfx.apply(playability_label, axis=1)
    dfx["score"] = dfx.apply(session_score, axis=1)

    # (Optional) Drop any "no" rows if they slipped in
    dfx = dfx[dfx["label"] != "no"].copy()
    if dfx.empty:
        return dfx

    windows = []
    current = [dfx.iloc[0]]

    def flush(block_rows):
        block = pd.DataFrame(block_rows)
        # representative row = highest score
        rep = block.sort_values("score", ascending=False).iloc[0].to_dict()

        # label for block: if any maybe -> maybe else playable
        label_rank = {"playable": 0, "maybe": 1}
        worst = max(block["label"], key=lambda x: label_rank.get(x, 999))
        rep["block_label"] = worst

        start = block_rows[0]["date"]
        last = block_rows[-1]["date"]
        end = last + pd.Timedelta(hours=1)

        rep["start"] = start
        rep["end"] = end
        rep["day"] = start.date()

        windows.append(rep)

    for i in range(1, len(dfx)):
        prev = dfx.iloc[i - 1]["date"]
        cur = dfx.iloc[i]["date"]

        same_day = prev.date() == cur.date()
        consecutive = (cur - prev) == pd.Timedelta(hours=1)

        if same_day and consecutive:
            current.append(dfx.iloc[i])
        else:
            flush(current)
            current = [dfx.iloc[i]]

    flush(current)

    return pd.DataFrame(windows).sort_values("score", ascending=False).reset_index(drop=True)


# ---------- 4) Build the Telegram-style message ----------

def tennis_telegram_summary(df: pd.DataFrame, tz: str = "Europe/London") -> str:
    windows = build_windows(df, tz=tz)
    if windows.empty:
        return "🎾 No playable windows found in your filtered data."

    best = windows.iloc[0]

    def fmt_day(dt):
        return dt.strftime("%a %d %b")

    def fmt_time_range(start, end):
        return f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"

    # Header "Best session"
    best_sky = sky_emoji(best["weather_code"])
    best_wind = add_wind_emoji(best["wind_speed_10m"], best["wind_gusts_10m"])
    header = (
        "🎾 *Tennis Playability Report* (from your filtered playable rows)\n\n"
        f"🏆 *Best session (overall):* *{fmt_day(best['start'])}, {fmt_time_range(best['start'], best['end'])}* "
        f"{best_sky}{best_wind}\n"
        f"Feels like *{best['apparent_temperature']:.0f}°C* • PoP *{best['precipitation_probability']:.0f}%* "
        f"• Rain *{best['rain']:.1f}mm* • Wind/Gust *{best['wind_speed_10m']:.0f}/{best['wind_gusts_10m']:.0f}*\n\n"
    )

    # Body list
    body_lines = ["*Upcoming playable windows (ranked best → worst)*"]
    for idx, row in windows.iterrows():
        is_best = idx == 0
        label = row["block_label"]
        score = int(row["score"])

        status = status_emoji(label, score, is_best)
        sky = sky_emoji(row["weather_code"])
        wind = add_wind_emoji(row["wind_speed_10m"], row["wind_gusts_10m"])
        rain_em = add_rain_emoji(row["rain"], row["precipitation_probability"], row["weather_code"])

        line = (
            f"{status} *{fmt_day(row['start'])}* {sky}{rain_em}{wind}  | "
            f"*{fmt_time_range(row['start'], row['end'])}*  | "
            f"feels *{row['apparent_temperature']:.0f}°C* | "
            f"PoP *{row['precipitation_probability']:.0f}%* | "
            f"rain *{row['rain']:.1f}mm* | "
            f"gust *{row['wind_gusts_10m']:.0f}*  "
            f"(_score {score}/100_)"
        )
        body_lines.append(line + "\n")

    # Legend
    legend = (
        "\n\n_Emoji legend:_ 🔥 best vibes • ✅ solid • ⚠️ playable but annoying • "
        "☀️/🌤️/☁️ sky • 🌦️ drizzle risk • ☔ measurable rain • 🌬️ gusty"
    )

    # Telegram supports MarkdownV2 or HTML; this string is Markdown-ish.
    return header + "\n".join(body_lines) + legend
