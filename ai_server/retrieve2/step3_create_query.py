from ai_server.retrieve2.step2_process_json import process_json_to_list
from llama_index.core import Settings
from openai import OpenAI
from dotenv import load_dotenv
import re
import os
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm_create_query(path_pdf):
    converted_data = process_json_to_list(path_pdf)
    context_queries, product_keys = create_json(converted_data)
    # for key in context_queries:
    #     context_prompt = context_queries[key]
    #     prompt = prompt_create_query(context_prompt)
    #     response = client.responses.create(
    #         model="gpt-4o-mini",
    #         input=prompt,
    #         temperature=0
    #     )
    #     output_text = response.output_text.strip()
    #     context_queries[key]["query"] = output_text
    return context_queries, product_keys


def create_json(converted_data):
    context_prompts = {}  # Đổi từ list sang dict
    product_keys = {}

    for item in converted_data:
        ten_san_pham = item['ten_san_pham']
        for muc in item['cac_muc']:
            ten_hang_hoa = muc['ten_hang_hoa']
            thong_so_ky_thuat = muc['thong_so_ky_thuat']
            for key, value in thong_so_ky_thuat.items():
                if isinstance(value, list):
                    q = value[0]
                    k = value[1]
                    value_str = ' '.join(value)
                else:
                    q = None
                    k = value
                    value_str = value

                # Ghi vào context_prompts
                context_prompts[key] = {
                    "ten_san_pham": ten_san_pham,
                    "ten_hang_hoa": ten_hang_hoa,
                    "value": value_str,
                    "yeu_cau_ky_thuat_chi_tiet": k,
                    "yeu_cau_ky_thuat": q
                }

                # Ghi vào product_keys
                if ten_san_pham not in product_keys:
                    product_keys[ten_san_pham] = {}
                if ten_hang_hoa not in product_keys[ten_san_pham]:
                    product_keys[ten_san_pham][ten_hang_hoa] = []
                product_keys[ten_san_pham][ten_hang_hoa].append(key)
    return context_prompts, product_keys
