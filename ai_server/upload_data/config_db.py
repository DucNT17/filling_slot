from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from dotenv import load_dotenv
from llama_index.embeddings.openai import OpenAIEmbedding
import os
load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"), 
    api_key=os.getenv("QDRANT_API_KEY"),
)
aclient = AsyncQdrantClient(
    url=os.getenv("QDRANT_URL"), 
    api_key=os.getenv("QDRANT_API_KEY"),
) 

def config_db(collection_name):
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    vector_store = QdrantVectorStore(
        collection_name=collection_name,
        client=client,
        aclient=aclient,
        enable_hybrid=True,
        fastembed_sparse_model="Qdrant/bm25",
        batch_size=20,
    )
    return vector_store
