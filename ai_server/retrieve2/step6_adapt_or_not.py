
from ai_server.retrieve2.step5_track_reference import track_reference
from openai import AsyncOpenAI  # Changed to AsyncOpenAI
from dotenv import load_dotenv
import re
import json
import asyncio
import os
load_dotenv()

# Use AsyncOpenAI instead of OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def adapt_or_not(path_pdf, filename_ids, collection_name, max_concurrent=10):
    """
    Hàm này sẽ gọi các hàm khác để thực hiện quá trình truy xuất và đánh giá khả năng đáp ứng yêu cầu kỹ thuật.
    Reduced max_concurrent from 5 to 3 for OpenAI rate limits
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    context_queries, product_keys = await track_reference(path_pdf, filename_ids, collection_name)
    assistant_id = "asst_SIWbRtRbvCxXS9dgqvtj9U8O"
    
    tasks = []
    
    for product in product_keys:
        items = product_keys[product]
        for key in items:
            # Tạo task cho mỗi key
            task = process_product_key(
                semaphore, context_queries, product_keys, product, key, items[key], assistant_id
            )
            tasks.append(task)
    
    # Chạy tất cả tasks đồng thời với giới hạn semaphore
    await asyncio.gather(*tasks, return_exceptions=True)
    with open("D:/study/LammaIndex/output/context_queries.json", "w", encoding="utf-8") as f:
        json.dump(context_queries, f, ensure_ascii=False, indent=4)
    with open("D:/study/LammaIndex/output/product_keys.json", "w", encoding="utf-8") as f:
        json.dump(product_keys, f, ensure_ascii=False, indent=4)
    return context_queries, product_keys


async def process_product_key(semaphore, context_queries, product_keys, product, key, items_key, assistant_id):
    """
    Xử lý một product key cụ thể
    """
    async with semaphore:
        try:
            dap_ung_ky_thuat = ""
            tai_lieu_tham_chieu = ""
            
            for item in items_key:
                if item not in context_queries:
                    continue
                    
                yeu_cau_ky_thuat = context_queries[item].get('yeu_cau_ky_thuat_chi_tiet', "")
                kha_nang_dap_ung = context_queries[item].get('kha_nang_dap_ung', "Không đáp ứng")
                if kha_nang_dap_ung == "":
                    kha_nang_dap_ung = "Không đáp ứng"
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
                
            if dap_ung_ky_thuat and tai_lieu_tham_chieu:
                response = await evaluator_adaptability(dap_ung_ky_thuat, assistant_id)
                if response:
                    output_text = response.strip()
                    output_text = parse_output_text(output_text)
                    print(output_text)
                    product_keys[product][key].append(output_text['đáp ứng kỹ thuật'])
                    product_keys[product][key].append(tai_lieu_tham_chieu)
        except Exception as e:

            print(f"❌ Error processing product key {product}-{key}: {e}")


def parse_output_text(output_text: str) -> dict:
    DEFAULT_JSON = {"đáp ứng kỹ thuật": "0"}
    if output_text is None or output_text.strip() == "":
        return DEFAULT_JSON.copy()
    # B1: Tìm phần JSON đầu tiên trong chuỗi
    match = re.search(r"\{.*\}", output_text, re.DOTALL)
    if not match:
        return DEFAULT_JSON.copy()

    json_str = match.group(0).strip()

    # B2: Parse JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return DEFAULT_JSON.copy()

    # B3: Nếu không có key thì trả mặc định
    if "đáp ứng kỹ thuật" not in data:
        return DEFAULT_JSON.copy()

    return data



# Async version of create_thread
async def create_thread():
    """
    Now truly async create_thread
    """
    thread = await client.beta.threads.create()
    return thread.id


# === FULLY ASYNC EVALUATOR ADAPTABILITY ===
async def evaluator_adaptability(user_prompt, assistant_id):
    """
    Fully async version of evaluator_adaptability
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
            tool_choice={"type": "function", "function": {"name": "evaluate_requirement_fulfillment"}}
        )

        # 4. Chờ assistant xử lý (tối đa 30s) với async sleep
        for _ in range(30):
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
            return {
                "đáp ứng kỹ thuật": "0"
            }
            
    except Exception as e:
        print(f"❌ Error in evaluator_adaptability: {e}")
        return {
                "đáp ứng kỹ thuật": "0"
            }