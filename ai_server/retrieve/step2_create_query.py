from step1_extract_table_camelot import extract_table_json_camelot
from llama_index.core import Settings
from openai import OpenAI
from dotenv import load_dotenv
import re
import os
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm_create_query(path_pdf):
    converted_data = extract_table_json_camelot(path_pdf)
    context_prompts = create_context_prompts(converted_data)
    queries = []
    for item in context_prompts:
        for key, value in item.items():
            prompt = prompt_create_query(value)
            response = client.responses.create(
                model="gpt-4o-mini",  
                input=prompt,
                temperature=0
            )

            output_text = response.output_text.strip()
            queries.append(
                {
                    "key": key,
                    "value": value,
                    "query": output_text
                }
            )
    return queries
    

def prompt_create_query(context_prompt):
    prompt =  f"""
    Bạn sẽ nhận được một đoạn mô tả kỹ thuật ngắn gọn (context_prompt), thường là các mảnh thông tin kỹ thuật rời rạc. Nhiệm vụ của bạn là chuyển đổi đoạn mô tả đó thành một truy vấn (query) hoàn chỉnh bằng ngôn ngữ tự nhiên, với mục tiêu:

- Diễn đạt lại đoạn mô tả dưới dạng một câu hỏi hoặc câu truy vấn rõ ràng, dễ hiểu.
- Giữ nguyên đầy đủ tất cả các thông tin kỹ thuật có trong câu gốc (chế độ, dòng điện, điện áp, bước công suất,...).
- Không được loại bỏ hoặc làm mờ bất kỳ chi tiết kỹ thuật nào.
- Truy vấn cần phù hợp để tìm kiếm thông tin tương đồng về mặt ngữ nghĩa trong một hệ thống truy xuất dữ liệu kỹ thuật.

Dưới đây là các ví dụ:

**Input:** "Tải giả xả acquy Thông số kỹ thuật Dòng xả lớn nhất với dải điện áp 220V DC ÷ 240V DC – tương ứng với 1 bộ ≥ 70 A"

**Output:** "Dòng xả lớn nhất của tải giả xả acquy là bao nhiêu khi dải điện áp nằm trong khoảng 220V DC đến 240V DC, và tương ứng với 1 bộ thì có đạt dòng xả ≥ 70A không?"

---
**Input:** "Tải giả xả acquy Thông số kỹ thuật Các chế độ xả - Gồm 4 chế độ: dòng không đổi, công suất không đổi, theo đặc tính dòng cho trước, điều chỉnh thủ công."

**Output:** "Tải giả xả acquy hỗ trợ những chế độ xả nào? Có phải gồm dòng không đổi, công suất không đổi, theo đặc tính dòng định trước, và điều chỉnh thủ công không?"

---
**Input:** "Tải giả xả acquy Thông số kỹ thuật Bước công suất điều chỉnh xả tải 100 W"

**Output:** "Bước điều chỉnh công suất xả tải nhỏ nhất của tải giả xả acquy là bao nhiêu? Có phải là 100W không?"

---
Trả lời từng `context_prompt` theo cấu trúc như trên.


    DỮ LIỆU ĐẦU VÀO:
    ---
    {context_prompt}
    ---

    CHỈ CẦN TRẢ VỀ CÂU TRUY VẤN.
    """
    return prompt

def create_context_prompts(converted_data):
    context_prompts = []
    for item in converted_data:
        ten_san_pham = item['ten_san_pham']
        for muc in item['cac_muc']:
            ten_hang_hoa = muc['ten_hang_hoa']
            thong_so_ky_thuat = muc['thong_so_ky_thuat']
            for key, value in thong_so_ky_thuat.items():
                if isinstance(value, list):
                    value_str = ' '.join(value)
                else:
                    value_str = value
                query = {
                    key: f"{ten_san_pham} {ten_hang_hoa} {value_str}"
                }
                context_prompts.append(query)
    return context_prompts

