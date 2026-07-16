# flight-alerts

Daily flight price alerts for a one-way **SFO → DEL** trip. The script queries [SerpAPI](https://serpapi.com/)'s Google Flights engine across configured departure dates, filters results, sorts by price, and emails a summary.

## What it searches

| Setting | Value |
|---------|-------|
| **Route** | San Francisco (SFO) → Delhi (DEL), one-way |
| **Dates** | January 16, 17, and 18, 2027 (`OUTBOUND_DATES` in `flight_alert.py`) |
| **Stops** | Direct or ≤1 stop (`MAX_STOPS = 1`; SerpAPI `stops=2`) |
| **Max duration** | 24 hours total (`MAX_DURATION = 24 * 60` minutes) |
| **Results** | Top 20 cheapest itineraries after merging all dates (`MAX_RESULTS = 20`) |
| **Currency** | USD |

Past dates in `OUTBOUND_DATES` are skipped automatically at runtime. If no flights match, the alert email still sends with a "no qualifying flights" message.

## Schedule

GitHub Actions runs the alert on **Tuesdays and Fridays at 8:00 AM PST** (15:00 UTC). You can also trigger a run manually from the Actions tab.

## Configuration

Edit constants at the top of `flight_alert.py`:

| Constant | Description |
|----------|-------------|
| `OUTBOUND_DATES` | Tuple of `YYYY-MM-DD` departure dates to search |
| `MAX_DURATION` | Maximum total itinerary duration in minutes |
| `MAX_STOPS` | Maximum number of stops (0 = nonstop only, 1 = direct or one stop) |
| `MAX_RESULTS` | Number of cheapest itineraries to include in the email |

## Environment variables

| Variable | Purpose |
|----------|---------|
| `SERPAPI_KEY` | SerpAPI key |
| `GMAIL_USER` | Gmail address used to send mail |
| `GMAIL_APP_PASS` | Gmail [app password](https://support.google.com/accounts/answer/185833) (not your normal login password) |
| `TO_EMAIL` | Recipient address |

## Run locally

```bash
pip install -r requirements.txt
export SERPAPI_KEY=... GMAIL_USER=... GMAIL_APP_PASS=... TO_EMAIL=...
python flight_alert.py
```

## GitHub Actions

Workflow: [`.github/workflows/flight_alert.yml`](.github/workflows/flight_alert.yml)

Add the four environment variables above as **repository secrets** under Settings → Secrets and variables → Actions:

- `SERPAPI_KEY`
- `GMAIL_USER`
- `GMAIL_APP_PASS`
- `TO_EMAIL`

## Project layout

```
flight_alert.py              # Search, filter, and email logic
requirements.txt             # Python dependencies
.github/workflows/flight_alert.yml  # Scheduled CI job
```
