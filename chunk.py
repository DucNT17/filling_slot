import os
import json
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, Settings, PromptTemplate
from llama_index.core.schema import Document
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
print("Đã cấu hình LLM...")

# reader = SimpleDirectoryReader("./test_data", recursive=True, required_exts=[".md", ".markdown"])
reader = SimpleDirectoryReader(input_files=["./data/NetSure_732_Brochure.md"])
documents = reader.load_data(show_progress=True)
parser = MarkdownNodeParser(include_metadata=True, include_prev_next_rel=True)
nodes = parser.get_nodes_from_documents(documents)
print(f"Đã phân tích tài liệu thành {len(nodes)} chunks (nodes).")
node_map = {node.id_: node for node in nodes}

# class TechnicalSpecs(BaseModel):
#     specs: Dict[str, Any] = Field(default_factory=dict, description="Key-value pairs of technical specifications")

def get_llm_summary(node_content: str) -> str:
    template = "Please provide a concise, one-sentence summary of the following text.\nText:\n---\n{node_content}\n---\nSummary:"
    prompt_template = PromptTemplate(template)
    response = Settings.llm.predict(prompt_template, node_content=node_content)
    return response.strip()

# def extract_llm_technical_specs(node_content: str) -> Dict[str, Any]:
#     template = "Extract all technical specifications from the following text. If no technical specifications are found, return an empty dictionary.\nText:\n---\n{node_content}\n---"
#     prompt_template = PromptTemplate(template)
#     try:
#         response = Settings.llm.structured_predict(TechnicalSpecs, prompt_template, node_content=node_content)
#         return response.specs
#     except Exception as e:
#         print(f"Lỗi khi trích xuất thông số kỹ thuật: {e}")
#         return {}

# def detect_tables(node_content: str) -> List[str]:
#     if "| --- |" in node_content or "|---|" in node_content: return ["Detected Markdown Table"]
#     return []

# def detect_figures(node_content: str) -> List[str]:
#     figures = []
#     lines = node_content.split('\n')
#     for line in lines:
#         if line.strip().startswith("!") and line.strip().endswith("!"):
#             figures.append(line.strip().replace("!", "").strip())
#     return figures

print("Bắt đầu làm giàu metadata và tạo Document objects...")

product_name = "Unknown Product"
if nodes:
    first_node_content = nodes[0].get_content()
    first_line = first_node_content.split('\n')[0]
    if first_line.startswith("# "):
        product_name = first_line.strip("# ").strip()
print(f"Đã xác định tên sản phẩm: {product_name}")

final_documents: List[Document] = []

for i, node in enumerate(nodes):
    print(f"Đang xử lý chunk {i+1}/{len(nodes)}...")
    
    node_content = node.get_content()
    
    # xác định section_title
    section_title = "Content Block" # Giá trị mặc định
    first_line_of_node = node_content.strip().split('\n')[0]
    # Sử dụng regex để tìm các heading (từ # đến ######)
    match = re.match(r'^(#{1,6})\s+(.*)', first_line_of_node)
    if match:
        section_title = match.group(2).strip()
            
    # parent_id = node.parent_node.node_id if node.parent_node else None
    
    # sibling_ids = []
    # if parent_id:
    #     parent_node = node_map.get(parent_id)
    #     if parent_node:
    #         sibling_ids = [child.node_id for child in parent_node.children if child.node_id != node.id_]
            
    metadata_dict = {
        "chunk_id": node.id_,
        "document_id": node.ref_doc_id,
        "page_reference": node.metadata.get("page_label", 1),
        "product_name": product_name,
        "section_title": section_title,
        "summary": get_llm_summary(node_content),
        # "technical_specs": extract_llm_technical_specs(node_content),
        # "table_attached": detect_tables(node_content),
        # "figure_attached": detect_figures(node_content),
        # "parent_node_id": parent_id,
        # "sibling_nodes_id": sibling_ids
    }
    
    document_object = Document(text=node_content, metadata=metadata_dict)
    final_documents.append(document_object)

print("Hoàn tất quá trình!")
print(f"\nĐã tạo thành công {len(final_documents)} đối tượng Document.")
print("\nXem trước kết quả của một vài Document:")
if final_documents:
    for doc in final_documents: # In ra 3 document đầu tiên để kiểm tra
        print("--- Document Object ---")
        print(f"Content (doc.text):\n---\n{doc.text}...\n---") # In 100 ký tự đầu
        print(f"Metadata (doc.metadata):\n---\n{json.dumps(doc.metadata, indent=2, ensure_ascii=False)}")
        print("-----------------------\n")