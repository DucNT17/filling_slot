from step3_retrieve import retrieve_results
from openai import OpenAI
import json 

client = OpenAI()

SYSTEM_PROMPT = """
Bạn được cung cấp:
- Một hoặc nhiều đoạn văn bản (chunk) từ tài liệu kỹ thuật, kèm metadata: tên file, mục, bảng/hình (nếu có), số trang
- Một yêu cầu kỹ thuật cụ thể.

#Yêu cầu:
# 1. Tìm thông tin kỹ thuật liên quan trực tiếp đến yêu cầu kỹ thuật.
# 2. Trích xuất giá trị thông số để xác định khả năng đáp ứng theo yêu cầu.
# 3. Dẫn chứng rõ: file, section, table/figure name (nếu có), page, nội dung trích dẫn của những tài liệu liên quan, những tài liệu khác không liên quan thì bỏ qua.

# #Output: JSON gồm các trường:
- yeu_cau_ky_thuat
- kha_nang_dap_ung
- tai_lieu_tham_chieu" }

# Ví dụ:
Input:
Yêu cầu: "Số lượng khe cắm module chỉnh lưu (Rectifier): ≥ 4"  
Chunk: "...NetSure 731 A41-S8: 4 rectifier slots (standard), expandable to 6..."  
Metadata:  
- file: "Netsure-731-A41-user-manual.pdf"  
- section: "Table 1-1 Configuration of power system"  
- page: 2"
"""

# Định nghĩa function schema
FUNCTION_SCHEMA = {
    "name": "danh_gia_ky_thuat",
    "description": "Đánh giá khả năng đáp ứng của sản phẩm theo yêu cầu kỹ thuật từ chunk tài liệu.",
    "parameters": {
        "type": "object",
        "properties": {
            "yeu_cau_ky_thuat": {"type": "string"},
            "kha_nang_dap_ung": {"type": "string"},
            "tai_lieu_tham_chieu": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "section": {"type": "string"},
                    "table_or_figure": {"type": "string"},
                    "page": {"type": "integer"},
                    "evidence": {"type": "string"}
                },
                "required": ["file", "section", "page", "evidence"]
            }
        },
        "required": ["yeu_cau_ky_thuat", "kha_nang_dap_ung", "tai_lieu_tham_chieu"]
    }
}

def track_reference(pdf_path, collection_name):
    # Ví dụ sử dụng
    assistant_id = create_assistant()
    print(f"Assistant ID: {assistant_id}")

    # Tạo thread
    thread_id = create_thread()
    print(f"Thread ID: {thread_id}")

    context_queries, product_keys = retrieve_results(pdf_path, collection_name)
    for key in context_queries:
        value = context_queries[key]["query"]
        content = context_queries[key]["content"]
        # Ví dụ user prompt
        user_prompt = f'''
        Yêu cầu: {value}
        Chunk và metadata: {content}
        '''

        # Gọi hàm đánh giá
        result = evaluate_technical_requirement(thread_id, user_prompt, assistant_id)
        if result:
            print(json.dumps(result, indent=2, ensure_ascii=False))

# Hàm tạo Assistant bằng code
def create_assistant():
    assistant = client.beta.assistants.create(
        name="Technical Document Evaluator",
        instructions=SYSTEM_PROMPT,
        model="gpt-4o-mini",
        tools=[{"type": "function", "function": FUNCTION_SCHEMA}]
    )
    return assistant.id

# Hàm cập nhật Assistant (nếu cần sửa cấu hình)
def update_assistant(assistant_id):
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        instructions=SYSTEM_PROMPT,
        model="gpt-4o-mini",
        tools=[{"type": "function", "function": FUNCTION_SCHEMA}]
    )
    return assistant.id

# Hàm gửi yêu cầu tới thread (như code trước)
def evaluate_technical_requirement(thread_id, user_prompt, assistant_id):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_prompt
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        tools=[{"type": "function", "function": FUNCTION_SCHEMA}],
        tool_choice={"type": "function", "function": {"name": "danh_gia_ky_thuat"}}
    )

    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
    
    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            if message.role == "assistant" and message.content:
                for content in message.content:
                    if content.type == "tool_calls":
                        tool_call = content.tool_calls[0]
                        if tool_call.function.name == "danh_gia_ky_thuat":
                            return json.loads(tool_call.function.arguments)
    return None

# Hàm tạo thread
def create_thread():
    thread = client.beta.threads.create()
    return thread.id