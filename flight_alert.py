import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

SERPAPI_KEY = os.environ["SERPAPI_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_APP_PASS"]  # Gmail App Password, not account password
TO_EMAIL = os.environ["TO_EMAIL"]

DATES = ["2026-06-11", "2026-06-12"]
DEPARTURE_CUTOFF = 17 * 60  # 5PM in minutes
MAX_DURATION = 25 * 60       # 25hrs in minutes

def fetch_flights(date):
    params = {
    "engine": "google_flights",
    "departure_id": "SFO",
    "arrival_id": "DEL",
    "outbound_date": date,
    "type": "2",           # One way (was "1" = round trip — caused the 400)
    "outbound_times": "17,23",  # Departure after 5PM
    "max_duration": "1500",     # <25hrs in minutes
    "sort_by": "2",             # Sort by price
    "currency": "USD",
    "hl": "en",
    "api_key": SERPAPI_KEY,
}
    r = requests.get("https://serpapi.com/search", params=params)
    r.raise_for_status()
    return r.json()

def parse_time_to_minutes(t_str):
    # e.g. "6:30 PM" → minutes since midnight
    dt = datetime.strptime(t_str.strip(), "%I:%M %p")
    return dt.hour * 60 + dt.minute

def duration_to_minutes(d_str):
    # e.g. "22 hr 15 min" or "1 day 2 hr 10 min"
    total = 0
    if "day" in d_str:
        parts = d_str.split("day")
        total += int(parts[0].strip()) * 24 * 60
        d_str = parts[1]
    if "hr" in d_str:
        total += int(d_str.split("hr")[0].strip()) * 60
        d_str = d_str.split("hr")[1]
    if "min" in d_str:
        total += int(d_str.split("min")[0].strip())
    return total

def filter_flights(data, date):
    results = []
    for flight in data.get("best_flights", []) + data.get("other_flights", []):
        price = flight.get("price")
        total_duration = flight.get("total_duration")
        legs = flight.get("flights", [])
        if not legs or not price:
            continue

        results.append({
            "date": date,
            "price": price,
            "airline": legs[0].get("airline", ""),
            "dep_time": legs[0].get("departure_airport", {}).get("time", ""),
            "arr_time": legs[-1].get("arrival_airport", {}).get("time", ""),
            "stops": len(legs) - 1,
            "duration": f"{total_duration // 60}h {total_duration % 60}m" if total_duration else "?",
        })
    return results

    
def send_email(flights):
    if not flights:
        body = "No qualifying flights found today."
    else:
        flights.sort(key=lambda x: x["price"])  # ascending = cheapest first
        lines = [f"SFO→DEL Flights (dep after 5PM, <25hr total) — {datetime.now().date()}\n"]
        lines.append(f"{'Date':<12} {'Price':>8} {'Airline':<20} {'Dep':>8} {'Arr':<20} {'Stops':>6} {'Duration':>10}")
        lines.append("-" * 90)
        for f in flights:
            lines.append(
                f"{f['date']:<12} ${f['price']:>7} {f['airline']:<20} {f['dep_time']:>8} "
                f"{f['arr_time']:<20} {f['stops']:>6} {f['duration']:>10}"
            )
        body = "\n".join(lines)

    msg = MIMEText(body)
    msg["Subject"] = f"✈️ SFO→DEL Flight Alert — {datetime.now().date()}"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    print("Email sent.")

if __name__ == "__main__":
    all_flights = []
    for date in DATES:
        data = fetch_flights(date)
        all_flights.extend(filter_flights(data, date))
    send_email(all_flights)