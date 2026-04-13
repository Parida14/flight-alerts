import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

SERPAPI_KEY = os.environ["SERPAPI_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_APP_PASS"]
TO_EMAIL = os.environ["TO_EMAIL"]

MAX_DURATION = 23 * 60  # minutes
# One API call per date; cap listed results after global sort
MAX_RESULTS = 20

OUTBOUND_DATES = ("2026-07-13",)

def serpapi_get(params):
    r = requests.get("https://serpapi.com/search", params={**params, "api_key": SERPAPI_KEY})
    r.raise_for_status()
    return r.json()

def fetch_one_way(outbound_date):
    return serpapi_get({
        "engine": "google_flights",
        "type": "2",
        "departure_id": "BOM",
        "arrival_id": "SFO",
        "outbound_date": outbound_date,
        "max_duration": str(MAX_DURATION),
        "sort_by": "2",
        "currency": "USD",
        "hl": "en",
    })

def summarize_flights(legs):
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
    combined = []
    for outbound_date in OUTBOUND_DATES:
        data = fetch_one_way(outbound_date)
        flights = data.get("best_flights", []) + data.get("other_flights", [])
        for f in flights:
            legs = f.get("flights", [])
            if not legs:
                continue
            summaries, dur_str = summarize_flights(legs)
            stops = len(legs) - 1
            combined.append({
                "outbound_date": outbound_date,
                "price": f.get("price", 0),
                "summaries": summaries,
                "dur": dur_str,
                "stops": stops,
            })

    combined.sort(key=lambda x: x["price"])
    return combined[:MAX_RESULTS]

def send_email(flights):
    date_label = "Jul 13"
    lines = [f"✈️  One-way BOM → SFO ({date_label}, 2026)  |  {datetime.now().date()}\n"]
    lines.append("Max 26hr total | Sorted by price ascending")
    lines.append("=" * 80)

    if not flights:
        lines.append("\nNo qualifying flights found today.")
    else:
        for i, f in enumerate(flights, 1):
            lines.append(f"\n#{i}  💰 ${f['price']}  |  Depart {f['outbound_date']}")
            lines.append(f"  ✈  ({f['stops']} stop{'s' if f['stops'] != 1 else ''}, {f['dur']})")
            for s in f["summaries"]:
                lines.append(s)
            lines.append("-" * 80)

    body = "\n".join(lines)
    msg = MIMEText(body)
    msg["Subject"] = f"✈️ One-way BOM→SFO ({date_label}) — {datetime.now().date()}"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    print(f"Email sent: {len(flights)} itineraries.")

if __name__ == "__main__":
    flights = parse_and_combine()
    send_email(flights)
