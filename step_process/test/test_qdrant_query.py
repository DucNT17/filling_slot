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
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
    FilterCondition
)

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_API_KEY")
os.environ["QDRANT_API_KEY"] = os.getenv("QDRANT_API_KEY")

# Cấu hình client Qdrant
client = QdrantClient(
    url="https://a8bcf78f-0147-411f-aa58-079f863fcd6d.us-west-1-0.aws.cloud.qdrant.io:6333",
    api_key=os.getenv("QDRANT_API_KEY"),
)
aclient = AsyncQdrantClient(
    url="https://a8bcf78f-0147-411f-aa58-079f863fcd6d.us-west-1-0.aws.cloud.qdrant.io:6333",
    api_key=os.getenv("QDRANT_API_KEY"),
)

# Cấu hình LLM và Embedding
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini")

# Khởi tạo Vector Store
vector_store = QdrantVectorStore(
    collection_name="thong_tin_san_pham",
    client=client,
    aclient=aclient,
)
filters = MetadataFilters(
    filters=[
        MetadataFilter(key="file_name", operator=FilterOperator.EQ, value="NetSure_732_User_Manual"),
        MetadataFilter(key="type", operator=FilterOperator.EQ, value="chunk_document"),
    ],
    condition=FilterCondition.AND,
)

index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

retriever = index.as_retriever(similarity_top_k=5, verbose=True)

query_str = f"""Sản phẩm Netsure 732 có đấp ứng được tiêu chuẩn IEC60950-1 không? (trả lời bằng tiếng việt)"""

# --- Thay đổi từ đây ---
query_engine = RetrieverQueryEngine.from_args(
    retriever=retriever,
)

# 2. Thực hiện truy vấn qua Query Engine
print("Bắt đầu truy vấn với Query Engine...")
response = query_engine.query(query_str)


# 3. In câu trả lời được tổng hợp bởi LLM và các nguồn tham khảo
print("\n" + "="*50)
print("Câu trả lời từ LLM:")
print(str(response))
print("="*50 + "\n")


print("Nguồn tham khảo (Source Nodes):")
if not response.source_nodes:
    print("Không tìm thấy thông tin nào phù hợp.")
else:
    for node in response.source_nodes:
        print(f"Metadata: {node.metadata}")
        print(f"Score: {node.score:.4f}")
        print(f"Content: {node.text[:300]}...") # In một đoạn nội dung để xem trước
        print("-" * 100)


# response_nodes = retriever.retrieve(query_str)

# print("\nKết quả tìm kiếm:")
# if not response_nodes:
#     print("Không tìm thấy thông tin nào phù hợp.")
# else:
#     for doc in response_nodes:
#         # print(f"Content: {doc.get_content()}")
#         print(f"Metadata: {doc.metadata}")
#         print("-" * 100)


# --- Cấu hình Auto-Retriever ---
# vector_store_info = VectorStoreInfo(
#     content_info="Thông tin chi tiết và thông số kỹ thuật về các sản phẩm điện tử",
#     metadata_info=[
#         {
#             "name": "type",
#             "type": "string",
#             "description": (
#                 "Loại của khối dữ liệu. Có thể là 'summary_document' (tóm tắt toàn bộ tài liệu) "
#                 "hoặc 'chunk_document' (một đoạn chi tiết từ tài liệu). "
#                 "Hãy sử dụng 'chunk_document' khi câu hỏi yêu cầu thông tin, thông số cụ thể."
#             ),
#         },
#         {
#             "name": "file_name",
#             "type": "string",
#             "description": "Tên của file tài liệu gốc, ví dụ: 'NetSure_732_Brochure.pdf'. Dùng để lọc chính xác theo một tài liệu.",
#         },
#         {
#             "name": "product_name",
#             "type": "string",
#             "description": "Tên của sản phẩm được đề cập trong tài liệu, ví dụ: 'NetSure™ 732 A41'.",
#         },
#         {
#             "name": "page",
#             "type": "integer",
#             "description": "Số trang trong tài liệu gốc nơi thông tin được trích xuất.",
#         },
#     ],
# )

# # 2. Khởi tạo Auto-Retriever
# retriever = VectorIndexAutoRetriever(
#     index,
#     vector_store_info=vector_store_info,
#     similarity_top_k=5, 
#     verbose=True, 
# )

# query_str = "Số lượng khe cắm module chỉnh lưu (Rectifier) của Netsure™ 732 A41 là bao nhiêu? "

# print("Bắt đầu truy vấn với Auto-Retriever...")

# response_nodes = retriever.retrieve(query_str)

# print("\nKết quả tìm kiếm:")
# if not response_nodes:
#     print("Không tìm thấy thông tin nào phù hợp.")
# else:
#     for doc in response_nodes:
#         print(f"Content: {doc.get_content()}")
#         print(f"Metadata: {doc.metadata}")
#         print("-----")

