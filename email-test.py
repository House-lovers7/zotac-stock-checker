import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 環境変数のロード
load_dotenv()

# メール設定を取得
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

print(f"送信元メール: {EMAIL_ADDRESS}")
print(f"宛先メール: {RECIPIENT_EMAIL}")
print(f"パスワード設定: {'あり' if EMAIL_PASSWORD else 'なし'}")

# メール送信テスト関数
def test_email():
    try:
        # メール作成
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = "【テスト】ZOTAC在庫監視ツールのメール送信テスト"
        
        body = """
        これはZOTAC在庫監視ツールのメール送信テストです。
        
        このメールが届いていれば、設定は正常です。
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # サーバー接続
        print("SMTPサーバーに接続しています...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # ログイン
        print("ログインしています...")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        # メール送信
        print("メールを送信しています...")
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, text)
        server.quit()
        
        print("メール送信成功！宛先のメールボックスを確認してください。")
        return True
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

# テスト実行
if __name__ == "__main__":
    print("メール送信テストを開始します...")
    
    # 設定チェック
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL]):
        print("メール設定が不完全です。.envファイルを確認してください。")
    else:
        test_email()
