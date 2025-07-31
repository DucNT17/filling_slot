from step_3_chunking import get_nodes_from_document
import re
from llama_index.core import Document
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings
import json
import uuid

PAGE_MARKER_TEMPLATE = "[[__PAGE_{page}__]]"
PAGE_MARKER_RE = re.compile(r"\[\[__PAGE_(\d+)__\]\]")
HEADING_RE = re.compile(r'^\s*(#{1,6})\s+(.*\S)\s*$') 


def get_node_metadata(pdf_path):
    nodes, file_name, product_name, merged_text  = get_nodes_from_document(pdf_path)
    document_id = uuid.uuid1() 
    metadata_dict = {}
    current_page = 0  # bắt đầu theo yêu cầu của bạn
    summary_document = ""
    documents = []
    for idx, node in enumerate(nodes, start=1):
        pages_found = find_all_pages_in_text(node.text)

        if not pages_found:
            node_page = current_page + 1
            
        elif len(pages_found) == 1:
            # Node chứa đúng 1 marker
            node_page = pages_found[0]
            current_page = pages_found[0]

        else:
            # Node chứa Nhiều marker (bắc cầu nhiều trang)
            node_page = pages_found[0]        # page của node = page đầu tiên
            current_page = pages_found[-1]    # cập nhật current sang page cuối cùng

        # Gắn page chính cho node
        node.metadata["page"] = node_page

        # Làm sạch text
        cleaned_text = strip_page_markers(node.text)
        node.text = cleaned_text

            # --- 3. Trích heading cấp # và ## từ text đã sạch ---
        lvl1_local, lvl2_local = extract_levels_from_text(cleaned_text)

        # Cập nhật ngữ cảnh heading
        if lvl1_local is not None:
            current_level1 = lvl1_local
            current_level2 = None  # reset khi đổi level1
        if lvl2_local is not None:
            current_level2 = lvl2_local

        # --- 4. Gán heading ngữ cảnh vào metadata ---
        node.metadata["level1"] = current_level1
        node.metadata["level2"] = current_level2

        summary_info = get_llm_summary(node.text)
        node.metadata["summary"] = summary_info["summary"]
        node.metadata["table_name"] = summary_info["table_name"]
        node.metadata["figure_name"] = summary_info["figure_name"]
        node.metadata["document_id"] = str(document_id)
        node.metadata["chunk_id"] = f"{node.metadata["file_name"]}_{idx}"
        node.metadata["type"] = "chunk_document"
        summary_document += node.metadata["summary"] + "\n"
        documents.append(
            Document(
                text=cleaned_text,
                metadata=node.metadata
            )
        )
        # Lưu metadata
        metadata_dict[idx] = dict(node.metadata)
    documents.append(
        Document(
            text=get_llm_summary_document(merged_text),
            metadata={
                "file_name": file_name,
                "product_name": product_name,
                "document_id": str(document_id),
                "type": "summary_document"
            }
        )
    )
    metadata_dict[str(document_id)] = dict({
                "file_name": file_name,
                "product_name": product_name,
                "document_id": str(document_id),
                "type": "summary_document",
                "summary": get_llm_summary_document(merged_text)
            })
    return documents

 

def get_llm_summary_document(document_content: str) -> str:
    template = (
        """You are a product classification and summarization assistant.
            Your task is to read the attached document and produce a short and concise summary that includes:
            1. **Product Category**: What kind of product is this? Identify its general type (e.g., power controller, DC power system, battery management unit).
            2. **High-Level Feature Summary**: In 3–4 bullet points, describe the product’s main functions and capabilities in a concise, non-technical way.
            Keep the total summary under 100 words. Focus on clarity and high-level classification
            .\n"
        "Document:\n---\n{document_content}\n---\nSummary:"""
    )
    prompt_template = PromptTemplate(template)
    response = Settings.llm.predict(prompt_template, document_content=document_content)
    return response.strip()

def get_llm_summary(node_content: str) -> dict:
    """
    Gọi LLM để lấy thông tin từ node_content:
    - summary: 1 câu tóm tắt ngắn gọn.
    - table_name: tên bảng (hoặc 'None' nếu không có).
    - figure_name: tên hình (hoặc 'None' nếu không có).
    Trả về dict.
    """
    template = (
        "Analyze the following text and provide a JSON object with the fields:\n"
        "- summary: A one-sentence summary of the text.\n"
        "- table_name: If a table is present, provide its name; if the table is only named like 'Table 1.1' or has no name, infer a meaningful name like 'Table 1-1 Configuration of power system'; otherwise, return 'None'.\n"
        "- figure_name: The name of the figure if present, otherwise 'None'.\n\n"
        "Text:\n---\n{node_content}\n---\n\n"
        "Return ONLY the JSON object, nothing else."
    )
    prompt_template = PromptTemplate(template)
    response = Settings.llm.predict(prompt_template, node_content=node_content).strip()
    # Ví dụ response: {"summary": "This text describes ...", "table_name": "Table 1", "figure_name": "None"}
    response = re.sub(r"^```(json)?|```$", "", response, flags=re.MULTILINE).strip()
    result = json.loads(response)
    print(result)
    # Đảm bảo luôn có 3 key
    for key in ["summary", "table_name", "figure_name"]:
        result.setdefault(key, "None")
    return result 
    
def find_all_pages_in_text(text: str):
    """Trả về list số trang xuất hiện trong text theo thứ tự. Loại bỏ trùng lặp liên tiếp."""
    pages = [int(m.group(1)) for m in PAGE_MARKER_RE.finditer(text)]
    dedup = []
    for p in pages:
        if not dedup or dedup[-1] != p:
            dedup.append(p)
    return dedup
def strip_page_markers(text: str) -> str:
    """Xoá marker trang khỏi text để không ảnh hưởng embedding."""
    cleaned = PAGE_MARKER_RE.sub("", text)
    return cleaned.strip("\n\r ")

def extract_levels_from_text(text: str):
    """
    Duyệt tất cả dòng trong node (đã sạch marker) để tìm heading.
    Trả về (level1, level2) — nếu không thấy thì None.
    Khi gặp # mới -> reset level2 (vì bối cảnh đổi).
    Lấy heading cuối cùng của từng cấp xuất hiện trong node.
    """
    level1 = None
    level2 = None
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        hashes, title = m.groups()
        depth = len(hashes)
        title = title.strip()
        if depth == 1:
            level1 = title
            level2 = None  # reset khi vào level1 mới
        elif depth == 2:
            level2 = title
        # depth >= 3: bỏ qua (có thể lưu sau)
    return level1, level2