from fastapi import FastAPI
from typing import Optional
import datetime as dt
import pytz
import pandas as pd
import numpy as np
import yfinance as yf

app = FastAPI(title="Sector Score API", version="1.0")

DEFAULT_TICKERS = ["XLK","XLF","XLV","XLE","XLI","XLY","XLP","XLU","XLRE","XLB","XLC"]
EASTERN = pytz.timezone("US/Eastern")
OPEN_TIME = dt.time(9, 30)
CUTOFF_TIME = dt.time(9, 45)
REGULAR_MINUTES = 390.0
SLICE_MINUTES = 15.0

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Sector Score API is running"}

def find_last_trading_date(date_guess, ticker="SPY"):
    # Walk back up to 10 days to find a date with 1m data
    for _ in range(10):
        if date_guess.weekday() >= 5:  # weekend
            date_guess -= dt.timedelta(days=1)
            continue
        start = EASTERN.localize(dt.datetime.combine(date_guess, dt.time(0,0))).astimezone(pytz.utc)
        end   = start + dt.timedelta(days=1)
        df = yf.download(ticker, interval="1m", start=start, end=end,
                         prepost=True, progress=False, auto_adjust=False, threads=False)
        if not df.empty:
            return date_guess
        date_guess -= dt.timedelta(days=1)
    return None

def resolve_target_datetime(user_date=None):
    now_et = dt.datetime.now(pytz.utc).astimezone(EASTERN)
    if user_date is not None:
        target_date = user_date
        target_dt = EASTERN.localize(dt.datetime.combine(target_date, CUTOFF_TIME))
    else:
        target_date = now_et.date()
        target_dt = EASTERN.localize(dt.datetime.combine(target_date, CUTOFF_TIME))
        if now_et < target_dt:
            target_date = target_date - dt.timedelta(days=1)
            target_dt = EASTERN.localize(dt.datetime.combine(target_date, CUTOFF_TIME))
    checked = find_last_trading_date(target_date)
    if checked is None:
        raise RuntimeError("Could not find a recent trading day with intraday data.")
    if checked != target_date:
        target_date = checked
        target_dt = EASTERN.localize(dt.datetime.combine(target_date, CUTOFF_TIME))
    return target_date, target_dt

def fetch_intraday_1m(ticker, date_et):
    start = EASTERN.localize(dt.datetime.combine(date_et, dt.time(0,0))).astimezone(pytz.utc)
    end   = start + dt.timedelta(days=1)
    df = yf.download(ticker, interval="1m", start=start, end=end,
                     prepost=True, progress=False, auto_adjust=False, threads=False)
    if df.empty:
        return df
    
    # Handle MultiIndex columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    if df.index.tz is None:
        df = df.tz_localize("UTC")
    df = df.tz_convert(EASTERN)
    df = df.rename(columns=str.lower)  # open, high, low, close, volume
    return df

def fetch_daily(ticker):
    df = yf.download(ticker, interval="1d", period="90d",
                     auto_adjust=False, progress=False, threads=False)
    if df.empty:
        return df
    
    # Handle MultiIndex columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df = df.rename(columns=str.lower)
    return df

