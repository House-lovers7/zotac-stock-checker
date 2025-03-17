import requests
from bs4 import BeautifulSoup, Tag
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import logging
from typing import Optional, List, Union, Dict, Any, Tuple, cast
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
EMAIL_ADDRESS: Optional[str] = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD: Optional[str] = os.getenv('EMAIL_PASSWORD')
RECIPIENT_EMAIL: Optional[str] = os.getenv('RECIPIENT_EMAIL')

# 監視する商品のURL
PRODUCT_URL: str = "https://zotac.co.jp/product-category/graphics-card/?yith_wcan=1&filter_gpu=geforce-rtx-5090&query_type_gpu=or"

# 「在庫切れ」のテキスト(在庫がない時に表示されるテキスト)
OUT_OF_STOCK_TEXT: str = "在庫切れ"
# 在庫切れを示すクラス
OUT_OF_STOCK_CLASS: str = "ast-shop-product-out-of-stock"

# 在庫チェック間隔（秒）
CHECK_INTERVAL: int = 300  # 5分ごと

def send_email(product_name: str, product_url: str, price: str) -> bool:
    """
    商品が入荷した時にメールを送信する
    
    Args:
        product_name: 商品名
        product_url: 商品ページのURL
        price: 商品の価格
        
    Returns:
        bool: メール送信が成功したかどうか
    """
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL]):
        logging.error("メール設定が不完全です。.envファイルを確認してください。")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = f"【入荷通知】{product_name}が入荷しました！"
        
        body = f"""
        お知らせ: {product_name} が入荷しました！
        
        価格: {price}
        
        商品URL: {product_url}
        
        早めにご確認ください。
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(str(EMAIL_ADDRESS), str(EMAIL_PASSWORD))
        text = msg.as_string()
        server.sendmail(str(EMAIL_ADDRESS), str(RECIPIENT_EMAIL), text)
        server.quit()
        
        logging.info(f"入荷通知メールを送信しました: {product_name}")
        return True
    except Exception as e:
        logging.error(f"メール送信エラー: {e}")
        return False

def check_stock() -> None:
    """
    ZOTACウェブサイトで商品の在庫状況を確認する
    """
    try:
        headers: Dict[str, str] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response: requests.Response = requests.get(PRODUCT_URL, headers=headers)
        response.raise_for_status()
        
        soup: BeautifulSoup = BeautifulSoup(response.text, 'html.parser')
        
        # 商品リストを取得
        products: List[Tag] = soup.select('ul.products li.product')
        
        if not products:
            logging.warning("商品が見つかりませんでした。セレクタを確認してください。")
            return
        
        for product in products:
            # 商品名を取得
            product_name_elem: Optional[Tag] = product.select_one('.woocommerce-loop-product__title')
            if not product_name_elem:
                continue
            
            product_name: str = product_name_elem.text.strip()
            
            # 在庫状況を確認（スパンの存在で在庫切れを判断）
            out_of_stock_elem: Optional[Tag] = product.select_one('.' + OUT_OF_STOCK_CLASS)
            product_status: Union[List[str], str] = product.get('class', '')
            
            # リスト型または文字列型を考慮
            outofstock_in_status: bool = False
            if isinstance(product_status, list):
                outofstock_in_status = 'outofstock' in product_status
            else:
                outofstock_in_status = 'outofstock' in str(product_status)
            
            # 在庫切れでないか確認（out_of_stock_elemがなく、かつclassに'outofstock'が含まれていない場合は在庫あり）
            if not out_of_stock_elem and not outofstock_in_status:
                # 商品URLを取得
                product_link: Optional[Tag] = product.select_one('a.woocommerce-LoopProduct-link')
                product_url: Optional[str] = None
                
                if product_link and product_link.has_attr('href'):
                    product_url = cast(str, product_link['href'])
                
                # 価格を取得
                price_elem: Optional[Tag] = product.select_one('.price')
                price: str = price_elem.text.strip() if price_elem else "価格不明"
                
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

def main() -> None:
    """
    メインプログラム - 定期的に在庫をチェックする
    """
    logging.info("ZOTAC在庫監視スクリプトを開始しました")
    
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
