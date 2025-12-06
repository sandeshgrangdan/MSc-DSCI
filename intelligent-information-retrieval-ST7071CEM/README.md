
# 🚀 FastAPI Application – Setup & Run Guide (Using UV)

This project uses **UV** to manage Python environments and dependencies.
Follow the steps below to set up and start the FastAPI server.

---

## 📦 Prerequisites

Before you begin, ensure you have:

* **Python 3.12** installed
* **UV** installed → [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
* (Optional) **curl**, **HTTPie**, or **Postman** for testing the API

---

## 🛠️ Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/sandeshgrangdan/MSc-DSCI.git
```

### 2️⃣ Navigate into the project folder

```bash
cd intelligent-information-retrieval-ST7071CEM
```

### 3️⃣ Create a virtual environment using UV

```bash
uv venv
```

### 4️⃣ Activate the virtual environment

```bash
source .venv/bin/activate
```

### 5️⃣ Install dependencies defined in `pyproject.toml`

```bash
uv sync
```

---

## ▶️ Running the FastAPI Server

To start the FastAPI app (usually `main.py` or `app.py`):

```bash
uv run uvicorn main:app --reload
```

Or, if your file is located elsewhere:

```bash
uv run uvicorn app.main:app --reload
```

The Search Engine will be available at:

```
http://127.0.0.1:8000
```

---

## 📄 Interactive API Docs

FastAPI automatically generates documentation:

* Swagger UI → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc → [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---
