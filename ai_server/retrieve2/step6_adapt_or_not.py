
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
    with open("output/context_queries.json", "w", encoding="utf-8") as f:
        json.dump(context_queries, f, ensure_ascii=False, indent=4)
    with open("output/product_keys.json", "w", encoding="utf-8") as f:
        json.dump(product_keys, f, ensure_ascii=False, indent=4)
    return context_queries, product_keys


async def process_product_key(semaphore, context_queries, product_keys, product, key, items_key, assistant_id):
    """
    Xử lý một product key cụ thể - xử lý từng item riêng biệt
    """
    async with semaphore:
        for item in items_key:
            try:
                if item not in context_queries:
                    print(f"⚠️ Item {item} not found in context_queries")
                    continue
                    
                yeu_cau_ky_thuat = context_queries[item].get('value', "")
                kha_nang_dap_ung = context_queries[item].get('kha_nang_dap_ung', "Không có thông tin")
                module_name = context_queries[item].get('ten_hang_hoa', "")
                if kha_nang_dap_ung == "":
                    kha_nang_dap_ung = "Không có thông tin"

                user_prompt = f'Module {module_name} có yêu cầu kỹ thuật là: "{yeu_cau_ky_thuat}", khả năng đáp ứng của sản phẩm hiện tại là: "{kha_nang_dap_ung}".'

                if user_prompt.strip():
                    print(f"🔄 Processing item {item}...")
                    response = await evaluator_adaptability(user_prompt, assistant_id)
                    if response:
                        output_text = response.strip()
                        output_text = parse_output_text(output_text)
                        print(f"✅ Processing item {item}: {output_text}")
                        # Lưu kết quả vào context_queries
                        context_queries[item]['adapt_or_not'] = output_text['đáp ứng kỹ thuật']
                    else:
                        print(f"⚠️ No response for item {item}, setting default")
                        context_queries[item]['adapt_or_not'] = "0"
                else:
                    print(f"⚠️ Empty content for item {item}, setting default")
                    context_queries[item]['adapt_or_not'] = "0"
                    
            except Exception as e:
                print(f"❌ Error processing item {item}: {e}")
                # Đảm bảo luôn có giá trị mặc định cho item bị lỗi
                try:
                    context_queries[item]['adapt_or_not'] = "0"
                except:
                    print(f"❌ Cannot set default value for item {item}")


def parse_output_text(output_text: str) -> dict:
    DEFAULT_JSON = {"đáp ứng kỹ thuật": "0"}
    
    # Kiểm tra đầu vào
    if output_text is None or output_text.strip() == "":
        print("⚠️ Output text is None or empty, returning default")
        return DEFAULT_JSON.copy()
    
    # B1: Tìm phần JSON đầu tiên trong chuỗi
    match = re.search(r"\{.*\}", output_text, re.DOTALL)
    if not match:
        print("⚠️ No JSON found in output text, returning default")
        return DEFAULT_JSON.copy()

    json_str = match.group(0).strip()
    print(f"📝 Found JSON string: {json_str}")

    # B2: Parse JSON
    try:
        data = json.loads(json_str)
        print(f"✅ Successfully parsed JSON: {data}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}, returning default")
        return DEFAULT_JSON.copy()

    # B3: Kiểm tra có phải là dict không
    if not isinstance(data, dict):
        print("⚠️ Parsed data is not a dictionary, returning default")
        return DEFAULT_JSON.copy()

    # B4: Kiểm tra có key "đáp ứng kỹ thuật" không
    if "đáp ứng kỹ thuật" not in data:
        print("⚠️ Missing 'đáp ứng kỹ thuật' key, returning default")
        return DEFAULT_JSON.copy()

    # B5: Validate và normalize giá trị của key "đáp ứng kỹ thuật"
    dap_ung_value = data["đáp ứng kỹ thuật"]
    
    # Chỉ chấp nhận 0 hoặc 1
    try:
        if isinstance(dap_ung_value, (int, float)):
            # Chuyển đổi về 0 hoặc 1
            normalized_value = "1" if dap_ung_value > 0 else "0"
        elif isinstance(dap_ung_value, str):
            dap_ung_value = dap_ung_value.strip()
            # Xử lý string đơn giản "0", "1"
            if dap_ung_value in ["0", "1"]:
                normalized_value = dap_ung_value
            # Xử lý fraction
            elif '/' in dap_ung_value:
                try:
                    numerator, denominator = dap_ung_value.split('/')
                    numerator = int(numerator)
                    denominator = int(denominator)
                    if denominator > 0 and numerator > 0:
                        normalized_value = "1"
                    else:
                        normalized_value = "0"
                except (ValueError, ZeroDivisionError):
                    normalized_value = "0"
            # Xử lý số string khác
            elif re.match(r'^\d+(\.\d+)?$', dap_ung_value):
                try:
                    num_value = float(dap_ung_value)
                    normalized_value = "1" if num_value > 0 else "0"
                except ValueError:
                    normalized_value = "0"
            else:
                print(f"⚠️ Invalid string value: {dap_ung_value}, returning default")
                return DEFAULT_JSON.copy()
        else:
            print(f"⚠️ Invalid value type: {type(dap_ung_value)}, returning default")
            return DEFAULT_JSON.copy()
            
        print(f"✅ Normalized value: {dap_ung_value} -> {normalized_value}")
        return {"đáp ứng kỹ thuật": normalized_value}
        
    except Exception as e:
        print(f"⚠️ Error normalizing value {dap_ung_value}: {e}, returning default")
        return DEFAULT_JSON.copy()



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
            
            # Validate JSON trả về từ assistant
            try:
                # Thử parse để đảm bảo là JSON hợp lệ
                parsed_json = json.loads(call.function.arguments)
                if isinstance(parsed_json, dict) and "đáp ứng kỹ thuật" in parsed_json:
                    return call.function.arguments
                else:
                    print("⚠️ Assistant returned invalid JSON structure")
                    return json.dumps({"đáp ứng kỹ thuật": "0"})
            except json.JSONDecodeError:
                print("⚠️ Assistant returned invalid JSON")
                return json.dumps({"đáp ứng kỹ thuật": "0"})

        elif run.status == "completed":
            messages = await client.beta.threads.messages.list(thread_id=thread_id)
            for msg in messages.data:
                print(f"[{msg.role}] {msg.content[0].text.value}")
            print("⚠️ Run completed but no tool call found")
            return json.dumps({"đáp ứng kỹ thuật": "0"})

        else:
            print(f"⚠️ Unexpected run status: {run.status}")
            return json.dumps({"đáp ứng kỹ thuật": "0"})

    except Exception as e:
        print(f"❌ Error in evaluator_adaptability: {e}")
        return json.dumps({"đáp ứng kỹ thuật": "0"})