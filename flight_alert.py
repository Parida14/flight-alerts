import requests
import smtplib
import json
from email.mime.text import MIMEText
from datetime import datetime
import os

SERPAPI_KEY = os.environ["SERPAPI_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_APP_PASS"]
TO_EMAIL = os.environ["TO_EMAIL"]

MAX_DURATION = 26 * 60  # 26hrs in minutes per leg

MULTI_CITY = json.dumps([
    {"departure_id": "SFO", "arrival_id": "DEL", "date": "2026-06-12"},
    {"departure_id": "BOM", "arrival_id": "SFO", "date": "2026-07-13"},
])

def fetch_flights():
    params = {
        "engine": "google_flights",
        "type": "3",                  # Multi-city
        "multi_city_json": MULTI_CITY,
        "max_duration": str(MAX_DURATION),
        "sort_by": "2",               # Sort by price
        "currency": "USD",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }
    r = requests.get("https://serpapi.com/search", params=params)
    r.raise_for_status()
    return r.json()

def parse_flights(data):
    results = []
    for flight in data.get("best_flights", []) + data.get("other_flights", []):
        price = flight.get("price")
        legs = flight.get("flights", [])
        total_duration = flight.get("total_duration")
        if not legs or not price:
            continue

        # Build per-leg summary
        leg_summaries = []
        for leg in legs:
            dep = leg.get("departure_airport", {})
            arr = leg.get("arrival_airport", {})
            leg_summaries.append(
                f"{dep.get('id','?')}({dep.get('time','?')}) → {arr.get('id','?')}({arr.get('time','?')}) "
                f"[{leg.get('airline','')} {leg.get('flight_number','')}]"
            )

        duration_str = f"{total_duration // 60}h {total_duration % 60}m" if total_duration else "?"
        stops = len(legs) - 1

        results.append({
            "price": price,
            "legs": leg_summaries,
            "stops": stops,
            "duration": duration_str,
        })

    # Sort ascending by price (API may already do this, but enforce locally)
    results.sort(key=lambda x: x["price"])
    return results

def send_email(flights):
    lines = [f"✈️  SFO→DEL (Jun 12) + BOM→SFO (Jul 13) — Multi-city Alert {datetime.now().date()}\n"]
    lines.append(f"Max duration per leg: 26hr | Sorted by total price ascending\n")
    lines.append("=" * 80)

    if not flights:
        lines.append("No qualifying flights found today.")
    else:
        for i, f in enumerate(flights, 1):
            lines.append(f"\n#{i}  💰 ${f['price']}  |  Stops: {f['stops']}  |  Total duration: {f['duration']}")
            for j, leg in enumerate(f["legs"], 1):
                lines.append(f"  Leg {j}: {leg}")
            lines.append("-" * 80)

    body = "\n".join(lines)
    msg = MIMEText(body)
    msg["Subject"] = f"✈️ Multi-city Flight Alert SFO↔DEL — {datetime.now().date()}"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    print(f"Email sent with {len(flights)} results.")

if __name__ == "__main__":
    data = fetch_flights()
    flights = parse_flights(data)
    send_email(flights)