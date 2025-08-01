import json
import os
from llama_index.core import SimpleDirectoryReader
from openai import OpenAI
from dotenv import load_dotenv
import re
import camelot
load_dotenv()

# Đặt API key (nếu chưa đặt)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def extract_json_llm(pdf_path):
    table_to_markdown= extract_table_markdown(pdf_path)
    prompt = prompt_llm(table_to_markdown)
    response = client.responses.create(
        model="gpt-4o-mini",  # Hoặc gpt-4o-mini
        input=prompt,
        temperature=0
    )

    output_text = response.output_text.strip()
    # Loại bỏ các khối ```json hoặc ```
    data = re.sub(r"^```json\s*|\s*```$", "", output_text, flags=re.MULTILINE).strip()
    return data

def prompt_llm(markdown_content):
    prompt = f"""
    Bạn là trợ lý trích xuất cấu trúc. Hãy phân tích Markdown sau và tạo JSON theo QUY TẮC, chỉ sử dụng các bảng liên quan thông số kỹ thuật và các tiêu chuẩn tối thiểu — thường là bảng gồm 3 cột: "STT", "Hàng hóa", "Yêu cầu kỹ thuật".

    MỤC TIÊU JSON:
    [
    {{
        "ten_san_pham": "<string>",
        "cac_muc": [
        {{
            "ten_hang_hoa": "<string>",
            "thong_so_ky_thuat": {{
            "<ID1>": "<string hoặc list [<tên>, <mô tả>]>",
            "<ID2>": "<...>"
            }}
        }},
        ...
        ]
    }},
    ...
    ]

    QUY TẮC:
    1. Mỗi phần lớn bắt đầu bằng tiêu đề tên sản phẩm sẽ tạo ra một phần tử trong danh sách JSON (một sản phẩm).
    2. Trường 'ten_san_pham' lấy từ dòng tiêu đề đầu tiên thể hiện tên hàng hóa chính.
    3. Mỗi bảng kỹ thuật bên dưới tiêu đề là một nhóm 'cac_muc' của sản phẩm đó.
    4. Trong mỗi bảng:
    - 'ten_hang_hoa' lấy từ cột "Hàng hóa" tại các dòng có giá trị ở cột "STT".
    - Với mục 'Yêu cầu chung':
        - Nếu cột “Yêu cầu kỹ thuật” chứa nhiều mục gạch đầu dòng bắt đầu bằng dấu `-`:
        👉 **Mỗi mục bắt đầu bằng `-` là một thông số riêng biệt (atomic), lưu dưới một key riêng.**
        👉 Mỗi mục `- ...` sẽ được lưu dạng `"KEY": "<nội dung không có dấu -" >`.
    - Với mục 'Thông số kỹ thuật':
        - Nếu dòng con có cả "Hàng hóa" và "Yêu cầu kỹ thuật" → lưu dưới dạng `"KEY": ["<Hàng hóa>", "<Yêu cầu kỹ thuật>"]`.
    5. Mã hóa key: viết tắt 3 chữ cái đầu (không dấu, in hoa) của 'ten_hang_hoa' + số thứ tự 3 chữ số (bắt đầu từ 001).
    6. Chuẩn hóa nội dung:
    - Bỏ dấu `-` đầu dòng nếu có.
    - Không gộp nhiều dòng vào 1 key. Mỗi dòng kỹ thuật là một key riêng biệt, theo thứ tự.
    7. Không suy diễn, không thêm dữ liệu ngoài.
    8. Trả về JSON hợp lệ (UTF-8), KHÔNG chú thích hay giải thích gì thêm.

    DỮ LIỆU GỐC:
    ---
    {markdown_content}
    ---

    HÃY TRẢ LỜI CHỈ BẰNG JSON HỢP LỆ.
    """
    return prompt

def table_to_markdown(table_data):
    """Convert table data to markdown format"""
    if not table_data:
        return ""
    
    markdown_lines = []
    
    # Add header row
    if len(table_data) > 0:
        header = "| " + " | ".join(str(cell).strip() for cell in table_data[0]) + " |"
        markdown_lines.append(header)
        
        # Add separator row
        separator = "| " + " | ".join("---" for _ in table_data[0]) + " |"
        markdown_lines.append(separator)
        
        # Add data rows (skip header)
        for row in table_data[1:]:
            row_str = "| " + " | ".join(str(cell).strip() for cell in row) + " |"
            markdown_lines.append(row_str)
    
    return "\n".join(markdown_lines) 

def get_continued_tables(tables, threshold):

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

def extract_table_markdown(pdf_path):

    # extract tables
    tables = camelot.read_pdf(pdf_path, flavor = 'lattice', pages = 'all')

    # get continued tables
    continued_tables = get_continued_tables(tables, 15);

    # get the name of the PDF file we are processing (without the extension)
    pdf_file_name = os.path.splitext(os.path.basename(args.path))[0]

    # the path where we're writing the file to
    # (same place where we processed the file from)
    file_path = os.path.dirname(args.path)

    written = []
    longest_table_info = None
    max_content_length = 0

    # iterate over found tables
    for i, table in enumerate(tables):

        # if table was already written as part of a group
        if table in written: continue

        # check if the current table is a continued table
        is_continued = any(table in sublist for sublist in continued_tables)

        # define the filename for the Markdown file
        file_name = f"{pdf_file_name}-page-{table.parsing_report['page']}-table-{table.parsing_report['order']}.md"

        # collect all table data (current table + continued tables if any)
        all_table_data = list(table.data)

        # if the current table is a continued table, append all subsequent continued tables data
        if is_continued:

            # get the index of the group in "continued_tables" associated with the current table
            group_index = next(index for index, sublist in enumerate(continued_tables) if table in sublist)

            # iterate over the tables in said group and append their data
            for continued_table in continued_tables[group_index]:

                # skip the current table as it's already added
                if continued_table == table or continued_table in written: continue

                # append the data of the continued table
                all_table_data.extend(continued_table.data)

                # keep track of written tables so that are not written again in the main iteration
                written.append(continued_table)

        # convert to markdown
        markdown_content = table_to_markdown(all_table_data)
        
        # calculate content length (number of characters)
        content_length = len(markdown_content)
        
        # check if this table has the longest content so far
        if content_length > max_content_length:
            max_content_length = content_length
            longest_table_info = {
                'file_name': file_name,
                'markdown_content': markdown_content,
                'table': table,
                'page': table.parsing_report['page'],
                'order': table.parsing_report['order'],
                'content_length': content_length
            }

    # write only the longest table to file
    return longest_table_info["markdown_content"]