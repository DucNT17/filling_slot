import os
import json
from typing import List, Dict, Any, Optional, Literal

# --- Cấu hình và Biến môi trường ---
# Trong một ứng dụng thực tế, các biến này sẽ được tải từ .env hoặc file cấu hình
# Đảm bảo bạn đã cài đặt các thư viện cần thiết:
# pip install llama-index llama-index-llms-openai llama-index-embeddings-openai llama-index-vector-stores-chroma pydantic PyPDF2 reportlab llama-parse chromadb
# Bạn cũng cần khóa API LlamaParse và OpenAI:
# export LLAMAPARSE_API_KEY="YOUR_LLAMAPARSE_API_KEY"
# export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
LLAMAPARSE_API_KEY = os.getenv("LLAMAPARSE_API_KEY", "YOUR_LLAMAPARSE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
VECTOR_DB_PATH = "./chroma_db" # Đường dẫn cho ChromaDB cục bộ

# --- Pydantic Models để trao đổi dữ liệu có cấu trúc ---
from pydantic import BaseModel, Field

class TenderRequirementDetail(BaseModel):
    """Chi tiết yêu cầu kỹ thuật đã phân tích."""
    parameter_name: str = Field(description="Tên thông số kỹ thuật (e.g., 'Số lượng khe cắm module chỉnh lưu')")
    value: str = Field(description="Giá trị yêu cầu (e.g., '4', '0~40', 'Có')")
    unit: Optional[str] = Field(None, description="Đơn vị của giá trị (e.g., 'cái', '°C', 'W')")
    comparison_operator: Optional[str] = Field(None, description="Toán tử so sánh (e.g., '>=', '<=', '=', 'range', 'semantic')")
    condition: Optional[str] = Field(None, description="Bất kỳ điều kiện hoặc ràng buộc nào đi kèm")

class TenderRequirement(BaseModel):
    """Đại diện có cấu trúc của một yêu cầu kỹ thuật từ hồ sơ mời thầu."""
    item_no: str = Field(description="Hạng mục số (e.g., 'III', '1', '2')")
    goods_name: str = Field(description="Tên hàng hoá (e.g., 'Bộ chuyển đổi nguồn 220VAC/48VDC')")
    requirement_category: Optional[str] = Field(None, description="Danh mục yêu cầu (e.g., 'Yêu cầu chung', 'Cấu hình thiết bị nguồn')")
    original_text: str = Field(description="Văn bản gốc của yêu cầu kỹ thuật trong hồ sơ mời thầu")
    parsed_detail: TenderRequirementDetail = Field(description="Chi tiết yêu cầu kỹ thuật đã phân tích")

class ProductReference(BaseModel):
    """Thông tin về nơi tìm thấy thông số kỹ thuật sản phẩm."""
    document_name: str = Field(description="Tên tài liệu tham chiếu (e.g., 'NetSure 732_User Manual.pdf')")
    section: Optional[str] = Field(None, description="Phần, chương, mục, bảng (nếu có)")
    page: str = Field(description="Số trang")
    line_or_context: Optional[str] = Field(None, description="Dòng hoặc ngữ cảnh cụ thể trong tài liệu")

class RetrievedProductSpec(BaseModel):
    """Đại diện có cấu trúc của một thông số kỹ thuật sản phẩm được truy xuất."""
    parameter_name: str = Field(description="Tên thông số kỹ thuật của sản phẩm")
    value: str = Field(description="Giá trị thông số của sản phẩm")
    unit: Optional[str] = Field(None, description="Đơn vị của giá trị thông số sản phẩm")
    condition: Optional[str] = Field(None, description="Điều kiện hoặc ràng buộc liên quan đến thông số sản phẩm")
    original_text_in_doc: str = Field(description="Đoạn văn bản gốc từ tài liệu sản phẩm chứa thông tin")
    reference: ProductReference = Field(description="Thông tin tham chiếu đến tài liệu sản phẩm")

class ComplianceResult(BaseModel):
    """Kết quả đánh giá đáp ứng cho một yêu cầu duy nhất."""
    tender_requirement: TenderRequirement = Field(description="Yêu cầu kỹ thuật gốc từ hồ sơ mời thầu")
    retrieved_spec: Optional[RetrievedProductSpec] = Field(None, description="Thông số kỹ thuật sản phẩm tìm được")
    compliance_status: Literal["Đáp ứng", "Không đáp ứng", "Đáp ứng một phần", "Không tìm thấy thông tin"] = Field(description="Trạng thái đáp ứng")
    notes: Optional[str] = Field(None, description="Ghi chú chi tiết về việc đáp ứng hoặc lý do không đáp ứng")

# --- Module 1: Document Preprocessor ---
from llama_parse import LlamaParse
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.schema import Document

class DocumentPreprocessor:
    """
    Xử lý phân tích tài liệu PDF, chia nhỏ nội dung và trích xuất siêu dữ liệu.
    Sử dụng LlamaParse để phân tích PDF nâng cao.
    """
    def __init__(self, llama_parse_api_key: str):
        self.parser = LlamaParse(api_key=llama_parse_api_key, result_type="markdown") # Có thể dùng "json"
        self.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)

    def process_documents(self, file_paths: List[str]) -> List[Document]:
        """
        Phân tích tài liệu và chuyển đổi chúng thành đối tượng Document của LlamaIndex.
        Siêu dữ liệu như file_name và page_label sẽ tự động được thêm bởi SimpleDirectoryReader.
        """
        print(f"Đang xử lý tài liệu: {file_paths}")
        reader = SimpleDirectoryReader(input_files=file_paths)
        raw_documents = reader.load_data()

        parsed_documents = self.parser.get_documents(raw_documents)

        # Chia nhỏ tài liệu thành các node/chunk để nhúng
        pipeline = IngestionPipeline(node_parser=self.node_parser)
        nodes = pipeline.run(documents=parsed_documents)
        
        print(f"Hoàn thành xử lý. Đã tạo {len(nodes)} node.")
        return nodes

