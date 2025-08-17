import camelot
import os
import json

def extract_table_json_camelot(pdf_path):
    get_raw_json = get_biggest_table(pdf_path)
    data = get_raw_json["data"]
    return data

def table_to_json(table_data, table_info):
    """Convert table data to JSON format"""
    if not table_data:
        return {}
    
    # Create JSON structure
    json_data = {
        "metadata": {
            "source_file": table_info["source_file"],
            "page": table_info["page"],
            "table_order": table_info["order"],
            "total_rows": len(table_data),
            "total_columns": len(table_data[0]) if table_data else 0
        },
        "headers": [],
        "data": []
    }
    
    # Add headers (first row)
    if len(table_data) > 0:
        headers = [str(cell).strip() for cell in table_data[0]]
        
        # Replace first 3 headers with fixed names
        if len(headers) >= 1:
            headers[0] = "STT"
        if len(headers) >= 2:
            headers[1] = "hang_hoa"
        if len(headers) >= 3:
            headers[2] = "yeu_cau_ky_thuat"
            
        json_data["headers"] = headers
        
        # Add data rows (skip header)
        for i, row in enumerate(table_data[1:], 1):
            row_dict = {}
            for j, cell in enumerate(row):
                # Use header as key, fallback to column index if header is empty
                key = json_data["headers"][j] if j < len(json_data["headers"]) and json_data["headers"][j] else f"column_{j}"
                row_dict[key] = str(cell).strip()
            
            json_data["data"].append({
                "row_index": i,
                "values": row_dict
            })
    
    return json_data

def get_continued_tables(tables, threshold= 50):

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
                group_counter += 1;

        # if this is not a continuation of the previous table
        else:

            # increment the group number
            group_counter += 1;

        # the current table becomes the previous table for the next iteration
        previous_table = table

    # transform the dictionary into an array of arrays
    continued_tables = [value for value in continued_tables.values()]

    # return the combined tables
    return continued_tables

def get_biggest_table(pdf_path, threshold= 50):
    tables = camelot.read_pdf(pdf_path, flavor = 'lattice', pages = 'all')
    continued_tables = get_continued_tables(tables, threshold)

    # get the name of the PDF file we are processing (without the extension)
    pdf_file_name = os.path.splitext(os.path.basename(pdf_path))[0]

    processed = []
    all_table_jsons = []

    # iterate over found tables
    for i, table in enumerate(tables):

        # if table was already processed as part of a group
        if table in processed: continue

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
                if continued_table == table or continued_table in processed: continue

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
        
        # return the JSON of the largest table
        print(json.dumps(largest_table, ensure_ascii=False, indent=2))
        return largest_table
    else:
        print("No tables found in the PDF.")
        return None