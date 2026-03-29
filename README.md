# flight-alerts

Small script that queries [SerpAPI](https://serpapi.com/)’s Google Flights engine for **one-way** **SFO → DEL** itineraries, merges results across configured departure dates, sorts by **price**, and emails a summary.

## What it searches

- **Route:** San Francisco (SFO) → Delhi (DEL), one-way  
- **Dates:** set in `OUTBOUND_DATES` in `flight_alert.py` (currently June 11–13, 2026)  
- **Filters:** total itinerary duration capped at **26 hours**; results limited to **25** rows after sorting  

Change `OUTBOUND_DATES`, `MAX_DURATION`, or `MAX_RESULTS` in `flight_alert.py` if your trip or limits differ.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `SERPAPI_KEY` | SerpAPI key |
| `GMAIL_USER` | Gmail address used to send mail |
| `GMAIL_APP_PASS` | Gmail [app password](https://support.google.com/accounts/answer/185833) (not your normal login password) |
| `TO_EMAIL` | Recipient address |

## Run locally

```bash
pip install requests
export SERPAPI_KEY=... GMAIL_USER=... GMAIL_APP_PASS=... TO_EMAIL=...
python flight_alert.py
```

## GitHub Actions

[`.github/workflows/flight_alert.yml`](.github/workflows/flight_alert.yml) runs daily (scheduled) or on demand. Add the same variables as **repository secrets** in the repo settings.
