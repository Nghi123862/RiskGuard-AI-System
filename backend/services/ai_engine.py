from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

# Cấu hình Model PhoBERT
MODEL_NAME = "wonrax/phobert-base-vietnamese-sentiment"

print("⏳ Đang tải Model AI...")

# 1. Tải Tokenizer & Model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
ai_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

print("✅ Model AI đã sẵn sàng hoạt động!")

# ==============================================================================
# [PHẦN MỚI 1] DANH SÁCH TỪ KHÓA CỨNG (BLACKLIST)
# Bạn có thể thêm bao nhiêu từ tùy thích vào đây
# ==============================================================================
HARD_KEYWORDS = [
    "giết người", "đầu độc", "tử vong", "tàn độc", "xác chết", 
    "hiếp dâm", "cưỡng bức", "ma túy", "con tin", "khủng bố",
    "xyanua", "thuốc độc", "tự tử", "đánh đập", "bạo hành", "lừa đảo"
]

def predict_risk_phobert(text):
    """
    Input: Đoạn văn bản tiếng Việt
    Output: Dictionary kết quả đánh giá rủi ro (Kết hợp Từ khóa + AI)
    """
    short_text = text[:1000] # Lấy 1000 ký tự đầu
    text_lower = short_text.lower()
    
    # Biến lưu kết quả
    risk_score = 0
    final_label = "SAFE"
    detected_keywords = []

    # ==========================================================================
    # [PHẦN MỚI 2] QUÉT TỪ KHÓA TRƯỚC (ƯU TIÊN 1)
    # ==========================================================================
    keyword_score = 0
    for word in HARD_KEYWORDS:
        if word in text_lower:
            detected_keywords.append(word)
            keyword_score += 25 # Tìm thấy 1 từ cộng 25 điểm (4 từ là max 100)
    
    # Chốt điểm từ khóa (tối đa 100)
    keyword_score = min(keyword_score, 100)

    # ==========================================================================
    # [PHẦN CŨ] CHẠY AI (ƯU TIÊN 2)
    # ==========================================================================
    ai_score = 0
    try:
        result = ai_pipeline(short_text)[0]
        label = result['label']
        confidence = result['score']

        if label == 'NEG': # Nếu AI thấy tiêu cực
            ai_score = int(confidence * 100)
            # Chỉ thêm từ khóa AI nếu chưa có từ khóa cứng nào
            if keyword_score == 0:
                detected_keywords.append("AI_NEGATIVE_CONTENT")
        else:
            # Tích cực hoặc trung tính
            ai_score = 0 

    except Exception as e:
        print(f"Lỗi AI: {e}")
        ai_score = 0

    # ==========================================================================
    # [PHẦN MỚI 3] TỔNG HỢP KẾT QUẢ
    # Lấy điểm cao nhất giữa (Từ khóa) và (AI)
    # ==========================================================================
    
    final_score = max(keyword_score, ai_score)

    # Gán nhãn dựa trên điểm số cuối cùng
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
        "model_used": "Hybrid (PhoBERT + Keywords)"
    }