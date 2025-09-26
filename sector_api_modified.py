from fastapi import FastAPI
from typing import Optional
import datetime as dt
import pytz
import pandas as pd
import numpy as np
import yfinance as yf

app = FastAPI(title="Sector API Bearish", version="1.0")

DEFAULT_TICKERS = ["XLK","XLF","XLV","XLE","XLI","XLY","XLP","XLU","XLRE","XLB","XLC"]
EASTERN = pytz.timezone("US/Eastern")
OPEN_TIME = dt.time(9, 30)
CUTOFF_TIME = dt.time(9, 45)
REGULAR_MINUTES = 390.0
SLICE_MINUTES = 15.0

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Sector API is running"}

def find_last_trading_date_simple(date_guess):
    # Simple logic without checking SPY
    # Skip weekends
    while date_guess.weekday() >= 5:  # Saturday = 5, Sunday = 6
        date_guess -= dt.timedelta(days=1)
    return date_guess

def resolve_target_datetime(user_date=None):
    now_et = dt.datetime.now(pytz.utc).astimezone(EASTERN)
    if user_date is not None:
        target_date = user_date
    else:
        target_date = now_et.date()
        target_dt = EASTERN.localize(dt.datetime.combine(target_date, CUTOFF_TIME))
        if now_et < target_dt:
            target_date = target_date - dt.timedelta(days=1)
    
    # Use simple weekend check instead of SPY validation
    target_date = find_last_trading_date_simple(target_date)
    target_dt = EASTERN.localize(dt.datetime.combine(target_date, CUTOFF_TIME))
    return target_date, target_dt

def fetch_intraday_1m(ticker, date_et):
    try:
        start = EASTERN.localize(dt.datetime.combine(date_et, dt.time(0,0))).astimezone(pytz.utc)
        end = start + dt.timedelta(days=1)
        df = yf.download(ticker, interval="1m", start=start, end=end,
                         prepost=True, progress=False, auto_adjust=False, threads=False)
        
        # Fix for MultiIndex columns
        if not df.empty and isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if df.empty:
            return df
        if df.index.tz is None:
            df = df.tz_localize("UTC")
        df = df.tz_convert(EASTERN)
        df = df.rename(columns=str.lower)
        return df
    except Exception as e:
        print(f"Error fetching intraday for {ticker}: {e}")
        return pd.DataFrame()

def fetch_daily(ticker):
    try:
        df = yf.download(ticker, interval="1d", period="90d",
                         auto_adjust=False, progress=False, threads=False)
        
        # Fix for MultiIndex columns
        if not df.empty and isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if df.empty:
            return df
        df = df.rename(columns=str.lower)
        return df
    except Exception as e:
        print(f"Error fetching daily for {ticker}: {e}")
        return pd.DataFrame()

# ... rest of compute_score_for_ticker function stays the same ...

@app.get("/sectors-test")
def sectors_test():
    """Test with just daily data to see if anything works"""
    results = []
    for ticker in DEFAULT_TICKERS[:3]:  # Test with just 3 tickers
        try:
            df = yf.download(ticker, period="5d", progress=False)
            if not df.empty and len(df) >= 2:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                close_today = float(df['Close'].iloc[-1])
                close_yesterday = float(df['Close'].iloc[-2])
                change = ((close_today - close_yesterday) / close_yesterday * 100)
                results.append({"ticker": ticker, "change_pct": round(change, 2)})
            else:
                results.append({"ticker": ticker, "error": "No data"})
        except Exception as e:
            results.append({"ticker": ticker, "error": str(e)[:50]})
    
    return {"results": results}

@app.get("/test")
def test():
    return {"status": "working", "time": str(dt.datetime.now())}
