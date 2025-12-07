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
import secrets
from datetime import datetime, timedelta
from typing import Annotated
from bson import ObjectId

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
# Thư viện đọc file mới cài
from pypdf import PdfReader
from docx import Document

# --- CẤU HÌNH BẢO MẬT ---
SECRET_KEY = "RISKGUARD_SECRET_KEY_SIEU_BAO_MAT_2025" # Bạn có thể đổi chuỗi này tùy thích
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Token sống trong 30 phút

# Giả lập Database người dùng (User: admin / Pass: admin123)
# Pass đã được mã hóa bằng Bcrypt
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        # 👇 DÁN CHUỖI BẠN VỪA COPY VÀO GIỮA DẤU NHÁY NÀY 👇
        "hashed_password": "$2b$12$/tCYU8kNLrcu77/ReH5VQeYcqzocVfRL6vHwzwrIC4n0J/AhZnBuG" 
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

app = FastAPI(title=API_TITLE, version=API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- CÁC HÀM BỔ TRỢ BẢO MẬT ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = FAKE_USERS_DB.get(username)
    if user is None:
        raise credentials_exception
    return user

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
# 1. API ĐĂNG NHẬP (MỚI) - Để lấy Token
@app.post("/api/v1/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = FAKE_USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/results")
def get_all_results(current_user: Annotated[dict, Depends(get_current_user)]):
    return list(results_collection.find({}, {"_id": 0}).sort("scanned_at", -1).limit(50))

@app.delete("/api/v1/results/{request_id}")
def delete_scan_result(request_id: str, current_user: Annotated[dict, Depends(get_current_user)]):
    # Tìm và xóa dựa trên request_id
    result = results_collection.delete_one({"request_id": request_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi để xóa")
    return {"message": "Đã xóa thành công!"}

@app.post("/api/v1/scan/url")
def request_url_scan(request: URLScanRequest, current_user: Annotated[dict, Depends(get_current_user)]):
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
# SỬA DÒNG NÀY: Đảo current_user lên trước file
async def upload_file_scan(
    current_user: Annotated[dict, Depends(get_current_user)], # <--- Đưa lên đầu
    file: UploadFile = File(...) 
):
    request_id = str(uuid.uuid4())
    
    # ... (Phần code bên trong giữ nguyên không đổi) ...
    
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
# --- [MỚI] TÍNH NĂNG CHAT VỚI AI ---
class ChatRequest(BaseModel):
    message: str
    context: str = "" # Nội dung bài viết đang xem (để AI hiểu ngữ cảnh)

@app.post("/api/v1/chat")
def chat_with_ai(request: ChatRequest, current_user: Annotated[dict, Depends(get_current_user)]):
    try:
        # Chuẩn bị Prompt (Câu lệnh)
        # Kỹ thuật: RAG đơn giản (Retrieval Augmented Generation)
        # Đưa nội dung bài viết vào để AI trả lời dựa trên đó
        full_prompt = f"""
        Dựa trên nội dung văn bản sau đây:
        ---
        {request.context[:2000]} 
        ---
        
        Hãy trả lời câu hỏi của người dùng: "{request.message}"
        Trả lời ngắn gọn, súc tích bằng tiếng Việt.
        """

        # Gọi sang Ollama (Qwen2.5)
        # Lưu ý: Bạn có thể dùng chung hàm trong ai_engine hoặc gọi thẳng requests ở đây cho nhanh
        import requests
        OLLAMA_URL = "http://localhost:11434/api/generate"
        
        payload = {
            "model": "qwen3:8b", # Hoặc qwen3:8b tùy máy bạn
            "prompt": full_prompt,
            "stream": False
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            result_text = response.json().get("response", "AI không trả lời.")
            return {"reply": result_text}
        else:
            return {"reply": "Lỗi kết nối với bộ não AI."}

    except Exception as e:
        print(f"Lỗi Chat API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    