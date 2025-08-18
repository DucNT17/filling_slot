import os
import tempfile
import asyncio
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import send_file, jsonify
from sqlalchemy.orm import Session
from backend.models.models import Product, FileVectorStore
from sqlalchemy.orm import Session
from backend.models.models import Category, ProductLine, Product, FileVectorStore
# Import hàm async & tạo excel file
from ai_server.retrieve2.step7_write_on_excel import create_excel_file
from ai_server.retrieve2.step6_adapt_or_not import adapt_or_not # giả sử nằm đây

class ExcelService:
    def __init__(self, db: Session):
        self.db = db

    def generate_excel_from_pdf_by_filename_ids(self, pdf_file, filename_ids_str, collection_name="hello_my_friend"):
        # Validate file
        if pdf_file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        if not pdf_file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "File must be a PDF"}), 400

        # Parse filename IDs
        if filename_ids_str.strip():
            filename_ids = [fid.strip() for fid in filename_ids_str.split(",") if fid.strip()]
        else:
            # Nếu không có filename_ids, lấy tất cả files
            files = self.db.query(FileVectorStore).all()
            filename_ids = [file.id for file in files]

        if not filename_ids:
            return jsonify({"error": "No files found"}), 400

        # Validate filename_ids exist in database
        existing_files = self.db.query(FileVectorStore).filter(FileVectorStore.id.in_(filename_ids)).all()
        if not existing_files:
            return jsonify({"error": "No valid filename IDs found"}), 400

        # Save PDF to temp dir
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(temp_dir, filename)
        pdf_file.save(pdf_path)

        # Run async to process với filename_ids
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            context_queries, filename_keys = loop.run_until_complete(
                adapt_or_not(pdf_path, filename_ids, collection_name)
            )
            wb = create_excel_file(context_queries, filename_keys)

            # Save Excel file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"bang_tuyen_bo_dap_ung_{timestamp}.xlsx"
            excel_path = os.path.join(temp_dir, excel_filename)
            wb.save(excel_path)

            # Return file
            return send_file(
                excel_path,
                as_attachment=True,
                download_name=excel_filename,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        finally:
            loop.close()

    # Keep old method for backward compatibility
    def generate_excel_from_pdf(self, pdf_file, product_ids_str, collection_name="hello_my_friend"):
        # Validate file
        if pdf_file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        if not pdf_file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "File must be a PDF"}), 400

        # Parse product IDs
        if product_ids_str.strip():
            product_ids = [pid.strip() for pid in product_ids_str.split(",") if pid.strip()]
        else:
            products = self.db.query(Product).all()
            product_ids = [str(product.id) for product in products]

        if not product_ids:
            return jsonify({"error": "No products found"}), 400

        # Save PDF to temp dir
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(temp_dir, filename)
        pdf_file.save(pdf_path)

        # Run async to process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            context_queries, product_keys = loop.run_until_complete(
                adapt_or_not(pdf_path, product_ids, collection_name)
            )
            wb = create_excel_file(context_queries, product_keys)

            # Save Excel file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"bang_tuyen_bo_dap_ung_{timestamp}.xlsx"
            excel_path = os.path.join(temp_dir, excel_filename)
            wb.save(excel_path)

            # Return file
            return send_file(
                excel_path,
                as_attachment=True,
                download_name=excel_filename,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        finally:
            loop.close()