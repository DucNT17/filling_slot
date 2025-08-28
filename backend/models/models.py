from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.connect_db import Base

class Category(Base):
    __tablename__ = "category"

    id = Column(String, primary_key=True, index=True)  # không auto-gen
    name = Column(String, nullable=False, unique=True)

    product_lines = relationship("ProductLine", back_populates="category", cascade="all, delete-orphan")


class ProductLine(Base):
    __tablename__ = "product_line"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

    category_id = Column(String, ForeignKey("category.id", ondelete="CASCADE"), nullable=False)
    category = relationship("Category", back_populates="product_lines")

    products = relationship("Product", back_populates="product_line", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "product"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

    product_line_id = Column(String, ForeignKey("product_line.id", ondelete="CASCADE"), nullable=False)
    product_line = relationship("ProductLine", back_populates="products")

    files = relationship("FileVectorStore", back_populates="product", cascade="all, delete-orphan")


class FileVectorStore(Base):
    __tablename__ = "file_vector_store"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

    product_id = Column(String, ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    product = relationship("Product", back_populates="files")
