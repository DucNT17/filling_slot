from ai_server.upload_data.step_2_process_data_md import process_data_md
from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser

def get_nodes_from_document(pdf_path):
    merged_text, product_name, file_name = process_data_md(pdf_path)
    big_document = Document(
        text=merged_text,
        metadata={
            "file_name": file_name,
            "product_name": product_name,
        },
    )
    md_parser = MarkdownNodeParser(include_metadata=True, include_prev_next_rel=True)
    nodes = md_parser.get_nodes_from_documents([big_document])
    return nodes, file_name, product_name, merged_text