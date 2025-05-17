# Prevención de Riesgos Laborales (Labour Risk Assessment) Course assistant

This repository contains a Retrieval-Augmented Generation (RAG) solution for automatically answering of Prevención de Riesgos Laborales course exam questions via a Gradio UI.

I chose courses from Coformación as they are accesible without a login. There are two types of courses:
- basic (30 hours:) https://cursoriesgoslaborales.com/lecciones/introduccion-al-curso-de-prevencion-de-riesgos-laborales/
- advance (60 hours): https://cursoprl60.com

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

## Scrape the data from LINE Campus

You’ll need your LINE Business ID and saved cookies to pull down the official exam content:

### Save your cookies
1. **Run and login**
    ```bash
    python save_cookies.py 
    ```

2. **Scrape each course’s questions**
    ```bash
    python scrape_course.py --course basic
    python scrape_shiken.py --course advanced
    ```