# kafka_producer.py
import json
from confluent_kafka import Producer
from config import KAFKA_BOOTSTRAP_SERVERS

class KafkaService:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'socket.timeout.ms': 10000,
        })

    def delivery_report(self, err, msg):
        """Hàm callback để biết tin nhắn đã gửi thành công hay chưa"""
        if err is not None:
            print(f'❌ Gửi thất bại: {err}')
        else:
            print(f'✅ Đã gửi tin nhắn tới topic: {msg.topic()} [{msg.partition()}]')

    def send_message(self, topic: str, data: dict):
        """Gửi dữ liệu (dict) vào Kafka"""
        try:
            # Trigger gửi tin nhắn bất đồng bộ
            self.producer.produce(
                topic,
                key=None, # Có thể dùng key nếu muốn đảm bảo thứ tự
                value=json.dumps(data).encode('utf-8'), # Chuyển Dict -> JSON bytes
                callback=self.delivery_report
            )
            # Yêu cầu gửi ngay lập tức
            self.producer.flush() 
            return True
        except Exception as e:
            print(f"Lỗi Kafka: {e}")
            return False

# Tạo một instance dùng chung
kafka_service = KafkaService()