from llama_parse import LlamaParse
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.llms.openai import OpenAI
import chromadb
from chromadb.config import Settings
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

# Đặt OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_API_KEY")
embedding = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)

# Định dạng marker
PAGE_MARKER_TEMPLATE = "[[__PAGE_{page}__]]"
PAGE_MARKER_RE = re.compile(r"\[\[__PAGE_(\d+)__\]\]")

# 1. Parse PDF sang Markdown
parser = LlamaParse(
    result_type="markdown",
    auto_mode=True,
    auto_mode_trigger_on_image_in_page=True,
    auto_mode_trigger_on_table_in_page=True,
    skip_diagonal_text=True,
    preserve_layout_alignment_across_pages=True,
    num_workers=4,
    max_timeout=180,
    )  # hoặc "md"
pdf_path = r"D:\\study\\LammaIndex\\documents\\NetSure_732_Brochure.pdf"
file_name = os.path.splitext(os.path.basename(pdf_path))[0]
print("Đang parse PDF sang Markdown...")
parsed_docs = parser.load_data(pdf_path)  # Mỗi trang PDF -> 1 Document dạng markdown

# 2. Gộp tất cả thành 1 Document lớn, giữ đánh dấu page
parts = []
for i, d in enumerate(parsed_docs, start=1):
    parts.append(f"\n{PAGE_MARKER_TEMPLATE.format(page=i)}\n")
    parts.append(d.text)

merged_text = "".join(parts)

big_document = Document(
    text=merged_text,
    metadata={
        "file_name": file_name,
        "product_name": "NetSure 732"
    }
)
print(f"Tổng số trang parse được: {len(parsed_docs)}")


md_parser = MarkdownNodeParser(include_metadata=True, include_prev_next_rel=True)
nodes = md_parser.get_nodes_from_documents([big_document])

def extract_page_from_node_text(text: str, max_lines_to_check: int = 5):
    """
    Kiểm tra tối đa `max_lines_to_check` dòng đầu của node để tìm marker trang.
    Trả về int page nếu tìm được, ngược lại trả về None.
    """
    lines = text.splitlines()
    for line in lines[:max_lines_to_check]:
        m = PAGE_MARKER_RE.search(line)
        if m:
            return int(m.group(1))
    return None

def strip_page_markers(text: str) -> str:
    """Xoá mọi marker trang trong text."""
    return PAGE_MARKER_RE.sub("", text).lstrip("\n\r")

# =========================
# 5. Gắn page metadata & làm sạch node text
# =========================
metadata_dict = {}
current_page = 1  # fallback mặc định

metadata_dict = {}
# 4. Gắn metadata 'page' cho từng chunk dựa vào page_map

for idx, node in enumerate(nodes, start=1):
    detected_page = extract_page_from_node_text(node.text)

    if detected_page is not None:
        current_page = detected_page  # cập nhật vì node này mở đầu page mới

    # gán vào metadata node
    node.metadata["page"] = current_page

    # xóa marker khỏi text node để không dính vào embeddings
    cleaned_text = strip_page_markers(node.text)
    node.text = cleaned_text

    # lưu metadata vào dict xuất JSON
    metadata_dict[idx] = dict(node.metadata)
# ghi ra file JSON
with open("D:\\study\\LammaIndex\\output\\chunk\\metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata_dict, f, ensure_ascii=False, indent=4)

output_file = "D:\\study\\LammaIndex\\output\\chunk\\chunks_NetSure_732_Brochure1.md"
with open(output_file, "w", encoding="utf-8") as f:
    for idx, node in enumerate(nodes, start=1):
        cleaned_text = strip_page_markers(node.text)
        f.write(f"# Chunk {idx}\n")
        f.write(cleaned_text + "\n\n\n\n")

print(f"Đã ghi {len(nodes)} chunk vào {output_file}")