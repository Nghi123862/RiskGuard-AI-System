# File: backend/services/ai_engine.py (Phiên bản gọi Ollama Qwen2.5)
import requests
import json
import re

# --- CẤU HÌNH KẾT NỐI OLLAMA ---
# Đảm bảo bạn đã chạy lệnh: "ollama run qwen2.5:7b" trên máy
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"  # Hoặc đổi thành "qwen3:8b" nếu bạn đang có sẵn

print(f"🤖 Đang kết nối với AI Model: {MODEL_NAME}...")

# --- DANH SÁCH TỪ KHÓA CỨNG (Lớp bảo vệ 1) ---
HARD_KEYWORDS = [
    "giết người", "đầu độc", "tử vong", "tàn độc", "xác chết", 
    "hiếp dâm", "cưỡng bức", "ma túy", "con tin", "khủng bố",
    "xyanua", "thuốc độc", "tự tử", "đánh đập", "bạo hành", 
    "lừa đảo", "đánh bạc", "cá độ", "phản động", "việt tân"
]

def predict_risk_phobert(text):
    """
    Hàm phân tích rủi ro sử dụng Hybrid AI (Từ khóa + Qwen2.5 LLM)
    (Tên hàm giữ nguyên để không làm hỏng file worker.py)
    """
    if not text: return {"risk_score": 0, "label": "SAFE"}
    
    # Cắt ngắn văn bản để tránh quá tải
    short_text = text[:2000]
    text_lower = short_text.lower()
    
    # ---------------------------------------------------------
    # 1. QUÉT TỪ KHÓA (Rule-based) - Nhanh và Chắc chắn
    # ---------------------------------------------------------
    keyword_score = 0
    detected_keywords = []
    
    for word in HARD_KEYWORDS:
        if word in text_lower:
            detected_keywords.append(word)
            keyword_score += 25 
    
    keyword_score = min(keyword_score, 100)

    # ---------------------------------------------------------
    # 2. PHÂN TÍCH BẰNG QWEN (LLM) - Thông minh và Hiểu ngữ cảnh
    # ---------------------------------------------------------
    ai_score = 0
    ai_reason = ""
    
    try:
        # Prompt: Câu lệnh ra lệnh cho AI
        prompt = f"""
        Phân tích đoạn văn bản sau để phát hiện nội dung độc hại (bạo lực, tội phạm, lừa đảo, phản động, tệ nạn xã hội).
        
        Văn bản: "{short_text}"
        
        Yêu cầu trả lời CHỈ BẰNG định dạng JSON (không giải thích thêm):
        {{
            "score": <số điểm rủi ro từ 0-100>,
            "label": "<SAFE, WARNING, hoặc DANGEROUS>",
            "reason": "<giải thích ngắn gọn lý do bằng tiếng Việt>"
        }}
        """

        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json", # Bắt buộc Qwen trả về JSON chuẩn
            "options": {
                "temperature": 0.1 # Giảm độ sáng tạo để kết quả ổn định
            }
        }

        # Gửi request sang Ollama
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            result_json = response.json()
            ai_response_text = result_json.get("response", "{}")
            
            # Parse kết quả JSON từ AI
            try:
                ai_data = json.loads(ai_response_text)
                ai_score = ai_data.get("score", 0)
                ai_reason = ai_data.get("reason", "")
                
                # Nếu AI thấy rủi ro, thêm lý do vào danh sách hiển thị
                if ai_score > 30:
                    detected_keywords.insert(0, f"AI: {ai_reason}")
                    
            except json.JSONDecodeError:
                print("⚠️ Lỗi parse JSON từ AI")
        else:
            print(f"⚠️ Ollama Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Lỗi kết nối AI: {e}")

    # ---------------------------------------------------------
    # 3. TỔNG HỢP KẾT QUẢ
    # ---------------------------------------------------------
    final_score = max(keyword_score, ai_score)
    
    if final_score > 75: 
        final_label = "DANGEROUS"
    elif final_score > 30: 
        final_label = "WARNING"
    else: 
        final_label = "SAFE"

    return {
        "risk_score": final_score,
        "label": final_label,
        "detected_keywords": detected_keywords,
        "model_used": f"Hybrid (Keywords + {MODEL_NAME})"
    }