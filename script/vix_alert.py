import os
import requests
import yfinance as yf
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from pathlib import Path

THRESHOLD = float(os.getenv("THRESHOLD"))
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DRY_RUN = (os.getenv("DRY_RUN") or "").lower() == "true"

STATE_DIR = Path(".vix_cache")
STATE_DIR.mkdir(exist_ok=True)
MARKER = STATE_DIR / "sent.marker"

def in_post_close_window_today_et():
    ny = ZoneInfo("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:  # 土日
        return False
    # 16:10〜23:59 ET のみ実行（クローズ後にデータが出揃う想定）
    start = dtime(16, 10)
    end   = dtime(23, 59, 59)
    return start <= now.time() <= end

def fetch_latest_vix():
    vix = yf.Ticker("^VIX")
    hist = vix.history(period="7d")  # 念のため少し広め
    last = hist.tail(1).iloc[0]
    vix_date = last.name.tz_localize(None).date()  # Index=Timestamp
    value = float(last["Close"])
    return str(vix_date), value

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
    headers = {"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()

def main():
    # 当日中にすでに送っていたらスキップ（キャッシュ復元でマーカーあり）
    if MARKER.exists():
        print("[INFO] Already sent today (cache marker exists). Skip.")
        return

    # クローズ後の当日時間帯のみ実行（場中/深夜帯の誤送防止）
    if not in_post_close_window_today_et():
        print("[INFO] Outside post-close window. Skip.")
        return

    ny = ZoneInfo("America/New_York")
    ny_today = datetime.now(ny).date()

    date_str, value = fetch_latest_vix()
    vix_date = datetime.fromisoformat(date_str).date()

    # yfinanceの最終行が今日(ET)の終値になっていなければスキップ（祝日/未更新対策）
    if vix_date != ny_today:
        print(f"[INFO] Latest daily VIX is for {vix_date}, but today is {ny_today}. Skip.")
        return

    print(f"[INFO] Latest VIX: {value:.2f} (date={date_str}), threshold={THRESHOLD}")
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
        MARKER.write_text("sent")
        print("[INFO] Alert sent and marker written.")
    else:
        print("[INFO] Threshold not crossed; no email sent.")

if __name__ == "__main__":
    main()
