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
markdown_path = "D:\\study\\LammaIndex\\documents\\Chuong_V_Yeu_cau_ky_thuat-page-2-table-1.md"  # Thay bằng file markdown của bạn

# Đọc nội dung markdown từ file bằng llama_index
documents = SimpleDirectoryReader(input_files=[markdown_path]).load_data()
markdown_content = "\n".join([doc.text for doc in documents])

# Prompt yêu cầu sinh JSON
prompt = f"""
Bạn là trợ lý trích xuất cấu trúc. Hãy phân tích Markdown sau và tạo JSON theo QUY TẮC, chỉ sử dụng các bảng liên quan thông số kỹ thuật và các tiêu chuẩn tối thiểu — thường là bảng gồm 3 cột: "STT", "Hàng hóa", "Yêu cầu kỹ thuật".

MỤC TIÊU JSON:
[
  {{
    "ten_san_pham": "<string>",
    "cac_muc": [
      {{
        "ten_hang_hoa": "<string>",
        "thong_so_ky_thuat": {{
          "<ID1>": "<string hoặc list [<tên>, <mô tả>]>",
          "<ID2>": "<...>"
        }}
      }},
      ...
    ]
  }},
  ...
]

QUY TẮC:
1. Mỗi phần lớn bắt đầu bằng tiêu đề tên sản phẩm sẽ tạo ra một phần tử trong danh sách JSON (một sản phẩm).
2. Trường 'ten_san_pham' lấy từ dòng tiêu đề đầu tiên thể hiện tên hàng hóa chính.
3. Mỗi bảng kỹ thuật bên dưới tiêu đề là một nhóm 'cac_muc' của sản phẩm đó.
4. Trong mỗi bảng:
   - 'ten_hang_hoa' lấy từ cột "Hàng hóa" tại các dòng có giá trị ở cột "STT".
   - Với mục 'Yêu cầu chung':
     - Nếu cột “Yêu cầu kỹ thuật” chứa nhiều mục gạch đầu dòng bắt đầu bằng dấu `-`:
       👉 **Mỗi mục bắt đầu bằng `-` là một thông số riêng biệt (atomic), lưu dưới một key riêng.**
       👉 Mỗi mục `- ...` sẽ được lưu dạng `"KEY": "<nội dung không có dấu -" >`.
   - Với mục 'Thông số kỹ thuật':
     - Nếu dòng con có cả "Hàng hóa" và "Yêu cầu kỹ thuật" → lưu dưới dạng `"KEY": ["<Hàng hóa>", "<Yêu cầu kỹ thuật>"]`.
5. Mã hóa key: viết tắt 3 chữ cái đầu (không dấu, in hoa) của 'ten_hang_hoa' + số thứ tự 3 chữ số (bắt đầu từ 001).
6. Chuẩn hóa nội dung:
   - Bỏ dấu `-` đầu dòng nếu có.
   - Không gộp nhiều dòng vào 1 key. Mỗi dòng kỹ thuật là một key riêng biệt, theo thứ tự.
7. Không suy diễn, không thêm dữ liệu ngoài.
8. Trả về JSON hợp lệ (UTF-8), KHÔNG chú thích hay giải thích gì thêm.

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
