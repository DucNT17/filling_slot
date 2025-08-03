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
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
    FilterCondition
)
from step2_create_query import llm_create_query
from config_db import config_db

def retrieve_results(path_pdf, collection_name):
    context_queries, product_keys = llm_create_query(path_pdf)
    for product in product_keys:
        file_names = retrieve_document(product, collection_name)
        items = product_keys[product]
        for item in items:
            if item not in context_queries:
                continue
            query = context_queries[item]["query"]
            content = retrieve_chunk(file_names, query, collection_name)
            context_queries[item]["relevant_context"] = content

    return context_queries, product_keys

def retrieve_document(query_str, collection_name):
    file_names = []
    vector_store = config_db(collection_name)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    
    filters_document = MetadataFilters(
        filters=[
            MetadataFilter(key="type", operator=FilterOperator.EQ, value="summary_document"),
        ],
    condition=FilterCondition.AND,
    )
    retriever_document = index.as_retriever(similarity_top_k=5, verbose=True, filters=filters_document)
    
    results = retriever_document.retrieve(query_str)

    for result in results:
        metadata = result.metadata
        file_names.append(metadata["file_name"])

    return file_names

def retrieve_chunk(file_names, query_str, collection_name):
    vector_store = config_db(collection_name)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    
    filters_chunk = MetadataFilters(
        filters=[
            MetadataFilter(key="file_name", operator=FilterOperator.IN, value=file_names),
            MetadataFilter(key="type", operator=FilterOperator.EQ, value="chunk_document"),
        ],
        condition=FilterCondition.AND,
    )

    retriever_chunk = index.as_retriever(similarity_top_k=5, verbose=True, filters=filters_chunk)
    
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