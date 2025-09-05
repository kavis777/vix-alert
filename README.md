# VIX Alert (GitHub Actions + SendGrid)

FRED の VIXCLS（終値）を毎朝 JST でチェックし、**35 超**なら**固定メール 1 通**を送る最小構成。

## セットアップ

1. このリポを GitHub へ作成（下の自動化コマンドで可）
2. `Settings > Secrets and variables > Actions` に登録
   - **Secrets**
     - `SENDGRID_API_KEY` : SendGrid の API Key（Mail Send 権限）
     - `FROM_EMAIL` : 送信元（検証済み推奨）
     - `TO_EMAIL` : 宛先（固定）
   - **Variables**（任意）
     - `THRESHOLD` : 既定 35
     - `DRY_RUN` : `"true"`で送信せずログのみ
3. スケジュール: vix-alert.yml の cron を参照

## 手動テスト

- Actions → `vix-alert` → `Run workflow`
- まずは `DRY_RUN="true"` でログのみ確認 → 問題なければ外す
