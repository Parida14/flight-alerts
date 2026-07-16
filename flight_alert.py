import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

SERPAPI_KEY = os.environ["SERPAPI_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_APP_PASS"]
TO_EMAIL = os.environ["TO_EMAIL"]

MAX_DURATION = 24 * 60  # minutes
MAX_STOPS = 1           # direct or 1 stop max (SerpAPI stops=2)
# One API call per date; cap listed results after global sort
MAX_RESULTS = 20

OUTBOUND_DATES = ("2027-01-16", "2027-01-17", "2027-01-18")

def serpapi_get(params):
    r = requests.get("https://serpapi.com/search", params={**params, "api_key": SERPAPI_KEY})
    r.raise_for_status()
    return r.json()

def fetch_one_way(outbound_date):
    return serpapi_get({
        "engine": "google_flights",
        "type": "2",
        "departure_id": "BOM,DEL",
        "arrival_id": "SFO",
        "outbound_date": outbound_date,
        "max_duration": str(MAX_DURATION),
        "stops": "2",
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
    today = datetime.now().date()
    for outbound_date in OUTBOUND_DATES:
        if datetime.strptime(outbound_date, "%Y-%m-%d").date() < today:
            print(f"Skipping past outbound date: {outbound_date}")
            continue
        data = fetch_one_way(outbound_date)
        flights = data.get("best_flights", []) + data.get("other_flights", [])
        for f in flights:
            legs = f.get("flights", [])
            if not legs:
                continue
            stops = len(legs) - 1
            if stops > MAX_STOPS:
                continue
            summaries, dur_str = summarize_flights(legs)
            total_minutes = sum(leg.get("duration", 0) for leg in legs)
            if total_minutes > MAX_DURATION:
                continue
            combined.append({
                "outbound_date": outbound_date,
                "price": f.get("price", 0),
                "summaries": summaries,
                "dur": dur_str,
                "stops": stops,
            })

    combined.sort(key=lambda x: x["price"])
    return combined[:MAX_RESULTS]

def format_date_label(dates):
    months = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
              7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
    parts = []
    year = None
    for d in dates:
        dt = datetime.strptime(d, "%Y-%m-%d")
        year = dt.year
        parts.append(f"{months[dt.month]} {dt.day}")
    label = " / ".join(parts) if len(parts) > 1 else parts[0]
    return label, year

def send_email(flights):
    date_label, year = format_date_label(OUTBOUND_DATES)
    lines = [f"✈️  One-way BOM/DEL → SFO ({date_label}, {year})  |  {datetime.now().date()}\n"]
    lines.append(f"Direct or ≤1 stop | Max {MAX_DURATION // 60}hr total | Sorted by price ascending")
    lines.append("=" * 80)

    if not flights:
        lines.append("\nNo qualifying flights found today.")
    else:
        for i, f in enumerate(flights, 1):
            lines.append(f"\n#{i}  💰 ${f['price']}  |  Depart {f['outbound_date']}")
            lines.append(f"  ✈  ({'nonstop' if f['stops'] == 0 else '1 stop'}, {f['dur']})")
            for s in f["summaries"]:
                lines.append(s)
            lines.append("-" * 80)

    body = "\n".join(lines)
    msg = MIMEText(body)
    msg["Subject"] = f"✈️ One-way BOM/DEL→SFO ({date_label}, {year}) — {datetime.now().date()}"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    print(f"Email sent: {len(flights)} itineraries.")

if __name__ == "__main__":
    flights = parse_and_combine()
    send_email(flights)
