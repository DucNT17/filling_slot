import requests
import os
import re
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup

url = "https://www.vertiv.com/api-lang/en-PH/searchProductTypeResults/search"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

payload = {
    "facetGroups": [],
    "pageSize": 10,
    "pageNumber": 0,
    "productTypeId": "b62d802f-f832-45e8-8262-9d33e88a8fbe"
}

def sanitize_folder_name(name):
    """Làm sạch tên thư mục để tránh ký tự không hợp lệ"""
    # Loại bỏ ký tự đặc biệt và thay thế bằng underscore
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

def crawl_product_details(product_page_url):
    """Crawl thông tin chi tiết từ trang sản phẩm"""
    try:
        product_page_url += '#/benefits-features'  # Thêm phần này vào cuối URL
        # Tạo URL đầy đủ nếu cần
        if not product_page_url.startswith('https://www.vertiv.com'):
            if product_page_url.startswith('/'):
                product_page_url = 'https://www.vertiv.com' + product_page_url +'#/benefits-features'
            else:
                product_page_url = 'https://www.vertiv.com/' + product_page_url + '#/benefits-features'
        
        print(f"Đang crawl thông tin từ: {product_page_url}")
        
        # Gửi request để lấy nội dung trang
        response = requests.get(product_page_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Lấy description từ h1 class="h2 productnamedata"
            description = ""
            description_element = soup.find('h1', class_='h2 productnamedata')
            if description_element:
                # Tìm thẻ p tiếp theo có class chứa description
                next_p = description_element.find_next('p', class_='shade-100 product-hero-description')
                if next_p:
                    description = next_p.get_text(strip=True)
            
            # Lấy key benefits từ div class="key-benefits key-benefits--newline"
            features_benefits = "Benefits: "
            key_benefits_element = soup.find_all('div', class_='presentation-content')
            for i, element in enumerate(key_benefits_element, start=1):
                if element:
                    features_benefits_texts = element.find_all(text=True, recursive=True)
                    features_benefits += ' '.join(features_benefits_texts).strip() + " "
                if i == 1:
                    features_benefits += "Features: "
                

            return {
                "description": description,
                "features_benefits": features_benefits
            }
        else:
            print(f"Lỗi khi crawl {product_page_url}: {response.status_code}")
            return {"description": "", "features_benefits": ""}
            
    except Exception as e:
        print(f"Lỗi khi crawl thông tin từ {product_page_url}: {str(e)}")
        return {"description": "", "features_benefits": ""}

def download_pdf(url, folder_path, filename):
    """Tải file PDF từ URL và lưu vào thư mục"""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Đã tải: {filename}")
            return True
        else:
            print(f"Lỗi tải {filename}: {response.status_code}")
            return False
    except Exception as e:
        print(f"Lỗi khi tải {filename}: {str(e)}")
        return False

def get_all_products():
    """Lấy tất cả sản phẩm từ tất cả các trang"""
    all_items = []
    page_number = 0
    
    while True:
        # Cập nhật page number cho mỗi lần gọi
        current_payload = payload.copy()
        current_payload["pageNumber"] = page_number
        
        print(f"Đang lấy dữ liệu trang {page_number}...")
        response = requests.post(url, headers=headers, json=current_payload)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if not items:  # Nếu không có items nào, nghĩa là đã hết trang
                break
                
            all_items.extend(items)
            print(f"Đã lấy {len(items)} sản phẩm từ trang {page_number}")
            
            # Kiểm tra xem có trang tiếp theo không
            total_pages = data.get('totalPages', 1)
            if page_number >= total_pages:
                break
                
            page_number += 1
        else:
            print(f"Lỗi khi lấy trang {page_number}: {response.status_code}")
            break
    
    print(f"Tổng cộng đã lấy {len(all_items)} sản phẩm từ {page_number} trang")
    return all_items

# Lấy tất cả sản phẩm
all_products = get_all_products()

# Tạo thư mục downloads nếu chưa có
downloads_dir = "downloads1"
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)

# Danh sách để lưu thông tin JSON
products_info = []

# Xử lý từng item
for item in all_products:
        display_name = item.get('displayName', 'Unknown_Product')
        product_type = item.get('productType', 'Unknown_Type')
        product_page_url = item.get('productPageUrl', '')
        folder_name = sanitize_folder_name(display_name)
        
        # Crawl thông tin chi tiết từ trang sản phẩm
        product_details = crawl_product_details(product_page_url)
        
        # Tạo thư mục cho productType trước
        product_type_folder = os.path.join(downloads_dir, sanitize_folder_name(product_type))
        if not os.path.exists(product_type_folder):
            os.makedirs(product_type_folder)
            print(f"Đã tạo thư mục productType: {product_type}")
        
        # Tạo thư mục cho sản phẩm trong productType
        product_folder = os.path.join(product_type_folder, folder_name)
        if not os.path.exists(product_folder):
            os.makedirs(product_folder)
            print(f"Đã tạo thư mục sản phẩm: {folder_name} trong {product_type}")
        
        # Lấy các quickLinks
        quick_links = item.get('quickLinks', [])
        downloaded_files = []
        
        for link in quick_links:
            link_name = link.get('name', '')
            link_url = link.get('url', '')
            
            # Chỉ tải Product Brochure và Operations Manual
            if link_name in ['Product Brochure', 'Operations Manual'] and link_url:
                # Thêm domain nếu URL chưa có https://www.vertiv.com
                if not link_url.startswith('https://www.vertiv.com'):
                    if link_url.startswith('/'):
                        link_url = 'https://www.vertiv.com' + link_url
                    else:
                        link_url = 'https://www.vertiv.com/' + link_url
                
                # Lấy tên file từ URL
                parsed_url = urlparse(link_url)
                filename = os.path.basename(parsed_url.path)
                
                # Nếu không có extension, thêm .pdf
                if not filename.endswith('.pdf'):
                    filename = f"{link_name.replace(' ', '_')}.pdf"
                
                print(f"Đang tải {link_name} cho {display_name}...")
                if download_pdf(link_url, product_folder, filename):
                    downloaded_files.append({
                        "type": link_name,
                        "filename": filename,
                        "path": os.path.join(product_folder, filename)
                    })
        
        # Tạo thông tin JSON cho sản phẩm
        product_info = {
            "product_name": display_name,
            "product_type": product_type,
            "description": product_details["description"],
            "features_benefits": product_details["features_benefits"],
            "folder_path": product_folder,
            "downloaded_files": downloaded_files,
            "product_page_url": product_page_url
        }
        
        products_info.append(product_info)

# Lưu thông tin tất cả sản phẩm vào file JSON
json_file_path = os.path.join(downloads_dir, "dc-power-systems.json")
with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(products_info, f, ensure_ascii=False, indent=2)

print(f"Đã lưu thông tin {len(products_info)} sản phẩm vào {json_file_path}")
print("Hoàn thành tải xuống!")
