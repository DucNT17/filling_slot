from step4_track_reference import track_reference
from openai import OpenAI
from dotenv import load_dotenv
import re
import json

client = OpenAI()

def adapt_or_not(path_pdf, collection_name):
    """
    Hàm này sẽ gọi các hàm khác để thực hiện quá trình truy xuất và đánh giá khả năng đáp ứng yêu cầu kỹ thuật.
    """
    
    context_queries, product_keys = track_reference(path_pdf, collection_name)
    
    for product in product_keys:
        items = product_keys[product]
        for key in items:
            dap_ung_ky_thuat = ""
            tai_lieu_tham_chieu = ""
            for item in items[key]:
                if item not in context_queries:
                    continue
                yeu_cau_ky_thuat = context_queries[item]['yeu_cau_ky_thuat_chi_tiet']
                kha_nang_dap_ung = context_queries[item]['kha_nang_dap_ung']
                dap_ung_ky_thuat += f"{yeu_cau_ky_thuat} || {kha_nang_dap_ung}\n"
                tai_lieu = context_queries[item]['tai_lieu_tham_chieu']
                tai_lieu_tham_chieu += f"file {tai_lieu['file']},trang: {tai_lieu['page']}, trong bảng(figure):{tai_lieu['table_or_figure']},evidence :{tai_lieu['evidence']} \n"
            if dap_ung_ky_thuat != "" and tai_lieu_tham_chieu != "":
                prompt = prompt_adapt_or_not(dap_ung_ky_thuat, tai_lieu_tham_chieu)
                response = client.responses.create(
                    model="gpt-4o-mini",
                    input=prompt,
                    temperature=0
                )
                output_text = response.output_text.strip()
                output_text = parse_output_text(output_text)
                print(output_text)
                product_keys[product][key].append(output_text['đáp ứng kỹ thuật'])
                product_keys[product][key].append(output_text['tài liệu'])    
    return context_queries, product_keys



def prompt_adapt_or_not(dap_ung_ky_thuat: str, tai_lieu_tham_chieu: str) -> str:
    prompt = f"""
Tôi có một danh sách các thông số kỹ thuật và khả năng đáp ứng tương ứng, mỗi dòng được ngăn cách bằng '||' theo định dạng:

    yêu cầu kỹ thuật || khả năng đáp ứng

Dưới đây là danh sách đầu vào:
{dap_ung_ky_thuat}

Ngoài ra, tôi cũng có các tài liệu tham chiếu như sau:
{tai_lieu_tham_chieu}

Yêu cầu của bạn là:
1. Kiểm tra xem khả năng đáp ứng có thỏa mãn từng yêu cầu kỹ thuật hay không.
2. Nếu tất cả các yêu cầu đều được đáp ứng, trả về "đáp ứng", ngược lại trả về "không đáp ứng".
3. Gộp lại các tài liệu tham chiếu bị trùng để tránh lặp lại(ví dụ như tên file, trang, bảng).

Chỉ trả về kết quả theo định dạng JSON như sau:

{{
    "đáp ứng kỹ thuật": "Đáp ứng" hoặc "Không đáp ứng",
    "tài liệu": "danh sách tài liệu đã rút gọn viết dưới dạng txt"
}}
"""
    return prompt

def parse_output_text(output_text: str) -> dict:
    # B1: Loại bỏ phần ```json ... ```
    cleaned = re.sub(r"^```json\n|```$", "", output_text.strip())

    # B2: Giải mã các ký tự escape như \n, \"
    unescaped = cleaned.encode("utf-8")

    # B3: Chuyển thành dict
    return json.loads(unescaped)