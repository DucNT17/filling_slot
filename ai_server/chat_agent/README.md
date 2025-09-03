# Chat Agent Module

## Tổng quan

Module Chat Agent cung cấp khả năng chat thông minh với vector database sử dụng LlamaIndex và OpenAI.

## Cấu trúc Module

```
ai_server/chat_agent/
├── __init__.py              # Module initialization
├── chat_agent.py           # Main ChatAgent class
├── test_chat_agent.py      # Test script
└── README.md              # This file
```

## Sử dụng

### Import ChatAgent

```python
from ai_server.chat_agent import ChatAgent

# Khởi tạo agent
agent = ChatAgent(collection_name="hello_my_friend")

# Chat với agent
response = agent.chat("Câu hỏi của bạn?")
print(response['answer'])
```

### Chạy Test

```bash
cd ai_server/chat_agent
python test_chat_agent.py
```

## API Reference

### ChatAgent Class

#### `__init__(collection_name, llm_model)`

- `collection_name`: Tên collection trong Qdrant
- `llm_model`: Model LLM (default: "gpt-4o-mini")

#### `chat(question, product_ids, file_ids, categories)`

- **Sync method** để chat với agent
- Returns: Dict với answer, source_documents, success

#### `chat_async(question, product_ids, file_ids, categories)`  

- **Async method** để chat với agent
- Returns: Dict với answer, source_documents, success

#### `health_check()`

- Kiểm tra trạng thái agent
- Returns: Dict với status, message

#### `get_available_products()`

- Lấy danh sách products trong vector database
- Returns: List các products

#### `create_filters(product_ids, file_ids, categories)`

- Tạo filters để lọc dữ liệu
- Returns: MetadataFilters object

## Dependencies

- llama_index
- openai
- qdrant-client
- python-dotenv

## Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key
QDRANT_URL=your_qdrant_url  
QDRANT_API_KEY=your_qdrant_api_key
```

## Examples

### Basic Chat

```python
from ai_server.chat_agent import ChatAgent

agent = ChatAgent()
response = agent.chat("Thông tin sản phẩm NetSure?")

if response['success']:
    print("Answer:", response['answer'])
    print("Sources:", len(response['source_documents']))
else:
    print("Error:", response['error'])
```

### Chat với Filters

```python
response = agent.chat(
    "Thông số kỹ thuật?",
    product_ids=["product_1", "product_2"],
    categories=["Power System"]
)
```

### Async Chat

```python
import asyncio

async def main():
    agent = ChatAgent()
    response = await agent.chat_async("Câu hỏi?")
    print(response['answer'])

asyncio.run(main())
```

## Error Handling

```python
try:
    response = agent.chat("Câu hỏi")
    if not response['success']:
        print(f"Error: {response['error']}")
except Exception as e:
    print(f"Exception: {e}")
```
