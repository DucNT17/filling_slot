import os
import asyncio
from werkzeug.utils import secure_filename
from ai_server.retrieve2.step7_write_on_excel import create_json_to_excel
from sqlalchemy.orm import Session
from backend.models.models import Product

# Folder để lưu file tạm
TEMP_FOLDER = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")), "temp_uploads")

class ProcessToExcelService:
    def __init__(self, db: Session):
        self.db = db

    async def process_pdf_to_excel(self, pdf_file, product_ids=None, collection_name="hello_my_friend"):
        """
        Process PDF file and generate Excel output
        Args:
            pdf_file: Uploaded PDF file
            product_ids: List of product IDs (optional, if None will get all products)
            collection_name: Collection name for vector store
        Returns:
            dict: Result information including file path
        """
        try:
            # Create temp folder if not exists
            os.makedirs(TEMP_FOLDER, exist_ok=True)
            
            # Save PDF file temporarily
            filename = secure_filename(pdf_file.filename)
            if not filename.lower().endswith(".pdf"):
                raise ValueError("File must be a PDF")
            
            pdf_path = os.path.join(TEMP_FOLDER, filename)
            pdf_file.save(pdf_path)
            
            # If no product_ids provided, get all products from database
            if not product_ids:
                products = self.db.query(Product).all()
                product_ids = [product.id for product in products]
            
            # Call the async function to create Excel
            await create_json_to_excel(pdf_path, product_ids, collection_name)
            
            # Clean up temp file
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            
            return {
                "status": "success",
                "message": "Excel file generated successfully",
                "excel_path": "D:/study/LammaIndex/output/bang_tuyen_bo_dap_ung10.xlsx",
                "processed_file": filename,
                "product_count": len(product_ids)
            }
            
        except Exception as e:
            # Clean up temp file in case of error
            if 'pdf_path' in locals() and os.path.exists(pdf_path):
                os.remove(pdf_path)
            raise e

    def get_all_products(self):
        """Get all products from database"""
        products = self.db.query(Product).all()
        return [{"id": p.id, "name": p.name} for p in products]