from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import ChatPromptTemplate
from pathlib import Path
import os
import glob
from system_prompt import SYSTEM_PROMPT
from langchain_ollama import OllamaLLM
import gradio as gr

# Load environment variables
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
OUTPUT_DIR = Path("knowledge_content/texts")
MODEL = "qwen3:14b" # Running in ollama on local
db_name = "vector_db_courses"

def add_metadata(doc, doc_type):
    doc.metadata["doc_type"] = doc_type
    return doc

# Get a list of all folder from the directory
# Those are results from scraping course material (scrape_course.py)
folders = glob.glob(f'{OUTPUT_DIR}/*')
documents = []

# Read files by TextLoader and store them into a list of texts
# loader_cls: Loader class to use for loading files
for folder in folders:
    doc_type = os.path.basename(folder)
    loader = DirectoryLoader(folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
    folder_docs = loader.load()
    documents.extend([add_metadata(doc, doc_type) for doc in folder_docs])

# Split raw documents into chunks by 1000 - roughly 250-300 tokens
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
chunks = text_splitter.split_documents(documents)
print(f"Prepared {len(chunks)} chunks.")

# Using OpenAI text-embedding-3-small model for embeddings, $0.02/1M tokens
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    chunk_size=200, # Maximum number of texts to embed in each batch
    api_key=openai_api_key)

# Rebuild the vector DB
if os.path.exists(db_name):
    Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=db_name
)
print(f"Vector database ready with {vectorstore._collection.count()} chunks.")

# Placeholders for retrieval context
messages = [("system", SYSTEM_PROMPT),("human",
                                        "[Contexto] \n{context}\n\n"
                                        "[Pregunta] \n{question}\n\n"
                                        "Primero, enumera brevemente los pasos del pensamiento y luego da tu respuesta")]

prompt = ChatPromptTemplate.from_messages(messages)

# Increasing the temperature will make the model answer more creatively.
llm = OllamaLLM(model=MODEL, temperature=0.0)

# Wraps ChromaDB vector store
retriever = vectorstore.as_retriever(search_kwargs={"k":6}) # k: Amount of documents to return

# Put everything together
chain = ConversationalRetrievalChain.from_llm(llm, retriever=retriever, combine_docs_chain_kwargs={"prompt": prompt})

# Test question
# question = "Cual son las referencias legales en que está basada la normativa de prevención de riesgos laborales?"
# response = chain({"question": question, "chat_history": []})

def answer_question(user_input):
    if not user_input.strip():
        return "Por favor, introduzca su pregunta"
    result = chain.invoke({
        "question": user_input,
        "chat_history": []
    })
    return result["answer"]

# UI to paste questions
with gr.Blocks() as demo:
    gr.Markdown("Asistente de prueba del curso de Prevención de Riesgos Laborales")
    inputs = gr.Textbox(
        label="Introduzca las opciones de pregunta y respuesta",
        placeholder="Introduzca la pregunta y cuatro opciones aquí",
        lines=8
    )
    outputs = gr.Textbox(label="Respuesta", lines=6, interactive=False)
    btn = gr.Button("Respuesta")
    btn.click(answer_question, inputs=inputs, outputs=outputs).then(lambda : "", None, inputs)
    demo.queue()

if __name__ == '__main__':
    demo.launch(server_name="0.0.0.0", server_port=7860)
