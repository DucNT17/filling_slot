import camelot
import json
import os
from docx import Document
from docx.shared import Inches
from docx.enum.table import WD_TABLE_ALIGNMENT

def table_to_json(table_data, table_info):
    """Convert table data to JSON format"""
    if not table_data:
        return {}
    
    headers = table_data[0] if table_data else []
    rows = table_data[1:] if len(table_data) > 1 else []
    
    json_data = {
        "metadata": {
            "source_file": table_info["source_file"],
            "page": table_info["page"],
            "order": table_info["order"],
            "total_rows": len(rows),
            "total_columns": len(headers)
        },
        "headers": headers,
        "data": rows
    }
    
    return json_data

def get_continued_tables(tables, threshold=50):
    continued_tables = {}
    previous_table = False
    group_counter = 0

    # typical height of a pdf is 842 points and bottom margins are anywhere between 56 and 85 points
    # therefore, accounting for margins, 792
    page_height = 792

    # iterate over the tables
    for i, table in enumerate(tables):

        # if a previous table exists (remember, we start with this as false)
        # and the previous table was on the previous page
        # and the number of columns of both tables is the same
        if previous_table and table.page == previous_table.page + 1 and len(table.cols) == len(previous_table.cols):

            # get the bottom coordinate of the previous table
            # note that for pdfs the origin (0, 0) typically starts from the bottom-left corner of the page,
            # with the y-coordinate increasing as you move upwards
            # this is why for {x0, y0, x1, y1} we need the y0 as the bottom
            previous_table_bottom = previous_table._bbox[1]

            # get the top coordinate of the current table
            # for {x0, y0, x1, y1} we need the y1 as the top
            current_table_top = table._bbox[3]

            # if the previous table ends in the last 15% of the page and the current table starts in the first 15% of the page
            if previous_table_bottom < (threshold / 100) * page_height and current_table_top > (1 - threshold / 100) * page_height:

                # if we don't have started this group of tables
                if (continued_tables.get(group_counter) is None):

                    # start by adding the first table
                    continued_tables[group_counter] = [previous_table]

                # add any of the sunsequent tables to the group
                continued_tables[group_counter].append(table)

            # if this is not a continuation of the previous table
            else:

                # increment the group number
                group_counter += 1

        # if this is not a continuation of the previous table
        else:

            # increment the group number
            group_counter += 1

        # the current table becomes the previous table for the next iteration
        previous_table = table

    # transform the dictionary into an array of arrays
    continued_tables = [value for value in continued_tables.values()]

    # return the combined tables
    return continued_tables

def save_table_to_word(table_json, output_path):
    """Save table data to Word document (only first 3 columns)"""
    doc = Document()
    
    # Add title
    title = doc.add_heading(f'Bảng từ file: {table_json["metadata"]["source_file"]}', 0)
    
    # Add metadata information
    metadata_para = doc.add_paragraph()
    metadata_para.add_run('Thông tin bảng:\n').bold = True
    metadata_para.add_run(f'• Trang: {table_json["metadata"]["page"]}\n')
    metadata_para.add_run(f'• Thứ tự: {table_json["metadata"]["order"]}\n')
    metadata_para.add_run(f'• Tổng số dòng: {table_json["metadata"]["total_rows"]}\n')
    metadata_para.add_run(f'• Tổng số cột gốc: {table_json["metadata"]["total_columns"]}\n')
    metadata_para.add_run(f'• Số cột được lưu: 3 (3 cột đầu tiên)\n')
    
    # Add space
    doc.add_paragraph()
    
    # Create table if data exists
    if table_json["headers"] and table_json["data"]:
        # Only take first 3 columns
        headers_first_3 = table_json["headers"][:3]
        
        # Calculate number of columns (max 3)
        num_cols = min(3, len(table_json["headers"]))
        num_rows = len(table_json["data"]) + 1  # +1 for header
        
        # Create table
        table = doc.add_table(rows=num_rows, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = 'Table Grid'
        
        # Add headers (only first 3)
        header_cells = table.rows[0].cells
        for i, header in enumerate(headers_first_3):
            if i < len(header_cells):
                header_cells[i].text = str(header)
                # Make header bold
                for paragraph in header_cells[i].paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
        
        # Add data rows (only first 3 columns)
        for row_idx, row_data in enumerate(table_json["data"]):
            if row_idx + 1 < len(table.rows):
                row_cells = table.rows[row_idx + 1].cells
                # Only take first 3 columns of each row
                row_data_first_3 = row_data[:3]
                for col_idx, cell_data in enumerate(row_data_first_3):
                    if col_idx < len(row_cells):
                        row_cells[col_idx].text = str(cell_data)
    
    # Save document
    doc.save(output_path)
    print(f"Đã lưu bảng (3 cột đầu tiên) vào file Word: {output_path}")

def get_biggest_table_and_save_to_word(pdf_path, output_word_path=None, threshold=50):
    """Extract largest table from PDF and save to Word document"""
    
    # Read tables from PDF
    tables = camelot.read_pdf(pdf_path, flavor='lattice', pages='all')
    continued_tables = get_continued_tables(tables, threshold)

    # get the name of the PDF file we are processing (without the extension)
    pdf_file_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Create output path if not provided
    if output_word_path is None:
        output_word_path = f"{pdf_file_name}_largest_table.docx"

    processed = []
    all_table_jsons = []

    # iterate over found tables
    for i, table in enumerate(tables):

        # if table was already processed as part of a group
        if table in processed: 
            continue

        # check if the current table is a continued table
        is_continued = any(table in sublist for sublist in continued_tables)

        # collect all table data (current table + continued tables if any)
        all_table_data = list(table.data)

        # if the current table is a continued table, append all subsequent continued tables data
        if is_continued:

            # get the index of the group in "continued_tables" associated with the current table
            group_index = next(index for index, sublist in enumerate(continued_tables) if table in sublist)

            # iterate over the tables in said group and append their data
            for continued_table in continued_tables[group_index]:

                # skip the current table as it's already added
                if continued_table == table or continued_table in processed: 
                    continue

                # append the data of the continued table (skip header for subsequent tables)
                all_table_data.extend(continued_table.data[1:] if len(continued_table.data) > 1 else [])

                # keep track of processed tables
                processed.append(continued_table)

        # convert to JSON
        table_info = {
            "source_file": pdf_file_name,
            "page": table.parsing_report['page'],
            "order": table.parsing_report['order']
        }
        
        json_data = table_to_json(all_table_data, table_info)
        all_table_jsons.append(json_data)
        
        # mark current table as processed
        processed.append(table)

    # find the table with the most rows
    if all_table_jsons:
        largest_table = max(all_table_jsons, key=lambda x: x.get('metadata', {}).get('total_rows', 0))
        
        # Save to Word document
        save_table_to_word(largest_table, output_word_path)
        
        # Also print JSON for reference
        print("Thông tin bảng lớn nhất:")
        print(json.dumps(largest_table, ensure_ascii=False, indent=2))
        
        return largest_table
    else:
        print("Không tìm thấy bảng nào trong file PDF.")
        return None

# Example usage:
if __name__ == "__main__":
    # Sử dụng function
    pdf_file_path = "D:\\study\\LammaIndex\\documents\\22.2024.Codien Chuong V Yeu cau ve ky thuat (1).pdf"  # Thay đổi đường dẫn file PDF của bạn
    output_word_file = "D:\\study\\LammaIndex\\output\\largest_table.docx"  # Tên file Word output (tùy chọn)

    # Gọi function để extract và lưu bảng
    get_biggest_table_and_save_to_word(pdf_file_path, output_word_file)