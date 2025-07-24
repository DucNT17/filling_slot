import chromadb
from chromadb.config import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
import os

# Đặt OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# 1. Kết nối với ChromaDB (đã persist)
client = chromadb.PersistentClient(path="D:\\study\\LammaIndex\\chroma_store")

# 2. Lấy collection
collection = client.get_collection("netsure_docs")

# 3. Tạo embedding cho câu hỏi
embedding_model = OpenAIEmbedding(model="text-embedding-3-small")
query = "Tuân thủ tiêu chuẩn IEC 60950-1"
query_vec = embedding_model.get_text_embedding(query)

# 4. Query top 3 kết quả gần nhất
results = collection.query(
    query_embeddings=[query_vec],
    n_results=3  # lấy top 3 kết quả
)

# 5. In kết quả
for i in range(len(results["ids"][0])):
    print(f"--- Kết quả {i+1} ---")
    print("ID:", results["ids"][0][i])
    print("Metadata:", results["metadatas"][0][i])
    print("Snippet:", results["documents"][0][i][:200], "...\n")
