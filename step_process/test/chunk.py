import os
from llama_index.core import SimpleDirectoryReader, Settings
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
print("Đã cấu hình LLM...")

reader = SimpleDirectoryReader(input_files=["D:\\study\\LammaIndex\\data\\NetSure_732_User_Manual.md"])
documents = reader.load_data(show_progress=True)

parser = MarkdownNodeParser(include_metadata=True, include_prev_next_rel=True)
nodes = parser.get_nodes_from_documents(documents)
# print("2312412: ", nodes)

# Ghi các chunk ra file markdown
output_file = "D:\\study\\LammaIndex\\output\\chunk\\chunks_NetSure_732_User_Manual.md"
with open(output_file, "w", encoding="utf-8") as f:
    for idx, node in enumerate(nodes, start=1):
        f.write(f"# Chunk {idx}\n")
        f.write(node.text + "\n\n\n\n")

print(f"Đã ghi {len(nodes)} chunk vào {output_file}")