from llama_parse import LlamaParse
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.llms.openai import OpenAI
import chromadb
from chromadb.config import Settings
import os

# Đặt OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
embedding = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)

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
                "product_name": "NetSure 732"
            }
        )
    )

print(f"Tổng số trang parse được: {len(documents)}")

# 3. Chunk với SemanticSplitter


parser = MarkdownNodeParser(include_metadata=True, include_prev_next_rel=True)
nodes = parser.get_nodes_from_documents(documents)

# nodes = splitter.get_nodes_from_documents(documents)
# client = chromadb.PersistentClient(path="D:\\study\\LammaIndex\\chroma_store")

# collection = client.get_or_create_collection(
#     name="netsure_docs",
#     # metadata tùy ý
# )

# # Batch tốt hơn là từng cái
# ids = []
# embeddings = []
# metadatas = []
# documents = []

# for node in nodes:
#     id = node.id_
#     page = node.metadata.get("page")
#     file_name = node.metadata.get("file_name")
#     product_name = node.metadata.get("product_name")
#     product_name_vietnamese = node.metadata.get("product_name_vietnamese")
#     text = node.text
#     text_embedding = f"---------{product_name}--------{product_name_vietnamese}--------\n\n{text}"
#     vec = embedding.get_text_embedding(text_embedding)
#     ids.append(f"{page}_{product_name}_{id}")
#     embeddings.append(vec)
#     metadatas.append({
#         "page": page,
#         "file_name": file_name
#     })
#     documents.append(text)
# collection.add(
#     ids=ids,
#     embeddings=embeddings,
#     metadatas=metadatas,
#     documents=documents
# )
# print("Đã add vào Chroma xong:", len(ids))