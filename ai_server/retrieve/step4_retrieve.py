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
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from llama_index.core import StorageContext, VectorStoreIndex
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
from ai_server.retrieve.track_reference_function import track_reference_async
from ai_server.retrieve.adapt_or_not_function import adapt_or_not_async
from ai_server.retrieve.compare_function import compare_function, merge_dicts
import re
import asyncio
from typing import Dict, Any, Tuple
from llama_index.core import QueryBundle
from llama_index.core.postprocessor import LLMRerank
from concurrent.futures import ThreadPoolExecutor

clientOpenAI = OpenAI()

async def retrieve_results(path_pdf, collection_name):
    """
    Async version of retrieve_results using semaphore for concurrency control
    """
    # Run llm_create_query in thread pool since it's synchronous
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        context_queries, product_keys = await loop.run_in_executor(
            executor, llm_create_query, path_pdf
        )
    
    for product in product_keys:
        product_line = await retrieve_product_line_async(product)
        product_line = product_line.replace('"', '').replace("'", "")
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
        
        # Run OpenAI API call in thread pool
        with ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(
                executor,
                lambda: clientOpenAI.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt_yeu_cau_ky_thuat}],
                    temperature=0
                )
            )
        
        product_requirement = f"{product}: {response.choices[0].message.content.strip()}" 
        products = await retrieve_document_async(collection_name, product_line, product_requirement)
        print("products:", products)
        
        kha_nang_dap_ung_tham_chieu_final = {}
        adapt_or_not_final = {}
        sum = 0
        
        for item in products:  #Mỗi sản phẩm liên quan
            kha_nang_dap_ung_tham_chieu_step = {}
            adapt_or_not_step = {}
            product_id = item["product_id"]
            print(f"Processing product_id: {product_id}")
            
            kha_nang_dap_ung_tham_chieu_step = await process_requirements_async_with_semaphore(
                collection_name, all_requirements, context_queries, product_id, max_concurrent=10
            )
            # print(f"Processed kha_nang_dap_ung_tham_chieu_step for product_id {product_id}: {kha_nang_dap_ung_tham_chieu_step}")
            
            kha_nang_dap_ung_tham_chieu_step = await track_reference_async(context_queries, kha_nang_dap_ung_tham_chieu_step)
            kha_nang_dap_ung_tham_chieu_step, adapt_or_not_step = await adapt_or_not_async(kha_nang_dap_ung_tham_chieu_step, adapt_or_not_step, all_requirements, context_queries)

            sum_local = compare_function(adapt_or_not_step)
            if sum_local > sum:
                sum = sum_local
                kha_nang_dap_ung_tham_chieu_final = copy.deepcopy(kha_nang_dap_ung_tham_chieu_step)
                adapt_or_not_final = copy.deepcopy(adapt_or_not_step)
            
            # Save files in thread pool
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    save_json_files,
                    product_id,
                    kha_nang_dap_ung_tham_chieu_step,
                    adapt_or_not_step
                )
                
        context_queries = merge_dicts(kha_nang_dap_ung_tham_chieu_final, context_queries)
        for key in adapt_or_not_final:
            if key in product_keys[product]:
                product_keys[product][key].extend(adapt_or_not_final[key])
            else:
                print(f"Warning: Key '{key}' không tồn tại trong product_keys[{product}]")

    # Save final results in thread pool
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(
            executor,
            save_final_results,
            context_queries,
            product_keys
        )

    return context_queries, product_keys

