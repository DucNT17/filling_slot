from openai import OpenAI
from dotenv import load_dotenv
import re
import json

clientOpenAI = OpenAI()

def adapt_or_not(kha_nang_dap_ung_tham_chieu_step, adapt_or_not_step, all_requirements, context_queries):
    """
    Hàm này sẽ gọi các hàm khác để thực hiện quá trình truy xuất và đánh giá khả năng đáp ứng yêu cầu kỹ thuật.
    """
    
    for key in all_requirements:
        dap_ung_ky_thuat = ""
        tai_lieu_tham_chieu = ""
        weight = 0
        for item in all_requirements[key]:
            if item not in kha_nang_dap_ung_tham_chieu_step:
                continue
            yeu_cau_ky_thuat = context_queries[item].get('yeu_cau_ky_thuat_chi_tiet', "")
            kha_nang_dap_ung = kha_nang_dap_ung_tham_chieu_step[item].get('kha_nang_dap_ung', "")
            dap_ung_ky_thuat += f"{yeu_cau_ky_thuat} || {kha_nang_dap_ung}\n"
    
            tai_lieu = kha_nang_dap_ung_tham_chieu_step[item].get('tai_lieu_tham_chieu', {})
            file = tai_lieu.get("file", "")
            page = tai_lieu.get("page", "")
            table_or_figure = tai_lieu.get("table_or_figure", "")
            evidence = tai_lieu.get("evidence", "")
    
            tai_lieu_text = f"{file}, trang: {page}"
            if table_or_figure or table_or_figure not in ["", None,"None"]:
                tai_lieu_text += f", trong bảng(figure): {table_or_figure}"
            tai_lieu_text += f", evidence: {evidence}\n\n"
            tai_lieu_tham_chieu += tai_lieu_text
            weight += 1
        if dap_ung_ky_thuat and tai_lieu_tham_chieu :
            prompt = prompt_adapt_or_not(dap_ung_ky_thuat)
            response = clientOpenAI.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                temperature=0
            )
            output_text = response.output_text.strip()
            output_text = parse_output_text(output_text)
            if key not in adapt_or_not_step:
                adapt_or_not_step[key] = []
            adapt_or_not_step[key].append(weight)
            adapt_or_not_step[key].append(output_text['đáp ứng kỹ thuật'])
            adapt_or_not_step[key].append(tai_lieu_tham_chieu)
    return kha_nang_dap_ung_tham_chieu_step, adapt_or_not_step



def prompt_adapt_or_not(dap_ung_ky_thuat: str) -> str:
    prompt = f"""
Bạn sẽ được cung cấp một danh sách các cặp “yêu cầu kỹ thuật || khả năng đáp ứng” trong file dap_ung_ky_thuat.
Nhiệm vụ của bạn:
1. Với từng cặp, đánh giá xem khả năng đáp ứng có thực sự đáp ứng yêu cầu kỹ thuật không.
2. Tổng hợp kết quả:
  – Nếu tất cả các yêu cầu đều được đáp ứng, chỉ trả về "1"
  – Nếu không có yêu cầu nào được đáp ứng, chỉ trả về "0"
  – Nếu chỉ một phần yêu cầu được đáp ứng, chỉ trả về theo định dạng "x/y", trong đó:
       - x là số yêu cầu được đáp ứng
       - y là tổng số yêu cầu
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