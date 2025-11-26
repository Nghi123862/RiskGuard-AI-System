from pymongo import MongoClient

# Kết nối đến MongoDB chạy trên Docker (localhost:27017)
client = MongoClient("mongodb://localhost:27017/")

# Chọn Database tên là 'risk_system'
db = client["risk_system"]

# Các Collection (Bảng)
results_collection = db["scan_results"]