# config.py
import os

# Cấu hình Kafka
# Lưu ý: Vì chạy code này ở máy local (bên ngoài Docker) nên kết nối vào localhost:9092
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092" 
KAFKA_TOPIC_URL_SCAN = "scan_url_requests"
KAFKA_TOPIC_FILE_SCAN = "scan_file_requests"

# Cấu hình API
API_TITLE = "Risk Assessment System API"
API_VERSION = "v1.0"