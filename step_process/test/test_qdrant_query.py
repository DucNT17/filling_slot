from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_parse import LlamaParse
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SemanticSplitterNodeParser
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_API_KEY")
os.environ["QDRANT_API_KEY"] = os.getenv("QDRANT_API_KEY")
client = QdrantClient(
    url="https://a8bcf78f-0147-411f-aa58-079f863fcd6d.us-west-1-0.aws.cloud.qdrant.io:6333", 
    api_key=os.getenv("QDRANT_API_KEY"),
)

aclient = AsyncQdrantClient(
    url="https://a8bcf78f-0147-411f-aa58-079f863fcd6d.us-west-1-0.aws.cloud.qdrant.io:6333", 
    api_key=os.getenv("QDRANT_API_KEY"),
)

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
embedding = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini")

vector_store = QdrantVectorStore(
    "thong_tin_san_pham",
    client=client,
    aclient=aclient,
    enable_hybrid=True,
    fastembed_sparse_model="Qdrant/bm25",
    batch_size=20,
)


index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

query_engine = index.as_query_engine(
    similarity_top_k=2, sparse_top_k=5, vector_store_query_mode="hybrid"
)

response = query_engine.query(
    "Bộ chuyển đổi nguồn 220VAC/ 48VDC (kèm theo 02 dàn acquy 200Ah) có Yêu cầu chung  là Tuân thủ tiêu chuẩn IEC 60950-1."
)
print(response)