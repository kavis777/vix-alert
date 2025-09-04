# VIX Alert (GitHub Actions + SendGrid)

FREDのVIXCLS（終値）を毎朝JSTでチェックし、**35超**なら**固定メール1通**を送る最小構成。

## セットアップ
1. このリポをGitHubへ作成（下の自動化コマンドで可）
2. `Settings > Secrets and variables > Actions` に登録
   - **Secrets**
     - `SENDGRID_API_KEY` : SendGridのAPI Key (Mail Send権限)
     - `FROM_EMAIL` : 送信元（検証済み推奨）
     - `TO_EMAIL` : 宛先（固定）
   - **Variables**（任意）
     - `THRESHOLD` : 既定 35
     - `DRY_RUN` : `"true"`で送信せずログのみ
3. スケジュール: `22:30 UTC` 実行 → JSTで翌朝 `07:30`

## 手動テスト
- Actions → `vix-alert` → `Run workflow`  
- まずは `DRY_RUN="true"` でログのみ確認 → 問題なければ外す
