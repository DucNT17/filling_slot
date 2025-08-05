from retrieve.step5_track_reference import track_reference
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
                yeu_cau_ky_thuat = context_queries[item].get('yeu_cau_ky_thuat_chi_tiet', "")
                kha_nang_dap_ung = context_queries[item].get('kha_nang_dap_ung', "")
                dap_ung_ky_thuat += f"{yeu_cau_ky_thuat} || {kha_nang_dap_ung}\n"

                tai_lieu = context_queries[item].get('tai_lieu_tham_chieu', {})
                file = tai_lieu.get("file", "")
                page = tai_lieu.get("page", "")
                table_or_figure = tai_lieu.get("table_or_figure", "")
                evidence = tai_lieu.get("evidence", "")

                tai_lieu_text = f"{file}, trang: {page}"
                if table_or_figure:
                    tai_lieu_text += f", trong bảng(figure): {table_or_figure}"
                tai_lieu_text += f", evidence: {evidence}\n\n"
                tai_lieu_tham_chieu += tai_lieu_text
            if dap_ung_ky_thuat and tai_lieu_tham_chieu :
                prompt = prompt_adapt_or_not(dap_ung_ky_thuat)
                response = client.responses.create(
                    model="gpt-4o-mini",
                    input=prompt,
                    temperature=0
                )
                output_text = response.output_text.strip()
                output_text = parse_output_text(output_text)
                print(output_text)
                product_keys[product][key].append(output_text['đáp ứng kỹ thuật'])
                product_keys[product][key].append(tai_lieu_tham_chieu)
    return context_queries, product_keys



def prompt_adapt_or_not(dap_ung_ky_thuat: str) -> str:
    prompt = f"""
Bạn sẽ được cung cấp một danh sách các cặp “yêu cầu kỹ thuật || khả năng đáp ứng” trong file dap_ung_ky_thuat.
Nhiệm vụ của bạn:
1. Với từng cặp, đánh giá xem khả năng đáp ứng có thực sự đáp ứng yêu cầu kỹ thuật không.
2. Tổng hợp kết quả:
  – Nếu tất cả các yêu cầu đều được đáp ứng, trả về "Đáp ứng"
  – Nếu không có yêu cầu nào được đáp ứng, trả về "Không đáp ứng"
  – Nếu chỉ một phần yêu cầu được đáp ứng, trả về theo định dạng "Đáp ứng: x/y = z%", trong đó:
       - x là số yêu cầu được đáp ứng
       - y là tổng số yêu cầu
       - z% là phần trăm làm tròn đến số nguyên gần nhất
📤 Kết quả chỉ trả về dưới dạng JSON với cấu trúc sau: {{
 "đáp ứng kỹ thuật": "<kết quả đánh giá>"
}}

Danh sách các cặp “yêu cầu kỹ thuật || khả năng đáp ứng” : {dap_ung_ky_thuat}
"""
    return prompt

def parse_output_text(output_text: str) -> dict:
    # B1: Loại bỏ phần ```json ... ```
    cleaned = re.sub(r"^```json\n|```$", "", output_text.strip())
    print(cleaned)
    # B2: Giải mã các ký tự escape như \n, \"
    unescaped = cleaned.encode("utf-8")

    # B3: Chuyển thành dict
    return json.loads(unescaped)