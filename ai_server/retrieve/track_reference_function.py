from openai import OpenAI
import json 
import time

clientOpenAI = OpenAI()

SYSTEM_PROMPT = """
Bạn được cung cấp:
- Một hoặc nhiều đoạn văn bản (chunk) từ tài liệu kỹ thuật, kèm metadata: tên file, mục, bảng/hình (nếu có), số trang
- Một yêu cầu kỹ thuật cụ thể.
- Một đoạn văn mẫu.

Yêu cầu trả lời bằng tiếng việt:
- 1. Tìm thông tin kỹ thuật liên quan trực tiếp đến yêu cầu kỹ thuật.
- 2. Trích xuất giá trị thông số để xác định khả năng đáp ứng theo yêu cầu và trả về đoạn văn tương tự giống đoạn văn mẫu không thêm bớt nhưng thông số phải chính xác có trong tài liệu không được bịa đặt.
- 3. Dẫn chứng rõ: file, section, table/figure name (nếu có), page, nội dung trích dẫn của những tài liệu liên quan, nội dung trích dẫn giữ nguyên không được dịch , những tài liệu khác không liên quan thì bỏ qua.
 
Trả kết quả bằng cách gọi function `danh_gia_ky_thuat` với các tham số phù hợp.
# Ví dụ:
Input:
Yêu cầu: "Số lượng khe cắm module chỉnh lưu (Rectifier): ≥ 4"  
Chunk: "...NetSure 731 A41-S8: 4 rectifier slots (standard), expandable to 6..."  
Metadata:  
- file: "Netsure-731-A41-user-manual.pdf"  
- section: "Table 1-1 Configuration of power system"  
- page: 2"
Đoạn văn mẫu: Số lượng khe cắm module chỉnh lưu (Rectifier): ≥ 4 (ví dụ tìm trong tài liệu số lượng là 5 thì trả về "Số lượng khe cắm module chỉnh lưu (Rectifier): 5")
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
def extract_first_json_object(json_str: str):
    s = json_str.strip()
    
    # Tìm dấu '{' đầu tiên
    start_index = s.find('{')
    if start_index == -1:
        print("❌ Không tìm thấy JSON object nào.")
        return None

    # Duyệt từ đó để tìm dấu '}' kết thúc object đầu tiên
    brace_count = 0
    for i in range(start_index, len(s)):
        if s[i] == '{':
            brace_count += 1
        elif s[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i + 1  # Cắt đến sau dấu '}'
                break
    else:
        print("❌ Không tìm thấy JSON đóng đúng.")
        return None

    first_json_str = s[start_index:end_index]

    # Kiểm tra xem có parse được không
    result = json.loads(first_json_str)
    return result

def track_reference(context_queries,kha_nang_dap_ung_tham_chieu_step):
    # Ví dụ sử dụng
    assistant_id = create_assistant()
    print(f"Assistant ID: {assistant_id}")

    # Tạo thread
    thread_id = create_thread()
    print(f"Thread ID: {thread_id}")
    for key in kha_nang_dap_ung_tham_chieu_step:
        value = context_queries[key]["value"]
        content = kha_nang_dap_ung_tham_chieu_step[key]["relevant_context"]
        form = context_queries[key]["yeu_cau_ky_thuat_chi_tiet"]
        # Ví dụ user prompt
        user_prompt = f'''
        Yêu cầu: {value}
        Chunk và metadata: {content}
        Đoạn văn mẫu: {form}
        '''

        # Gọi hàm đánh giá
        result = evaluate_technical_requirement(user_prompt, assistant_id)
        if isinstance(result, str):
            result = extract_first_json_object(result)
        kha_nang_dap_ung_tham_chieu_step[key]["kha_nang_dap_ung"] = result.get('kha_nang_dap_ung', "")
        kha_nang_dap_ung_tham_chieu_step[key]["tai_lieu_tham_chieu"] = {
            "file": result['tai_lieu_tham_chieu']['file'],
            "section": result['tai_lieu_tham_chieu'].get('section', ''),
            "table_or_figure": result['tai_lieu_tham_chieu'].get('table_or_figure', ''),
            "page": result['tai_lieu_tham_chieu'].get('page', 0),
            "evidence": result['tai_lieu_tham_chieu'].get('evidence', '')
        }
        kha_nang_dap_ung_tham_chieu_step[key].pop("relevant_context", None)  # Xoá trường không cần thiết
    
    return kha_nang_dap_ung_tham_chieu_step

# Hàm tạo Assistant bằng code
def create_assistant():
    assistant = clientOpenAI.beta.assistants.create(
        name="Technical Document Evaluator",
        instructions=SYSTEM_PROMPT,
        model="gpt-4o-mini",
        tools=[{"type": "function", "function": FUNCTION_SCHEMA}]
    )
    return assistant.id

# Hàm tạo thread
def create_thread():
    thread = clientOpenAI.beta.threads.create()
    return thread.id

# === UPDATE ASSISTANT ===
def update_assistant(assistant_id):
    assistant = clientOpenAI.beta.assistants.update(
        assistant_id=assistant_id,
        instructions=SYSTEM_PROMPT,
        model="gpt-4o-mini",
        tools=[{"type": "function", "function": FUNCTION_SCHEMA}]
    )
    return assistant.id

# === EVALUATE TECHNICAL REQUIREMENT ===
def evaluate_technical_requirement(user_prompt, assistant_id):
    # 1. Tạo thread riêng cho mỗi lần gọi
    thread = clientOpenAI.beta.threads.create()
    thread_id = thread.id

    # 2. Gửi message vào thread
    clientOpenAI.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_prompt
    )

    # 3. Tạo run
    run = clientOpenAI.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        tool_choice={"type": "function", "function": {"name": "danh_gia_ky_thuat"}}
    )

    # 4. Chờ assistant xử lý (tối đa 20s)
    for _ in range(20):
        run = clientOpenAI.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
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
        messages = clientOpenAI.beta.threads.messages.list(thread_id=thread_id)
        for msg in messages.data:
            print(f"[{msg.role}] {msg.content[0].text.value}")
        return None

    else:
        print(f"Run status: {run.status}")
        return None
