# Deployment Instructions - Yahoo Finance Sector API

## Files Included

1. **sector_api_modified.py** - Main API application (returns bottom 4 weakest sectors)
2. **requirements.txt** - Python dependencies including yfinance
3. **README.md** - API documentation
4. **.gitignore** - Git ignore rules
5. **Dockerfile** - Docker configuration for Render

## Step 1: Clear Your GitHub Repository

Since you're reverting from Twelve Data to Yahoo Finance:

1. Go to your GitHub repository
2. Delete all existing files (especially the old sector_api_modified.py)
3. You can either:
   - Delete files one by one using the trash icon
   - Or press `.` to open github.dev and delete multiple files at once

## Step 2: Upload New Files

1. Click **"Add file"** → **"Upload files"**
2. Upload all 5 files:
   - sector_api_modified.py
   - requirements.txt
   - README.md
   - .gitignore
   - Dockerfile
3. Commit message: **"Revert to Yahoo Finance with bottom 4 sectors"**
4. Click **"Commit changes"**

## Step 3: Render Will Auto-Deploy

- Render will detect the changes and automatically redeploy
- This takes about 3-5 minutes
- Watch the build logs for any errors

## Step 4: Test Your API

Once deployed, test these endpoints:

1. **Health check:**
   ```
   https://sector-api-bearish.onrender.com/
   ```

2. **Get bottom 4 sectors:**
   ```
   https://sector-api-bearish.onrender.com/sectors
   ```

3. **Test with specific date:**
   ```
   https://sector-api-bearish.onrender.com/sectors?date=2024-09-20
   ```

4. **API Documentation:**
   ```
   https://sector-api-bearish.onrender.com/docs
   ```

## Important Notes

### About Yahoo Finance on Cloud Servers

- Yahoo Finance sometimes blocks requests from cloud servers like Render
- This is intermittent - it may work sometimes and fail other times
- If you get "No data" errors, try:
  1. Testing during market hours
  2. Running the code locally (works perfectly on local machines)
  3. Waiting and trying again later

### Local Testing (Always Works)

If Render has issues with Yahoo Finance, run locally:

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/sector-api.git
cd sector-api

# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn sector_api_modified:app --reload

# Open browser to http://localhost:8000/docs
```

## What This API Does

- Analyzes 11 sector ETFs during market open
- Uses 1-minute data for precise opening range analysis (9:30-9:45 AM)
- Calculates strength scores based on:
  - Price movement from previous close
  - Opening range breakout/breakdown
  - Relative volume
- Returns the **4 weakest sectors** (lowest strength scores)

## Typical Response

```json
{
  "date": "2024-09-24",
  "bottom4": ["XLE", "XLU", "XLRE", "XLB"],
  "rows": [
    // Detailed data for all sectors
  ]
}
```

## Use Cases

- **Short selling**: Target the weakest sectors
- **Risk avoidance**: Stay away from underperforming sectors
- **Sector rotation**: Move from weak to strong sectors

## Troubleshooting

### If all tickers fail on Render:
- Yahoo Finance is likely blocking Render's IP
- Solution: Run the API locally instead

### If some tickers fail:
- This is normal - Yahoo sometimes has partial data
- The API will return data for sectors that work

### If deployment fails:
- Check Render logs for specific errors
- Common issues:
  - Missing dependencies in requirements.txt
  - Docker build errors (try deleting Dockerfile to use Python environment)

## Support

- FastAPI docs: https://fastapi.tiangolo.com
- yfinance docs: https://pypi.org/project/yfinance/
- Render docs: https://render.com/docs

Good luck with your deployment!
