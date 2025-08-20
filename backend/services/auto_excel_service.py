import os
import tempfile
from werkzeug.utils import secure_filename
from flask import send_file, jsonify
import asyncio
from ai_server.retrieve.step7_write_on_excel import create_json_to_excel
from datetime import datetime

class AutoExcelService:
    def __init__(self, db_session=None):
        self.db = db_session
    
    def generate_excel_auto(self, pdf_file, collection_name="hello_my_friend"):
        """
        Tự động tạo file Excel từ PDF sử dụng step7
        
        Args:
            pdf_file: File PDF được upload
            collection_name: Tên collection trong database
            
        Returns:
            Flask response với file Excel hoặc error message
        """
        try:
            # Tạo thư mục tạm để lưu file PDF
            with tempfile.TemporaryDirectory() as temp_dir:
                # Lưu file PDF tạm thời
                filename = secure_filename(pdf_file.filename)
                pdf_path = os.path.join(temp_dir, filename)
                pdf_file.save(pdf_path)
                
                # Gọi hàm async create_json_to_excel
                wb = asyncio.run(create_json_to_excel(pdf_path, collection_name))
                
                # Lưu file Excel vào thư mục output
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                excel_filename = f"bang_tuyen_bo_dap_ung_auto_{timestamp}.xlsx"
                excel_path = os.path.join("D:/study/LammaIndex/output", excel_filename)
                
                # Tạo thư mục output nếu chưa tồn tại
                os.makedirs(os.path.dirname(excel_path), exist_ok=True)
                
                # Lưu workbook
                wb.save(excel_path)
                
                # Trả về file Excel
                return send_file(
                    excel_path,
                    as_attachment=True,
                    download_name=excel_filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
        except Exception as e:
            print(f"Error in generate_excel_auto: {str(e)}")
            return jsonify({"error": f"Failed to generate Excel automatically: {str(e)}"}), 500
    
    def get_processing_status(self):
        """
        Lấy trạng thái xử lý (có thể mở rộng cho tracking progress)
        """
        return {"status": "ready", "message": "Service ready for auto processing"}
