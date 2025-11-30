#!/usr/bin/env python3
"""
Generate a morning market snapshot for key futures and Treasury yields.

At (or before) 7:00 AM local time the script:
- Pulls 5-minute Yahoo Finance data for each instrument
- Computes Asia session (midnight -> 06:59) open/close/range
- Computes London session (07:00 -> run time) open/close/range
- Records the latest price at run time
- Emits commentary based on London sweeping Asia highs/lows

The timezone defaults to America/New_York but can be overridden.

Examples:
    # Default (uses current time, America/New_York, JSON output)
    python market_data/fetch_market_data.py

    # Generate Markdown table for a specific timestamp
    python market_data/fetch_market_data.py \
        --run-at 2025-11-29T07:00:00-05:00 \
        --timezone America/New_York \
        --format markdown

    # Save JSON snapshot to file
    python market_data/fetch_market_data.py --output examples/market_overview.json
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf
from zoneinfo import ZoneInfo

UTC = timezone.utc
DEFAULT_TZ = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class Instrument:
    symbol: str
    label: str
    category: str


INSTRUMENTS: List[Instrument] = [
    Instrument("ES=F", "E-mini S&P 500", "Index Future"),
    Instrument("NQ=F", "E-mini Nasdaq 100", "Index Future"),
    Instrument("YM=F", "E-mini Dow Jones", "Index Future"),
    Instrument("GC=F", "Gold", "Metal Future"),
    Instrument("CL=F", "Crude Oil WTI", "Energy Future"),
    Instrument("SI=F", "Silver", "Metal Future"),
    Instrument("^FVX", "US 5Y Treasury Yield", "Treasury Yield"),
    Instrument("^TNX", "US 10Y Treasury Yield", "Treasury Yield"),
    Instrument("^TYX", "US 30Y Treasury Yield", "Treasury Yield"),
]

SESSION_DEFS = {
    "asia": {
        "label": "Asia Session",
        "start_time": time(0, 0),
        "end_time": time(6, 59, 59),
    },
    "london": {
        "label": "London Session",
        "start_time": time(7, 0),
        "end_time": None,  # runs until report time
    },
}


def safe_float(value: float | int | None) -> Optional[float]:
    if value is None:
        return None
    if pd.isna(value):
        return None
    return round(float(value), 4)


def fetch_intraday(
    symbol: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    period: str = "2d",
    interval: str = "5m",
) -> pd.DataFrame:
    download_kwargs: Dict[str, object] = {
        "interval": interval,
        "auto_adjust": False,
        "progress": False,
    }

    if start and end:
        download_kwargs["start"] = start.astimezone(UTC).replace(tzinfo=None)
        download_kwargs["end"] = end.astimezone(UTC).replace(tzinfo=None)
    else:
        download_kwargs["period"] = period

    logging.info(
        "[Market] Fetching %s [%s] from %s to %s",
        symbol,
        download_kwargs.get("interval"),
        download_kwargs.get("start") or f"period={download_kwargs.get('period')}",
        download_kwargs.get("end"),
    )

    try:
        df = yf.download(symbol, **download_kwargs)
    except Exception as err:
        logging.error("[Market] Error downloading %s data: %s", symbol, err)
        return pd.DataFrame()
    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        if len(df.columns.levels) > 1:
            df.columns = df.columns.get_level_values(0)
        else:
            df = df.droplevel(0, axis=1)

    if df.index.tz is None:
        df.index = df.index.tz_localize(UTC)
    else:
        df.index = df.index.tz_convert(UTC)

    df = df.sort_index()

    if df.empty:
        logging.warning("[Market] No data returned for %s in requested window", symbol)
        return df

    logging.info(
        "[Market] Fetched %s rows for %s (%s -> %s)",
        len(df),
        symbol,
        df.index[0],
        df.index[-1],
    )

    logging.debug("First rows for %s:\n%s", symbol, df.head().to_string())
    logging.debug("Last rows for %s:\n%s", symbol, df.tail().to_string())

    return df


def get_series(df: pd.DataFrame, names: List[str]) -> Optional[pd.Series]:
    lower_map = {col.lower(): col for col in df.columns}
    for name in names:
        key = name.lower()
        if key in lower_map:
            return df[lower_map[key]]
    return None


def get_from_row(row: pd.Series, names: List[str]) -> Optional[float]:
    lower_map = {idx.lower(): idx for idx in row.index}
    for name in names:
        key = name.lower()
        if key in lower_map:
            return safe_float(row[lower_map[key]])
    return None


def session_window(session_key: str, run_dt: datetime, tz: ZoneInfo) -> tuple[datetime, datetime]:
    spec = SESSION_DEFS[session_key]
    local_run = run_dt.astimezone(tz)
    session_date = local_run.date()

    start_local = datetime.combine(session_date, spec["start_time"], tzinfo=tz)
    if spec["end_time"] is None:
        end_local = local_run
    else:
        end_local = datetime.combine(session_date, spec["end_time"], tzinfo=tz)
        if end_local > local_run:
            end_local = local_run

    start_utc = start_local.astimezone(UTC)
    end_utc = end_local.astimezone(UTC)
    return start_utc, end_utc


def slice_window(df: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
    if df.empty:
        return df
    mask = (df.index >= start) & (df.index <= end)
    return df.loc[mask]


def compute_session_metrics(df: pd.DataFrame, start: datetime, end: datetime) -> Dict[str, Optional[float]]:
    window = slice_window(df, start, end)
    if window.empty:
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "open": None,
            "close": None,
            "high": None,
            "low": None,
            "range": None,
        }

    first_row = window.iloc[0]
    last_row = window.iloc[-1]

    open_price = get_from_row(first_row, ["Open"])
    close_price = get_from_row(last_row, ["Close", "Adj Close"])

    high_series = get_series(window, ["High"])
    low_series = get_series(window, ["Low"])

    high_price = safe_float(high_series.max()) if high_series is not None else None
    low_price = safe_float(low_series.min()) if low_series is not None else None
    session_range = safe_float(high_series.max() - low_series.min()) if (high_series is not None and low_series is not None) else None

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "open": open_price,
        "close": close_price,
        "high": high_price,
        "low": low_price,
        "range": session_range,
    }


def latest_price(df: pd.DataFrame, run_dt: datetime) -> Optional[float]:
    if df.empty:
        return None

    close_series = get_series(df, ["Close", "Adj Close"])
    if close_series is None:
        return None

    window = close_series.loc[close_series.index <= run_dt]
    if window.empty:
        return None
    return safe_float(window.iloc[-1])


def build_comment(asia: Dict[str, Optional[float]], london: Dict[str, Optional[float]]) -> str:
    if not asia or not london:
        return "Insufficient data"

    asia_high = asia.get("high")
    asia_low = asia.get("low")
    london_high = london.get("high")
    london_low = london.get("low")
    london_close = london.get("close")

    if None in (asia_high, asia_low, london_high, london_low, london_close):
        return "Insufficient data"

    swept_high = london_high > asia_high
    swept_low = london_low < asia_low

    if swept_high and swept_low:
        return "London Swept Both Highs and Lows"

    if london_close > asia_high:
        return "London Swept Asia High"

    if london_close < asia_low:
        return "London Swept Asia Low"

    return "London consolidating"


def build_market_snapshot(run_dt: datetime, tz: ZoneInfo, lookback_minutes: int = 24 * 60) -> Dict[str, object]:
    snapshot = {
        "generated_at": run_dt.astimezone(tz).isoformat(),
        "timezone": tz.key if hasattr(tz, "key") else str(tz),
        "symbols": [],
    }

    run_dt_utc = run_dt.astimezone(UTC)
    start_utc = run_dt_utc - timedelta(minutes=lookback_minutes)

    for instrument in INSTRUMENTS:
        logging.info("[Market] Processing symbol %s (%s)", instrument.symbol, instrument.label)
        fetch_end = run_dt_utc + timedelta(minutes=5)
        intraday = fetch_intraday(
            instrument.symbol,
            start=start_utc,
            end=fetch_end,
        )
        sessions = {}
        for key in SESSION_DEFS:
            start, end = session_window(key, run_dt, tz)
            metrics = compute_session_metrics(intraday, start, end)
            metrics["label"] = SESSION_DEFS[key]["label"]
            sessions[key] = metrics

        price_now = latest_price(intraday, run_dt_utc)
        comment = build_comment(sessions.get("asia", {}), sessions.get("london", {}))

        snapshot["symbols"].append(
            {
                "symbol": instrument.symbol,
                "label": instrument.label,
                "category": instrument.category,
                "asia": sessions["asia"],
                "london": sessions["london"],
                "price_at_run": price_now,
                "comment": comment,
            }
        )
        logging.info(
            "[Market] Done %s | Asia range=%s | London range=%s | Price=%s | Comment=%s",
            instrument.symbol,
            sessions["asia"].get("range"),
            sessions["london"].get("range"),
            price_now,
            comment,
        )

    return snapshot


def format_markdown(snapshot: Dict[str, object]) -> str:
    headers = [
        "Symbol",
        "Asia Open",
        "Asia Close",
        "Asia Range",
        "London Open",
        "London Close",
        "London Range",
        "Price @ Run",
        "Comments",
    ]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join([" --- "] * len(headers)) + "|"]

    for symbol in snapshot["symbols"]:
        asia = symbol["asia"]
        london = symbol["london"]
        row = [
            symbol["symbol"],
            format_price(asia.get("open")),
            format_price(asia.get("close")),
            format_range(asia.get("range")),
            format_price(london.get("open")),
            format_price(london.get("close")),
            format_range(london.get("range")),
            format_price(symbol.get("price_at_run")),
            symbol.get("comment", ""),
        ]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def format_price(value: Optional[float]) -> str:
    return f"{value:.2f}" if value is not None else "—"


def format_range(value: Optional[float]) -> str:
    return f"{value:.2f}" if value is not None else "—"


def format_timestamp(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%b %d, %Y %I:%M %p %Z")
    except ValueError:
        return value


def generate_market_table_html(snapshot: Dict[str, object]) -> str:
    rows: List[str] = []
    for symbol in snapshot.get("symbols", []):
        asia = symbol.get("asia", {})
        london = symbol.get("london", {})
        row = f"""
            <tr>
                <td class="symbol-cell">
                    <div class="symbol-code">{symbol.get('symbol')}</div>
                    <div class="symbol-label">{symbol.get('label')}</div>
                </td>
                <td>{format_price(asia.get('open'))}</td>
                <td>{format_price(asia.get('close'))}</td>
                <td>{format_range(asia.get('range'))}</td>
                <td>{format_price(london.get('open'))}</td>
                <td>{format_price(london.get('close'))}</td>
                <td>{format_range(london.get('range'))}</td>
                <td>{format_price(symbol.get('price_at_run'))}</td>
                <td class="comment-cell">{symbol.get('comment', '')}</td>
            </tr>
        """
        rows.append(row)

    if not rows:
        rows.append(
            """
            <tr>
                <td colspan="9" class="empty-cell">No market data available.</td>
            </tr>
            """
        )

    generated_at = format_timestamp(snapshot.get("generated_at"))

    return f"""
    <div class="market-overview">
        <div class="market-overview-header">
            <h2>Global Market Overview</h2>
            <div class="market-overview-subtitle">As of {generated_at}</div>
        </div>
        <div class="table-wrapper">
            <table class="market-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Asia Open</th>
                        <th>Asia Close</th>
                        <th>Asia Range</th>
                        <th>London Open</th>
                        <th>London Close</th>
                        <th>London Range</th>
                        <th>Price @ Run</th>
                        <th>Comments</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    </div>
    """


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Asia/London session snapshot via Yahoo Finance")
    parser.add_argument("--output", help="Write JSON snapshot to file")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Console output format")
    parser.add_argument("--timezone", default="America/New_York", help="IANA timezone for session boundaries")
    parser.add_argument(
        "--run-at",
        help="Override report timestamp (ISO-8601). Naive values assume provided timezone.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=36,
        help="How many hours of intraday data to request before run time",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging (very verbose)")
    parser.add_argument("--log-file", help="Append verbose logs to this file")
    return parser.parse_args()


def resolve_run_datetime(args: argparse.Namespace, tz: ZoneInfo) -> datetime:
    if args.run_at:
        parsed = datetime.fromisoformat(args.run_at)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=tz)
        return parsed
    return datetime.now(tz)


def main() -> None:
    args = parse_args()

    level = logging.WARNING
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO

    logging_config = {
        "level": level,
        "format": "%(asctime)s [%(levelname)s] %(message)s",
    }

    if args.log_file:
        logging_config["filename"] = args.log_file
        logging_config["filemode"] = "a"

    logging.basicConfig(**logging_config)

    tz = ZoneInfo(args.timezone)
    run_dt = resolve_run_datetime(args, tz)
    snapshot = build_market_snapshot(run_dt=run_dt, tz=tz, lookback_minutes=args.lookback_hours * 60)

    if args.output or args.format == "json":
        indent = 2 if args.pretty else None
        json_payload = json.dumps(snapshot, indent=indent)
        if args.format == "json":
            print(json_payload)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(json_payload)

    if args.format == "markdown":
        print(format_markdown(snapshot))


if __name__ == "__main__":
    main()