async def retrieve_document_async(collection_name, product_line, query_str):
    """
    Async wrapper for retrieve_document
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor,
            retrieve_document_sync,
            collection_name,
            product_line,
            query_str
        )

def retrieve_document_sync(collection_name, product_line, query_str):
    """
    Synchronous version of retrieve_document (original logic)
    """
    product_ids = []
    try:
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
                    "product_id": metadata["product_id"]
                }
            )
    except Exception as e:
        print(f"Lỗi trong retrieve_document: {e}")
        
    return product_ids

async def retrieve_chunk_with_semaphore(semaphore, product_id, query_str, collection_name, item_key, context_queries):
    """
    Wrapper function to handle semaphore and update context_queries
    """
    async with semaphore:
        content = await retrieve_chunk_async(product_id, query_str, collection_name)
        if content:
            context_queries[item_key] = {'relevant_context': content}

async def retrieve_chunk_async(product_id, query_str, collection_name):
    """
    Async wrapper for retrieve_chunk using thread pool
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        content = await loop.run_in_executor(
            executor, 
            retrieve_chunk_sync, 
            product_id, 
            query_str, 
            collection_name
        )
    return content

def retrieve_chunk_sync(product_id, query_str, collection_name):
    """
    Synchronous version of retrieve_chunk (original logic)
    """
    try:
        vector_store = config_db(collection_name)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        
        filters_chunk = MetadataFilters(
            filters=[
                MetadataFilter(key="product_id", operator=FilterOperator.EQ, value=product_id),
                MetadataFilter(key="type", operator=FilterOperator.EQ, value="chunk_document"),
            ],
            condition=FilterCondition.AND,
        )
        query_bundle = QueryBundle(query_str)
        retriever_chunk = index.as_retriever(
            similarity_top_k=10,
            sparse_top_k=15,
            # verbose=True,
            vector_store_query_mode=VectorStoreQueryMode.HYBRID,
            filters=filters_chunk,
            hybrid_top_k=10,
            alpha=0.7
        )
        retrieved_nodes = retriever_chunk.retrieve(query_bundle)
        reranker = LLMRerank(
            # choice_select_prompt=custom_rerank_prompt,
            choice_batch_size=5,
            top_n=5,
            llm=Settings.llm
        )
        results = reranker.postprocess_nodes(
            retrieved_nodes, query_bundle
        )
    
        
        content = ""
        for i, result in enumerate(results, start=1):
            metadata = result.metadata
            file_name = metadata.get("file_name", "unknown") + ".pdf"
            page = metadata.get("page", "unknown")
            table = metadata.get("table_name", "N/A")
            figure_name = metadata.get("figure_name", "N/A")
            text = result.text.strip()
            content += f"""
            ========== CHUNK {i} ========
            page: {page}
            file: {file_name}
            figure: {figure_name}
            table: {table}

            Nội dung của chunk: {text}
            ========== CHUNK {i} END ==========\n\n"""
        return content
    except Exception as e:
        print(f"Lỗi trong retrieve_chunk_sync: {e}")
        return ""

async def process_single_item_with_semaphore(semaphore, item, key, context_queries, product_id, collection_name):
    """
    Wrapper function to handle semaphore for single item processing
    """
    async with semaphore:
        return await process_single_item_async(item, key, context_queries, product_id, collection_name)

async def process_single_item_async(item: str, key: str, context_queries: Dict, product_id: Any, collection_name: str) -> tuple:
    """
    Async wrapper for processing single item
    """
    try:
        if item not in context_queries:
            return item, None
        
        query = context_queries[item].get("value", "")
        content = await retrieve_chunk_async(product_id, query, collection_name)
        print(f"Processed item: {item}")
        
        return item, {
            'relevant_context': content
        }
    except Exception as e:
        print(f"Lỗi khi xử lý item {item}: {e}")
        return item, None

