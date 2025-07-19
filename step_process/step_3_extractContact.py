import json
import os
from llama_index.core import SimpleDirectoryReader
from openai import OpenAI
from dotenv import load_dotenv
import re
load_dotenv()
# Đặt API key (nếu chưa đặt)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

client = OpenAI()

# Đường dẫn file markdown
markdown_path = "D:\\study\\LammaIndex\\data\\bang_tuyen_bo.md"  # Thay bằng file markdown của bạn

# Đọc nội dung markdown từ file bằng llama_index
documents = SimpleDirectoryReader(input_files=[markdown_path]).load_data()
markdown_content = "\n".join([doc.text for doc in documents])

# Prompt yêu cầu sinh JSON
prompt = f"""
Bạn là trợ lý trích xuất cấu trúc. Hãy phân tích Markdown sau và tạo JSON theo QUY TẮC.

MỤC TIÊU JSON:
{{
  "ten_san_pham": "<string>",
  "cac_muc": [
    {{
      "ten_hang_hoa": "<string>",
      "thong_so_ky_thuat": {{
        "<ID1>": "<một thông số atomic>",
        "<ID2>": "<...>"
      }}
    }},
    ...
  ]
}}

QUY TẮC:
1. Lấy 'ten_san_pham' từ dòng tiêu đề có tên hàng hoá chính.
2. Mỗi nhóm nội dung (ví dụ 'Yêu cầu chung', 'Cấu hình thiết bị nguồn', 'Đầu vào AC', 'Đầu ra DC') là một phần tử trong mảng "cac_muc".
3. Trường 'thong_so_ky_thuat' là dict:
   - Key = viết tắt 2-3 chữ cái đầu (không dấu, in hoa) của 'ten_hang_hoa' + số thứ tự 3 chữ số (bắt đầu 001).
   - Value = một câu/bullet/leaf cuối cùng sau chuẩn hóa.
4. Bỏ ký hiệu (-, +, ●, <br/>) và flatten phân cấp như "Attomat DC: PL (Priority LLVD) Loại 32A: ≥ 02 cái".
5. Không suy diễn, chỉ dùng nội dung gốc.
6. JSON hợp lệ, UTF-8.

DỮ LIỆU GỐC:
---
{markdown_content}
---

HÃY TRẢ LỜI CHỈ BẰNG JSON HỢP LỆ.
"""

# Gọi OpenAI qua llama_index hoặc OpenAI client trực tiếp
response = client.responses.create(
    model="gpt-4o-mini",  # Hoặc gpt-4o-mini
    input=prompt,
    temperature=0
)

output_text = response.output_text.strip()
# Loại bỏ các khối ```json hoặc ```
output_text = re.sub(r"^```json\s*|\s*```$", "", output_text, flags=re.MULTILINE).strip()
print("Kết quả JSON:")
print(output_text)

# Parse và lưu file JSON
try:
    json_data = json.loads(output_text)
    os.makedirs("output", exist_ok=True)
    with open("output/thong_so.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print("Đã lưu JSON vào output/thong_so.json")
except json.JSONDecodeError:
    print("Phản hồi không phải JSON hợp lệ. Vui lòng kiểm tra output_text.")
