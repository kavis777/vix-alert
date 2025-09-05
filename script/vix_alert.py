# script/vix_alert.py
import os
import requests
import yfinance as yf

THRESHOLD = float(os.getenv("THRESHOLD"))
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DRY_RUN = (os.getenv("DRY_RUN") or "").lower() == "true"

def fetch_latest_vix():
    vix = yf.Ticker("^VIX")
    hist = vix.history(period="5d")
    last_row = hist.tail(1).iloc[0]
    date_str = str(last_row.name.date())
    value = float(last_row["Close"])
    return date_str, value

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
    print(f"[INFO] Latest VIXCLS (Yahoo Finance): {value:.2f} (date={date_str}), threshold={THRESHOLD}")
    if value > THRESHOLD:
        subject = f"[VIXアラート] {date_str} 終値 {value:.2f} (閾値 {THRESHOLD}超)"
        body = (
            f"VIX 終値が閾値を上回りました。\n"
            f"- 日付: {date_str}\n"
            f"- VIX 終値: {value:.2f}\n"
            f"- 閾値: {THRESHOLD}\n"
            "データソース: Yahoo Finance (^VIX)\n"
            "\n"
            "このメールはGitHub Actions + SendGridによる自動通知です。"
        )
        send_email(subject, body)
        print("[INFO] Alert sent.")
    else:
        print("[INFO] Threshold not crossed; no email sent.")

if __name__ == "__main__":
    main()
