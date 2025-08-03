from step3_retrieve import retrieve_results
from openai import OpenAI
import json 
import time

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
        content = context_queries[key]["relevant_context"]
        # Ví dụ user prompt
        user_prompt = f'''
        Yêu cầu: {value}
        Chunk và metadata: {content}
        '''

        # Gọi hàm đánh giá
        result = evaluate_technical_requirement(user_prompt, assistant_id)
        context_queries[key]["response"] = result
    
    return context_queries, product_keys

# Hàm tạo Assistant bằng code
def create_assistant():
    assistant = client.beta.assistants.create(
        name="Technical Document Evaluator",
        instructions=SYSTEM_PROMPT,
        model="gpt-4o-mini",
        tools=[{"type": "function", "function": FUNCTION_SCHEMA}]
    )
    return assistant.id

# Hàm tạo thread
def create_thread():
    thread = client.beta.threads.create()
    return thread.id

# === UPDATE ASSISTANT ===
def update_assistant(assistant_id):
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        instructions=SYSTEM_PROMPT,
        model="gpt-4o-mini",
        tools=[{"type": "function", "function": FUNCTION_SCHEMA}]
    )
    return assistant.id

# === EVALUATE TECHNICAL REQUIREMENT ===
def evaluate_technical_requirement(user_prompt, assistant_id):
    # 1. Tạo thread riêng cho mỗi lần gọi
    thread = client.beta.threads.create()
    thread_id = thread.id

    # 2. Gửi message vào thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_prompt
    )

    # 3. Tạo run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        tool_choice={"type": "function", "function": {"name": "danh_gia_ky_thuat"}}
    )

    # 4. Chờ assistant xử lý (tối đa 20s)
    for _ in range(20):
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run.status not in ["queued", "in_progress"]:
            break
        time.sleep(1)

    # 5. Lấy arguments trực tiếp
    if run.status == "requires_action":
        call = run.required_action.submit_tool_outputs.tool_calls[0]
        print(f"👉 Assistant đã gọi tool: {call.function.name}")
        print("🧠 Dữ liệu JSON assistant muốn trả về:")
        print(call.function.arguments)
        return call.function.arguments

    elif run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for msg in messages.data:
            print(f"[{msg.role}] {msg.content[0].text.value}")
        return None

    else:
        print(f"Run status: {run.status}")
        return None
