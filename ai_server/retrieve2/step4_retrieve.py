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
# from llama_index.postprocessor.colbert_rerank import ColbertRerank
from llama_index.core.postprocessor import LLMRerank
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
    FilterCondition
)
from ai_server.retrieve2.step3_create_query import llm_create_query
from ai_server.config_db import config_db
import asyncio
from concurrent.futures import ThreadPoolExecutor
from llama_index.core import QueryBundle
from llama_index.core.prompts import PromptTemplate
from llama_index.core.prompts.prompt_type import PromptType



async def retrieve_results(path_pdf, filename_ids, collection_name, max_concurrent=10):
    """
    Async version of retrieve_results using semaphore for concurrency control
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Run llm_create_query in thread pool since it's synchronous
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        context_queries, product_keys = await loop.run_in_executor(
            executor, llm_create_query, path_pdf
        )

    # Collect all tasks to run concurrently
    tasks = []
    
    for product in product_keys:
        items = product_keys[product]
        for key in items:
            for item in items[key]:
                if item not in context_queries:
                    continue
                
                # Create async task for each retrieve operation
                task = retrieve_chunk_with_semaphore(
                    semaphore, 
                    filename_ids, 
                    context_queries[item]["ten_hang_hoa"] +": " + context_queries[item]["value"], 
                    collection_name,
                    item,
                    context_queries
                )
                tasks.append(task)
    
    # Run all tasks concurrently
    await asyncio.gather(*tasks)
    
    return context_queries, product_keys

async def retrieve_chunk_with_semaphore(semaphore, filename_ids, query, collection_name, item_key, context_queries):
    """
    Wrapper function to handle semaphore and update context_queries
    """
    async with semaphore:
        content = await retrieve_chunk_async(filename_ids, query, collection_name)
        context_queries[item_key]["relevant_context"] = content

async def retrieve_chunk_async(filename_ids, query_str, collection_name):
    """
    Truly async version of retrieve_chunk using thread pool
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        content = await loop.run_in_executor(
            executor, 
            retrieve_chunk_sync, 
            filename_ids, 
            query_str, 
            collection_name
        )
    return content

def retrieve_chunk_sync(filename_ids, query_str, collection_name):
    """
    Synchronous version of retrieve_chunk (original logic)
    """
    rerank_prompt = """
A list of documents (chunks of text) is shown below. 
Each document has a number next to it. A question is also provided.
 
Task:
- Rank the documents by how useful they are for answering the question. 
- Assign each selected document a relevance score from 1 to 10 
  (10 = highly relevant and specific, 1 = barely relevant).
- Exclude documents that are not relevant.
- Output only the ranked list in descending order of relevance.
 
Example format:
Document 1:
<text of document 1>
 
Document 2:
<text of document 2>
 
...
 
Question: <the user’s query>
 
Answer:
Doc: 2, Relevance: 9
Doc: 5, Relevance: 7
Doc: 3, Relevance: 4
 
---
 
Now try this:
 
{context_str}
Question: {query_str}
Answer:
"""
    custom_rerank_prompt = PromptTemplate(
    rerank_prompt, prompt_type=PromptType.CHOICE_SELECT
)
    vector_store = config_db(collection_name)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    filters_chunk = MetadataFilters(
        filters=[
            MetadataFilter(key="filename_id", operator=FilterOperator.IN, value=filename_ids),
            MetadataFilter(key="type", operator=FilterOperator.EQ, value="chunk_document"),
        ],
        condition=FilterCondition.AND,
    )
    query_bundle = QueryBundle(query_str)
    retriever_chunk = index.as_retriever(
        similarity_top_k=10,
        sparse_top_k=15,
        # verbose=True,
        enable_hybrid=True,
        filters=filters_chunk
    )
    retrieved_nodes = retriever_chunk.retrieve(query_bundle)
    reranker = LLMRerank(
        # choice_select_prompt=custom_rerank_prompt,
        choice_batch_size=10,
        top_n=5,
        llm=Settings.llm
    )
    results = reranker.postprocess_nodes(
        retrieved_nodes, query_bundle
    )
    
    # results = retriever_chunk.retrieve(query_str)

    # results = colbert_reranker.postprocess_nodes(
    #     nodes=initial_nodes,
    #     query_str=query_str
    # )
    content = ""
    for i, result in enumerate(results, start=1):
        metadata = result.metadata
        file_name = metadata["file_name"] + ".pdf"
        page = metadata["page"]
        table = metadata["table_name"]
        figure_name = metadata.get("figure_name")
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