import uuid
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from backend.models.models import Category, ProductLine, Product, FileVectorStore


class CategoryCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str) -> Category:
        """Tạo category mới"""
        category_id = f"cat_{uuid.uuid1()}"
        category = Category(id=category_id, name=name)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get_by_id(self, category_id: str) -> Optional[Category]:
        """Lấy category theo ID"""
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_by_name(self, name: str) -> Optional[Category]:
        """Lấy category theo tên"""
        return self.db.query(Category).filter(Category.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """Lấy tất cả categories với phân trang"""
        return self.db.query(Category).offset(skip).limit(limit).all()

    def get_with_product_lines(self, category_id: str) -> Optional[Category]:
        """Lấy category kèm product lines"""
        return (
            self.db.query(Category)
            .options(joinedload(Category.product_lines))
            .filter(Category.id == category_id)
            .first()
        )

    def update(self, category_id: str, name: str) -> Optional[Category]:
        """Cập nhật category"""
        category = self.get_by_id(category_id)
        if category:
            category.name = name
            self.db.commit()
            self.db.refresh(category)
        return category

    def delete(self, category_id: str) -> bool:
        """Xóa category và tất cả product lines, products, files liên quan"""
        category = self.get_by_id(category_id)
        if category:
            # Xóa tất cả files của tất cả products trong category này
            product_lines = self.db.query(ProductLine).filter(ProductLine.category_id == category_id).all()
            for product_line in product_lines:
                products = self.db.query(Product).filter(Product.product_line_id == product_line.id).all()
                for product in products:
                    files = self.db.query(FileVectorStore).filter(FileVectorStore.product_id == product.id).all()
                    for file in files:
                        self.db.delete(file)
                    self.db.delete(product)
                self.db.delete(product_line)
            
            # Sau đó xóa category
            self.db.delete(category)
            self.db.commit()
            return True
        return False


class ProductLineCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, category_id: str) -> ProductLine:
        """Tạo product line mới"""
        product_line_id = f"pl_{uuid.uuid1()}"
        product_line = ProductLine(id=product_line_id, name=name, category_id=category_id)
        self.db.add(product_line)
        self.db.commit()
        self.db.refresh(product_line)
        return product_line

    def get_by_id(self, product_line_id: str) -> Optional[ProductLine]:
        """Lấy product line theo ID"""
        return self.db.query(ProductLine).filter(ProductLine.id == product_line_id).first()

    def get_by_name_and_category(self, name: str, category_id: str) -> Optional[ProductLine]:
        """Lấy product line theo tên và category"""
        return (
            self.db.query(ProductLine)
            .filter(ProductLine.name == name, ProductLine.category_id == category_id)
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ProductLine]:
        """Lấy tất cả product lines với phân trang"""
        return self.db.query(ProductLine).offset(skip).limit(limit).all()

    def get_by_category(self, category_id: str) -> List[ProductLine]:
        """Lấy tất cả product lines theo category"""
        return self.db.query(ProductLine).filter(ProductLine.category_id == category_id).all()

    def get_with_products(self, product_line_id: str) -> Optional[ProductLine]:
        """Lấy product line kèm products"""
        return (
            self.db.query(ProductLine)
            .options(joinedload(ProductLine.products))
            .filter(ProductLine.id == product_line_id)
            .first()
        )

    def update(self, product_line_id: str, name: str) -> Optional[ProductLine]:
        """Cập nhật product line"""
        product_line = self.get_by_id(product_line_id)
        if product_line:
            product_line.name = name
            self.db.commit()
            self.db.refresh(product_line)
        return product_line

    def delete(self, product_line_id: str) -> bool:
        """Xóa product line và tất cả products, files liên quan"""
        product_line = self.get_by_id(product_line_id)
        if product_line:
            # Xóa tất cả files của các products trong product line này
            products = self.db.query(Product).filter(Product.product_line_id == product_line_id).all()
            for product in products:
                files = self.db.query(FileVectorStore).filter(FileVectorStore.product_id == product.id).all()
                for file in files:
                    self.db.delete(file)
                self.db.delete(product)
            
            # Sau đó xóa product line
            self.db.delete(product_line)
            self.db.commit()
            return True
        return False


class ProductCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, product_line_id: str) -> Product:
        """Tạo product mới"""
        product_id = f"p_{uuid.uuid1()}"
        product = Product(id=product_id, name=name, product_line_id=product_line_id)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_by_id(self, product_id: str) -> Optional[Product]:
        """Lấy product theo ID"""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_by_name_and_product_line(self, name: str, product_line_id: str) -> Optional[Product]:
        """Lấy product theo tên và product line"""
        return (
            self.db.query(Product)
            .filter(Product.name == name, Product.product_line_id == product_line_id)
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """Lấy tất cả products với phân trang"""
        return self.db.query(Product).offset(skip).limit(limit).all()

    def get_by_product_line(self, product_line_id: str) -> List[Product]:
        """Lấy tất cả products theo product line"""
        return self.db.query(Product).filter(Product.product_line_id == product_line_id).all()

    def get_with_files(self, product_id: str) -> Optional[Product]:
        """Lấy product kèm files"""
        return (
            self.db.query(Product)
            .options(joinedload(Product.files))
            .filter(Product.id == product_id)
            .first()
        )

    def get_full_info(self, product_id: str) -> Optional[Product]:
        """Lấy product với đầy đủ thông tin (category, product_line, files)"""
        return (
            self.db.query(Product)
            .options(
                joinedload(Product.product_line).joinedload(ProductLine.category),
                joinedload(Product.files)
            )
            .filter(Product.id == product_id)
            .first()
        )

    def update(self, product_id: str, name: str) -> Optional[Product]:
        """Cập nhật product"""
        product = self.get_by_id(product_id)
        if product:
            product.name = name
            self.db.commit()
            self.db.refresh(product)
        return product

    def delete(self, product_id: str) -> bool:
        """Xóa product và tất cả files liên quan"""
        product = self.get_by_id(product_id)
        if product:
            # Xóa tất cả files liên quan trước
            files = self.db.query(FileVectorStore).filter(FileVectorStore.product_id == product_id).all()
            for file in files:
                self.db.delete(file)
            
            # Sau đó xóa product
            self.db.delete(product)
            self.db.commit()
            return True
        return False


class FileVectorStoreCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, product_id: str) -> FileVectorStore:
        """Tạo file mới"""
        file_id = f"f_{uuid.uuid1()}"
        file_store = FileVectorStore(id=file_id, name=name, product_id=product_id)
        self.db.add(file_store)
        self.db.commit()
        self.db.refresh(file_store)
        return file_store

    def get_by_id(self, file_id: str) -> Optional[FileVectorStore]:
        """Lấy file theo ID"""
        return self.db.query(FileVectorStore).filter(FileVectorStore.id == file_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[FileVectorStore]:
        """Lấy tất cả files với phân trang"""
        return self.db.query(FileVectorStore).offset(skip).limit(limit).all()

    def get_by_product(self, product_id: str) -> List[FileVectorStore]:
        """Lấy tất cả files theo product"""
        return self.db.query(FileVectorStore).filter(FileVectorStore.product_id == product_id).all()

    def get_with_product_info(self, file_id: str) -> Optional[FileVectorStore]:
        """Lấy file kèm thông tin product"""
        return (
            self.db.query(FileVectorStore)
            .options(
                joinedload(FileVectorStore.product)
                .joinedload(Product.product_line)
                .joinedload(ProductLine.category)
            )
            .filter(FileVectorStore.id == file_id)
            .first()
        )

    def update(self, file_id: str, name: str) -> Optional[FileVectorStore]:
        """Cập nhật file name"""
        file_store = self.get_by_id(file_id)
        if file_store:
            file_store.name = name
            self.db.commit()
            self.db.refresh(file_store)
        return file_store

    def delete(self, file_id: str) -> bool:
        """Xóa file"""
        file_store = self.get_by_id(file_id)
        if file_store:
            self.db.delete(file_store)
            self.db.commit()
            return True
        return False

    def get_by_ids(self, file_ids: List[str]) -> List[FileVectorStore]:
        """Lấy multiple files theo danh sách IDs"""
        return self.db.query(FileVectorStore).filter(FileVectorStore.id.in_(file_ids)).all()


class CRUDService:
    """Main CRUD service class combining all CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.category = CategoryCRUD(db)
        self.product_line = ProductLineCRUD(db)
        self.product = ProductCRUD(db)
        self.file = FileVectorStoreCRUD(db)

    def get_hierarchy_structure(self) -> List[dict]:
        """Lấy cấu trúc phân cấp đầy đủ"""
        categories = (
            self.db.query(Category)
            .options(
                joinedload(Category.product_lines)
                .joinedload(ProductLine.products)
                .joinedload(Product.files)
            )
            .all()
        )
        
        result = []
        for category in categories:
            cat_data = {
                "id": category.id,
                "name": category.name,
                "product_lines": []
            }
            
            for product_line in category.product_lines:
                pl_data = {
                    "id": product_line.id,
                    "name": product_line.name,
                    "products": []
                }
                
                for product in product_line.products:
                    prod_data = {
                        "id": product.id,
                        "name": product.name,
                        "files": [
                            {"id": f.id, "name": f.name}
                            for f in product.files
                        ]
                    }
                    pl_data["products"].append(prod_data)
                
                cat_data["product_lines"].append(pl_data)
            
            result.append(cat_data)
        
        return result
