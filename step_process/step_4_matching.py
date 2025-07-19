import json
import chromadb
from llama_index.embeddings.openai import OpenAIEmbedding
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
# Đặt OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_queries(data):
    ten_san_pham = data.get("ten_san_pham", "").strip()
    queries = []          # Mỗi phần tử: (code, spec_text, full_query)
    for muc in data.get("cac_muc", []):
        thong_so = muc.get("thong_so_ky_thuat", {})
        for code, spec in thong_so.items():
            spec_clean = spec.strip()
            # Ghép theo yêu cầu: ten_san_pham + 1 phần tử trong thong_so_ky_thuat
            full_query = f"{ten_san_pham} - {spec_clean}"
            queries.append((code, spec_clean, full_query))
    return queries

def query_chroma(queries, n_results=2, collection_name="netsure_docs"):
    client = chromadb.PersistentClient(path="D:\\study\\LammaIndex\\chroma_store")
    collection = client.get_collection(collection_name)
    embedding_model = OpenAIEmbedding(model="text-embedding-3-small")
    results_per_code = {}
    for code, spec_text, full_query in queries:
        query_vec = embedding_model.get_text_embedding(spec_text)
        # Query ChromaDB
        res = collection.query(query_embeddings=[query_vec], n_results=n_results)
        results_per_code[code] = {
            "query": spec_text,
            "raw": res
        }
    return results_per_code

if __name__ == "__main__":
    data = load_data("D:\\study\\LammaIndex\\output\\test.json")
    queries = build_queries(data)
    for q in queries:
        print("Code:", q[0])
        print("Query:", q[2])
    results = query_chroma(queries)
    # In kết quả demo
    for code, info in results.items():
        print(f"\n== {code} ==")
        print("Query:", info["query"])
        print("Kết quả:", info["raw"])