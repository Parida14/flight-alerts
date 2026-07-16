# flight-alerts

Small script that queries [SerpAPI](https://serpapi.com/)'s Google Flights engine for **one-way** **BOM/DEL → SFO** itineraries, merges results across configured departure dates, sorts by **price**, and emails a summary.

## What it searches

- **Route:** Mumbai (BOM) or Delhi (DEL) → San Francisco (SFO), one-way  
- **Dates:** set in `OUTBOUND_DATES` in `flight_alert.py` (currently January 16–18, 2027)  
- **Filters:** direct or **≤1 stop**; total itinerary duration capped at **24 hours**; results limited to **20** rows after sorting  

Change `OUTBOUND_DATES`, `MAX_DURATION`, `MAX_STOPS`, or `MAX_RESULTS` in `flight_alert.py` if your trip or limits differ.

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
