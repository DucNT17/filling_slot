from retrieve.step1_extract_table_camelot import extract_table_json_camelot
import uuid
import re

# [{'ten_san_pham': 'Tải giả xả acquy',
#   'cac_muc': [{'ten_hang_hoa': 'Yêu cầu chung',
#     'thong_so_ky_thuat': {'5AEBD': 'Các loại thiết bị, vật tư, phụ kiện phải có nguồn gốc xuất xứ, có chứng nhận chất lượng sản phẩm của nhà sản xuất.',
#      '26659': 'Thiết bị mới 100% chưa qua sử dụng',
#      '5E9BA': 'Thiết bị phải được sản xuất từ năm 2021 trở lại đây',
#      '60BF4': 'Thời  gian  bảo  hành:  theo  tiêu  chuẩn  của  nhà  sản xuất, tối thiểu 12 tháng.'}}]
def process_json_to_list(path_pdf):
    data = extract_table_json_camelot(path_pdf)
    converted_data = convert_to_new_format(data)
    return converted_data


def clean_text(text):
    """Làm sạch text, loại bỏ ký tự xuống dòng thừa"""
    return re.sub(r'\n+', '', text.strip())

def split_requirements(text):
    """Tách các yêu cầu dựa trên dấu gạch đầu dòng"""
    requirements = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            requirements.append(line[2:].strip())
        elif line and not any(line.startswith(prefix) for prefix in ['- ']):
            if requirements:
                requirements[-1] += ' ' + line
            else:
                requirements.append(line)
    return requirements

def generate_random_key():
    """Tạo key random 5 ký tự từ UUID"""
    return str(uuid.uuid4()).replace('-', '')[:5].upper()

# Convert table data to new format:
def convert_to_new_format(data):
    result = []
    current_product = None
    current_category = None
    
    for item in data:
        values = item['values']
        stt_raw  = values['STT']
        hang_hoa = clean_text(values['hang_hoa'])
        yeu_cau = values['yeu_cau_ky_thuat']


        stt = stt_raw.strip()

        roman_pattern = r'^(VII|VIII|IX|X|XI|XII|I{1,3}|IV|V|VI)\s+(.+)'
        roman_match = re.match(roman_pattern, stt)
        # Nếu STT là số La Mã (I, II, III...) thì đây là tên sản phẩm
        hang_hoa_roman_match = re.match(roman_pattern, hang_hoa)
        if roman_match and not hang_hoa and not yeu_cau:
            if current_product:
                result.append(current_product)
            
            roman_num = roman_match.group(1)  # Số La Mã
            product_name = roman_match.group(2)  # Tên sản phẩm
            
            current_product = {
                "ten_san_pham": product_name,
                "cac_muc": []
            }
            current_category = None
        elif hang_hoa_roman_match and not stt_raw and not yeu_cau:
            if current_product:
                result.append(current_product)
            
            roman_num = hang_hoa_roman_match.group(1)  # Số La Mã
            product_name = hang_hoa_roman_match.group(2)  # Tên sản phẩm
            
            current_product = {
                "ten_san_pham": product_name,
                "cac_muc": []
            }
            current_category = None        
        
        elif stt in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV']:
            if current_product:
                result.append(current_product)
            
            current_product = {
                "ten_san_pham": hang_hoa,
                "cac_muc": []
            }
            current_category = None
            
        # Nếu STT là số (1, 2, 3...) thì đây là danh mục
        elif stt.isdigit():
            current_category = {
                "ten_hang_hoa": hang_hoa,
                "thong_so_ky_thuat": {}
            }
            
            # Xử lý yêu cầu kỹ thuật cho danh mục
            if yeu_cau.strip():
                requirements = split_requirements(yeu_cau)
                for req in requirements:
                    key = generate_random_key()  # Tạo key random
                    current_category["thong_so_ky_thuat"][key] = clean_text(req)
            if current_product:
                current_product["cac_muc"].append(current_category)
                
        # Nếu STT trống thì đây là thông số kỹ thuật chi tiết
        elif stt == '' and current_category and hang_hoa:
            # Tạo key random cho thông số kỹ thuật
            key = generate_random_key()
            
            # Làm sạch tên hàng hóa và yêu cầu kỹ thuật
            clean_hang_hoa = clean_text(hang_hoa)
            clean_yeu_cau = clean_text(yeu_cau)
            
            current_category["thong_so_ky_thuat"][key] = [clean_hang_hoa, clean_yeu_cau]
        elif stt == '' and current_category and not hang_hoa:
            if yeu_cau.strip():
                requirements = split_requirements(yeu_cau)
                
                # Lấy key cuối cùng trong thong_so_ky_thuat (nếu có)
                existing_keys = list(current_category["thong_so_ky_thuat"].keys())
                last_key = existing_keys[-1] if existing_keys else None
                
                for req in requirements:
                    clean_req = clean_text(req)
                    
                    # Kiểm tra chữ cái đầu có viết hoa HOẶC có gạch đầu dòng không
                    has_dash = req.strip().startswith('- ')
                    has_uppercase = clean_req and clean_req[0].isupper()
                    
                    if has_uppercase or has_dash:
                        # Chữ đầu viết hoa HOẶC có gạch đầu dòng -> tạo key mới
                        key = generate_random_key()
                        current_category["thong_so_ky_thuat"][key] = clean_req
                        last_key = key
                    else:
                        # Chữ đầu không viết hoa VÀ không có gạch đầu dòng -> nối vào key trước đó
                        if last_key and last_key in current_category["thong_so_ky_thuat"]:
                            current_category["thong_so_ky_thuat"][last_key] += " " + clean_req
                        else:
                            # Nếu không có key trước đó thì vẫn tạo key mới
                            key = generate_random_key()
                            current_category["thong_so_ky_thuat"][key] = clean_req
                            last_key = key
    
    # Thêm sản phẩm cuối cùng
    if current_product:
        result.append(current_product)
    
    return result