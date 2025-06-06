# Prevención de Riesgos Laborales (Labour Risk Assessment) Course assistant

This repository contains a Retrieval-Augmented Generation (RAG) solution for automatically answering of Prevención de Riesgos Laborales course exam questions via a Gradio UI.

I chose courses from Coformación as they are accesible without a login. There are two types of courses:
- basic (30 hours:) https://cursoriesgoslaborales.com/lecciones/introduccion-al-curso-de-prevencion-de-riesgos-laborales/
- advance (60 hours): https://cursoprl60.com

I followed this project as a reference: https://rafaelviana.com/posts/line-badge 

---

## Setup

1. Create a python environment:
```bash
python -m venv venv
source venv/bin/activate
```
or with anaconda
```bash
conda create -n scrape-labour-risk-assesment-env python=3.11 -y
conda activate scrape-labour-risk-assesment-env
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Install Playwright binaries:
```bash
playwright install
```

## Run the model on Ollama
The project uses a `MODEL` constant, that should match with the model installed on local: `qwen3:14b`:
```bash
ollama run qwen3:14b
```
To use a different Ollama model, replace
> `qwen3:14b` above and update 
> `MODEL = "<your-model-name>"` in the code.

## Set up OpenAI api key
Create a file `.env` and add a key `OPENAI_API_KEY` with you api key from https://openai.com/api/

## Scrape the data from courses

 ```bash
 python scrape_course.py --course basic
 python scrape_course.py --course advanced
 ```

## Launch RAG chain with the Gradio IO
```bash
python llm.py
```

This process builds ChromaDB and sets up the chain.
In the end, it executes demo.launch() to start Gradio interface.

Navigate to http://localhost:8090, paste your exam question + answer choices and click "Respuesta".

## Other
There is a file `calculate_tokens.py` that helps to get total tokens from `knowledge_content` folder, that are used to create embeddings by OpenAIEmbeddings.

```bash
python calculate_tokens.py
```