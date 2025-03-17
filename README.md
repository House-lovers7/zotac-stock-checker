# ZOTAC在庫監視ツール

ZOTAC公式サイトの商品在庫（特にグラフィックカード）を監視し、入荷時にメール通知を送信するPythonスクリプトです。

## ディレクトリ構成

```
zotac-stock-checker/
│
├── zotac_stock_checker.py     # 通常の在庫監視スクリプト
├── zotac-test-mode.py         # テストモード付き在庫監視スクリプト
├── email-test.py              # メール送信のみをテストするスクリプト
├── zotac_stock_checker.log    # 実行ログファイル（実行時に自動生成）
├── .env                       # 環境変数を設定するファイル（メール設定など）
└── requirements.txt           # 必要なPythonパッケージのリスト
```

## 必要条件

* Python 3.6以上
* インターネット接続
* メール送信用のアカウント（Gmail推奨）

## インストール方法

1. 必要なパッケージをインストール:

   ```bash
   pip install requests beautifulsoup4 python-dotenv
   ```

   または:

   ```bash
   pip install -r requirements.txt
   ```
2. `.env` ファイルを作成し、以下の内容を設定:

   ```
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   RECIPIENT_EMAIL=recipient_email@example.com
   ```

   **注意** : Gmailを使用する場合、通常のパスワードではなく「アプリパスワード」が必要です。
   これはGoogleアカウントの2段階認証を有効にした後に取得できます。
   [Google アカウント設定](https://myaccount.google.com/apppasswords) から取得してください。

## 使用方法

### メール送信のテスト

まず、メール設定が正しいかテストします:

```bash
python email-test.py
```

### テストモードでの実行

実際のサイトにアクセスせずにテストメールを送信します:

```bash
python zotac-test-mode.py --test
```

### 通常モードでの実行

実際に在庫監視を開始します:

```bash
python zotac_stock_checker.py
```

または:

```bash
python zotac-test-mode.py
```

### バックグラウンド実行（Linux/macOS）

```bash
nohup python zotac_stock_checker.py > nohup.out 2>&1 &
```

## カスタマイズ

スクリプト内の以下の変数を変更することで、動作をカスタマイズできます:

* `PRODUCT_URL`: 監視したい製品ページのURL
* `CHECK_INTERVAL`: 在庫チェックの間隔（秒単位、テスト時は60秒、本番では3600秒=1時間推奨）
* `OUT_OF_STOCK_TEXT`: 在庫切れを示すテキスト
* `OUT_OF_STOCK_CLASS`: 在庫切れを示すHTMLクラス

## 常時実行の設定

### Linuxサーバーの場合（systemdサービス）

1. サービスファイルの作成:

```bash
sudo nano /etc/systemd/system/zotac-checker.service
```

2. 以下の内容を記述:

```
[Unit]
Description=ZOTAC Stock Checker Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /フルパス/zotac_stock_checker.py
WorkingDirectory=/フルパス/
Restart=always
User=あなたのユーザー名

[Install]
WantedBy=multi-user.target
```

3. サービスの有効化と開始:

```bash
sudo systemctl enable zotac-checker.service
sudo systemctl start zotac-checker.service
```

### Windowsの場合（タスクスケジューラ）

1. タスクスケジューラを開く
2. 「基本タスクの作成」→名前と説明を入力
3. トリガーを「コンピューターの起動時」に設定
4. アクションを「プログラムの開始」に設定
5. プログラムに `python`、引数に `フルパス\zotac_stock_checker.py`を指定

## ログの確認

実行中のスクリプトのログは `zotac_stock_checker.log` に記録されます:

```bash
tail -f zotac_stock_checker.log
```

## トラブルシューティング

* **メールが送信されない** :
* `.env`ファイルの設定（特にアプリパスワード）を確認
* Gmailの「安全性の低いアプリのアクセス」設定を確認
* スパムフォルダを確認
* **商品が検出されない** :
* ウェブサイトの構造が変更された可能性があります
* HTMLセレクタ（`OUT_OF_STOCK_CLASS`など）を確認・更新
* **エラーが発生する** :
* ログファイルでエラーメッセージを確認
* 必要なパッケージがすべてインストールされているか確認

## 免責事項

このスクリプトは個人利用を目的としています。ウェブサイトに過度な負荷をかけないよう、チェック間隔は適切な値（1時間以上推奨）に設定してください。

---

最終更新日: 2025年3月17日
