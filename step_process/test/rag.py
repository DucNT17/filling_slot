import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, PromptTemplate, Settings
from llama_index.core.vector_stores import VectorStoreInfo
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.settings import Settings
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
    FilterCondition
)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_API_KEY")
os.environ["QDRANT_API_KEY"] = os.getenv("QDRANT_API_KEY")

# Cấu hình LLM và Embedding
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini")


def search_rag(url: str, api_key: str, query: str, collection_name: str = "thong_tin_san_pham", file_name: str = "NetSure_732_User_Manual"):
    # Cấu hình client Qdrant
    client = QdrantClient(
        url=url,
        api_key=api_key,
    )
    aclient = AsyncQdrantClient(
        url=url,
        api_key=api_key,
    )
    # Khởi tạo Vector Store
    vector_store = QdrantVectorStore(
        collection_name=collection_name,
        client=client,
        aclient=aclient,
    )
    filters = MetadataFilters(
        filters=[
            MetadataFilter(key="file_name", operator=FilterOperator.EQ, value=file_name),
            MetadataFilter(key="type", operator=FilterOperator.EQ, value="chunk_document"),
        ],
        condition=FilterCondition.AND,
    )

    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    retriever = index.as_retriever(similarity_top_k=5, verbose=True, filters=filters)

    query = query

    # --- Thay đổi từ đây ---
    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever
    )

    # 2. Thực hiện truy vấn qua Query Engine
    print("Bắt đầu truy vấn với Query Engine...")
    response = query_engine.retrieve(query)
    text_content = ""
    for node in response:
        text_content += node.get_content()
    return text_content


def create_query(requirement: str, text_content: str):
    template = (
        "Based on the following text, create a comprehensive summary for the entire document.\n"
        "Document:\n---\n{requirement}\n {text_content}---\nSummary:"
    )
    prompt_template = PromptTemplate(template)
    response = Settings.llm.predict(prompt_template, requirement=requirement, text_content=text_content)
    return response.strip()

def read_json_file(file_path: str):
    import json
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data