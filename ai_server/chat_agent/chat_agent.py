from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterOperator, FilterCondition
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from ai_server.config_db import config_db
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import asyncio

load_dotenv()


class ChatAgent:
    def __init__(self, collection_name: str = "hello_my_friend", llm_model: str = "gpt-4o-mini"):
        """
        Khởi tạo ChatAgent với vector database

        Args:
            collection_name: Tên collection trong Qdrant
            llm_model: Model LLM để sử dụng
        """
        self.collection_name = collection_name

        # Cấu hình Settings
        Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
        Settings.llm = OpenAI(model=llm_model, temperature=0.1)

        # Khởi tạo vector store và index
        self.vector_store = config_db(collection_name)
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store)

        # Tạo query engine với context
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=5,
            response_mode="compact"
        )

    def create_filters(self, product_ids: Optional[List[str]] = None,
                       file_ids: Optional[List[str]] = None,
                       categories: Optional[List[str]] = None) -> Optional[MetadataFilters]:
        """
        Tạo filters để lọc dữ liệu trong vector database

        Args:
            product_ids: List product IDs để lọc
            file_ids: List file IDs để lọc  
            categories: List categories để lọc

        Returns:
            MetadataFilters object hoặc None
        """
        filters_list = []

        if product_ids:
            filters_list.append(
                MetadataFilter(key="product_id",
                               operator=FilterOperator.IN, value=product_ids)
            )

        if file_ids:
            filters_list.append(
                MetadataFilter(
                    key="file_id", operator=FilterOperator.IN, value=file_ids)
            )

        if categories:
            filters_list.append(
                MetadataFilter(
                    key="category", operator=FilterOperator.IN, value=categories)
            )

        if filters_list:
            return MetadataFilters(
                filters=filters_list,
                condition=FilterCondition.AND
            )
        return None

    async def chat_async(self, question: str,
                         product_ids: Optional[List[str]] = None,
                         file_ids: Optional[List[str]] = None,
                         categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Chat async với agent

        Args:
            question: Câu hỏi của user
            product_ids: List product IDs để lọc context
            file_ids: List file IDs để lọc context
            categories: List categories để lọc context

        Returns:
            Dict chứa response và metadata
        """
        try:
            # Tạo filters nếu có
            filters = self.create_filters(product_ids, file_ids, categories)

            # Tạo retriever với filters
            if filters:
                retriever = self.index.as_retriever(
                    similarity_top_k=5,
                    filters=filters,
                    verbose=True
                )
                # Tạo query engine mới với retriever có filter
                from llama_index.core.query_engine import RetrieverQueryEngine
                query_engine = RetrieverQueryEngine.from_args(retriever)
            else:
                query_engine = self.query_engine

            # Thực hiện query
            response = await query_engine.aquery(question)

            # Lấy thông tin về source documents
            source_docs = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    if hasattr(node, 'metadata'):
                        source_docs.append({
                            'file_name': node.metadata.get('file_name', 'Unknown'),
                            'product_name': node.metadata.get('product_name', 'Unknown'),
                            'category': node.metadata.get('category', 'Unknown'),
                            'score': getattr(node, 'score', 0.0)
                        })

            return {
                'answer': str(response),
                'source_documents': source_docs,
                'question': question,
                'success': True
            }

        except Exception as e:
            return {
                'answer': f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi: {str(e)}",
                'source_documents': [],
                'question': question,
                'success': False,
                'error': str(e)
            }

    def chat(self, question: str,
             product_ids: Optional[List[str]] = None,
             file_ids: Optional[List[str]] = None,
             categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Chat sync với agent

        Args:
            question: Câu hỏi của user
            product_ids: List product IDs để lọc context
            file_ids: List file IDs để lọc context
            categories: List categories để lọc context

        Returns:
            Dict chứa response và metadata
        """
        try:
            # Kiểm tra xem có event loop đang chạy không
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Nếu loop đang chạy, tạo task mới
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            self._run_chat_async, question, product_ids, file_ids, categories)
                        return future.result()
                else:
                    # Nếu loop không chạy, dùng run_until_complete
                    return loop.run_until_complete(
                        self.chat_async(question, product_ids,
                                        file_ids, categories)
                    )
            except RuntimeError:
                # Không có event loop, tạo mới
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.chat_async(question, product_ids,
                                        file_ids, categories)
                    )
                    return result
                finally:
                    loop.close()
        except Exception as e:
            return {
                'answer': f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi: {str(e)}",
                'source_documents': [],
                'question': question,
                'success': False,
                'error': str(e)
            }

    def _run_chat_async(self, question: str, product_ids: Optional[List[str]], file_ids: Optional[List[str]], categories: Optional[List[str]]) -> Dict[str, Any]:
        """Helper method để chạy chat_async trong thread riêng"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.chat_async(question, product_ids, file_ids, categories)
            )
        finally:
            loop.close()

    def get_available_products(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách products có trong vector database

        Returns:
            List các products
        """
        try:
            # Thực hiện query để lấy metadata
            sample_response = self.query_engine.query("list products")

            products = []
            if hasattr(sample_response, 'source_nodes'):
                seen_products = set()
                for node in sample_response.source_nodes:
                    if hasattr(node, 'metadata'):
                        product_id = node.metadata.get('product_id')
                        if product_id and product_id not in seen_products:
                            products.append({
                                'product_id': product_id,
                                'product_name': node.metadata.get('product_name', 'Unknown'),
                                'category': node.metadata.get('category', 'Unknown')
                            })
                            seen_products.add(product_id)

            return products
        except Exception as e:
            print(f"Error getting available products: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái của agent

        Returns:
            Dict chứa thông tin trạng thái
        """
        try:
            # Test query đơn giản
            test_response = self.query_engine.query("hello")
            return {
                'status': 'healthy',
                'collection_name': self.collection_name,
                'llm_model': Settings.llm.model,
                'embed_model': Settings.embed_model.model_name,
                'message': 'Agent is working properly'
            }
        except Exception as e:
            return {
                'status': 'error',
                'collection_name': self.collection_name,
                'error': str(e),
                'message': 'Agent has issues'
            }
