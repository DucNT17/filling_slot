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
    Phiên bản async của hàm adapt_or_not
    """
    assistant_id = "asst_SIWbRtRbvCxXS9dgqvtj9U8O"
    print(f"Assistant ID: {assistant_id}")
    
    # Tạo semaphore để giới hạn số requests đồng thời
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_requirement(key: str):
        async with semaphore:
            try:
                print(f"🚀 Đang xử lý requirement: {key}")
                
                dap_ung_ky_thuat = ""
                tai_lieu_tham_chieu = ""
                
                # Thu thập thông tin từ tất cả items trong requirement
                for item in all_requirements[key]:
                    if item not in kha_nang_dap_ung_tham_chieu_step:
                        continue
                        
                    yeu_cau_ky_thuat = context_queries[item].get('yeu_cau_ky_thuat_chi_tiet', "")
                    kha_nang_dap_ung = kha_nang_dap_ung_tham_chieu_step[item].get('kha_nang_dap_ung', "Không có thông tin")
                    if kha_nang_dap_ung == "":
                        kha_nang_dap_ung = "Không có thông tin"
                    dap_ung_ky_thuat += f"{yeu_cau_ky_thuat} || {kha_nang_dap_ung}\n"
            
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
                
                # Chỉ xử lý nếu có dữ liệu
                if dap_ung_ky_thuat and tai_lieu_tham_chieu:
                    print(f"📞 Gọi API cho key: {key}")
                    result = await Evaluator_adaptability_async(dap_ung_ky_thuat, assistant_id)
                    result = parse_output_text(result)  # result đã là dict
                    
                    output_text = result['đáp ứng kỹ thuật']
                    
                    print(f"✅ Hoàn thành key: {key}")
                    return key, output_text, tai_lieu_tham_chieu
                else:
                    print(f"⚠️ Không có dữ liệu cho key: {key}")
                    return key, None, None
                    
            except Exception as e:
                print(f"❌ Lỗi xử lý key {key}: {str(e)}")
                return key, None, None
    
    # Tạo tasks cho tất cả requirements
    tasks = [process_requirement(key) for key in all_requirements]
    
    print(f"🏃‍♂️ Bắt đầu xử lý {len(tasks)} requirements với {max_concurrent} requests đồng thời...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Xử lý kết quả
    for result in results:
        weight = 0
        if isinstance(result, Exception):
            print(f"❌ Task failed: {result}")
            continue
            
        key, output_text, tai_lieu_tham_chieu = result
        
        if output_text is not None and tai_lieu_tham_chieu is not None:
            if key not in adapt_or_not_step:
                adapt_or_not_step[key] = []
            weight = len(all_requirements[key])  # Trọng số là số lượng item đã có
            adapt_or_not_step[key].append(weight)
            adapt_or_not_step[key].append(output_text)
            adapt_or_not_step[key].append(tai_lieu_tham_chieu)
    
    print("🎉 Hoàn thành tất cả requirements!")
    return kha_nang_dap_ung_tham_chieu_step, adapt_or_not_step


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