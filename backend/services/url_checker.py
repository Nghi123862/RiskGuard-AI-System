import re
from urllib.parse import urlparse

# Danh sách các từ khóa thường thấy trong link lừa đảo
PHISHING_KEYWORDS = [
    "verify", "account", "secure", "banking", "login", "signin", 
    "confirm", "update", "wallet", "bonus", "gift", "free", 
    "violation", "suport", "hotro", "tang-qua", "trung-thuong",
    "garena", "facebook", "zalo", "telegram"
]

# Danh sách tên miền uy tín (Whitelist) - Để tránh bắt nhầm
WHITELIST_DOMAINS = [
    "facebook.com", "google.com", "zalo.me", "telegram.org",
    "vnexpress.net", "dantri.com.vn", "thanhnien.vn", "tuoitre.vn",
    "vietcombank.com.vn", "techcombank.com.vn", "mbbank.com.vn"
]

def check_phishing_url(url):
    """
    Phân tích URL để tìm dấu hiệu lừa đảo.
    Trả về: (Điểm rủi ro, Lý do)
    """
    score = 0
    reasons = []
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # 1. Kiểm tra Whitelist (Nếu là trang xịn thì bỏ qua)
        if any(domain.endswith(d) for d in WHITELIST_DOMAINS):
            return 0, []

        # 2. Kiểm tra nếu dùng IP Address thay vì tên miền (Dấu hiệu nguy hiểm)
        # Ví dụ: http://192.168.1.1/login
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain):
            score += 60
            reasons.append("URL_IS_IP_ADDRESS")

        # 3. Kiểm tra độ dài tên miền (Lừa đảo thường dùng tên miền rất dài)
        if len(domain) > 30:
            score += 20
            reasons.append("LONG_DOMAIN_NAME")

        # 4. Kiểm tra số lượng dấu gạch ngang (Dấu hiệu tên miền fake)
        # Ví dụ: vietcombank-verify-secure-login.com
        if domain.count("-") > 3:
            score += 30
            reasons.append("EXCESSIVE_HYPHENS")

        # 5. Quét từ khóa nhạy cảm trong tên miền và đường dẫn
        found_keywords = []
        for word in PHISHING_KEYWORDS:
            if word in domain or word in path:
                found_keywords.append(word)
                score += 15 # Mỗi từ khóa nhạy cảm cộng 15 điểm
        
        if found_keywords:
            reasons.append(f"SUSPICIOUS_KEYWORDS: {', '.join(found_keywords)}")

        # 6. Kiểm tra giao thức (Không có HTTPS thường rủi ro hơn)
        if parsed.scheme != "https":
            score += 10
            reasons.append("NO_HTTPS")

    except Exception as e:
        print(f"Lỗi check URL: {e}")
    
    # Chốt điểm tối đa là 100
    return min(score, 100), reasons