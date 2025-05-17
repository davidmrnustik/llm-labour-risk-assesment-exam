from pathlib import Path
import glob
import tiktoken
import os
from langchain_community.document_loaders import TextLoader

# This code counts how many tokens documents contain
OUTPUT_DIR = Path("knowledge_content")
TEXT_DIR = OUTPUT_DIR / "texts"

encoding = tiktoken.encoding_for_model("text-embedding-3-small")
files = glob.glob(f"{TEXT_DIR}/*")
stats = []

for file in files:
    filename = os.path.basename(file)
    loader = TextLoader(f"{TEXT_DIR}/{filename}")
    file_docs = loader.load()
    content = ""
    for doc in file_docs:
        content = doc.page_content

    tokens = encoding.encode(content)
    stats.append({"filename": filename, "tokens": len(tokens)})

print(stats)
