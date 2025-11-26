import requests
from bs4 import BeautifulSoup

def crawl_website(url):
    """
    Input: URL trang web
    Output: (Tiêu đề, Nội dung văn bản sạch)
    """
    try:
        # Giả lập trình duyệt để tránh bị chặn
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None, f"Lỗi truy cập: Status code {response.status_code}"

        soup = BeautifulSoup(response.content, 'html.parser')

        # Xóa các thẻ không cần thiết (script, style)
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()

        title = soup.title.string if soup.title else "No Title"
        
        # Lấy text và làm sạch khoảng trắng thừa
        text = soup.get_text(separator=' ')
        clean_text = ' '.join(text.split())

        return title, clean_text

    except Exception as e:
        return None, str(e)