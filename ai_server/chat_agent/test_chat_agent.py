#!/usr/bin/env python3
"""
Test script for ChatAgent
Run this to test the ChatAgent functionality
"""

from ai_server.chat_agent import ChatAgent
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to Python path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()


async def test_chat_agent():
    """Test ChatAgent functionality"""
    print("🤖 Testing ChatAgent...")

    try:
        # Initialize ChatAgent
        print("📦 Initializing ChatAgent...")
        agent = ChatAgent(collection_name="hello_my_friend")

        # Health check
        print("🏥 Performing health check...")
        health = agent.health_check()
        print(f"Health status: {health}")

        if health['status'] != 'healthy':
            print("❌ Agent is not healthy, stopping test")
            return

        # Test simple query
        print("\n💬 Testing simple query...")
        test_questions = [
            "Xin chào, bạn có thể giúp tôi không?",
            "Tôi muốn tìm hiểu về sản phẩm NetSure",
            "Thông số kỹ thuật của bộ chuyển đổi nguồn là gì?"
        ]

        for question in test_questions:
            print(f"\n❓ Question: {question}")
            response = await agent.chat_async(question)

            if response['success']:
                print(f"✅ Answer: {response['answer'][:200]}...")
                if response['source_documents']:
                    print(
                        f"📄 Referenced {len(response['source_documents'])} documents:")
                    for doc in response['source_documents'][:2]:  # Show first 2 docs
                        print(
                            f"   - {doc['file_name']} ({doc['product_name']})")
            else:
                print(f"❌ Error: {response.get('error', 'Unknown error')}")

        # Test with filters
        print("\n🔍 Testing with product filter...")
        response = await agent.chat_async(
            "Thông tin về sản phẩm này là gì?",
            # You can add specific product_ids if you know them
            # product_ids=["some-product-id"]
        )

        if response['success']:
            print(f"✅ Filtered Answer: {response['answer'][:200]}...")
        else:
            print(
                f"❌ Filtered Error: {response.get('error', 'Unknown error')}")

        print("\n🎉 ChatAgent test completed successfully!")

    except Exception as e:
        print(f"💥 Error during test: {str(e)}")
        import traceback
        traceback.print_exc()


def test_sync_chat():
    """Test synchronous chat functionality"""
    print("\n🔄 Testing synchronous chat...")

    try:
        agent = ChatAgent(collection_name="hello_my_friend")
        response = agent.chat(
            "Hello, can you help me with product information?")

        if response['success']:
            print(f"✅ Sync Answer: {response['answer'][:200]}...")
        else:
            print(f"❌ Sync Error: {response.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"💥 Sync test error: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting ChatAgent tests...")
    print("=" * 50)

    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        sys.exit(1)

    print("✅ Environment variables check passed")

    # Run async test
    asyncio.run(test_chat_agent())

    # Run sync test
    test_sync_chat()

    print("\n" + "=" * 50)
    print("🏁 All tests completed!")
