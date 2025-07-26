from docx import Document

def table_to_markdown(doc_path, output_md, escape_pipes=True):
    doc = Document(doc_path)
    md_lines = []
    
    def clean_cell_text(text):
        """Làm sạch text trong cell để phù hợp với markdown"""
        cleaned = (text.strip()
                   .replace("\n", " ")
                   .replace("\r", " ")
                   .replace("  ", " ")   # Thay thế nhiều space bằng 1 space
                   )
        if escape_pipes:
            cleaned = cleaned.replace("|", "\\|")  # Escape dấu | để không làm hỏng bảng markdown
        return cleaned
    
    for table in doc.tables:
        # Lấy tiêu đề và xử lý xuống dòng
        headers = [clean_cell_text(cell.text) for cell in table.rows[0].cells]
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Lấy dữ liệu (bỏ qua header)
        for row in table.rows[1:]:
            cells = [clean_cell_text(cell.text) for cell in row.cells]
            md_lines.append("| " + " | ".join(cells) + " |")
        
        md_lines.append("")  # Thêm dòng trống giữa các bảng
    
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Đã xuất Markdown: {output_md}")

def batch_convert_docx_to_markdown(input_folder, output_folder):
    """Chuyển đổi tất cả file .docx trong folder thành markdown"""
    import os
    import glob
    
    # Tạo thư mục output nếu chưa có
    os.makedirs(output_folder, exist_ok=True)
    
    # Tìm tất cả file .docx
    docx_files = glob.glob(os.path.join(input_folder, "*.docx"))
    
    for docx_file in docx_files:
        # Tạo tên file output
        base_name = os.path.splitext(os.path.basename(docx_file))[0]
        output_file = os.path.join(output_folder, f"{base_name}.md")
        
        # Chuyển đổi
        table_to_markdown(docx_file, output_file)
        print(f"Đã chuyển đổi: {docx_file} -> {output_file}")

# Ví dụ chạy
table_to_markdown(
    "D:\\study\\LammaIndex\\output\\output_no_repeat.docx",
    "D:\\study\\LammaIndex\\data\\bang_tuyen_bo.md"
)