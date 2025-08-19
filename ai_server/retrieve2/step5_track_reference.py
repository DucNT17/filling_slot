from ai_server.retrieve2.step4_retrieve import retrieve_results
from openai import AsyncOpenAI  # Changed to AsyncOpenAI
import json 
import asyncio
import re
import os
from dotenv import load_dotenv
load_dotenv()

# Use AsyncOpenAI instead of OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEFAULT_OBJECT = {
    "yeu_cau_ky_thuat": "",
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

async def track_reference(pdf_path, filename_ids, collection_name, max_concurrent=5):
    """
    Async version of track_reference with concurrent processing
    Note: Reduced max_concurrent from 10 to 5 for OpenAI rate limits
    """
    # Semaphore để kiểm soát số lượng requests đồng thời
    semaphore = asyncio.Semaphore(max_concurrent)
    
    assistant_id = "asst_FZIBIfjPM3kCoxURARvM27UV"
    print(f"Assistant ID: {assistant_id}")

    # Tạo thread (now async)
    thread_id = await create_thread()
    print(f"Thread ID: {thread_id}")

    # Retrieve results
    context_queries, product_keys = await retrieve_results(pdf_path, filename_ids, collection_name)
    
    # Tạo danh sách tasks để xử lý đồng thời
    tasks = []
    for key in context_queries:
        task = process_query_with_semaphore(
            semaphore,
            key,
            context_queries[key],
            assistant_id
        )
        tasks.append(task)
    
    # Chạy tất cả tasks đồng thời
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Cập nhật kết quả vào context_queries
    for key, result in zip(context_queries.keys(), results):
        if isinstance(result, Exception):
            print(f"❌ Lỗi xử lý key {key}: {result}")
            continue
            
        if result is None:
            print(f"⚠️ Không có kết quả cho key {key}")
            continue
            
        context_queries[key]["kha_nang_dap_ung"] = result.get('kha_nang_dap_ung', '')
        context_queries[key]["tai_lieu_tham_chieu"] = {
            "file": result.get('tai_lieu_tham_chieu', {}).get('file', ''),
            "section": result.get('tai_lieu_tham_chieu', {}).get('section', ''),
            "table_or_figure": result.get('tai_lieu_tham_chieu', {}).get('table_or_figure', ''),
            "page": result.get('tai_lieu_tham_chieu', {}).get('page', 0),
            "evidence": result.get('tai_lieu_tham_chieu', {}).get('evidence', '')
        }
        context_queries[key].pop("relevant_context", None)  # Xoá trường không cần thiết
    
    return context_queries, product_keys


async def process_query_with_semaphore(semaphore, key, query_data, assistant_id):
    """
    Process a single query with semaphore control
    """
    async with semaphore:
        value = query_data["value"]
        content = query_data["relevant_context"]
        form = query_data["yeu_cau_ky_thuat_chi_tiet"]
        
        # Tạo user prompt
        user_prompt = f'''
        Yêu cầu: {value}
        Chunk và metadata: {content}
        Đoạn văn mẫu: {form}
        '''

        # Gọi hàm đánh giá
        result = await evaluate_technical_requirement(user_prompt, assistant_id)
        if isinstance(result, str):
            result = extract_first_json_object(result)
            
        return result


# Now truly async create_thread
async def create_thread():
    """
    Async version of create_thread
    """
    thread = await client.beta.threads.create()
    return thread.id


# === FULLY ASYNC EVALUATE TECHNICAL REQUIREMENT ===
async def evaluate_technical_requirement(user_prompt, assistant_id):
    """
    Fully async version of evaluate_technical_requirement
    """
    try:
        # 1. Tạo thread riêng cho mỗi lần gọi
        thread = await client.beta.threads.create()
        thread_id = thread.id

        # 2. Gửi message vào thread
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_prompt
        )

        # 3. Tạo run
        run = await client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            tool_choice={"type": "function", "function": {"name": "kha_nang_dap_ung"}}
        )

        # 4. Chờ assistant xử lý (tối đa 30s) với async sleep
        for i in range(30):
            run = await client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run.status not in ["queued", "in_progress"]:
                break
            await asyncio.sleep(1)  # Now using async sleep
        
        # 5. Lấy arguments trực tiếp
        if run.status == "requires_action":
            call = run.required_action.submit_tool_outputs.tool_calls[0]
            print(f"👉 Assistant đã gọi tool: {call.function.name}")
            print("🧠 Dữ liệu JSON assistant muốn trả về:")
            print(call.function.arguments)
            return call.function.arguments

        elif run.status == "completed":
            messages = await client.beta.threads.messages.list(thread_id=thread_id)
            for msg in messages.data:
                print(f"[{msg.role}] {msg.content[0].text.value}")
            return None

        else:
            print(f"Run status: {run.status}")
            return None
            
    except Exception as e:
        print(f"❌ Error in evaluate_technical_requirement: {e}")
        return None
