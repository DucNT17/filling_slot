import json
from ai_server.upload_data.step_5_upload_data2db import upload_data2db_from_folder
import os
# Mở và đọc file JSON
# with open('D:\\study\\LammaIndex\\downloads1\\dc-power-systems.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)

description = "Liebert PEX efficiently reduces operating costs with enhanced capacity fit into compact footprint. Combining the best accessories such as inverter compressor, EC fan, EEV & microchannel coil, Liebert PEX4 with superior technology allows modern data centers to enjoy abundant load variations with premium efficiency."
features_benefits = """Key Features Premium efficiency with intelligent controller, optimized algorithms, and touchscreen interface for synchronized multi-unit operation.
zInverter compressor with variable speed BPM motor (1000–7200 RPM), wide operating range, EMF filter, eco-friendly R410A refrigerant, and EEV, achieving part-load COP > 5.5.
High-efficiency EC fan with backward-curved blades, variable speed control, and in-floor downflow option for up to 30% energy savings.
Compact microchannel coil with 40% smaller size, 40% higher heat transfer, 50% less refrigerant usage, and low air-side pressure drop.
Electronic expansion valve for precise variable capacity control, stable superheat, and enhanced dehumidification.

Benefits
Lower operating costs through high energy efficiency and optimized part-load performance.
High reliability under all conditions with intelligent control.
Significant energy savings from EC fan and inverter technology.
Environmentally friendly with reduced refrigerant volume and R410A use.
Space-saving compact, lightweight design.
Flexible cooling performance with precise temperature and humidity control.."""
folder_path = "/Users/nguyensiry/Downloads/Đieu_hoa/Tài liệu kỹ thuật VTC"
markdown_path = f"output/Vertiv Liebert PEX4 Brochure.md"
file_brochure_name = "Vertiv Liebert PEX4 Brochure"

upload_data2db_from_folder(folder_path, collection_name="hello_my_friend", category="Thermal Management", product_line="Room Cooling", product_name="P1060", description=description, features_benefits=features_benefits, brochure_file_path=markdown_path, file_brochure_name=file_brochure_name)  
