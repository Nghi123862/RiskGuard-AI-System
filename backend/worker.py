# File: backend/worker.py (Phiên bản Chuẩn - Hỗ trợ URL & FILE)
import json
from datetime import datetime
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_URL_SCAN
from database import results_collection
from services.crawler import crawl_website
from services.ai_engine import predict_risk_phobert

# --- LƯU Ý: Chọn thư viện Kafka phù hợp với máy bạn ---
# Nếu bạn dùng kafka-python-ng (như đã sửa ở bước trước), hãy dùng dòng này:
from kafka import KafkaConsumer 

# Nếu bạn dùng confluent-kafka, hãy dùng dòng này (bỏ comment):
# from confluent_kafka import Consumer

print(f"👷 Worker đang khởi động...")

# Cấu hình Consumer (Dùng kafka-python-ng cho ổn định trên Windows)
try:
    consumer = KafkaConsumer(
        KAFKA_TOPIC_URL_SCAN,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id='risk_scanner_group_1',
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    print(f"✅ Đã kết nối Kafka! Đang lắng nghe topic '{KAFKA_TOPIC_URL_SCAN}'")
except Exception as e:
    print(f"❌ Lỗi kết nối Kafka: {e}")
    exit(1)

try:
    # Vòng lặp Consumer của kafka-python-ng hơi khác confluent một chút
    for msg in consumer:
        # Lấy dữ liệu đã được giải mã tự động
        data = msg.value
        
        request_id = data.get('request_id')
        scan_type = data.get('type', 'URL') 
        target = data.get('target')         
        
        print(f"\n⚡ Đang xử lý: {target} (Loại: {scan_type})")

        content = ""
        title = target

        # --- LOGIC RẼ NHÁNH ---
        if scan_type == 'URL':
            # Nếu là URL -> Phải đi Crawl
            print("   ---> Đang tải trang web...")
            fetched_title, fetched_content = crawl_website(target)
            
            if not fetched_title: # Crawl lỗi
                print(f"   ❌ Lỗi crawl: {fetched_content}")
                # Lưu lỗi vào DB để Frontend biết
                results_collection.insert_one({
                    "request_id": request_id,
                    "url": target,
                    "status": "FAILED",
                    "error": fetched_content,
                    "scanned_at": datetime.utcnow()
                })
                continue

            title = fetched_title
            content = fetched_content
            
        elif scan_type == 'FILE':
            # Nếu là FILE -> Nội dung đã được Backend gửi kèm
            print("   ---> Đang đọc nội dung file từ tin nhắn...")
            content = data.get('content', "")
            title = f"FILE: {target}"

        # --- CHẠY AI (Phần chung) ---
        if content:
            print(f"   🧠 Đang chạy AI Hybrid phân tích...")
            analysis = predict_risk_phobert(content)

            # Đóng gói kết quả
            result_doc = {
                "request_id": request_id,
                "url": target,
                "page_title": title,
                "content_preview": content[:500], # Lưu 500 ký tự đầu
                "analysis": analysis,
                "status": "COMPLETED",
                "scanned_at": datetime.utcnow()
            }
            
            # Lưu vào MongoDB
            results_collection.insert_one(result_doc)
            print(f"✅ Đã lưu kết quả! [Label: {analysis['label']}]")

except KeyboardInterrupt:
    print("🛑 Đang dừng Worker...")
finally:
    consumer.close()