# --- Module 2: Product Knowledge Base Builder ---
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

class ProductKnowledgeBaseBuilder:
    """
    Xây dựng và quản lý cơ sở dữ liệu vector cho tài liệu sản phẩm.
    """
    def __init__(self, openai_api_key: str, persist_dir: str = "./chroma_db"):
        self.openai_api_key = openai_api_key
        self.persist_dir = persist_dir
        self.llm = OpenAI(api_key=self.openai_api_key, model="gpt-4o") # Sử dụng LLM mạnh mẽ để nhúng tốt hơn
        self.embed_model = OpenAIEmbedding(api_key=self.openai_api_key, model="text-embedding-ada-002")
        
        # Khởi tạo ChromaDB client
        self.db = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.db.get_or_create_collection("product_docs")
        self.vector_store = ChromaVectorStore(collection=self.collection)

        self.service_context = ServiceContext.from_defaults(
            llm=self.llm, embed_model=self.embed_model
        )
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store, service_context=self.service_context
        )
        self.query_engine = self.index.as_query_engine() # Để truy vấn cấp cao hơn nếu cần

    def build_from_nodes(self, nodes: List[Document]):
        """Đưa các node (chunks) vào cơ sở dữ liệu vector."""
        print(f"Đang đưa {len(nodes)} node vào cơ sở tri thức...")
        self.index.insert_nodes(nodes)
        self.db.persist() # Lưu cơ sở dữ liệu
        print("Cơ sở tri thức đã được xây dựng và duy trì.")

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Thực hiện tìm kiếm tương đồng trên cơ sở tri thức.
        Trả về danh sách các từ điển với nội dung văn bản và siêu dữ liệu.
        """
        print(f"Đang truy vấn cơ sở tri thức cho: '{query_text}'")
        query_embedding = self.embed_model.get_text_embedding(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas']
        )
        
        retrieved_info = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                doc_content = results['documents'][0][i]
                metadata = results['metadatas'][0][i]
                retrieved_info.append({
                    "text": doc_content,
                    "metadata": metadata
                })
        print(f"Đã truy xuất {len(retrieved_info)} chunk liên quan.")
        return retrieved_info


# --- Agent 1: Tender Requirement Extractor ---
from llama_index.core.llms import ChatMessage

class TenderRequirementExtractor:
    """
    Agent chịu trách nhiệm trích xuất các yêu cầu kỹ thuật có cấu trúc từ tài liệu mời thầu.
    """
    def __init__(self, llm: OpenAI):
        self.llm = llm

    def extract_requirements(self, tender_document_text: str) -> List[TenderRequirement]:
        """
        Trích xuất các yêu cầu có cấu trúc từ văn bản tài liệu mời thầu.
        Điều này sẽ liên quan đến việc nhắc LLM phân tích các phần và bảng cụ thể.
        """
        print("Đang trích xuất yêu cầu từ tài liệu mời thầu...")
        
        prompt = f"""
        Bạn là một chuyên gia phân tích yêu cầu kỹ thuật. Nhiệm vụ của bạn là đọc và phân tích các yêu cầu kỹ thuật từ hồ sơ mời thầu được cung cấp.
        Trích xuất từng yêu cầu kỹ thuật chi tiết từ phần "Yêu cầu kỹ thuật" (thường trong các bảng) và chuyển đổi chúng thành định dạng JSON cấu trúc.
        Mỗi đối tượng JSON phải tuân thủ định dạng TenderRequirement sau:

        class TenderRequirement(BaseModel):
            item_no: str = Field(description="Hạng mục số (e.g., 'III', '1', '2')")
            goods_name: str = Field(description="Tên hàng hoá (e.g., 'Bộ chuyển đổi nguồn 220VAC/48VDC')")
            requirement_category: Optional[str] = Field(None, description="Danh mục yêu cầu (e.g., 'Yêu cầu chung', 'Cấu hình thiết bị nguồn')")
            original_text: str = Field(description="Văn bản gốc của yêu cầu kỹ thuật trong hồ sơ mời thầu")
            parsed_detail: TenderRequirementDetail = Field(description="Chi tiết yêu cầu kỹ thuật đã phân tích")

        class TenderRequirementDetail(BaseModel):
            parameter_name: str = Field(description="Tên thông số kỹ thuật (e.g., 'Số lượng khe cắm module chỉnh lưu')")
            value: str = Field(description="Giá trị yêu cầu (e.g., '4', '0~40', 'Có')")
            unit: Optional[str] = Field(None, description="Đơn vị của giá trị (e.g., 'cái', '°C', 'W')")
            comparison_operator: Optional[str] = Field(None, description="Toán tử so sánh (e.g., '>=', '<=', '=', 'range', 'semantic')")
            condition: Optional[str] = Field(None, description="Bất kỳ điều kiện hoặc ràng buộc nào đi kèm")

        Hướng dẫn trích xuất:
        - Đảm bảo trích xuất chính xác 'item_no', 'goods_name', 'requirement_category' từ ngữ cảnh của yêu cầu.
        - Đối với 'parsed_detail', hãy cố gắng phân tích càng chi tiết càng tốt:
            - 'parameter_name': Tên rõ ràng của thông số kỹ thuật.
            - 'value': Giá trị số hoặc mô tả.
            - 'unit': Đơn vị chuẩn (nếu có).
            - 'comparison_operator': Sử dụng 'range' cho các dải (ví dụ: 'từ X đến Y'), các toán tử toán học cho số (>=, <=, =), và 'semantic' cho các yêu cầu mô tả.
            - 'condition': Bất kỳ điều kiện bổ sung nào (ví dụ: 'khi hoạt động hết công suất').
        - 'original_text': Giữ nguyên câu yêu cầu kỹ thuật đầy đủ từ hồ sơ mời thầu.
        - Nếu một giá trị là mô tả (ví dụ: "Có", "Tự động"), hãy đặt 'unit' và 'comparison_operator' là None.

        Dữ liệu hồ sơ mời thầu:
        {tender_document_text}

        Vui lòng trả về một mảng JSON (List[TenderRequirement]). Đảm bảo đầu ra là JSON hợp lệ.
        """

        messages = [
            ChatMessage(role="system", content=prompt),
            ChatMessage(role="user", content=tender_document_text)
        ]

        try:
            # LLM sẽ tạo ra đầu ra có cấu trúc
            # Với LlamaIndex, nếu bạn sử dụng response_model, nó sẽ tự động phân tích.
            response = self.llm.chat(messages, response_model=List[TenderRequirement])
            extracted_requirements = response
            print(f"Đã trích xuất {len(extracted_requirements)} yêu cầu.")
            return extracted_requirements
        except Exception as e:
            print(f"Lỗi khi trích xuất yêu cầu: {e}")
            # Xử lý lỗi: trả về danh sách rỗng hoặc một phần và gắn cờ để người dùng xem xét
            return []


# --- Agent 2: Product Specification Matcher ---
class ProductSpecMatcher:
    """
    Agent chịu trách nhiệm truy vấn cơ sở tri thức sản phẩm và trích xuất các
    thông số kỹ thuật sản phẩm liên quan và các tham chiếu của chúng.
    """
    def __init__(self, kb_builder: ProductKnowledgeBaseBuilder, llm: OpenAI):
        self.kb_builder = kb_builder
        self.llm = llm

    def match_and_extract(self, requirement: TenderRequirement) -> Optional[RetrievedProductSpec]:
        """
        Tìm các thông số kỹ thuật sản phẩm liên quan cho một yêu cầu mời thầu nhất định.
        """
        print(f"Đang đối sánh thông số sản phẩm cho yêu cầu: {requirement.parsed_detail.parameter_name}")
        query_text = f"{requirement.goods_name} {requirement.parsed_detail.parameter_name} {requirement.parsed_detail.value} {requirement.parsed_detail.unit or ''}"
        
        # Bước 1: Truy xuất các đoạn văn bản có thể liên quan từ cơ sở dữ liệu vector
        retrieved_chunks = self.kb_builder.query(query_text, top_k=5)

        if not retrieved_chunks:
            print(f"Không tìm thấy đoạn văn bản liên quan cho '{requirement.parsed_detail.parameter_name}'.")
            return None

        # Bước 2: Sử dụng LLM để trích xuất thông số chính xác từ các đoạn văn bản đã truy xuất và lấy tham chiếu
        context_text = "\n---\n".join([c['text'] for c in retrieved_chunks])
        
        prompt = f"""
        Bạn là một chuyên gia về sản phẩm. Dựa trên yêu cầu kỹ thuật sau và các thông tin tài liệu sản phẩm được cung cấp,
        hãy trích xuất thông số kỹ thuật chính xác của sản phẩm liên quan và thông tin tham chiếu của nó.

        Yêu cầu kỹ thuật cần tìm:
        Tên hàng hoá: {requirement.goods_name}
        Thông số: {requirement.parsed_detail.parameter_name}
        Giá trị yêu cầu: {requirement.parsed_detail.value} {requirement.parsed_detail.unit or ''}
        Điều kiện: {requirement.parsed_detail.condition or 'Không có'}

        Các đoạn văn bản từ tài liệu sản phẩm có thể liên quan:
        {context_text}

        Từ các đoạn văn bản trên, hãy xác định thông số kỹ thuật của sản phẩm đáp ứng yêu cầu.
        Đảm bảo trích xuất 'parameter_name', 'value', 'unit' và 'condition' từ thông số sản phẩm.
        Đặc biệt quan trọng, hãy xác định 'document_name', 'page', 'section', và 'line_or_context' từ metadata của đoạn văn bản *chính xác nhất* đã sử dụng để tạo 'reference'.

        Cấu trúc đầu ra mong muốn (JSON):
        class RetrievedProductSpec(BaseModel):
            parameter_name: str = Field(description="Tên thông số kỹ thuật của sản phẩm")
            value: str = Field(description="Giá trị thông số của sản phẩm")
            unit: Optional[str] = Field(None, description="Đơn vị của giá trị thông số sản phẩm")
            condition: Optional[str] = Field(None, description="Điều kiện hoặc ràng buộc liên quan đến thông số sản phẩm")
            original_text_in_doc: str = Field(description="Đoạn văn bản gốc từ tài liệu sản phẩm chứa thông tin")
            reference: ProductReference = Field(description="Thông tin tham chiếu đến tài liệu sản phẩm")

        class ProductReference(BaseModel):
            document_name: str = Field(description="Tên tài liệu tham chiếu (e.g., 'NetSure 732_User Manual.pdf')")
            section: Optional[str] = Field(None, description="Phần, chương, mục, bảng (nếu có)")
            page: str = Field(description="Số trang")
            line_or_context: Optional[str] = Field(None, description="Dòng hoặc ngữ cảnh cụ thể trong tài liệu")

        Nếu không tìm thấy thông tin phù hợp, trả về JSON rỗng hoặc {{"retrieved_spec": null}}.
        """
        
        full_prompt_messages = [
            ChatMessage(role="system", content=prompt),
            ChatMessage(role="user", content=f"Yêu cầu: {requirement.original_text}\n\nThông tin tài liệu sản phẩm:\n{context_text}")
        ]

        try:
            response = self.llm.chat(full_prompt_messages, response_model=RetrievedProductSpec)
            extracted_spec = response

            # Tinh chỉnh tham chiếu: LLM có thể chỉ đưa ra văn bản, cần ánh xạ lại với siêu dữ liệu
            best_match_metadata = None
            for chunk in retrieved_chunks:
                if extracted_spec.original_text_in_doc in chunk['text']:
                    best_match_metadata = chunk['metadata']
                    break
            
            if best_match_metadata:
                extracted_spec.reference.document_name = best_match_metadata.get("file_name", "N/A")
                extracted_spec.reference.page = str(best_match_metadata.get("page_label", "N/A"))
                extracted_spec.reference.section = best_match_metadata.get("section_name", None) # LlamaParse có thể cung cấp tên phần
                extracted_spec.reference.line_or_context = extracted_spec.original_text_in_doc[:100] + "..." if len(extracted_spec.original_text_in_doc) > 100 else extracted_spec.original_text_in_doc # Đoạn snippet
            else:
                 # Nếu không tìm thấy metadata phù hợp, vẫn cố gắng điền tên tài liệu chung
                extracted_spec.reference.document_name = "Tài liệu sản phẩm" 
                extracted_spec.reference.page = "N/A"
                extracted_spec.reference.line_or_context = "Không xác định"

            print(f"Đã trích xuất thông số cho '{requirement.parsed_detail.parameter_name}': {extracted_spec.parameter_name}")
            return extracted_spec

        except Exception as e:
            print(f"Lỗi khi đối sánh/trích xuất thông số sản phẩm cho '{requirement.parsed_detail.parameter_name}': {e}")
            return None


# --- Agent 3: Compliance Evaluator ---
class ComplianceEvaluator:
    """
    Agent chịu trách nhiệm so sánh các yêu cầu mời thầu với thông số kỹ thuật sản phẩm đã truy xuất
    và xác định trạng thái đáp ứng.
    """
    def __init__(self, llm: OpenAI):
        self.llm = llm
        # self.unit_converter = UnitConverter() # Khái niệm: một công cụ chuyển đổi đơn vị

    def evaluate_compliance(
        self,
        requirement: TenderRequirement,
        product_spec: Optional[RetrievedProductSpec]
    ) -> ComplianceResult:
        """
        So sánh yêu cầu với thông số kỹ thuật sản phẩm để xác định sự đáp ứng.
        """
        print(f"Đang đánh giá đáp ứng cho: {requirement.parsed_detail.parameter_name}")

        if product_spec is None:
            return ComplianceResult(
                tender_requirement=requirement,
                retrieved_spec=None,
                compliance_status="Không tìm thấy thông tin",
                notes="Không tìm thấy thông số kỹ thuật sản phẩm tương ứng trong tài liệu."
            )

        req_detail = requirement.parsed_detail
        prod_spec_detail = product_spec

        compliance_status = "Không đáp ứng"
        notes = ""

        try:
            # So sánh số học (cần phân tích và chuyển đổi đơn vị mạnh mẽ hơn trong thực tế)
            if req_detail.comparison_operator in [">=", "<=", "=", "range"]:
                # Chuyển đổi giá trị sang số để so sánh
                req_val = float(req_detail.value.replace('~', ',').split(',')[0]) # Lấy giá trị đầu tiên cho so sánh đơn giản
                prod_val = float(prod_spec_detail.value.replace('~', ',').split(',')[0])

                if req_detail.comparison_operator == ">=":
                    if prod_val >= req_val:
                        compliance_status = "Đáp ứng"
                    else:
                        notes = f"Giá trị sản phẩm ({prod_spec_detail.value}{prod_spec_detail.unit or ''}) thấp hơn yêu cầu tối thiểu ({req_detail.value}{req_detail.unit or ''})."
                elif req_detail.comparison_operator == "<=":
                    if prod_val <= req_val:
                        compliance_status = "Đáp ứng"
                    else:
                        notes = f"Giá trị sản phẩm ({prod_spec_detail.value}{prod_spec_detail.unit or ''}) cao hơn yêu cầu tối đa ({req_detail.value}{req_detail.unit or ''})."
                elif req_detail.comparison_operator == "=":
                    if prod_val == req_val:
                        compliance_status = "Đáp ứng"
                    else:
                        notes = f"Giá trị sản phẩm ({prod_spec_detail.value}{prod_spec_detail.unit or ''}) khác yêu cầu ({req_detail.value}{req_detail.unit or ''})."
                elif req_detail.comparison_operator == "range":
                    # Xử lý dải nhiệt độ, ví dụ "0~40" hoặc "(-10, 60)"
                    req_values = [float(v.strip()) for v in req_detail.value.strip('()[]').split('~' if '~' in req_detail.value else ',')]
                    if len(req_values) == 2:
                        req_min, req_max = req_values[0], req_values[1]
                        if req_min <= prod_val <= req_max:
                            compliance_status = "Đáp ứng"
                        else:
                            notes = f"Giá trị sản phẩm ({prod_spec_detail.value}{prod_spec_detail.unit or ''}) nằm ngoài dải yêu cầu ({req_detail.value}{req_detail.unit or ''})."
                    else:
                        compliance_status = "Đáp ứng một phần"
                        notes = "Không thể phân tích dải yêu cầu một cách chính xác. Cần kiểm tra thủ công."

            # So sánh ngữ nghĩa (dùng LLM) hoặc khi không có toán tử rõ ràng
            elif req_detail.comparison_operator == "semantic" or not req_detail.comparison_operator:
                llm_prompt = f"""
                Đánh giá xem thông số kỹ thuật sản phẩm sau có đáp ứng yêu cầu kỹ thuật được đưa ra hay không.
                Yêu cầu: "{req_detail.original_text}"
                Thông số kỹ thuật sản phẩm: "{prod_spec_detail.original_text_in_doc}"

                Trả lời bằng một trong các từ sau: "Đáp ứng", "Không đáp ứng", "Đáp ứng một phần".
                Nếu "Không đáp ứng" hoặc "Đáp ứng một phần", hãy giải thích ngắn gọn lý do.
                """
                messages = [ChatMessage(role="user", content=llm_prompt)]
                llm_response = self.llm.chat(messages).text
                
                if "Đáp ứng" in llm_response:
                    compliance_status = "Đáp ứng"
                elif "Đáp ứng một phần" in llm_response: # Ưu tiên kiểm tra "Đáp ứng một phần" trước
                    compliance_status = "Đáp ứng một phần"
                elif "Không đáp ứng" in llm_response:
                    compliance_status = "Không đáp ứng"
                else: # Mặc định là "Đáp ứng một phần" nếu phản hồi không rõ ràng
                    compliance_status = "Đáp ứng một phần"
                
                notes = llm_response # Giải thích của LLM trở thành ghi chú

        except ValueError:
            compliance_status = "Đáp ứng một phần" # Không thể phân tích thành số, cần kiểm tra thủ công
            notes = "Không thể so sánh số học do lỗi định dạng giá trị. Cần kiểm tra thủ công."
        except Exception as e:
            compliance_status = "Đáp ứng một phần"
            notes = f"Lỗi không xác định trong quá trình đánh giá: {e}. Cần kiểm tra thủ công."
            
        print(f"Trạng thái đáp ứng cho '{requirement.parsed_detail.parameter_name}': {compliance_status}")
        return ComplianceResult(
            tender_requirement=requirement,
            retrieved_spec=product_spec,
            compliance_status=compliance_status,
            notes=notes
        )

# --- Module 4: Report Entry Formatter ---
class ReportEntryFormatter:
    """
    Định dạng các kết quả đáp ứng riêng lẻ thành các hàng phù hợp cho bảng PDF cuối cùng.
    """
    def format_entry(self, compliance_result: ComplianceResult) -> Dict[str, str]:
        """
        Định dạng một ComplianceResult duy nhất thành một từ điển đại diện cho một hàng trong bảng báo cáo.
        """
        req = compliance_result.tender_requirement
        spec = compliance_result.retrieved_spec
        
        # Định dạng Hồ sơ tham chiếu
        reference_str = "Không tìm thấy thông tin tham chiếu."
        if spec and spec.reference and spec.reference.document_name != "N/A":
            ref = spec.reference
            section_info = f", {ref.section}" if ref.section else ""
            line_info = f" - {ref.line_or_context}" if ref.line_or_context else ""
            reference_str = f"{ref.document_name}{section_info} - trang {ref.page}{line_info}"

        # Định dạng Thông số kỹ thuật và các tiêu chuẩn của hàng hoá chào trong E-HSDT
        offered_spec_str = ""
        if spec:
            offered_spec_str = f"{spec.parameter_name}: {spec.value}{spec.unit or ''}"
            if spec.condition:
                offered_spec_str += f" ({spec.condition})"
            
            # Thêm ghi chú hoặc lý do trực tiếp vào cột này nếu trạng thái không phải "Đáp ứng" hoàn toàn
            if compliance_result.compliance_status != "Đáp ứng" and compliance_result.notes:
                offered_spec_str += f"\n(Ghi chú: {compliance_result.notes})"
        elif compliance_result.compliance_status == "Không tìm thấy thông tin":
            offered_spec_str = "Không tìm thấy thông tin sản phẩm trong tài liệu cung cấp."
            if compliance_result.notes:
                offered_spec_str += f"\n(Ghi chú: {compliance_result.notes})"
        
        # Điều chỉnh trạng thái hiển thị theo yêu cầu của mẫu: chỉ "Đáp ứng" hoặc "Không đáp ứng"
        display_status = compliance_result.compliance_status
        if display_status == "Đáp ứng một phần":
            display_status = "Không đáp ứng" # Chuyển thành "Không đáp ứng" nếu chỉ đáp ứng một phần
        elif display_status == "Không tìm thấy thông tin":
             display_status = "Không đáp ứng" # Chuyển thành "Không đáp ứng" nếu không tìm thấy thông tin
        
        return {
            "Hạng mục SO": req.item_no,
            "Tên hàng hoá": req.goods_name,
            "Thông số kỹ thuật và các tiêu chuẩn của hàng hoá trong E-HSMT": req.original_text,
            "Thông số kỹ thuật và các tiêu chuẩn của hàng hoá chào trong E-HSDT": offered_spec_str,
            "Hồ sơ tham chiếu": reference_str,
            "Tính đáp ứng của hàng hoá": display_status
        }


# --- Module 5: Final Report Assembler ---
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class FinalReportAssembler:
    """
    Tập hợp báo cáo PDF cuối cùng dựa trên các mục đáp ứng đã định dạng.
    Sao chép cấu trúc của 'Bang Tuyen Bo Dap Ung.R1.pdf'.
    """
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self.styles.add(self.styles['Normal'], 'TitleStyle', fontSize=16, alignment=TA_CENTER, spaceAfter=14, fontName='Helvetica-Bold')
        self.styles.add(self.styles['Normal'], 'HeaderStyle', fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold')
        self.styles.add(self.styles['Normal'], 'BodyStyle', fontSize=8, alignment=TA_LEFT)
        # Để hỗ trợ tiếng Việt trong ReportLab, bạn cần đăng ký font hỗ trợ Unicode
        # Tuy nhiên, điều này phức tạp hơn và không được bao gồm trực tiếp trong ví dụ này.
        # Nếu không, các ký tự tiếng Việt có dấu có thể không hiển thị đúng.

    def generate_pdf_report(self, formatted_entries: List[Dict[str, str]], output_filename: str = "Bảng tuyên bố đáp ứng.pdf"):
        """
        Tạo báo cáo PDF bằng ReportLab.
        """
        filepath = os.path.join(self.output_dir, output_filename)
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []

        # Tiêu đề
        elements.append(Paragraph("BẢNG TUYÊN BỐ ĐÁP ỨNG VỀ KỸ THUẬT", self.styles['TitleStyle']))
        elements.append(Spacer(1, 0.2 * 10))

        # Tiêu đề bảng
        table_headers = [
            Paragraph("Hạng mục SO", self.styles['HeaderStyle']),
            Paragraph("Tên hàng hoá", self.styles['HeaderStyle']),
            Paragraph("Thông số kỹ thuật và các tiêu chuẩn của hàng hoá trong E-HSMT", self.styles['HeaderStyle']),
            Paragraph("Thông số kỹ thuật và các tiêu chuẩn của hàng hoá chào trong E-HSDT", self.styles['HeaderStyle']),
            Paragraph("Hồ sơ tham chiếu", self.styles['HeaderStyle']),
            Paragraph("Tính đáp ứng của hàng hoá", self.styles['HeaderStyle'])
        ]

        # Chuẩn bị dữ liệu bảng
        data = [table_headers]
        for entry in formatted_entries:
            row = [
                Paragraph(entry["Hạng mục SO"], self.styles['BodyStyle']),
                Paragraph(entry["Tên hàng hoá"], self.styles['BodyStyle']),
                Paragraph(entry["Thông số kỹ thuật và các tiêu chuẩn của hàng hoá trong E-HSMT"], self.styles['BodyStyle']),
                Paragraph(entry["Thông số kỹ thuật và các tiêu chuẩn của hàng hoá chào trong E-HSDT"], self.styles['BodyStyle']),
                Paragraph(entry["Hồ sơ tham chiếu"], self.styles['BodyStyle']),
                Paragraph(entry["Tính đáp ứng của hàng hoá"], self.styles['BodyStyle']),
            ]
            data.append(row)

        # Phong cách bảng (có thể điều chỉnh để khớp chính xác với mẫu)
        # Chiều rộng cột được ước tính để khớp với PDF mẫu.
        col_widths = [0.8 * 72, 1.5 * 72, 2.5 * 72, 2.5 * 72, 2.0 * 72, 1.2 * 72] # 1 inch = 72 points
        table = Table(data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('WORDWRAP', (0,0), (-1,-1), True) # Đảm bảo văn bản tự động xuống dòng trong ô
        ]))

        elements.append(table)

        print(f"Đang tạo báo cáo PDF: {filepath}")
        doc.build(elements)
        print("Báo cáo PDF đã tạo thành công.")


# --- Lớp Điều phối chính: ComplianceReportGenerator ---
class ComplianceReportGenerator:
    def __init__(
        self,
        tender_doc_path: str,
        product_doc_paths: List[str],
        llama_parse_api_key: str,
        openai_api_key: str,
        vector_db_persist_dir: str = "./chroma_db"
    ):
        self.tender_doc_path = tender_doc_path
        self.product_doc_paths = product_doc_paths
        
        # Khởi tạo các thành phần cốt lõi
        self.llm = OpenAI(api_key=openai_api_key, model="gpt-4o")
        self.document_preprocessor = DocumentPreprocessor(llama_parse_api_key=llama_parse_api_key)
        self.kb_builder = ProductKnowledgeBaseBuilder(
            openai_api_key=openai_api_key, persist_dir=vector_db_persist_dir
        )
        
        # Khởi tạo các agent
        self.req_extractor = TenderRequirementExtractor(llm=self.llm)
        self.spec_matcher = ProductSpecMatcher(kb_builder=self.kb_builder, llm=self.llm)
        self.compliance_evaluator = ComplianceEvaluator(llm=self.llm)
        self.report_formatter = ReportEntryFormatter()
        self.report_assembler = FinalReportAssembler()

    def run_workflow(self):
        """
        Điều phối toàn bộ Workflow Tài liệu Tác tử để tạo báo cáo đáp ứng.
        """
        print("--- Bắt đầu Workflow Tạo Báo cáo Đáp ứng ---")

        # Bước 1: Xử lý Tài liệu Sản phẩm và Xây dựng Cơ sở Tri thức
        print("\n[Bước 1/5] Đang xử lý tài liệu sản phẩm và xây dựng cơ sở tri thức...")
        product_nodes = self.document_preprocessor.process_documents(self.product_doc_paths)
        self.kb_builder.build_from_nodes(product_nodes)

        # Bước 2: Xử lý Tài liệu Mời thầu và Trích xuất Yêu cầu
        print("\n[Bước 2/5] Đang xử lý tài liệu mời thầu và trích xuất yêu cầu...")
        tender_raw_doc = SimpleDirectoryReader(input_files=[self.tender_doc_path]).load_data()
        tender_parsed_docs = self.document_preprocessor.parser.get_documents(tender_raw_doc)
        
        # Nối tất cả văn bản đã phân tích từ tài liệu mời thầu để trích xuất.
        tender_full_text = "\n".join([doc.text for doc in tender_parsed_docs])
        
        tender_requirements = self.req_extractor.extract_requirements(tender_full_text)
        if not tender_requirements:
            print("Không có yêu cầu nào được trích xuất từ tài liệu mời thầu. Đang hủy bỏ workflow.")
            return

        # Bước 3: Đối sánh Thông số Sản phẩm và Đánh giá Đáp ứng cho từng yêu cầu
        print("\n[Bước 3/5] Đang đối sánh thông số sản phẩm và đánh giá đáp ứng...")
        all_compliance_results: List[ComplianceResult] = []
        for i, req in enumerate(tender_requirements):
            print(f"  Đang xử lý yêu cầu {i+1}/{len(tender_requirements)}: '{req.parsed_detail.parameter_name}'")
            # Điểm Human-in-the-loop 1: Xem xét yêu cầu đã trích xuất nếu độ tin cậy thấp
            
            retrieved_spec = self.spec_matcher.match_and_extract(req)
            # Điểm Human-in-the-loop 2: Xem xét thông số đã truy xuất nếu không tìm thấy hoặc mơ hồ
            
            compliance_result = self.compliance_evaluator.evaluate_compliance(req, retrieved_spec)
            all_compliance_results.append(compliance_result)
            # Điểm Human-in-the-loop 3: Xem xét trạng thái đáp ứng nếu "Không đáp ứng" hoặc "Đáp ứng một phần"

        # Bước 4: Định dạng Kết quả Đáp ứng cho Báo cáo
        print("\n[Bước 4/5] Đang định dạng kết quả đáp ứng cho báo cáo...")
        formatted_report_entries: List[Dict[str, str]] = []
        for result in all_compliance_results:
            formatted_entry = self.report_formatter.format_entry(result)
            formatted_report_entries.append(formatted_entry)

        # Bước 5: Tập hợp và Tạo Báo cáo PDF Cuối cùng
        print("\n[Bước 5/5] Đang tập hợp và tạo báo cáo PDF cuối cùng...")
        self.report_assembler.generate_pdf_report(formatted_report_entries)

        print("\n--- Workflow Tạo Báo cáo Đáp ứng đã Hoàn thành ---")
        print("Kiểm tra thư mục 'reports' để xem PDF đã tạo.")


# --- Khối thực thi chính ---
if __name__ == "__main__":
    # Định nghĩa đường dẫn file dựa trên các file bạn đã tải lên
    # Trong một tình huống thực tế, đây sẽ là đường dẫn file thực tế trên hệ thống.
    TENDER_DOCUMENT = "Chuong V Yeu cau ky thuat.pdf"
    PRODUCT_MANUAL = "NetSure 732_User Manual.pdf"
    PRODUCT_BROCHURE = "NetSure-732 Brochure.pdf"

    # Kiểm tra giả định cho biến môi trường (thay thế bằng khóa API thực của bạn)
    if not OPENAI_API_KEY.startswith("sk-") or not LLAMAPARSE_API_KEY.startswith("lp_"):
        print("CẢNH BÁO: Khóa API OpenAI và/hoặc LlamaParse chưa được đặt hoặc là giá trị giữ chỗ.")
        print("Vui lòng đặt các biến môi trường OPENAI_API_KEY và LLAMAPARSE_API_KEY.")
        # sys.exit(1) # Bỏ comment trong một script thực

    # Khởi tạo và chạy workflow
    generator = ComplianceReportGenerator(
        tender_doc_path=TENDER_DOCUMENT,
        product_doc_paths=[PRODUCT_MANUAL, PRODUCT_BROCHURE],
        llama_parse_api_key=LLAMAPARSE_API_KEY,
        openai_api_key=OPENAI_API_KEY,
        vector_db_persist_dir=VECTOR_DB_PATH
    )
    generator.run_workflow()

