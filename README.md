# VIX アラート通知システム

GitHub Actions と SendGrid を利用して、**CBOE VIX 指数（^VIX）の終値が閾値を超えたときにメール通知を送る仕組み**です。  
データソースには Yahoo Finance を使用しています。

---

## 🚀 セットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/kavis777/vix-alert.git
cd vix-alert
```

### 2. SendGrid の準備

1. **アカウント作成**

   - [SendGrid](https://sendgrid.com/) にアクセスして無料アカウントを作成します。
   - Free プランでも 1 日 100 通まで送信可能です。

2. **API キーの発行**

   - ダッシュボード → **Settings → API Keys**
   - 「Create API Key」をクリックし、`Full Access` ではなく **Mail Send 権限のみ** を選択して発行
   - 発行されたキーをコピー（あとで GitHub Secrets に設定）

3. **送信元アドレスの認証**
   SendGrid は「なりすましメール防止」のため、必ず送信元アドレスを認証する必要があります。方法は 2 つ：

   - **Single Sender Verification（簡易認証）**
     - ダッシュボード → **Sender Authentication → Verify an Address**
     - Gmail などの任意のメールアドレスを入力 → 認証メールが届く → リンクをクリックして完了
     - 個人利用やテストにはこれで十分
   - **Domain Authentication（推奨・本番向け）**
     - 自分のドメインを持っている場合はこちらを推奨
     - DNS（SPF/DKIM）設定が必要ですが、到達率が大幅に向上します
     - 例: `alert@yourdomain.com` のような独自ドメインのアドレスを使えるようになる

### 3. GitHub Secrets/Variables 設定

リポジトリ → **Settings → Secrets and variables → Actions**

- **Secrets**

  - `SENDGRID_API_KEY` : SendGrid API キー
  - `FROM_EMAIL` : SendGrid で認証した送信元アドレス
  - `TO_EMAIL` : 通知したい任意のメールアドレス
    - 最初は迷惑メールフォルダーに入ることが多いので、必ず「迷惑メールではない」に分類してください
    - 送信元と送信先を同じ Gmail にすると迷惑判定されやすいので、できれば別にするのがオススメです

- **Variables**
  - `THRESHOLD` : 通知判定の閾値（例: `35`）
  - `DRY_RUN` : `"true"` なら送信せずログ出力のみ

---

## ⚙️ 動作仕様

### 実行頻度

- GitHub Actions は **毎時 0 分（UTC）** に実行されます。

### 米国市場時間の制御

- 通知判定は **米国東部時間(ET) 16:10〜23:59** の間にのみ実施。
- これにより「市場クローズ後に終値が反映された時間帯」に限定して判定します。

### データソース

- Yahoo Finance の `^VIX` ティッカーから直近データを取得。
- 最新行の日付が「当日の米国日付」と一致する場合のみ判定対象。
- 祝日や休場日はスキップ。

### 通知条件

- `VIX終値 > THRESHOLD` の場合に通知。

### 1 日最大 1 通の制御

- GitHub Actions Cache を用いて「当日送信済みマーカー」を保存。
- 同じ米国日付に複数回実行されても、**最初の 1 回しか通知されない**。
- 翌営業日になるとキャッシュキーが切り替わり、再度送信可能。

---

## ✉️ 通知内容

- **件名例**

  ```
  [VIXアラート] 2025-09-05 終値 52.33 (閾値 35超)
  ```

- **本文例**

  ```
  VIX 終値が閾値を上回りました。
  - 日付: 2025-09-05
  - VIX 終値: 52.33
  - 閾値: 35
  データソース: Yahoo Finance (^VIX)

  このメールはGitHub Actions + SendGridによる自動通知です。
  ```

---

## ⚠️ 注意事項

- **迷惑メール**: Gmail 等では最初は迷惑メール判定されやすいです。「迷惑メールでない」フィルターを作成してください。
- **祝日**: 米国市場休場日は通知は送られません。
- **安定運用**: SendGrid のドメイン認証（SPF/DKIM 設定）を行うと到達率が向上します。
- **無料枠**: SendGrid Free プランは 1 日 100 通までです。
