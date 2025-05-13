from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
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

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
OUTPUT_DIR = Path("cursoriesgoslaborales/texts")
MODEL = "qwen3:14b"
db_name = "vector_db_courses"

def add_metadata(doc, doc_type):
    doc.metadata["doc_type"] = doc_type
    return doc


files = glob.glob(f'{OUTPUT_DIR}/*')
documents = []

for file in files:
    doc_type = os.path.basename(file)
    loader = TextLoader(f'{OUTPUT_DIR}/{doc_type}')
    file_docs = loader.load()
    documents.extend([add_metadata(doc, doc_type) for doc in file_docs])

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
chunks = text_splitter.split_documents(documents)
print(f"Prepared {len(chunks)} chunks.")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    chunk_size=200,
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

messages = [("system", SYSTEM_PROMPT),("human",
                                        "[Contexto] \n{context}\n\n"
                                        "[Pregunta] \n{question}\n\n"
                                        "Primero, enumera brevemente los pasos del pensamiento y luego da tu respuesta")]

prompt = ChatPromptTemplate.from_messages(messages)
llm = OllamaLLM(model=MODEL, temperature=0.0)
retriever = vectorstore.as_retriever(search_kwargs={"k":6})
chain = ConversationalRetrievalChain.from_llm(llm, retriever=retriever, combine_docs_chain_kwargs={"prompt": prompt})

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
