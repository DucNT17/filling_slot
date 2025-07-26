from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_parse import LlamaParse
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.embeddings.openai import OpenAIEmbedding
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
Settings.chunk_size = 4096
embedding = OpenAIEmbedding(model="text-embedding-3-small")

vector_store = QdrantVectorStore(
    "thong_tin_san_pham",
    client=client,
    aclient=aclient,
    enable_hybrid=True,
    fastembed_sparse_model="Qdrant/bm25",
    batch_size=20,
)

storage_context = StorageContext.from_defaults(vector_store=vector_store)
Settings.chunk_size = 4096

# 1. Parse PDF sang Markdown
parser = LlamaParse(result_type="markdown")  # hoặc "md"
pdf_path = r"D:\\study\\LammaIndex\\documents\\NetSure_732_User_Manual.pdf"
file_name = os.path.splitext(os.path.basename(pdf_path))[0]
print("Đang parse PDF sang Markdown...")
parsed_docs = parser.load_data(pdf_path)  # Mỗi trang PDF -> 1 Document dạng markdown

documents = []
for i, d in enumerate(parsed_docs, start=1):
    documents.append(
        Document(
            text=d.text,
            metadata={
                "page": i,
                "file_name": file_name,
                "product_name": "NetSure 732",
                "product_name_vietnamese": "Bộ chuyển đổi nguồn 220VAC/ 48VDC (kèm theo 02 dàn acquy 200Ah)",
            }
        )
    )
splitter = SemanticSplitterNodeParser(
    buffer_size=0,
    breakpoint_percentile_threshold=95,
    embed_model=embedding,
    include_metadata=True,
)

nodes = splitter.get_nodes_from_documents(documents)

documents = []
for node in nodes:
    id = node.id_
    page = node.metadata.get("page")
    file_name = node.metadata.get("file_name")
    product_name = node.metadata.get("product_name")
    product_name_vietnamese = node.metadata.get("product_name_vietnamese")
    text = node.text
    text_embedding = f"---------{product_name}--------{product_name_vietnamese}--------\n\n{text}"
    documents.append(
        Document(
            text=text_embedding,
            metadata={
                "page": page,
                "file_name": file_name,
                "product_name": product_name,
                "product_name_vietnamese": product_name_vietnamese,
            }
        )
    )

index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
)



# 6. Kiểm tra metadata đã lưu trong Qdrant
result = client.scroll(
    collection_name="thong_tin_san_pham",
    limit=5,
    with_payload=True,
    with_vectors=False
)
print("Dữ liệu trong Qdrant:")
for point in result[0]:
    print(point.payload)

