from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_parse import LlamaParse
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SemanticSplitterNodeParser
from qdrant_client.http.models import PayloadSchemaType, Filter, FieldCondition, MatchText, MatchValue
from ai_server.config_db import client, aclient, config_db


# ✅ Thay tên collection thật của bạn tại đây
collection_name = "hello_my_friend2"

product_id = "p_140e18ef-7c45-11f0-aa45-601895455aee"

client.delete(
    collection_name=collection_name,
    points_selector=Filter(
        must=[
            FieldCondition(
                key="product_id",  # trường payload
                match=MatchValue(value=product_id)
            )
        ]
    )
)