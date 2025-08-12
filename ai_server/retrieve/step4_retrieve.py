import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import VectorStoreInfo
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.settings import Settings
from llama_index.core import StorageContext, VectorStoreIndex
from qdrant_client.http.models import PayloadSchemaType, Filter, FieldCondition, MatchText
from llama_index.readers.file import MarkdownReader
import json
import copy
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
    FilterCondition
)
from ai_server.retrieve.step3_create_query import llm_create_query
from ai_server.config_db import config_db, client as qdrantClient
from openai import OpenAI
import time
from ai_server.retrieve.track_reference_function import track_reference
from ai_server.retrieve.adapt_or_not_function import adapt_or_not
from ai_server.retrieve.compare_function import compare_fuction, merge_dicts
import re
clientOpenAI = OpenAI()

def retrieve_results(path_pdf, collection_name):
    context_queries, product_keys = llm_create_query(path_pdf)
    for product in product_keys:
        product_line = retrieve_product_line(product)
        print(f"Product Line: {product_line}")
        query_str = f"{product}: "

        all_requirements = product_keys[product]
        for key in all_requirements:
            query_str += f"{key} :"
            for item in all_requirements[key]:
                if item not in context_queries:
                    continue
                query_str += context_queries[item]["value"]
            query_str += "\n"
        prompt_yeu_cau_ky_thuat = create_prompt_extract_module(query_str)
        response = clientOpenAI.responses.create(
            model="gpt-4o-mini",
            input=prompt_yeu_cau_ky_thuat,
            temperature=0
        )
        product_requirement = f"{product}: {response.output_text.strip()}" 
        products = retrieve_document(collection_name, product_line, product_requirement)  #search product (brochure, product_id)


        kha_nang_dap_ung_tham_chieu_final = {}
        adapt_or_not_final = {}
        sum = 0
        for item in products:  #Mỗi sản phẩm liên quan
            kha_nang_dap_ung_tham_chieu_step = {}
            adapt_or_not_step = {}
            product_search_id = []
            product_id = item["product_id"]
            brochure = item["brochure_file_path"]
            reader = MarkdownReader()
            documents = reader.load_data(file=f"D:/study/LammaIndex/{brochure}")
            markdown_text = "\n".join(doc.text for doc in documents)
            prompt_brochure = create_prompt_extract_module2(markdown_text)
            response = clientOpenAI.responses.create(
                model="gpt-4o-mini",
                input=prompt_brochure,
                temperature=0
            )
            product_brochure = response.output_text.strip()
            match = re.search(r'```json\s*(.*?)\s*```', product_brochure, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                json_str = response  # nếu không có code block thì dùng nguyên văn

            # Parse JSON thành list Python
            product_brochure = json.loads(json_str)
            product_component_id = retrieve_component(collection_name, product_brochure)
            product_search_id.extend(product_component_id)  
            product_search_id.append(product_id)

            product_search_id = set(product_search_id)
            
            for key in all_requirements:
                for item in all_requirements[key]:
                    if item not in context_queries:
                        continue
                    query = context_queries[item]["value"]
                    content = retrieve_chunk(product_search_id, query, collection_name)
                    if item not in kha_nang_dap_ung_tham_chieu_step:
                        kha_nang_dap_ung_tham_chieu_step[item] = {}
                    kha_nang_dap_ung_tham_chieu_step[item]['relevant_context'] = content
            kha_nang_dap_ung_tham_chieu_step = track_reference(context_queries, kha_nang_dap_ung_tham_chieu_step)
            
            kha_nang_dap_ung_tham_chieu_step, adapt_or_not_step = adapt_or_not(kha_nang_dap_ung_tham_chieu_step, adapt_or_not_step, all_requirements, context_queries)

            sum_local = compare_fuction(adapt_or_not_step)
            if sum_local > sum:
                sum = sum_local
                kha_nang_dap_ung_tham_chieu_final = copy.deepcopy(kha_nang_dap_ung_tham_chieu_step)
                adapt_or_not_final = copy.deepcopy(adapt_or_not_step)
            with open(f"D:/study/LammaIndex/output/kha_nang_dap_ung_{product_id}.json", "w", encoding="utf-8") as f:
                json.dump(kha_nang_dap_ung_tham_chieu_step, f, ensure_ascii=False, indent=4)
            with open(f"D:/study/LammaIndex/output/adapt_or_not_{product_id}.json", "w", encoding="utf-8") as f:
                json.dump(adapt_or_not_step, f, ensure_ascii=False, indent=4)
        context_queries = merge_dicts(kha_nang_dap_ung_tham_chieu_final, context_queries)
        for key in adapt_or_not_final:
            product_keys[product][key].extend(adapt_or_not_final[key])  # Giả sử bạn muốn lấy giá trị đầu tiên

        
    with open("D:/study/LammaIndex/output/context_queries.json", "w", encoding="utf-8") as f:
        json.dump(context_queries, f, ensure_ascii=False, indent=4)
    with open("D:/study/LammaIndex/output/product_keys.json", "w", encoding="utf-8") as f:
        json.dump(product_keys, f, ensure_ascii=False, indent=4)

    return context_queries, product_keys

def retrieve_document(collection_name, product_line, query_str):
    product_ids = []
    vector_store = config_db(collection_name)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    
    filters_document = MetadataFilters(
        filters=[
            MetadataFilter(key="product_line", operator=FilterOperator.EQ, value=product_line),
            MetadataFilter(key="type", operator=FilterOperator.EQ, value="summary_document"),
        ],
    condition=FilterCondition.AND,
    )
    retriever_document = index.as_retriever(similarity_top_k=3, sparse_top_k=10, verbose=True, enable_hybrid=True, filters=filters_document)

    results = retriever_document.retrieve(query_str)

    for result in results:
        metadata = result.metadata
        product_ids.append(
            {
                "product_id": metadata["product_id"],
                "brochure_file_path": metadata["brochure_file_path"],
            }
        )

    return product_ids

def retrieve_chunk(product_ids, query_str, collection_name):
    vector_store = config_db(collection_name)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    
    filters_chunk = MetadataFilters(
        filters=[
            MetadataFilter(key="product_id", operator=FilterOperator.IN, value=product_ids),
            MetadataFilter(key="type", operator=FilterOperator.EQ, value="chunk_document"),
        ],
        condition=FilterCondition.AND,
    )

    retriever_chunk = index.as_retriever(similarity_top_k=5, sparse_top_k=10, enable_hybrid=True, verbose=True, filters=filters_chunk)

    results = retriever_chunk.retrieve(query_str)
    content = ""
    for i, result in enumerate(results, start=1):
        metadata = result.metadata
        file_name = metadata["file_name"]+ ".pdf"
        page = metadata["page"]
        table = metadata["table_name"]
        figure_name = metadata.get("figure_name")
        text = result.text.strip()
        content += f"Chunk {i} trong file {file_name} tại trang {page}, có chứa bảng {table} và hình {figure_name} có nội dung:\n{text}\n\n"

    return content

def retrieve_product_line(product_name, assistant_id="asst_j5wHMN84dpSLXD2GMH5QifS0"):
    thread = clientOpenAI.beta.threads.create()
    thread_id = thread.id
    # 2. Gửi message vào thread
    clientOpenAI.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=product_name
    )
    run = clientOpenAI.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        tool_choice="auto"  # hoặc thay bằng tool cụ thể nếu cần
        # tool_choice={"type": "function", "function": {"name": "danh_gia_ky_thuat"}}
    )
    run_id = run.id
    # 4. Đợi assistant xử lý xong
    while True:
        run_status = clientOpenAI.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run_status.status == "completed":
            break
        elif run_status.status in ["failed", "cancelled", "expired"]:
            raise Exception(f"Run failed with status: {run_status.status}")
        time.sleep(1)

    # 5. Lấy kết quả trả về từ Assistant
    messages = clientOpenAI.beta.threads.messages.list(thread_id=thread_id)
    for message in reversed(messages.data):  # đảo ngược để lấy kết quả mới nhất trước
        if message.role == "assistant":
            for content in message.content:
                if content.type == "text":
                    return content.text.value

    return None

