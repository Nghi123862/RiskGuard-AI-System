# File: backend/worker.py (Phiên bản Chuẩn Bảo Mật)
import json
import requests
import sys
import os
from datetime import datetime
from kafka import KafkaConsumer 
from dotenv import load_dotenv 

# 1. Load biến môi trường từ file .env
load_dotenv()

# 2. Lấy cấu hình Telegram (An toàn)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_URL_SCAN
from database import results_collection
from services.crawler import crawl_website
from services.ai_engine import predict_risk_phobert

def send_telegram_alert(url, risk_score, label, keywords):
    """Gửi cảnh báo về điện thoại"""
    # Kiểm tra nếu chưa cấu hình Token thì bỏ qua
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: 
        print("⚠️ Chưa cấu hình Telegram Token trong file .env")
        return
    
    # Chỉ cảnh báo nếu Nguy hiểm hoặc Rủi ro cao
    if label == "SAFE": return

    icon = "🚨" if label == "DANGEROUS" else "⚠️"
    msg = f"""
{icon} <b>CẢNH BÁO RỦI RO NỘI DUNG</b> {icon}
-----------------------------
🔗 <b>Nguồn:</b> {url}
📊 <b>Mức độ:</b> {label} (Điểm: {risk_score}/100)
🔍 <b>Từ khóa:</b> {', '.join(keywords)}
🕒 <b>Thời gian:</b> {datetime.now().strftime('%H:%M %d/%m')}
    """
    try:
        url_req = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url_req, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"})
        print("📲 Đã gửi cảnh báo Telegram!")
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

print(f"👷 Worker Siêu cấp đang khởi động...")

# Kết nối Kafka
try:
    consumer = KafkaConsumer(
        KAFKA_TOPIC_URL_SCAN,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id='risk_scanner_group_1',
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    print(f"✅ Đã kết nối Kafka! Sẵn sàng chiến đấu.")
except Exception as e:
    print(f"❌ Lỗi Kafka: {e}")
    sys.exit(1)

# Vòng lặp chính
for msg in consumer:
    data = msg.value
    request_id = data.get('request_id')
    scan_type = data.get('type', 'URL')
    target = data.get('target')
    
    print(f"\n⚡ Xử lý: {target} [{scan_type}]")
    content = ""
    title = target

    # 1. LẤY NỘI DUNG
    if scan_type == 'URL':
        print("   ---> Crawling Web...")
        fetched_title, fetched_content = crawl_website(target)
        if not fetched_title:
            print(f"   ❌ Lỗi crawl: {fetched_content}")
            results_collection.insert_one({"request_id": request_id, "url": target, "status": "FAILED", "error": fetched_content, "scanned_at": datetime.utcnow()})
            continue
        title = fetched_title
        content = fetched_content
        
    elif scan_type == 'FILE':
        print("   ---> Reading File...")
        content = data.get('content', "")
        title = f"FILE: {target}"

    # 2. PHÂN TÍCH AI
    if content:
        print(f"   🧠 Running Hybrid AI...")
        analysis = predict_risk_phobert(content)

        # 3. GỬI CẢNH BÁO TELEGRAM
        if analysis['label'] in ['DANGEROUS', 'WARNING']:
            send_telegram_alert(target, analysis['risk_score'], analysis['label'], analysis['detected_keywords'])

        # 4. LƯU DB
        result_doc = {
            "request_id": request_id,
            "url": target,
            "page_title": title,
            "content_preview": content[:500],
            "analysis": analysis,
            "status": "COMPLETED",
            "scanned_at": datetime.utcnow()
        }
        results_collection.insert_one(result_doc)
        print(f"✅ Xong! Label: {analysis['label']}")