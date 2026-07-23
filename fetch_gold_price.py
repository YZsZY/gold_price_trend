from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import akshare as ak
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
PUBLIC_DIR = ROOT_DIR / "public"
DATA_FILE = DATA_DIR / "gold_prices.json"
PUBLIC_DATA_FILE = PUBLIC_DIR / "gold_prices.json"
PUBLIC_CONFIG_FILE = PUBLIC_DIR / "config.json"
TARGET_SYMBOLS = ("Au99.99", "Au99.95", "Au100g")
DAYS_TO_KEEP = 365


def normalize_date(value: object) -> str | None:
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except Exception:
        return None


def normalize_price(value: object) -> float | None:
    if pd.isna(value):
        return None
    try:
        return round(float(value), 2)
    except Exception:
        return None


def pick_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    normalized_columns = {str(column).strip(): column for column in columns}
    for candidate in candidates:
        if candidate in normalized_columns:
            return normalized_columns[candidate]
    for candidate in candidates:
        for column_name, original_column in normalized_columns.items():
            if candidate in column_name:
                return original_column
    return None


def load_existing_records() -> dict[str, dict[str, object]]:
    if not DATA_FILE.exists():
        return {}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    return {record["date"]: record for record in records if record.get("date")}


def fetch_history_records() -> list[dict[str, object]]:
    frame = ak.spot_hist_sge(symbol="Au99.99")

    if frame.empty:
        raise RuntimeError("The Shanghai Gold Exchange returned no Au99.99 historical price data")

    date_column = pick_column(frame.columns, ("\u65e5\u671f", "\u4ea4\u6613\u65e5", "date"))
    close_column = pick_column(frame.columns, ("\u6536\u76d8\u4ef7", "\u6536\u76d8", "close", "Close"))
    if not date_column or not close_column:
        raise RuntimeError(f"Unable to recognize historical price columns: {list(frame.columns)}")

    records: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        trade_date = normalize_date(row[date_column])
        close_price = normalize_price(row[close_column])
        if trade_date and close_price:
            records.append(
                {
                    "date": trade_date,
                    "price": close_price,
                    "source": "Shanghai Gold Exchange Au99.99",
                }
            )

    return records


def fetch_today_record() -> dict[str, object] | None:
    try:
        frame = ak.spot_quotations_sge(symbol="Au99.99")
    except Exception:
        return None

    if frame.empty:
        return None

    symbol_column = pick_column(frame.columns, ("\u54c1\u79cd", "\u5408\u7ea6", "symbol", "Symbol"))
    price_column = pick_column(frame.columns, ("\u6700\u65b0\u4ef7", "\u73b0\u4ef7", "\u6536\u76d8\u4ef7", "\u4ef7\u683c", "price", "close"))

    if not symbol_column or not price_column:
        return None

    for _, row in frame.iterrows():
        symbol = str(row[symbol_column]).strip()
        if not any(target in symbol for target in TARGET_SYMBOLS):
            continue

        price = normalize_price(row[price_column])
        if price:
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "price": price,
                "source": f"Shanghai Gold Exchange {symbol}",
            }

    return None


def save_records(records_by_date: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    cutoff_date = (datetime.now() - timedelta(days=DAYS_TO_KEEP - 1)).date()
    records = sorted(records_by_date.values(), key=lambda item: item["date"])
    records = [record for record in records if datetime.strptime(record["date"], "%Y-%m-%d").date() >= cutoff_date]
    records = records[-DAYS_TO_KEEP:]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)
        file.write("\n")

    with PUBLIC_DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)
        file.write("\n")

    return records


def write_public_config() -> None:
    password = os.environ.get("ACCESS_PASSWORD", "")
    if not password:
        raise RuntimeError("Please configure ACCESS_PASSWORD in GitHub repository Settings > Secrets and variables > Actions")

    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    with PUBLIC_CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump({"accessPasswordHash": password_hash}, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> None:
    records_by_date = load_existing_records()

    if len(records_by_date) < DAYS_TO_KEEP:
        for record in fetch_history_records():
            records_by_date[record["date"]] = record

    today_record = fetch_today_record()
    if today_record:
        records_by_date[today_record["date"]] = today_record

    records = save_records(records_by_date)
    write_public_config()
    latest_date = records[-1]["date"] if records else "none"
    print(f"Updated {len(records)} gold price records. Latest date: {latest_date}")


if __name__ == "__main__":
    main()
