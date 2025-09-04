# script/vix_alert.py
import os
import csv
import io
from urllib.request import urlopen, Request
import requests

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"

THRESHOLD = float(os.getenv("THRESHOLD"))
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DRY_RUN = (os.getenv("DRY_RUN") or "").lower() == "true"

def fetch_latest_vix():
    req = Request(FRED_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:
        text = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    date_key = "DATE" if "DATE" in reader.fieldnames else "observation_date"
    last_date, last_value = None, None
    for row in reader:
        if row["VIXCLS"] in ("", "."):
            continue
        last_date = row[date_key]
        last_value = float(row["VIXCLS"])
    return last_date, last_value

def send_email(subject, body):
    if DRY_RUN:
        print("[DRY_RUN] Subject:", subject)
        print(body)
        return
    url = "https://api.sendgrid.com/v3/mail/send"
    payload = {
        "personalizations": [{"to": [{"email": TO_EMAIL}]}],
        "from": {"email": FROM_EMAIL},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()

def main():
    date_str, value = fetch_latest_vix()
    print(f"[INFO] Latest VIXCLS: {value:.2f} (date={date_str}), threshold={THRESHOLD}")
    if value > THRESHOLD:
        subject = f"[VIXアラート] {THRESHOLD}超え: {value:.2f}（{date_str}）"
        body = (
            f"VIX 終値が閾値を上回りました。\n"
            f"- 日付: {date_str}\n"
            f"- VIX 終値: {value:.2f}\n"
            f"- 閾値: {THRESHOLD}\n"
            "データソース: FRED VIXCLS\n"
        )
        send_email(subject, body)
        print("[INFO] Alert sent.")
    else:
        print("[INFO] Threshold not crossed; no email sent.")

if __name__ == "__main__":
    main()
