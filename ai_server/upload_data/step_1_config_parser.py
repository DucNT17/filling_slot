from llama_parse import LlamaParse
import os

def config_parser(pdf_path):
    # 1. Parse PDF sang Markdown
    parser = LlamaParse(
        result_type="markdown",
        auto_mode=True,
        auto_mode_trigger_on_image_in_page=True,
        auto_mode_trigger_on_table_in_page=True,
        skip_diagonal_text=True,
        preserve_layout_alignment_across_pages=True,
        num_workers=4,
        max_timeout=1000,
    )  # hoặc "md"
    
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    print("Đang parse PDF sang Markdown...")
    parsed_docs = parser.load_data(pdf_path)  # Mỗi trang PDF -> 1 Document dạng markdown
    return parsed_docs, file_name
