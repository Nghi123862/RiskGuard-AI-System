import json
import requests
import sys
import os
import time
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
from dotenv import load_dotenv 

# 1. Load biến môi trường
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_URL_SCAN
from database import results_collection
from services.crawler import crawl_website
from services.ai_engine import predict_risk_phobert
from services.url_checker import check_phishing_url

def create_topic_if_not_exists():
    print(f"🔧 Đang kiểm tra Topic '{KAFKA_TOPIC_URL_SCAN}'...")
    admin_client = AdminClient({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    new_topics = [NewTopic(KAFKA_TOPIC_URL_SCAN, num_partitions=1, replication_factor=1)]
    futures = admin_client.create_topics(new_topics)
    for topic, future in futures.items():
        try:
            future.result()
            print(f"✅ Đã tạo Topic: {topic}")
        except Exception as e:
            if "TopicExists" in str(e): print(f"✅ Topic '{topic}' đã tồn tại.")

def send_telegram_alert(url, risk_score, label, keywords):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
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
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"})
        print("📲 Đã gửi cảnh báo Telegram!")
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

print(f"👷 Worker Siêu cấp đang khởi động...")
create_topic_if_not_exists()

conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'risk_scanner_group_1',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

try:
    consumer = Consumer(conf)
    consumer.subscribe([KAFKA_TOPIC_URL_SCAN])
    print(f"✅ Đã kết nối Kafka! Sẵn sàng chiến đấu.")
except Exception as e:
    print(f"❌ Lỗi khởi tạo Kafka: {e}")
    sys.exit(1)

# --- VÒNG LẶP CHÍNH ---
try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        if msg.error(): continue

        try:
            data = json.loads(msg.value().decode('utf-8'))
        except: continue

        request_id = data.get('request_id')
        scan_type = data.get('type', 'URL')
        target = data.get('target')
        
        print(f"\n⚡ Xử lý: {target} [{scan_type}]")
        
        # Mặc định các biến
        content = ""
        title = target
        url_score = 0
        url_reasons = []

        # 1. NẾU LÀ URL: KIỂM TRA TRƯỚC KHI CRAWL
        if scan_type == 'URL':
            print("   ---> Checking URL Structure...")
            url_score, url_reasons = check_phishing_url(target)
            
            print("   ---> Crawling Web...")
            fetched_title, fetched_content = crawl_website(target)
            
            # LOGIC QUAN TRỌNG: CỨU VỚT LINK CHẾT
            if not fetched_title:
                print(f"   ❌ Lỗi crawl (Web chết/Không truy cập được)")
                
                # Nếu web chết NHƯNG tên miền nhìn rất Lừa đảo (> 50 điểm)
                if url_score > 50:
                    print("   ⚠️ PHÁT HIỆN: Link chết nhưng tên miền LỪA ĐẢO -> Vẫn xử lý!")
                    title = "URL Độc hại (Không truy cập được)"
                    # Tạo nội dung giả để AI phân tích tiếp
                    content = f"Cảnh báo bảo mật: Trang web này không tồn tại hoặc đã bị chặn. Tuy nhiên, đường dẫn chứa các dấu hiệu lừa đảo: {', '.join(url_reasons)}"
                else:
                    # Nếu link sạch mà web chết -> Bỏ qua (Lỗi mạng bình thường)
                    results_collection.insert_one({"request_id": request_id, "url": target, "status": "FAILED", "error": fetched_content, "scanned_at": datetime.utcnow()})
                    continue
            else:
                title = fetched_title
                content = fetched_content
            
        elif scan_type == 'FILE':
            print("   ---> Reading File...")
            content = data.get('content', "")
            title = f"FILE: {target}"

        # 2. PHÂN TÍCH AI & TỔNG HỢP (Chạy cho cả Link sống và Link chết nhưng độc)
        if content:
            print(f"   🧠 Running Hybrid AI...")
            analysis = predict_risk_phobert(content)

            # Cộng điểm từ URL Checker (Lấy điểm cao nhất)
            final_score = max(analysis['risk_score'], url_score)
            
            # Cập nhật nhãn
            final_label = analysis['label']
            if final_score > 75: 
                final_label = "DANGEROUS"
            elif final_score > 30 and final_label == "SAFE":
                final_label = "WARNING"
                
            # Gộp lý do từ URL vào danh sách từ khóa
            if url_reasons:
                analysis['detected_keywords'] = url_reasons + analysis['detected_keywords']

            analysis['risk_score'] = final_score
            analysis['label'] = final_label

            # Gửi cảnh báo
            if analysis['label'] in ['DANGEROUS', 'WARNING']:
                send_telegram_alert(target, analysis['risk_score'], analysis['label'], analysis['detected_keywords'])

            # Lưu DB
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

except KeyboardInterrupt:
    print("🛑 Đang dừng Worker...")
finally:
    consumer.close()