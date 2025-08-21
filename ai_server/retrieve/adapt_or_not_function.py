from openai import OpenAI
from dotenv import load_dotenv
import re
import json
import time
clientOpenAI = OpenAI()
from typing import Dict, Tuple
import asyncio
# === ASYNC VERSION OF ADAPT_OR_NOT ===
async def adapt_or_not_async(kha_nang_dap_ung_tham_chieu_step: Dict, 
                           adapt_or_not_step: Dict, 
                           all_requirements: Dict,
                           context_queries: Dict,
                           max_concurrent: int = 5) -> Tuple[Dict, Dict]:
    """
    Phiên bản async của hàm adapt_or_not - xử lý từng item riêng biệt
    """
    assistant_id = "asst_SIWbRtRbvCxXS9dgqvtj9U8O"
    print(f"Assistant ID: {assistant_id}")
    
    # Tạo semaphore để giới hạn số requests đồng thời
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_item(item: str, requirement_key: str):
        async with semaphore:
            try:
                print(f"🚀 Đang xử lý item: {item} trong requirement: {requirement_key}")
                
                if item not in kha_nang_dap_ung_tham_chieu_step:
                    print(f"⚠️ Item {item} không tồn tại trong kha_nang_dap_ung_tham_chieu_step")
                    return item, "0"
                    
                yeu_cau_ky_thuat = context_queries[item].get('value', "")
                kha_nang_dap_ung = kha_nang_dap_ung_tham_chieu_step[item].get('kha_nang_dap_ung', "Không có thông tin")
                module_name = context_queries[item].get('ten_hang_hoa', "")
                if kha_nang_dap_ung == "":
                    kha_nang_dap_ung = "Không có thông tin"
                
                # Xử lý từng item riêng biệt
                user_prompt = f'Module {module_name} có yêu cầu kỹ thuật là: "{yeu_cau_ky_thuat}", khả năng đáp ứng của sản phẩm hiện tại là: "{kha_nang_dap_ung}".'

                if user_prompt.strip():
                    print(f"📞 Gọi API cho item: {item}")
                    result = await Evaluator_adaptability_async(user_prompt, assistant_id)
                    result = parse_output_text(result)
                    
                    adapt_value = result['đáp ứng kỹ thuật']
                    print(f"✅ Hoàn thành item: {item} - Result: {adapt_value}")
                    return item, adapt_value
                else:
                    print(f"⚠️ Không có dữ liệu cho item: {item}")
                    return item, "0"
                    
            except Exception as e:
                print(f"❌ Lỗi xử lý item {item}: {str(e)}")
                return item, "0"
    
    # Tạo tasks cho tất cả items
    tasks = []
    for requirement_key, items in all_requirements.items():
        for item in items:
            if item in kha_nang_dap_ung_tham_chieu_step:
                task = process_item(item, requirement_key)
                tasks.append((requirement_key, item, task))
    
    print(f"🏃‍♂️ Bắt đầu xử lý {len(tasks)} items với {max_concurrent} requests đồng thời...")
    
    # Chạy tất cả tasks BẤT ĐỒNG BỘ và thu thập kết quả
    task_list = [task for _, _, task in tasks]
    results = await asyncio.gather(*task_list, return_exceptions=True)
    
    # Xử lý kết quả
    for i, result in enumerate(results):
        try:
            if isinstance(result, Exception):
                print(f"❌ Task {i} failed: {result}")
                continue
                
            item, adapt_value = result
            # Lưu kết quả adapt_or_not vào kha_nang_dap_ung_tham_chieu_step
            kha_nang_dap_ung_tham_chieu_step[item]['adapt_or_not'] = adapt_value
        except Exception as e:
            print(f"❌ Error processing result {i}: {e}")
    
    # Cập nhật adapt_or_not_step với logic mới
    for requirement_key, items in all_requirements.items():
        dap_ung_count = 0  # Đếm số item đáp ứng
        total_items = 0    # Tổng số item
        tai_lieu_tham_chieu = ""
        
        for item in items:
            if item in kha_nang_dap_ung_tham_chieu_step:
                total_items += 1
                adapt_value = kha_nang_dap_ung_tham_chieu_step[item].get('adapt_or_not', "0")
                if adapt_value == "1":
                    dap_ung_count += 1
                
                # Thu thập tài liệu tham chiếu
                tai_lieu = kha_nang_dap_ung_tham_chieu_step[item].get('tai_lieu_tham_chieu', {})
                file = tai_lieu.get("file", "")
                page = tai_lieu.get("page", "")
                table_or_figure = tai_lieu.get("table_or_figure", "")
                evidence = tai_lieu.get("evidence", "")
        
                tai_lieu_text = f"{file}, trang: {page}"
                if table_or_figure:
                    tai_lieu_text += f", trong bảng(figure): {table_or_figure}"
                tai_lieu_text += f", evidence: {evidence}\n\n"
                tai_lieu_tham_chieu += tai_lieu_text
        
        if total_items > 0:
            # Lưu vào adapt_or_not_step với format mới
            adapt_or_not_step[requirement_key] = [
                dap_ung_count,  # Weight = số item đáp ứng
                f"{dap_ung_count}/{total_items}",  # Tỷ lệ đáp ứng
                tai_lieu_tham_chieu  # Tài liệu tham chiếu
            ]
    
    print("🎉 Hoàn thành tất cả items!")
    return kha_nang_dap_ung_tham_chieu_step, adapt_or_not_step


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

    # B5: Validate và normalize giá trị của key "đáp ứng kỹ thuật" - chỉ trả về 0 hoặc 1
    dap_ung_value = data["đáp ứng kỹ thuật"]
    
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



