from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_parse import LlamaParse
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SemanticSplitterNodeParser
from qdrant_client.http.models import PayloadSchemaType
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_API_KEY")
os.environ["QDRANT_API_KEY"] = os.getenv("QDRANT_API_KEY")

# Qdrant connection
client = QdrantClient(
    url="https://a8bcf78f-0147-411f-aa58-079f863fcd6d.us-west-1-0.aws.cloud.qdrant.io:6333", 
    api_key=os.getenv("QDRANT_API_KEY"),
)

aclient = AsyncQdrantClient(
    url="https://a8bcf78f-0147-411f-aa58-079f863fcd6d.us-west-1-0.aws.cloud.qdrant.io:6333", 
    api_key=os.getenv("QDRANT_API_KEY"),
)

# ✅ Thay tên collection thật của bạn tại đây
collection_name = "hello_my_friend"

# Tạo index cho 'document_id'
try:
    client.create_payload_index(
        collection_name=collection_name,
        field_name="file_name",
        field_schema=PayloadSchemaType.KEYWORD
    )
    print("✅ Index created for 'product_name'")
except Exception as e:
    print("⚠️ Could not create index for 'product_name':", e)

# Tạo index cho 'type'
try:
    client.create_payload_index(
        collection_name=collection_name,
        field_name="type",
        field_schema=PayloadSchemaType.KEYWORD
    )
    print("✅ Index created for 'type'")
except Exception as e:
    print("⚠️ Could not create index for 'type':", e)
