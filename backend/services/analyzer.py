def analyze_content(text):
    """
    Input: Văn bản sạch
    Output: Dictionary chứa kết quả đánh giá rủi ro
    """
    text_lower = text.lower()
    
    # Từ khóa rủi ro mẫu (Bạn có thể thêm nhiều hơn)
    bad_keywords = ["lừa đảo", "cờ bạc", "cá độ", "vũ khí", "bạo động", "tấn công", "sexy", "18+"]
    
    detected_words = []
    score = 0
    
    # Logic chấm điểm đơn giản
    for word in bad_keywords:
        if word in text_lower:
            detected_words.append(word)
            score += 10 # Mỗi từ tìm thấy cộng 10 điểm rủi ro

    # Chuẩn hóa điểm rủi ro (0 -> 100)
    risk_score = min(score, 100) 
    
    # Gán nhãn
    if risk_score > 70:
        label = "DANGEROUS"
    elif risk_score > 30:
        label = "WARNING"
    else:
        label = "SAFE"

    return {
        "risk_score": risk_score,
        "label": label,
        "detected_keywords": detected_words
    }