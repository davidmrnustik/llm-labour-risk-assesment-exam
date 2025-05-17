from pathlib import Path
import glob
import tiktoken
import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader

# This code counts how many tokens documents contain
OUTPUT_DIR = Path("knowledge_content")

encoding = tiktoken.encoding_for_model("text-embedding-3-small")
folders = glob.glob(f"{OUTPUT_DIR}/*")
stats = []

for folder in folders:
    doc_type = os.path.basename(folder)
    loader = DirectoryLoader(folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
    folder_docs = loader.load()
    tokens_sum = 0
    for doc in folder_docs:
        content = doc.page_content
        source = doc.metadata["source"]
        tokens = encoding.encode(content)
        tokens_sum += len(tokens)
        stats.append({"source": source, "tokens": len(tokens)})


print(stats)
print(f"Total tokens: {tokens_sum}")