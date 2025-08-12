from ai_server.upload_data.step_1_config_parser import config_parser
import re

PAGE_MARKER_TEMPLATE = "[[__PAGE_{page}__]]"
PAGE_MARKER_RE = re.compile(r"\[\[__PAGE_(\d+)__\]\]")
HEADING_RE = re.compile(r'^\s*(#{1,6})\s+(.*\S)\s*$')

def clean_line(line: str) -> str:
    """
    Lấy phần đầu của dòng trước khi gặp >4 dấu cách liên tiếp.
    Xóa # nếu có ở đầu.
    """
    # Nếu có nhiều hơn 4 dấu cách liên tiếp thì tách
    line = re.split(r'\s{5,}', line, maxsplit=1)[0]
    return line.lstrip('#').strip()

def remove_duplicate_headers(markdown_content):
    lines = markdown_content.splitlines()
    output_lines = []
    seen_headers = set()

    for line in lines:
        if line.startswith('# '):  # Chỉ check header cấp 1
            header_text = line[2:].strip()  # Bỏ '# ' và lấy tên header
            if header_text not in seen_headers:
                seen_headers.add(header_text)
                output_lines.append(line)
        else:
            output_lines.append(line)
    
    return '\n'.join(output_lines)

def merge_markdown_content(parsed_docs):
    parts = []
    product_name = "Unknown Product"
    for i, d in enumerate(parsed_docs, start=1):
        if i == 1:
            content = d.text.split('\n')

            # Tìm dòng đầu tiên hợp lệ
            first_non_empty_line = next(
                (line for line in content if line.strip()),
                None
            )

            if first_non_empty_line:
                product_name = clean_line(first_non_empty_line)

            print("Product name:", product_name)

        parts.append(d.text)
        parts.append(f"\n{PAGE_MARKER_TEMPLATE.format(page=i)}\n")

    merged_text = "".join(parts)
    merged_text = remove_duplicate_headers(merged_text)
    return merged_text, product_name

def process_data_md(pdf_path):
    parsed_docs, file_name = config_parser(pdf_path)
    merged_text, product_name = merge_markdown_content(parsed_docs)
    return merged_text, product_name, file_name