def compute_score_for_ticker(ticker, date_et, asof_dt_et):
    try:
        intraday = fetch_intraday_1m(ticker, date_et)
        daily = fetch_daily(ticker)

        if intraday.empty or daily.empty or len(daily) < 21:
            return {"ticker": ticker, "error": "Insufficient data"}

        dailydf = daily.copy()
        if dailydf.index.tz is None:
            dailydf.index = pd.to_datetime(dailydf.index).tz_localize(EASTERN)
        else:
            dailydf.index = dailydf.index.tz_convert(EASTERN)
        prev_daily = dailydf[dailydf.index.date < date_et]
        if prev_daily.empty:
            return {"ticker": ticker, "error": "No previous close"}
        pre_close = float(prev_daily.iloc[-1]["close"])

        day_slice = intraday[(intraday.index.date == date_et)]
        if day_slice.empty:
            return {"ticker": ticker, "error": "No intraday for target date"}

        # Opening range = 9:30–9:44 inclusive (first 15 minutes)
        end_or = (dt.datetime.combine(date_et, CUTOFF_TIME) - dt.timedelta(minutes=1)).time()
        or_slice = day_slice.between_time(OPEN_TIME, end_or)
        if or_slice.empty:
            return {"ticker": ticker, "error": "No 9:30–9:45 data"}

        opening_range_high = float(or_slice["high"].max())
        opening_range_low  = float(or_slice["low"].min())

        upto_cut = day_slice[day_slice.index <= asof_dt_et]
        if upto_cut.empty:
            return {"ticker": ticker, "error": "No price up to 9:45"}
        current_price = float(upto_cut["close"].iloc[-1])

        open_at_930 = float(or_slice["open"].iloc[0])
        overnight_gap = (open_at_930 - pre_close) / pre_close * 100.0
        intraday_move = (current_price - open_at_930) / open_at_930 * 100.0
        total_day_move = (current_price - pre_close) / pre_close * 100.0

        avg_20d_vol = float(dailydf["volume"].tail(20).mean())
        vol_15m = float(or_slice["volume"].sum())
        expected_15m = avg_20d_vol * (SLICE_MINUTES / REGULAR_MINUTES)
        relative_volume = vol_15m / expected_15m if expected_15m > 0 else np.nan

        if np.isnan(relative_volume):
            volume_score = 0
        elif relative_volume > 2.0:
            volume_score = 3
        elif relative_volume > 1.5:
            volume_score = 2
        elif relative_volume > 1.0:
            volume_score = 1
        else:
            volume_score = 0

        if opening_range_high == opening_range_low:
            or_position = 0.0
        elif current_price > opening_range_high:
            or_position = 2.0
        elif current_price < opening_range_low:
            or_position = -2.0
        else:
            or_position = ((current_price - opening_range_low) /
                           (opening_range_high - opening_range_low)) - 0.5

        strength_score = total_day_move + (0.5 * volume_score) + (2.0 * or_position)

        if strength_score > 3:
            color = "dark_green"
        elif strength_score > 1:
            color = "blue"
        elif strength_score > -1:
            color = "gray"
        elif strength_score > -3:
            color = "red"
        else:
            color = "dark_red"

        return {
            "ticker": ticker,
            "prev_close": round(pre_close, 4),
            "open_930": round(open_at_930, 4),
            "current_price_945": round(current_price, 4),
            "overnight_gap_pct": round(overnight_gap, 3),
            "intraday_move_pct": round(intraday_move, 3),
            "total_day_move_pct": round(total_day_move, 3),
            "opening_range_high": round(opening_range_high, 4),
            "opening_range_low": round(opening_range_low, 4),
            "or_position": round(or_position, 3),
            "avg_20d_vol": int(avg_20d_vol),
            "vol_15m": int(vol_15m),
            "relative_volume": round(relative_volume, 3) if not np.isnan(relative_volume) else None,
            "volume_score": volume_score,
            "strength_score": round(float(strength_score), 3),
            "color": color
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

@app.get("/sectors")
def sectors(tickers: Optional[str] = None, date: Optional[str] = None):
    tick_list = [t.strip().upper() for t in (tickers.split(",") if tickers else DEFAULT_TICKERS)]
    user_date = dt.date.fromisoformat(date) if date else None
    date_et, asof_dt_et = resolve_target_datetime(user_date=user_date)
    rows = [compute_score_for_ticker(t, date_et, asof_dt_et) for t in tick_list]
    good = [r for r in rows if "strength_score" in r]
    good.sort(key=lambda r: r["strength_score"], reverse=True)
    
    # Changed to get bottom 4 sectors instead of top 4
    bottom4 = [r["ticker"] for r in good[-4:]] if len(good) >= 4 else [r["ticker"] for r in good]
    
    return {"date": str(date_et), "bottom4": bottom4, "rows": good}

@app.get("/test")
def test():
    """Test endpoint to verify API is running"""
    return {
        "status": "working",
        "time": str(dt.datetime.now()),
        "message": "API is running. Note: Yahoo Finance may block some requests from cloud servers."
    }