async def retrieve_product_line_async(product_name, assistant_id="asst_CkhqaSBGeaIlLO5mY7puPybD"):
    """
    Async wrapper for retrieve_product_line
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor,
            retrieve_product_line_sync,
            product_name,
            assistant_id
        )

def retrieve_product_line_sync(product_name, assistant_id="asst_CkhqaSBGeaIlLO5mY7puPybD"):
    """
    Synchronous version of retrieve_product_line (original logic)
    """
    try:
        thread = clientOpenAI.beta.threads.create()
        thread_id = thread.id
        
        clientOpenAI.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=product_name
        )
        
        run = clientOpenAI.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            tool_choice="auto"
        )
        run_id = run.id
        
        max_wait_time = 300
        wait_time = 0
        while wait_time < max_wait_time:
            run_status = clientOpenAI.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Run failed with status: {run_status.status}")
            time.sleep(1)
            wait_time += 1
        
        if wait_time >= max_wait_time:
            raise Exception("Timeout: Assistant không phản hồi trong thời gian cho phép")

        messages = clientOpenAI.beta.threads.messages.list(thread_id=thread_id)
        for message in reversed(messages.data):
            if message.role == "assistant":
                for content in message.content:
                    if content.type == "text":
                        return content.text.value

        return None
    except Exception as e:
        print(f"Lỗi trong retrieve_product_line: {e}")
        return None

def create_prompt_extract_module(query_str):
    """
    This function remains synchronous as it's just string processing
    """
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
1. Only include core hardware modules essential for the product's operation (e.g., Rectifier Module, Controller, AC Input, AC Distribution, DC Distribution, Battery Distribution, Lightning Protection, Cooling System, Battery Bank).
2. Preserve the exact wording of component/module names from the text (do not paraphrase or generalize).
3. Include model numbers, codes, or exact designations only if explicitly stated in the text.  
   - If multiple models exist, list them separated by " / ".
4. If a component has sub-parts (e.g., BLVD/LLVD, Input/Output), keep them as separate lines with their full names.
5. Ignore optional accessories, warranty info, standards compliance, and marketing text unless they are part of the official component name/specification.
7. Do not infer or guess component names—extract only what is explicitly stated.    
"""
    return prompt

async def process_requirements_async_with_semaphore(collection_name, all_requirements: Dict, context_queries: Dict, product_id: Any, max_concurrent: int = 10) -> Dict:
    """
    Async version with semaphore for concurrency control
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    kha_nang_dap_ung_tham_chieu_step = {}
    
    # Collect all tasks to run concurrently
    tasks = []
    items_info = []  # To track which item corresponds to which result
    
    for key in all_requirements:
        for item in all_requirements[key]:
            if item in context_queries:
                task = process_single_item_with_semaphore(
                    semaphore, item, key, context_queries, product_id, collection_name
                )
                tasks.append(task)
                items_info.append((item, key))
    
    print(f"Bắt đầu xử lý {len(tasks)} tasks với tối đa {max_concurrent} concurrent...")
    
    try:
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Lỗi khi xử lý: {result}")
                continue
            
            item, data = result
            if data is not None:
                kha_nang_dap_ung_tham_chieu_step[item] = data
                
    except Exception as e:
        print(f"Lỗi trong process_requirements_async_with_semaphore: {e}")
    
    return kha_nang_dap_ung_tham_chieu_step

def save_json_files(product_id, kha_nang_dap_ung_tham_chieu_step, adapt_or_not_step):
    """
    Synchronous helper function for saving JSON files
    """
    try:
        with open(f"output/kha_nang_dap_ung_{product_id}.json", "w", encoding="utf-8") as f:
            json.dump(kha_nang_dap_ung_tham_chieu_step, f, ensure_ascii=False, indent=4)
        with open(f"output/adapt_or_not_{product_id}.json", "w", encoding="utf-8") as f:
            json.dump(adapt_or_not_step, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu file cho product_id {product_id}: {e}")

def save_final_results(context_queries, product_keys):
    """
    Synchronous helper function for saving final results
    """
    try:
        with open("output/context_queries.json", "w", encoding="utf-8") as f:
            json.dump(context_queries, f, ensure_ascii=False, indent=4)
        with open("output/product_keys.json", "w", encoding="utf-8") as f:
            json.dump(product_keys, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu file kết quả cuối: {e}")