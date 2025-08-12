import json
from ai_server.upload_data.step_5_upload_data2db import upload_data2db_from_folder
import os
# Mở và đọc file JSON
with open('D:\\study\\LammaIndex\\downloads1\\dc-power-systems.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    product_name = item.get('product_name', 'Unknown Product')
    product_type = item.get('product_type', 'Unknown Type')
    description = item.get('description', 'No description available.')
    features_benefits = item.get('features_benefits', 'No features or benefits listed.')
    folder_path = item.get('folder_path', 'No folder path specified.')
    downloaded_files = item.get('downloaded_files', [])
    markdown_path = ""
    for file_info in downloaded_files:
        if file_info.get('type') == 'Product Brochure':
            file_brochure_name = file_info.get('filename', '')
            brochure_file_path = file_info.get('path', '')
            
            # Convert to output/{filename}.md format
            if file_brochure_name:
                # Remove file extension and add .md
                filename_without_ext = os.path.splitext(file_brochure_name)[0]
                markdown_path = f"output/{filename_without_ext}.md" 

    upload_data2db_from_folder(folder_path, collection_name="hello_my_friend_test", category="Critical Power", product_line=product_type, product_name=product_name, description=description, features_benefits=features_benefits, brochure_file_path=markdown_path, file_brochure_name=file_brochure_name)  
