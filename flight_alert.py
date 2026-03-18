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

MAX_DURATION = 26 * 60  # minutes per leg
MAX_LEG2_RESULTS = 7    # fetch leg 2 for top N cheapest leg 1 options

MULTI_CITY = json.dumps([
    {"departure_id": "SFO", "arrival_id": "DEL", "date": "2026-06-12"},
    {"departure_id": "BOM", "arrival_id": "SFO", "date": "2026-07-13"},
])

def serpapi_get(params):
    r = requests.get("https://serpapi.com/search", params={**params, "api_key": SERPAPI_KEY})
    r.raise_for_status()
    return r.json()

def fetch_leg1():
    return serpapi_get({
        "engine": "google_flights",
        "type": "3",
        "multi_city_json": MULTI_CITY,
        "max_duration": str(MAX_DURATION),
        "sort_by": "2",
        "currency": "USD",
        "hl": "en",
    })

def fetch_leg2(departure_token):
    return serpapi_get({
        "engine": "google_flights",
        "type": "3",
        "multi_city_json": MULTI_CITY,
        "departure_token": departure_token,
        "max_duration": str(MAX_DURATION),
        "sort_by": "2",
        "currency": "USD",
        "hl": "en",
    })

def summarize_flights(legs, label):
    summaries = []
    total_duration = 0
    for leg in legs:
        dep = leg.get("departure_airport", {})
        arr = leg.get("arrival_airport", {})
        dur = leg.get("duration", 0)
        total_duration += dur
        summaries.append(
            f"  {dep.get('id','?')} {dep.get('time','?')} → {arr.get('id','?')} {arr.get('time','?')} "
            f"[{leg.get('airline','')} {leg.get('flight_number','')}]"
        )
    dur_str = f"{total_duration // 60}h {total_duration % 60}m"
    return summaries, dur_str

def parse_and_combine():
    leg1_data = fetch_leg1()
    leg1_flights = leg1_data.get("best_flights", []) + leg1_data.get("other_flights", [])

    # Sort leg 1 by price, take top N to avoid burning API quota
    leg1_flights.sort(key=lambda x: x.get("price", 9999))
    leg1_flights = leg1_flights[:MAX_LEG2_RESULTS]

    combined = []
    for l1 in leg1_flights:
        token = l1.get("departure_token")
        if not token:
            continue

        leg2_data = fetch_leg2(token)
        leg2_flights = leg2_data.get("best_flights", []) + leg2_data.get("other_flights", [])
        if not leg2_flights:
            continue

        # Pick cheapest leg 2 option
        leg2_flights.sort(key=lambda x: x.get("price", 9999))
        l2 = leg2_flights[0]

        l1_summaries, l1_dur = summarize_flights(l1.get("flights", []), "SFO→DEL")
        l2_summaries, l2_dur = summarize_flights(l2.get("flights", []), "BOM→SFO")

        total_price = l2.get("price", 0)  # multi-city: final leg price = combined total
        l1_stops = len(l1.get("flights", [])) - 1
        l2_stops = len(l2.get("flights", [])) - 1

        combined.append({
            "total_price": total_price,
            "l1_summaries": l1_summaries,
            "l1_dur": l1_dur,
            "l1_stops": l1_stops,
            "l2_summaries": l2_summaries,
            "l2_dur": l2_dur,
            "l2_stops": l2_stops,
        })

    combined.sort(key=lambda x: x["total_price"])
    return combined

def send_email(flights):
    lines = [f"✈️  SFO→DEL (Jun 12) + BOM→SFO (Jul 13)  |  {datetime.now().date()}\n"]
    lines.append("Max 26hr per leg | Sorted by total price ascending")
    lines.append("=" * 80)

    if not flights:
        lines.append("\nNo qualifying flights found today.")
    else:
        for i, f in enumerate(flights, 1):
            lines.append(f"\n#{i}  💰 Total: ${f['total_price']}")
            lines.append(f"  ✈ Leg 1: SFO → DEL  ({f['l1_stops']} stop{'s' if f['l1_stops'] != 1 else ''}, {f['l1_dur']})")
            for s in f["l1_summaries"]:
                lines.append(s)
            lines.append(f"  ✈ Leg 2: BOM → SFO  ({f['l2_stops']} stop{'s' if f['l2_stops'] != 1 else ''}, {f['l2_dur']})")
            for s in f["l2_summaries"]:
                lines.append(s)
            lines.append("-" * 80)

    body = "\n".join(lines)
    msg = MIMEText(body)
    msg["Subject"] = f"✈️ Multi-city Flight Alert SFO↔DEL — {datetime.now().date()}"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    print(f"Email sent: {len(flights)} itineraries.")

if __name__ == "__main__":
    flights = parse_and_combine()
    send_email(flights)