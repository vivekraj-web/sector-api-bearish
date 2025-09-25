# Sector Score API - Yahoo Finance Version

This API analyzes sector ETF performance and identifies the **bottom 4 weakest sectors** based on opening range breakouts and price movements in the first 15 minutes of trading.

## Features

- Analyzes 11 major SPDR sector ETFs
- Returns the 4 weakest performing sectors
- Uses 1-minute intraday data for precise opening range analysis
- Calculates strength scores based on price movement, volume, and opening range position
- Color-codes sectors by performance

## API Endpoints

### `GET /`
Health check endpoint

### `GET /sectors`
Returns sector analysis with the 4 weakest sectors

**Optional Parameters:**
- `tickers`: Comma-separated list of ticker symbols (default: all 11 sector ETFs)
- `date`: Analysis date in ISO format (YYYY-MM-DD)

**Example Response:**
```json
{
  "date": "2024-09-24",
  "bottom4": ["XLE", "XLU", "XLRE", "XLB"],
  "rows": [
    {
      "ticker": "XLK",
      "prev_close": 175.23,
      "open_930": 175.45,
      "current_price_945": 176.45,
      "overnight_gap_pct": 0.125,
      "intraday_move_pct": 0.570,
      "total_day_move_pct": 0.696,
      "opening_range_high": 176.50,
      "opening_range_low": 175.30,
      "or_position": 0.958,
      "avg_20d_vol": 12500000,
      "vol_15m": 450000,
      "relative_volume": 0.936,
      "volume_score": 0,
      "strength_score": -1.234,
      "color": "gray"
    }
  ]
}
```

## Strength Score Calculation

The strength score combines:
- **Total day move**: Percentage change from previous close
- **Volume score** (0-3 points): Based on 15-minute volume vs 20-day average
  - 3 points: >2x average
  - 2 points: >1.5x average  
  - 1 point: >1x average
  - 0 points: Below average
- **Opening range position** (-2 to +2):
  - +2: Price above opening range high (bullish breakout)
  - -2: Price below opening range low (bearish breakdown)
  - -0.5 to +1.5: Position within the range

Formula: `strength_score = total_day_move + (0.5 × volume_score) + (2.0 × or_position)`

## Color Coding

- **Dark Green**: Score > 3 (Very strong)
- **Blue**: Score > 1 (Strong)
- **Gray**: Score > -1 (Neutral)
- **Red**: Score > -3 (Weak)
- **Dark Red**: Score ≤ -3 (Very weak)

## Default Sector ETFs

- **XLK**: Technology Select Sector SPDR
- **XLF**: Financial Select Sector SPDR
- **XLV**: Health Care Select Sector SPDR
- **XLE**: Energy Select Sector SPDR
- **XLI**: Industrial Select Sector SPDR
- **XLY**: Consumer Discretionary Select Sector SPDR
- **XLP**: Consumer Staples Select Sector SPDR
- **XLU**: Utilities Select Sector SPDR
- **XLRE**: Real Estate Select Sector SPDR
- **XLB**: Materials Select Sector SPDR
- **XLC**: Communication Services Select Sector SPDR

## Deployment

### Local Development
```bash
pip install -r requirements.txt
uvicorn sector_api_modified:app --reload
```

Access API documentation at: http://localhost:8000/docs

### Render Deployment
This application is configured for deployment on Render.com. It will auto-deploy when pushed to GitHub.

## Important Notes

- **Market Hours**: Best results during US market hours (9:30 AM - 4:00 PM ET)
- **Data Source**: Uses Yahoo Finance via yfinance library
- **Cloud Limitations**: Yahoo Finance may occasionally block requests from cloud servers
- **Opening Range**: Analyzes the first 15 minutes of trading (9:30-9:45 AM ET)
- **Bottom 4**: Returns the 4 sectors with the lowest strength scores

## Use Cases

- **Short Selling**: Identify weak sectors for short opportunities
- **Risk Management**: Avoid sectors showing weakness
- **Sector Rotation**: Move capital from weak to strong sectors
- **Market Analysis**: Understand which sectors are underperforming

## Requirements

- Python 3.11+
- See `requirements.txt` for package dependencies

## License

MIT
