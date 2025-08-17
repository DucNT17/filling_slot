from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_parse import LlamaParse
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SemanticSplitterNodeParser
from qdrant_client.http.models import PayloadSchemaType, Filter, FieldCondition, MatchText

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
        field_name="product_line",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print("✅ Index created for 'product_line'")
except Exception as e:
    print("⚠️ Could not create index for 'product_line':", e)

# Tạo index cho 'type'
try:
    client.create_payload_index(
        collection_name=collection_name,
        field_name="product_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print("✅ Index created for 'product_id'")
except Exception as e:
    print("⚠️ Could not create index for 'product_id':", e)

# Tạo index cho 'type'
try:
    client.create_payload_index(
        collection_name=collection_name,
        field_name="type",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print("✅ Index created for 'type'")
except Exception as e:
    print("⚠️ Could not create index for 'type':", e)
try:
    client.create_payload_index(
        collection_name=collection_name,
        field_name="file_brochure_name",
        field_schema=PayloadSchemaType.TEXT,
    )
    print("✅ Index created for 'file_brochure_name'")
except Exception as e:
    print("⚠️ Could not create index for 'file_brochure_name':", e)


# # Check indexes
# collection_info = client.get_collection(collection_name=collection_name)
# payload_schema = collection_info.payload_schema
# print("Current indexes in collection:", payload_schema)

# # In danh sách các index payload
# if payload_schema:
#     print("Các index payload đã tạo:")
#     for field_name, schema in payload_schema.items():
#         print(f"Trường: {field_name}, Kiểu: {schema}")
# else:
#     print("Không có index payload nào được tạo trong collection này.")


# #Search index TEXT:
# # Tạo bộ lọc cho trường TEXT
# text_filter = Filter(
#     must=[
#         FieldCondition(
#             key='level1',
#             match=MatchText(text='Figure accessory')
#         )
#     ]
# )
# # Thực hiện scroll để lấy các bản ghi khớp với bộ lọc
# scroll_result, next_page = client.scroll(
#     collection_name=collection_name,
#     scroll_filter=text_filter,
#     limit=10  # Số lượng kết quả tối đa
# )

# # In kết quả
# if scroll_result:
#     print("Kết quả tìm kiếm:")
#     for result in scroll_result:
#         print(f"ID: {result.id}, Payload: {result.payload}")
# else:
#     print("Không tìm thấy bản ghi nào khớp với bộ lọc.")
