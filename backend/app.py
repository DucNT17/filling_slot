from flask import Flask, request, jsonify, send_file
from flasgger import Swagger
from backend.db.connect_db import SessionLocal, Base, engine
from backend.services.upload_data import ProductService
from backend.models.models import *
from ai_server.retrieve2.step7_write_on_excel import create_json_to_excel
from ai_server.retrieve2.step6_adapt_or_not import adapt_or_not
import asyncio
import os
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename
# Flask + Swagger
app = Flask(__name__)
swagger = Swagger(app)

# Tạo bảng nếu chưa có
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.route("/upload", methods=["POST"])
def upload_data():
    """
    Upload product and files (lưu vào folder output)
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: collection_name
        in: formData
        type: string
        required: false
        default: hello_my_friend
      - name: category
        in: formData
        type: string
        required: true
      - name: product_line
        in: formData
        type: string
        required: true
      - name: product_name
        in: formData
        type: string
        required: true
      - name: files
        in: formData
        type: file
        required: true
        multiple: true
      - name: description
        in: formData
        type: string
        required: true
      - name: features_benefits
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Data uploaded successfully
    """
    db = next(get_db())
    service = ProductService(db)

    category_name = request.form.get("category")
    product_line_name = request.form.get("product_line")
    product_name = request.form.get("product_name")
    files = request.files.getlist("files")
    description = request.form.get("description")
    features_benefits = request.form.get("features_benefits")
    collection_name = request.form.get("collection_name", "hello_my_friend")
    result = service.upload_product_with_files(
        category_name=category_name,
        product_line_name=product_line_name,
        product_name=product_name,
        files=files,
        description=description,
        features_benefits=features_benefits,
        collection_name=collection_name
    )

    return jsonify(result)

@app.route("/generate-excel", methods=["POST"])
def generate_excel():
    """
    Generate Excel file from PDF and product IDs
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: pdf_file
        in: formData
        type: file
        required: true
        description: PDF file to process
      - name: product_ids
        in: formData
        type: string
        required: false
        description: Comma-separated product IDs (if empty, all products will be used)
      - name: collection_name
        in: formData
        type: string
        required: false
        default: hello_my_friend
        description: Collection name for vector store
    responses:
      200:
        description: Excel file generated and returned
        content:
          application/vnd.openxmlformats-officedocument.spreadsheetml.sheet:
            schema:
              type: string
              format: binary
      400:
        description: Bad request - invalid input
      500:
        description: Internal server error
    """
    try:
        # Validate PDF file
        if 'pdf_file' not in request.files:
            return jsonify({"error": "No PDF file provided"}), 400
        
        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "File must be a PDF"}), 400

        # Get parameters
        product_ids_str = request.form.get('product_ids', '')
        collection_name = request.form.get('collection_name', 'hello_my_friend')
        
        # Parse product IDs
        if product_ids_str.strip():
            product_ids = [pid.strip() for pid in product_ids_str.split(',') if pid.strip()]
        else:
            # Get all product IDs from database
            db = next(get_db())
            products = db.query(Product).all()
            product_ids = [str(product.id) for product in products]

        if not product_ids:
            return jsonify({"error": "No products found"}), 400

        # Save PDF temporarily
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(temp_dir, filename)
        pdf_file.save(pdf_path)

        try:
            # Run async function to create Excel
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Call the async function and get workbook
            context_queries, product_keys = loop.run_until_complete(
                adapt_or_not(pdf_path, product_ids, collection_name)
            )
            
            # Import the create_excel_file function
            from ai_server.retrieve2.step7_write_on_excel import create_excel_file
            wb = create_excel_file(context_queries, product_keys)
            
            # Save to temporary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"bang_tuyen_bo_dap_ung_{timestamp}.xlsx"
            excel_path = os.path.join(temp_dir, excel_filename)
            wb.save(excel_path)

            # Return the file
            return send_file(
                excel_path,
                as_attachment=True,
                download_name=excel_filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        finally:
            # Clean up
            loop.close()
            # Note: temp files will be cleaned up by the system eventually
            # For immediate cleanup, you could add a background task

    except Exception as e:
        return jsonify({"error": f"Failed to generate Excel: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)