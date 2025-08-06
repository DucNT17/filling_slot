import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse

# Địa chỉ URL của trang bạn muốn đọc
url = 'https://www.vertiv.com/en-asia/products-catalog/critical-power/dc-power-systems/netsure-531-a91/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

def download_pdf(pdf_url, filename):
    """Download PDF file từ URL"""
    try:
        print(f"Đang tải xuống: {filename}")
        pdf_response = requests.get(pdf_url, headers=headers, stream=True)
        pdf_response.raise_for_status()
        
        # Tạo thư mục documents nếu chưa có
        documents_dir = os.path.join(os.path.dirname(__file__), '..', 'documents')
        os.makedirs(documents_dir, exist_ok=True)
        
        # Đường dẫn file đầy đủ
        file_path = os.path.join(documents_dir, filename)
        
        # Ghi file PDF
        with open(file_path, 'wb') as f:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Đã tải xuống thành công: {file_path}")
        return True
    except Exception as e:
        print(f"Lỗi khi tải xuống {filename}: {str(e)}")
        return False

# Gửi yêu cầu GET với headers
response = requests.get(url, headers=headers)

# Kiểm tra xem yêu cầu có thành công hay không (status code 200 là thành công)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Tìm div chứa các button PDF
    product_hero_buttons = soup.find('div', class_='product-hero-buttons')
    
    if product_hero_buttons:
        # Tìm tất cả các link PDF trong div này
        pdf_links = product_hero_buttons.find_all('a', href=True)
        
        downloaded_count = 0
        for link in pdf_links:
            href = link.get('href')
            if href and href.endswith('.pdf'):
                # Tạo URL đầy đủ
                full_url = urljoin(url, href)
                
                # Lấy tên file từ URL
                filename = os.path.basename(urlparse(href).path)
                
                # Xác định loại file dựa vào text của button
                link_text = link.get_text(strip=True)
                if 'Brochure' in link_text:
                    filename = f"netsure-531-a91-brochure.pdf"
                elif 'Manual' in link_text:
                    filename = f"netsure-531-a91-manual.pdf"
                
                print(f"Tìm thấy link PDF: {link_text} - {full_url}")
                
                # Download file
                if download_pdf(full_url, filename):
                    downloaded_count += 1
        
        print(f"\nĐã tải xuống thành công {downloaded_count} file PDF.")
    else:
        print("Không tìm thấy div 'product-hero-buttons'")
else:
    # Nếu yêu cầu không thành công, in ra thông báo lỗi
    print(f"Không thể lấy được trang web. Lỗi {response.status_code}")