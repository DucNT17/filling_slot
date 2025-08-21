from openai import OpenAI
import json 
import time
import asyncio
from typing import Dict, Any

clientOpenAI = OpenAI()

DEFAULT_OBJECT = {
    "kha_nang_dap_ung": "",
    "tai_lieu_tham_chieu": {
        "file": "",
        "section": "",
        "table_or_figure": "",
        "page": 0,
        "evidence": ""
    }
}

def fill_defaults(data: dict, defaults: dict) -> dict:
    """
    Đệ quy bổ sung các trường mặc định vào data nếu thiếu.
    """
    result = defaults.copy()
    for key, default_value in defaults.items():
        if key in data:
            if isinstance(default_value, dict) and isinstance(data[key], dict):
                result[key] = fill_defaults(data[key], default_value)
            else:
                result[key] = data[key]
    return result


def extract_first_json_object(json_str: str):
    s = json_str.strip()
    if not s or s is None or s == "":
        print("❌ Chuỗi rỗng.")
        return DEFAULT_OBJECT
    # Tìm dấu '{' đầu tiên
    start_index = s.find('{')
    if start_index == -1:
        print("❌ Không tìm thấy JSON object nào.")
        return DEFAULT_OBJECT

    # Duyệt từ đó để tìm dấu '}' kết thúc object đầu tiên
    brace_count = 0
    end_index = -1
    for i in range(start_index, len(s)):
        if s[i] == '{':
            brace_count += 1
        elif s[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i + 1  # Cắt đến sau dấu '}'
                break
    if end_index == -1:
        print("❌ Không tìm thấy JSON đóng đúng.")
        return DEFAULT_OBJECT

    first_json_str = s[start_index:end_index]
    # Kiểm tra xem có parse được không
    try:
        result = json.loads(first_json_str)
        # Bổ sung field mặc định nếu thiếu
        return fill_defaults(result, DEFAULT_OBJECT)
    except json.JSONDecodeError:
        return DEFAULT_OBJECT
    

async def track_reference_async(context_queries: Dict, kha_nang_dap_ung_tham_chieu_step: Dict, 
                               max_concurrent: int = 5) -> Dict:
    """
    Phiên bản async của track_reference với giới hạn số requests đồng thời
    """
    assistant_id = "asst_FZIBIfjPM3kCoxURARvM27UV"
    
    # Tạo semaphore để giới hạn số requests đồng thời
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single_item(key: str):
        async with semaphore:  # Giới hạn số requests đồng thời
            try:
                value = context_queries[key]["value"]
                content = kha_nang_dap_ung_tham_chieu_step[key]["relevant_context"]
                module_component = context_queries[key]["ten_hang_hoa"]

                user_prompt = f"""
                Các tài liệu kỹ thuật được cung cấp: {content},
                module/component: {module_component} ,
                yeu_cau_ky_thuat: {value},
                """
                
                print(f"🚀 Đang xử lý key: {key}")
                result = await evaluate_technical_requirement_async(user_prompt, assistant_id)
                
                if isinstance(result, str):
                    result = extract_first_json_object(result)
                
                return key, result
                
            except Exception as e:
                print(f"❌ Lỗi xử lý key {key}: {str(e)}")
                return key, DEFAULT_OBJECT
    
    # Tạo tasks cho tất cả items
    tasks = [process_single_item(key) for key in kha_nang_dap_ung_tham_chieu_step]
    
    # Chạy tất cả tasks song song
    print(f"🏃‍♂️ Bắt đầu xử lý {len(tasks)} items với {max_concurrent} requests đồng thời...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Xử lý kết quả
    for result in results:
        if isinstance(result, Exception):
            print(f"❌ Task failed: {result}")
            continue
            
        key, processed_result = result

        kha_nang_dap_ung_tham_chieu_step[key]["kha_nang_dap_ung"] = processed_result.get("kha_nang_dap_ung", "")
        kha_nang_dap_ung_tham_chieu_step[key]["tai_lieu_tham_chieu"] = {
            "file": processed_result.get("tai_lieu_tham_chieu", {}).get("file", ""),
            "section": processed_result.get("tai_lieu_tham_chieu", {}).get("section", ""),
            "table_or_figure": processed_result.get("tai_lieu_tham_chieu", {}).get("table_or_figure", ""),
            "page": processed_result.get("tai_lieu_tham_chieu", {}).get("page", 0),
            "evidence": processed_result.get("tai_lieu_tham_chieu", {}).get("evidence", "")
        }
        kha_nang_dap_ung_tham_chieu_step[key].pop("relevant_context", None)
        print(f"✅ Hoàn thành key: {key}")
    
    print("🎉 Hoàn thành tất cả!")
    return kha_nang_dap_ung_tham_chieu_step


# Hàm tạo thread
def create_thread():
    thread = clientOpenAI.beta.threads.create()
    return thread.id

# === EVALUATE TECHNICAL REQUIREMENT ===
async def evaluate_technical_requirement_async(user_prompt: str, assistant_id: str) -> Dict[str, Any]:
    """
    Phiên bản async của evaluate_technical_requirement
    """
    def _sync_evaluate():
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
            tool_choice={"type": "function", "function": {"name": "kha_nang_dap_ung"}}
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
            return DEFAULT_OBJECT
    
    # Chạy function sync trong thread pool
    return await asyncio.to_thread(_sync_evaluate)