# Hàm tạo thread
def create_thread():
    thread = clientOpenAI.beta.threads.create()
    return thread.id

# === ASYNC VERSION OF EVALUATOR_ADAPTABILITY ===
async def Evaluator_adaptability_async(user_prompt: str, assistant_id: str = "asst_SIWbRtRbvCxXS9dgqvtj9U8O") -> str:
    """
    Phiên bản async của Evaluator_adaptability với try-except handling
    """
    def _sync_evaluate():
        try:
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
                tool_choice={"type": "function", "function": {"name": "evaluate_requirement_fulfillment"}}
            )

            # 4. Chờ assistant xử lý (tối đa 20s)
            for _ in range(20):
                try:
                    run = clientOpenAI.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                    if run.status not in ["queued", "in_progress"]:
                        break
                except Exception as e:
                    print(f"⚠️ Lỗi khi retrieve run status: {str(e)}")
                    break
                time.sleep(1)

            # 5. Lấy arguments trực tiếp
            if run.status == "requires_action":
                try:
                    call = run.required_action.submit_tool_outputs.tool_calls[0]
                    print(f"👉 Assistant đã gọi tool: {call.function.name}")
                    print("🧠 Dữ liệu JSON assistant muốn trả về:")
                    print(call.function.arguments)
                    return call.function.arguments
                except Exception as e:
                    print(f"⚠️ Lỗi khi lấy tool call arguments: {str(e)}")
                    return json.dumps({"đáp ứng kỹ thuật": "0"})

            elif run.status == "completed":
                try:
                    messages = clientOpenAI.beta.threads.messages.list(thread_id=thread_id)
                    for msg in messages.data:
                        print(f"hello:.........[{msg.role}] {msg.content[0].text.value}")
                    return None
                except Exception as e:
                    print(f"⚠️ Lỗi khi lấy messages: {str(e)}")
                    return None

            else:
                print(f"Run status: {run.status}")
                return json.dumps({"đáp ứng kỹ thuật": "0"})
                
        except Exception as e:
            print(f"❌ Lỗi trong _sync_evaluate: {str(e)}")
            return json.dumps({"đáp ứng kỹ thuật": "0"})
    
    # Chạy function sync trong thread pool với try-except
    try:
        return await asyncio.to_thread(_sync_evaluate)
    except Exception as e:
        print(f"❌ Lỗi trong asyncio.to_thread: {str(e)}")
        return json.dumps({"đáp ứng kỹ thuật": "0"})