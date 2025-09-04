import os
import sys
import csv
import io
import json
from urllib.request import urlopen, Request

import requests  # SendGrid API

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"

THRESHOLD = float(os.getenv("THRESHOLD", "35"))
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DRY_RUN = os.getenv("DRY_RUN", "").lower() == "true"

def fetch_latest_vix():
    # FREDのCSV（VIXCLS）を取得し、最後の有効値を終値として採用
    req = Request(FRED_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(data))
    last_date, last_value = None, None
    for row in reader:
        date = row["DATE"]
        val = row["VIXCLS"].strip()
        if not val or val == ".":
            continue
        last_date = date
        last_value = float(val)

    if last_date is None or last_value is None:
        raise RuntimeError("No valid VIXCLS value found from FRED.")
    return last_date, last_value

def send_email_sendgrid(subject: str, body: str):
    if DRY_RUN:
        print("[DRY_RUN] Would send email:")
        print("Subject:", subject)
        print(body)
        return

    if not (SENDGRID_API_KEY and TO_EMAIL and FROM_EMAIL):
        raise RuntimeError("Missing SENDGRID_API_KEY or TO_EMAIL or FROM_EMAIL.")

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
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"SendGrid error: {r.status_code} {r.text}")

def main():
    date_str, value = fetch_latest_vix()
    print(f"[INFO] Latest VIXCLS: {value:.2f} (date={date_str}), threshold={THRESHOLD}")

    if value > THRESHOLD:
        subject = f"[VIXアラート] 35超え: {value:.2f}（{date_str}）"
        body = (
            "VIX 終値が閾値を上回りました。\n"
            f"- 日付（FRED観測日/米営業日）: {date_str}\n"
            f"- VIX 終値: {value:.2f}\n"
            f"- 閾値: {THRESHOLD}\n"
            "データソース: FRED VIXCLS（終値）\n"
            "備考: 最小構成につき同一日の重複送信抑止は未実装\n"
        )
        send_email_sendgrid(subject, body)
        print("[INFO] Alert sent.")
    else:
        print("[INFO] Threshold not crossed; no email sent.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[ERROR]", e, file=sys.stderr)
        sys.exit(1)
