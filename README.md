## Shanghai Gold Exchange Gold Price Trend Site

This repository uses GitHub Actions to fetch the Au99.99 gold price from the Shanghai Gold Exchange every day at 9:30 AM Beijing time, keep the latest 365 days of records, and deploy a static visualization site to GitHub Pages.

### Features

- **Automatic updates**: Runs every day at 9:30 AM Beijing time and can also be triggered manually from the Actions page.
- **Initial history backfill**: When local data contains fewer than 365 days, the script automatically fetches approximately the latest 365 days of historical prices.
- **Incremental maintenance**: Later runs update the current day's price and keep only the latest 365 days.
- **Trend chart**: The website supports weekly, monthly, and yearly gold price charts.
- **Access password**: The website password comes from the GitHub Actions Secret `ACCESS_PASSWORD`. Only the SHA-256 hash of the password is published.

### Setup

1. Add a new Secret named `ACCESS_PASSWORD` in `Settings > Secrets and variables > Actions`.
2. Set the Pages source to `GitHub Actions` in `Settings > Pages`.
3. Manually run `Update Gold Price and Deploy Site` from the `Actions` page, or wait for the scheduled 9:30 AM Beijing time run.
4. After the workflow completes, open the GitHub Pages URL to view the trend site.

### Local Development

Python 3.11 is recommended to match the GitHub Actions runtime.

```bash
export ACCESS_PASSWORD="your local access password"
pip install -r requirements.txt
python fetch_gold_price.py
python -m http.server 8000 --directory public
```

Then open `http://localhost:8000` in your browser.