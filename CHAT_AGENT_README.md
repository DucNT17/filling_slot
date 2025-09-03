# Chat Agent với Vector Database

## Tổng quan

Hệ thống Chat Agent này được tích hợp với vector database (Qdrant) để cung cấp khả năng chat thông minh với các tài liệu đã được tải lên. Agent sử dụng LlamaIndex và OpenAI để xử lý câu hỏi và tìm kiếm thông tin liên quan.

## Các thành phần

### 1. ChatAgent Class (`ai_server/chat_agent/chat_agent.py`)

- **Chức năng chính**: Xử lý chat với vector database
- **Tính năng**:
  - Chat đồng bộ và bất đồng bộ
  - Lọc theo product_id, file_id, category
  - Health check
  - Lấy danh sách products có sẵn

### 2. Backend APIs (`backend/app.py`)

#### `/chat` (POST)

- **Mô tả**: Chat với AI agent
- **Parameters**:
  - `question` (required): Câu hỏi của user
  - `collection_name` (optional): Tên collection trong Qdrant
  - `product_ids` (optional): Danh sách product IDs để lọc
  - `file_ids` (optional): Danh sách file IDs để lọc  
  - `categories` (optional): Danh sách categories để lọc

#### `/chat/health` (GET)

- **Mô tả**: Kiểm tra trạng thái của agent
- **Parameters**:
  - `collection_name` (optional): Tên collection

#### `/chat/products` (GET)

- **Mô tả**: Lấy danh sách products có trong vector database
- **Parameters**:
  - `collection_name` (optional): Tên collection

### 3. Frontend Component (`frontend/src/components/KnowledgeChat.tsx`)

- **Giao diện chat**: Chat interface với AI agent
- **Tính năng**:
  - Gửi/nhận tin nhắn
  - Hiển thị tài liệu tham khảo
  - Điều khiển collection name
  - Xóa cuộc trò chuyện
  - Kiểm tra trạng thái agent

## Cài đặt và Chạy

### 1. Cài đặt Dependencies

```bash
# Backend dependencies
pip install -r requirement.txt

# Frontend dependencies
cd frontend
npm install
```

### 2. Cấu hình Environment Variables

Tạo file `.env` với các biến sau:

```env
OPENAI_API_KEY=your_openai_api_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
LLAMA_API_KEY=your_llama_api_key
```

### 3. Khởi chạy Backend

```bash
cd backend
python app.py
```

Backend sẽ chạy tại: <http://localhost:5000>

### 4. Khởi chạy Frontend

```bash
cd frontend
npm run dev
```

Frontend sẽ chạy tại: <http://localhost:5173>

### 5. Test ChatAgent

```bash
cd ai_server/chat_agent
python test_chat_agent.py
```

## Cách sử dụng

### 1. Qua Frontend

1. Mở trình duyệt và truy cập frontend
2. Vào trang "Knowledge Chat"
3. Nhập câu hỏi và nhấn Enter
4. Xem phản hồi và tài liệu tham khảo

### 2. Qua API trực tiếp

```bash
# Test chat API
curl -X POST http://localhost:5000/chat \
  -F "question=Thông tin về sản phẩm NetSure là gì?" \
  -F "collection_name=hello_my_friend"

# Test health check
curl http://localhost:5000/chat/health?collection_name=hello_my_friend

# Test get products
curl http://localhost:5000/chat/products?collection_name=hello_my_friend
```

### 3. Qua Python Code

```python
from ai_server.chat_agent import ChatAgent

# Khởi tạo agent
agent = ChatAgent(collection_name="hello_my_friend")

# Chat đơn giản
response = agent.chat("Thông tin về sản phẩm NetSure?")
print(response['answer'])

# Chat với filter
response = agent.chat(
    "Thông số kỹ thuật?",
    product_ids=["product_1", "product_2"]
)
print(response['answer'])

# Health check
health = agent.health_check()
print(health['status'])
```

## Cấu trúc Response

### Chat Response

```json
{
  "answer": "Câu trả lời từ AI agent",
  "source_documents": [
    {
      "file_name": "NetSure_732_User_Manual",
      "product_name": "NetSure 732",
      "category": "Power System",
      "score": 0.85
    }
  ],
  "question": "Câu hỏi gốc",
  "success": true
}
```

### Health Check Response

```json
{
  "status": "healthy",
  "collection_name": "hello_my_friend",
  "llm_model": "gpt-4o-mini",
  "embed_model": "text-embedding-3-small",
  "message": "Agent is working properly"
}
```

## Troubleshooting

### Lỗi thường gặp

1. **"Cannot connect to Qdrant"**
   - Kiểm tra QDRANT_URL và QDRANT_API_KEY
   - Đảm bảo Qdrant service đang chạy

2. **"OpenAI API error"**
   - Kiểm tra OPENAI_API_KEY
   - Đảm bảo có đủ credits trong tài khoản OpenAI

3. **"Collection not found"**
   - Kiểm tra collection name có tồn tại trong Qdrant
   - Upload dữ liệu trước khi chat

4. **"No relevant documents found"**
   - Kiểm tra dữ liệu đã được upload vào vector database
   - Thử câu hỏi khác hoặc mở rộng phạm vi tìm kiếm

### Debug

1. **Kiểm tra logs**:

   ```bash
   # Backend logs
   tail -f backend.log
   
   # Frontend console
   # Mở Developer Tools trong trình duyệt
   ```

2. **Test từng component**:

   ```bash
   # Test ChatAgent
   cd ai_server/chat_agent && python test_chat_agent.py
   
   # Test API endpoints
   curl http://localhost:5000/chat/health
   ```

## Tính năng mở rộng

### 1. Thêm filters mới

Bạn có thể mở rộng filters trong `ChatAgent.create_filters()`:

```python
def create_filters(self, custom_field: Optional[List[str]] = None):
    filters_list = []
    
    if custom_field:
        filters_list.append(
            MetadataFilter(key="custom_field", operator=FilterOperator.IN, value=custom_field)
        )
    
    # ... existing filters
```

### 2. Thêm response modes

Có thể thêm các response modes khác trong `ChatAgent.__init__()`:

```python
self.query_engine = self.index.as_query_engine(
    similarity_top_k=5,
    response_mode="tree_summarize"  # hoặc "refine", "compact"
)
```

### 3. Thêm memory cho conversation

```python
from llama_index.core.memory import ChatMemoryBuffer

memory = ChatMemoryBuffer.from_defaults(token_limit=1500)
self.chat_engine = self.index.as_chat_engine(
    memory=memory,
    system_prompt="You are a helpful assistant..."
)
```

## Hiệu suất và Tối ưu hóa

### 1. Caching

- Agent instance được cache ở backend
- Có thể thêm Redis cache cho responses

### 2. Batch processing

- Xử lý nhiều queries cùng lúc
- Async processing cho better performance

### 3. Resource management

- Connection pooling cho Qdrant
- Memory management cho large documents

## Bảo mật

### 1. API Security

- Thêm authentication/authorization
- Rate limiting
- Input validation

### 2. Data Privacy

- Encrypt sensitive data
- Audit logs
- Access control

---

**Lưu ý**: Đây là phiên bản beta, có thể có bugs. Vui lòng report issues và feedback để cải thiện!
