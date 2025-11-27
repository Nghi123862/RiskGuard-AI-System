# File: backend/main.py (Phiên bản hỗ trợ File Upload)
import uuid
import shutil
import os
import pytesseract
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import API_TITLE, API_VERSION, KAFKA_TOPIC_URL_SCAN
from kafka_producer import kafka_service
from database import results_collection
from PIL import Image


# Thư viện đọc file mới cài
from pypdf import PdfReader
from docx import Document

app = FastAPI(title=API_TITLE, version=API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLScanRequest(BaseModel):
    url: str
    requested_by: str = "admin"

# --- HÀM PHỤ TRỢ: ĐỌC NỘI DUNG FILE ---
def extract_text_from_file(file_path: str, filename: str):
    text = ""
    try:
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            reader = PdfReader(file_path)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif lower_name.endswith(".docx"):
            doc = Document(file_path)
            for para in doc.paragraphs: text += para.text + "\n"
        
        # --- THÊM PHẦN NÀY: XỬ LÝ ẢNH ---
        elif lower_name.endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='vie') # lang='vie' để đọc tiếng Việt
        # --------------------------------
        
        else: # .txt
            with open(file_path, "r", encoding="utf-8") as f: text = f.read()
    except Exception as e:
        print(f"Lỗi đọc file: {e}")
        return None
    return text

# --- API ENDPOINTS ---

@app.get("/api/v1/results")
def get_all_results():
    return list(results_collection.find({}, {"_id": 0}).sort("scanned_at", -1).limit(50))

@app.post("/api/v1/scan/url")
def request_url_scan(request: URLScanRequest):
    request_id = str(uuid.uuid4())
    # Gửi URL vào Kafka, Worker sẽ tự Crawl
    payload = {
        "request_id": request_id,
        "type": "URL",         # Đánh dấu là URL
        "target": request.url,
        "content": None,       # Chưa có nội dung
        "timestamp": datetime.utcnow().isoformat(),
        "status": "QUEUED"
    }
    kafka_service.send_message(KAFKA_TOPIC_URL_SCAN, payload)
    return {"message": "Đã tiếp nhận URL", "request_id": request_id}

# [MỚI] API UPLOAD FILE
@app.post("/api/v1/scan/file")
async def upload_file_scan(file: UploadFile = File(...)):
    request_id = str(uuid.uuid4())
    
    # 1. Lưu file tạm thời để đọc
    os.makedirs("temp_uploads", exist_ok=True)
    temp_path = f"temp_uploads/{request_id}_{file.filename}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Đọc nội dung file ngay tại đây
    extracted_text = extract_text_from_file(temp_path, file.filename)
    
    # Xóa file tạm cho nhẹ máy
    os.remove(temp_path)
    
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Không đọc được nội dung file (File rỗng hoặc lỗi)")

    # 3. Gửi NỘI DUNG VĂN BẢN vào Kafka (Thay vì gửi file path)
    # Worker nhận được cái này sẽ bỏ qua bước Crawl, chạy thẳng vào AI
    payload = {
        "request_id": request_id,
        "type": "FILE",            # Đánh dấu là File
        "target": file.filename,   # Tên file
        "content": extracted_text[:5000], # Gửi nội dung (cắt 5000 ký tự đầu để Kafka không bị nghẽn)
        "timestamp": datetime.utcnow().isoformat(),
        "status": "QUEUED"
    }
    
    kafka_service.send_message(KAFKA_TOPIC_URL_SCAN, payload)
    return {"message": "Đã tiếp nhận File", "request_id": request_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    