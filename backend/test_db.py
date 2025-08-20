#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from backend.db.connect_db import SessionLocal, engine
from backend.models.models import Category, ProductLine, Product
from backend.services.crud_service import CRUDService

# Load environment variables
load_dotenv()


def test_db_connection():
    """Test database connection and basic operations"""
    try:
        print("🔍 Testing database connection...")

        # Test database URL
        db_url = os.getenv("DB_POSTGRES_URL")
        print(
            f"Database URL: {db_url[:20]}..." if db_url else "❌ No DB_POSTGRES_URL found")

        # Test engine connection
        print("🔗 Testing engine connection...")
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test")
            print(f"✅ Engine connection successful: {result.fetchone()}")

        # Test SessionLocal
        print("🗃️ Testing session...")
        db = SessionLocal()
        try:
            # Test basic query
            count = db.query(Category).count()
            print(f"✅ Session successful. Categories count: {count}")

            # Test CRUD service
            crud = CRUDService(db)
            categories = crud.category.get_all()
            print(f"✅ CRUD service successful. Categories: {len(categories)}")

            for cat in categories[:3]:  # Show first 3
                print(f"  - {cat.id}: {cat.name}")

        finally:
            db.close()

        print("🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_db_connection()
