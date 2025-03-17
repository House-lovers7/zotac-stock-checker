import sys

# テストモードを有効にする引数をチェック
if len(sys.argv) > 1 and sys.argv[1] == "--test":
    print("テストモードで実行します - 実際のサイトにアクセスせずに在庫ありとしてメールを送信します。")
    TEST_MODE = True
else:
    TEST_MODE = False

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import logging
import os
from dotenv import load_dotenv

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("zotac_stock_checker.log"),
        logging.StreamHandler()
    ]
)

# 環境変数のロード
load_dotenv()

# メール設定
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# メール設定チェック
if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL]):
    logging.error("メール設定が不完全です。.envファイルを確認してください。")
    sys.exit(1)

# 監視する商品のURL
PRODUCT_URL = "https://zotac.co.jp/product-category/graphics-card/?yith_wcan=1&filter_gpu=geforce-rtx-5090&query_type_gpu=or"

# 「在庫切れ」のテキスト(在庫がない時に表示されるテキスト)
OUT_OF_STOCK_TEXT = "在庫切れ"
# 在庫切れを示すクラス
OUT_OF_STOCK_CLASS = "ast-shop-product-out-of-stock"

# 在庫チェック間隔（秒）
CHECK_INTERVAL = 60 # 通常は3600（1時間）が推奨

def send_email(product_name, product_url, price):
    """
    商品が入荷した時にメールを送信する
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        
        # テストモードの場合はタイトルを変更
        if TEST_MODE:
            msg['Subject'] = f"【テスト】{product_name}の在庫通知テスト"
        else:
            msg['Subject'] = f"【入荷通知】{product_name}が入荷しました！"
        
        body = f"""
        {'これはテストメールです。' if TEST_MODE else 'お知らせ:'} {product_name} {'が入荷しました！' if not TEST_MODE else 'の在庫状況をチェックするテストです。'}
        
        価格: {price}
        
        商品URL: {product_url}
        
        {'このメールは在庫監視スクリプトのテストモードから送信されています。' if TEST_MODE else '早めにご確認ください。'}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        logging.info("SMTPサーバーに接続しています...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        logging.info("ログインしています...")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        logging.info("メールを送信しています...")
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, text)
        server.quit()
        
        logging.info(f"{'テスト' if TEST_MODE else '入荷通知'}メールを送信しました: {product_name}")
        return True
    except Exception as e:
        logging.error(f"メール送信エラー: {e}")
        return False

def check_stock():
    """
    ZOTACウェブサイトで商品の在庫状況を確認する
    """
    # テストモードの場合は実際のサイトにアクセスせずにテストメールを送信
    if TEST_MODE:
        logging.info("テストモード: サイトへのアクセスをスキップしてテストメールを送信します")
        product_name = "ZOTAC GAMING GeForce RTX 5090 SOLID OC"
        product_url = "https://zotac.co.jp/product/zotac-gaming-geforce-rtx-5090-solid-oc/"
        price = "¥452,800（税込）"
        send_email(product_name, product_url, price)
        return
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(PRODUCT_URL, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 商品リストを取得
        products = soup.select('ul.products li.product')
        
        if not products:
            logging.warning("商品が見つかりませんでした。セレクタを確認してください。")
            return
        
        for product in products:
            # 商品名を取得
            product_name_elem = product.select_one('.woocommerce-loop-product__title')
            if not product_name_elem:
                continue
            
            product_name = product_name_elem.text.strip()
            
            # 在庫状況を確認（スパンの存在で在庫切れを判断）
            out_of_stock_elem = product.select_one('.' + OUT_OF_STOCK_CLASS)
            product_status = product.get('class', '')
            
            # 在庫切れでないか確認（out_of_stock_elemがなく、かつclassに'outofstock'が含まれていない場合は在庫あり）
            if not out_of_stock_elem and 'outofstock' not in product_status:
                # 商品URLを取得
                product_link = product.select_one('a.woocommerce-LoopProduct-link')
                product_url = product_link['href'] if product_link and 'href' in product_link.attrs else None
                
                # 価格を取得
                price_elem = product.select_one('.price')
                price = price_elem.text.strip() if price_elem else "価格不明"
                
                logging.info(f"商品が入荷しました！: {product_name}")
                
                # メール送信
                if product_url:
                    send_email(product_name, product_url, price)
                else:
                    logging.error(f"商品URLが見つかりませんでした: {product_name}")
            else:
                logging.info(f"商品 {product_name} は在庫切れです。")
    
    except Exception as e:
        logging.error(f"在庫チェックエラー: {e}")

def main():
    """
    メインプログラム - 定期的に在庫をチェックする
    """
    logging.info(f"ZOTAC在庫監視スクリプトを開始しました{'（テストモード）' if TEST_MODE else ''}")
    
    if TEST_MODE:
        logging.info("テストモードでは1回だけ実行してメールを送信します")
        check_stock()
        logging.info("テスト完了")
        return
    
    try:
        while True:
            logging.info("在庫チェックを実行します...")
            check_stock()
            logging.info(f"{CHECK_INTERVAL}秒後に再チェックします")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logging.info("プログラムを終了します")

if __name__ == "__main__":
    main()