def create_prompt_extract_module(query_str):
    prompt = f"""
You are an expert in hardware product documentation analysis.  
Read the provided text (which can be either a detailed product brochure or a general product requirement) and extract ONLY the core physical hardware components/modules of the system.
 
For each component:
- If the text explicitly includes a model number, code, or exact specification tied to the component → output "<Full Component Name>: <Exact Model(s)/Code(s)>".
- If the text does NOT provide a model number or code → output only "<Full Component Name>".
 
Input:
<<<
{query_str}
>>>
 
Output format:
- <Component Name>[: <Model(s)/Code(s) if available>]
 
Rules:
1. Only include core hardware modules essential for the product’s operation (e.g., Rectifier Module, Controller, AC Input, AC Distribution, DC Distribution, Battery Distribution, Lightning Protection, Cooling System, Battery Bank).
2. Preserve the exact wording of component/module names from the text (do not paraphrase or generalize).
3. Include model numbers, codes, or exact designations only if explicitly stated in the text.  
   - If multiple models exist, list them separated by " / ".
4. If a component has sub-parts (e.g., BLVD/LLVD, Input/Output), keep them as separate lines with their full names.
5. Ignore optional accessories, warranty info, standards compliance, and marketing text unless they are part of the official component name/specification.
7. Do not infer or guess component names—extract only what is explicitly stated.    
"""
    return prompt

def create_prompt_extract_module2(query_str):
    prompt = f"""
    You are an expert in hardware product documentation analysis.  
Read the provided text (which can be either a detailed product brochure or a general product requirement) and extract ONLY the model numbers, codes, or exact designations of the core physical hardware components/modules of the system.

Input:
<<<
{query_str}
>>>

Output format:
A valid JSON array of strings, where each string is one model/code.  
Example:
["R48-121A3", "R56-3220"]

Rules:
1. Only extract model numbers, codes, or exact designations explicitly stated in the text.  
   - Do NOT include component/module names, descriptions, amperage, voltage, or units (e.g., "125 A / 2P" is ignored).
2. Extract models only from core hardware modules essential for the product’s operation (e.g., Rectifier Module, Controller, AC Input, AC Distribution, DC Distribution, Battery Distribution, Lightning Protection, Cooling System, Battery Bank).
3. Preserve the exact case, spacing, and characters from the original text.
4. If multiple models are listed together, split them into separate JSON array elements.
5. Ignore optional accessories, warranty info, standards compliance, and marketing text.
6. Do not infer or guess model numbers—extract only what is explicitly stated.
7. Output only a valid JSON array without extra text or explanations.

    """
    return prompt

def retrieve_component(collection_name, keyword_product_brochure):
    should_conditions = [
        FieldCondition(
            key='file_brochure_name',
            match=MatchText(text=kw)
        )
        for kw in keyword_product_brochure
    ]

    text_filter = Filter(
        should=should_conditions  # OR search
    )

    scroll_result, next_page = qdrantClient.scroll(
        collection_name=collection_name,
        scroll_filter=text_filter,
        limit=5
    )

    product_ids = []
    if scroll_result:
        print("Kết quả tìm kiếm:")
        for result in scroll_result:
            metadata = result.payload
            product_id = metadata.get("product_id", "")
            if product_id:
                product_ids.append(product_id)
    return product_ids
