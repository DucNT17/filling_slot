from llama_index.readers.file import MarkdownReader
import json

# Khởi tạo reader
reader = MarkdownReader()

# Đọc file markdown
documents = reader.load_data(file="D:\\study\\LammaIndex\\output\\NetSure -731 A41 Brochure.md")

# In nội dung
markdown_text = "\n".join(doc.text for doc in documents)

data = {
    "markdown": markdown_text
}

with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)