import argparse
import warnings
import camelot
import json
import os

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
        json_data["headers"] = [str(cell).strip() for cell in table_data[0]]
        
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

def main():

    class NewlineFormatter(argparse.RawDescriptionHelpFormatter):
        def _split_lines(self, text, width):
            return text.splitlines()

    # create argument parser
    parser = argparse.ArgumentParser(description = 'Returns an array of tables that should be grouped, also as an array.\nThe tables that should be grouped represent tables that span over multiple pages.', formatter_class = NewlineFormatter)
    parser.add_argument('--path', '-p', type = str, metavar = '', required = True, help = 'path to the PDF file containing tables')
    parser.add_argument('--threshold', '-t', type = int, metavar = '', default = 15, help = 'if the table on previous page ends in the last x%% of the page and\nthe table on the next page starts in the first x%% of the page,\ntables will be considered as spanning over those pages.\nDefault is 15')

    # parse command-line arguments
    args = parser.parse_args()

    # suppress warning about no tables found
    warnings.filterwarnings('ignore', message = 'No tables found on page-*')

    # extract tables
    tables = camelot.read_pdf(args.path, flavor = 'lattice', pages = 'all')

    # get continued tables
    continued_tables = get_continued_tables(tables, args.threshold);

    # get the name of the PDF file we are processing (without the extension)
    pdf_file_name = os.path.splitext(os.path.basename(args.path))[0]

    # the path where we're writing the file to
    # (same place where we processed the file from)
    file_path = os.path.dirname(args.path)

    written = []

    # iterate over found tables
    for i, table in enumerate(tables):

        # if table was already written as part of a group
        if table in written: continue

        # check if the current table is a continued table
        is_continued = any(table in sublist for sublist in continued_tables)

        # define the filename for the JSON file
        file_name = f"{pdf_file_name}-page-{table.parsing_report['page']}-table-{table.parsing_report['order']}.json"

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

        # convert to JSON and write to file
        table_info = {
            "source_file": pdf_file_name,
            "page": table.parsing_report['page'],
            "order": table.parsing_report['order']
        }
        
        json_data = table_to_json(all_table_data, table_info)
        
        with open(os.path.join(file_path, file_name), 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()