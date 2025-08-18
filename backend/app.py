from flask import Flask, request, jsonify, send_file
from flasgger import Swagger
from backend.db.connect_db import SessionLocal, Base, engine
from backend.services.upload_data import ProductService
from backend.services.processtoexcel import ExcelService
from backend.services.crud_service import CRUDService
from backend.models.models import *
import asyncio
import os
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename
# Flask + Swagger
app = Flask(__name__)

# Swagger configuration with tags
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/",
    "tags": [
        {
            "name": "Main API",
            "description": "Core functionality APIs"
        },
        {
            "name": "Default",
            "description": "CRUD operations and management APIs"
        }
    ]
}

swagger = Swagger(app, config=swagger_config)

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
    tags:
      - Main API
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
    Generate Excel file from PDF and filename IDs
    ---
    tags:
      - Main API
    consumes:
      - multipart/form-data
    parameters:
      - name: pdf_file
        in: formData
        type: file
        required: true
      - name: filename_ids
        in: formData
        type: string
        required: false
        description: Comma-separated filename IDs (e.g., f_123,f_456)
      - name: collection_name
        in: formData
        type: string
        required: false
        default: hello_my_friend
      - name: type
        in: formData
        type: string
        required: false
        default: manual
        description: Processing type (manual or auto)
    responses:
      200:
        description: Excel file or JSON response based on type
        content:
          application/vnd.openxmlformats-officedocument.spreadsheetml.sheet:
            schema:
              type: string
              format: binary
          application/json:
            schema:
              type: object
    """
    try:
        if "pdf_file" not in request.files:
            return jsonify({"error": "No PDF file provided"}), 400

        pdf_file = request.files["pdf_file"]
        filename_ids_str = request.form.get("filename_ids", "")
        collection_name = request.form.get("collection_name", "hello_my_friend")
        type = request.form.get("type", "manual")

        db = next(get_db())
        service = ExcelService(db)
        if type == "manual":
            return service.generate_excel_from_pdf_by_filename_ids(pdf_file, filename_ids_str, collection_name)
        return jsonify({"hello": "world"})
    except Exception as e:
        return jsonify({"error": f"Failed to generate Excel: {str(e)}"}), 500

# ==================== CRUD APIs ====================

# ===== Category APIs =====
@app.route("/categories", methods=["POST"])
def create_category():
    """
    Create a new category
    ---
    tags:
      - Default
    parameters:
      - name: name
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Category created successfully
      400:
        description: Category already exists
    """
    try:
        name = request.form.get("name") or request.json.get("name")
        if not name:
            return jsonify({"error": "Category name is required"}), 400
            
        db = next(get_db())
        crud = CRUDService(db)
        
        # Check if category already exists
        existing = crud.category.get_by_name(name)
        if existing:
            return jsonify({"error": "Category already exists"}), 400
            
        category = crud.category.create(name)
        return jsonify({"id": category.id, "name": category.name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/categories", methods=["GET"])
def get_categories():
    """
    Get all categories
    ---
    tags:
      - Default
    parameters:
      - name: skip
        in: query
        type: integer
        default: 0
      - name: limit
        in: query
        type: integer
        default: 100
    responses:
      200:
        description: List of categories
    """
    try:
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 100))
        
        db = next(get_db())
        crud = CRUDService(db)
        categories = crud.category.get_all(skip, limit)
        
        return jsonify([{"id": cat.id, "name": cat.name} for cat in categories])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/categories/<category_id>", methods=["GET"])
def get_category(category_id):
    """
    Get category by ID with product lines
    ---
    tags:
      - Default
    parameters:
      - name: category_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Category details
      404:
        description: Category not found
    """
    try:
        db = next(get_db())
        crud = CRUDService(db)
        category = crud.category.get_with_product_lines(category_id)
        
        if not category:
            return jsonify({"error": "Category not found"}), 404
            
        return jsonify({
            "id": category.id,
            "name": category.name,
            "product_lines": [{"id": pl.id, "name": pl.name} for pl in category.product_lines]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/categories/<category_id>", methods=["PUT"])
def update_category(category_id):
    """
    Update category
    ---
    tags:
      - Default
    parameters:
      - name: category_id
        in: path
        type: string
        required: true
      - name: name
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Category updated successfully
      404:
        description: Category not found
    """
    try:
        name = request.form.get("name") or request.json.get("name")
        if not name:
            return jsonify({"error": "Category name is required"}), 400
            
        db = next(get_db())
        crud = CRUDService(db)
        category = crud.category.update(category_id, name)
        
        if not category:
            return jsonify({"error": "Category not found"}), 404
            
        return jsonify({"id": category.id, "name": category.name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/categories/<category_id>", methods=["DELETE"])
def delete_category(category_id):
    """
    Delete category
    ---
    tags:
      - Default
    parameters:
      - name: category_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Category deleted successfully
      404:
        description: Category not found
    """
    try:
        db = next(get_db())
        crud = CRUDService(db)
        success = crud.category.delete(category_id)
        
        if not success:
            return jsonify({"error": "Category not found"}), 404
            
        return jsonify({"message": "Category deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Product Line APIs =====
@app.route("/product-lines", methods=["POST"])
def create_product_line():
    """
    Create a new product line
    ---
    tags:
      - Default
    parameters:
      - name: name
        in: formData
        type: string
        required: true
      - name: category_id
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Product line created successfully
    """
    try:
        name = request.form.get("name") or request.json.get("name")
        category_id = request.form.get("category_id") or request.json.get("category_id")
        
        if not name or not category_id:
            return jsonify({"error": "Name and category_id are required"}), 400
            
        db = next(get_db())
        crud = CRUDService(db)
        
        # Check if category exists
        if not crud.category.get_by_id(category_id):
            return jsonify({"error": "Category not found"}), 404
            
        product_line = crud.product_line.create(name, category_id)
        return jsonify({
            "id": product_line.id,
            "name": product_line.name,
            "category_id": product_line.category_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/product-lines", methods=["GET"])
def get_product_lines():
    """
    Get all product lines
    ---
    tags:
      - Default
    parameters:
      - name: category_id
        in: query
        type: string
        required: false
      - name: skip
        in: query
        type: integer
        default: 0
      - name: limit
        in: query
        type: integer
        default: 100
    responses:
      200:
        description: List of product lines
    """
    try:
        category_id = request.args.get("category_id")
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 100))
        
        db = next(get_db())
        crud = CRUDService(db)
        
        if category_id:
            product_lines = crud.product_line.get_by_category(category_id)
        else:
            product_lines = crud.product_line.get_all(skip, limit)
        
        return jsonify([{
            "id": pl.id,
            "name": pl.name,
            "category_id": pl.category_id
        } for pl in product_lines])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/product-lines/<product_line_id>", methods=["GET"])
def get_product_line(product_line_id):
    """
    Get product line by ID with products
    ---
    tags:
      - Default
    parameters:
      - name: product_line_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Product line details
      404:
        description: Product line not found
    """
    try:
        db = next(get_db())
        crud = CRUDService(db)
        product_line = crud.product_line.get_with_products(product_line_id)
        
        if not product_line:
            return jsonify({"error": "Product line not found"}), 404
            
        return jsonify({
            "id": product_line.id,
            "name": product_line.name,
            "category_id": product_line.category_id,
            "products": [{"id": p.id, "name": p.name} for p in product_line.products]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/product-lines/<product_line_id>", methods=["PUT"])
def update_product_line(product_line_id):
    """
    Update product line
    ---
    tags:
      - Default
    parameters:
      - name: product_line_id
        in: path
        type: string
        required: true
      - name: name
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Product line updated successfully
      404:
        description: Product line not found
    """
    try:
        name = request.form.get("name") or request.json.get("name")
        if not name:
            return jsonify({"error": "Product line name is required"}), 400
            
        db = next(get_db())
        crud = CRUDService(db)
        product_line = crud.product_line.update(product_line_id, name)
        
        if not product_line:
            return jsonify({"error": "Product line not found"}), 404
            
        return jsonify({
            "id": product_line.id,
            "name": product_line.name,
            "category_id": product_line.category_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/product-lines/<product_line_id>", methods=["DELETE"])
def delete_product_line(product_line_id):
    """
    Delete product line
    ---
    tags:
      - Default
    parameters:
      - name: product_line_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Product line deleted successfully
      404:
        description: Product line not found
    """
    try:
        db = next(get_db())
        crud = CRUDService(db)
        success = crud.product_line.delete(product_line_id)
        
        if not success:
            return jsonify({"error": "Product line not found"}), 404
            
        return jsonify({"message": "Product line deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Product APIs =====
@app.route("/products", methods=["POST"])
def create_product():
    """
    Create a new product
    ---
    tags:
      - Default
    parameters:
      - name: name
        in: formData
        type: string
        required: true
      - name: product_line_id
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Product created successfully
    """
    try:
        name = request.form.get("name") or request.json.get("name")
        product_line_id = request.form.get("product_line_id") or request.json.get("product_line_id")
        
        if not name or not product_line_id:
            return jsonify({"error": "Name and product_line_id are required"}), 400
            
        db = next(get_db())
        crud = CRUDService(db)
        
        # Check if product line exists
        if not crud.product_line.get_by_id(product_line_id):
            return jsonify({"error": "Product line not found"}), 404
            
        product = crud.product.create(name, product_line_id)
        return jsonify({
            "id": product.id,
            "name": product.name,
            "product_line_id": product.product_line_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products", methods=["GET"])
def get_products():
    """
    Get all products
    ---
    tags:
      - Default
    parameters:
      - name: product_line_id
        in: query
        type: string
        required: false
      - name: skip
        in: query
        type: integer
        default: 0
      - name: limit
        in: query
        type: integer
        default: 100
    responses:
      200:
        description: List of products
    """
    try:
        product_line_id = request.args.get("product_line_id")
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 100))
        
        db = next(get_db())
        crud = CRUDService(db)
        
        if product_line_id:
            products = crud.product.get_by_product_line(product_line_id)
        else:
            products = crud.product.get_all(skip, limit)
        
        return jsonify([{
            "id": p.id,
            "name": p.name,
            "product_line_id": p.product_line_id
        } for p in products])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    """
    Get product by ID with full info
    ---
    tags:
      - Default
    parameters:
      - name: product_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Product details
      404:
        description: Product not found
    """
    try:
        db = next(get_db())
        crud = CRUDService(db)
        product = crud.product.get_full_info(product_id)
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
            
        return jsonify({
            "id": product.id,
            "name": product.name,
            "product_line": {
                "id": product.product_line.id,
                "name": product.product_line.name,
                "category": {
                    "id": product.product_line.category.id,
                    "name": product.product_line.category.name
                }
            },
            "files": [{"id": f.id, "name": f.name} for f in product.files]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    """
    Update product
    ---
    tags:
      - Default
    parameters:
      - name: product_id
        in: path
        type: string
        required: true
      - name: name
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Product updated successfully
      404:
        description: Product not found
    """
    try:
        name = request.form.get("name") or request.json.get("name")
        if not name:
            return jsonify({"error": "Product name is required"}), 400
            
        db = next(get_db())
        crud = CRUDService(db)
        product = crud.product.update(product_id, name)
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
            
        return jsonify({
            "id": product.id,
            "name": product.name,
            "product_line_id": product.product_line_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    """
    Delete product
    ---
    tags:
      - Default
    parameters:
      - name: product_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Product deleted successfully
      404:
        description: Product not found
    """
    try:
        db = next(get_db())
        crud = CRUDService(db)
        success = crud.product.delete(product_id)
        
        if not success:
            return jsonify({"error": "Product not found"}), 404
            
        return jsonify({"message": "Product deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== File APIs =====
@app.route("/files", methods=["GET"])
def get_files():
    """
    Get all files
    ---
    tags:
      - Default
    parameters:
      - name: product_id
        in: query
        type: string
        required: false
      - name: skip
        in: query
        type: integer
        default: 0
      - name: limit
        in: query
        type: integer
        default: 100
    responses:
      200:
        description: List of files
    """
    try:
        product_id = request.args.get("product_id")
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 100))
        
        db = next(get_db())
        crud = CRUDService(db)
        
        if product_id:
            files = crud.file.get_by_product(product_id)
        else:
            files = crud.file.get_all(skip, limit)
        
        return jsonify([{
            "id": f.id,
            "name": f.name,
            "product_id": f.product_id
        } for f in files])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/files/<file_id>", methods=["GET"])
def get_file(file_id):
    """
    Get file by ID with product info
    ---
    tags:
      - Default
    parameters:
      - name: file_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: File details
      404:
        description: File not found
    """
    try:
        db = next(get_db())
        crud = CRUDService(db)
        file_store = crud.file.get_with_product_info(file_id)
        
        if not file_store:
            return jsonify({"error": "File not found"}), 404
            
        return jsonify({
            "id": file_store.id,
            "name": file_store.name,
            "product": {
                "id": file_store.product.id,
                "name": file_store.product.name,
                "product_line": {
                    "id": file_store.product.product_line.id,
                    "name": file_store.product.product_line.name,
                    "category": {
                        "id": file_store.product.product_line.category.id,
                        "name": file_store.product.product_line.category.name
                    }
                }
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/files/<file_id>", methods=["PUT"])
def update_file(file_id):
    """
    Update file name
    ---
    tags:
      - Default
    parameters:
      - name: file_id
        in: path
        type: string
        required: true
      - name: name
        in: formData
        type: string
        required: true
    responses:
      200:
        description: File updated successfully
      404:
        description: File not found
    """
    try:
        name = request.form.get("name") or request.json.get("name")
        if not name:
            return jsonify({"error": "File name is required"}), 400
            
        db = next(get_db())
        crud = CRUDService(db)
        file_store = crud.file.update(file_id, name)
        
        if not file_store:
            return jsonify({"error": "File not found"}), 404
            
        return jsonify({
            "id": file_store.id,
            "name": file_store.name,
            "product_id": file_store.product_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/files/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    """
    Delete file
    ---
    tags:
      - Default
    parameters:
      - name: file_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: File deleted successfully
      404:
        description: File not found
    """
    try:
        db = next(get_db())
        crud = CRUDService(db)
        success = crud.file.delete(file_id)
        
        if not success:
            return jsonify({"error": "File not found"}), 404
            
        return jsonify({"message": "File deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Hierarchy API =====
@app.route("/hierarchy", methods=["GET"])
def get_hierarchy():
    """
    Get full hierarchy structure
    ---
    tags:
      - Main API
    responses:
      200:
        description: Complete hierarchy structure
    """
    try:
        db = next(get_db())
        crud = CRUDService(db)
        hierarchy = crud.get_hierarchy_structure()
        return jsonify(hierarchy)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)