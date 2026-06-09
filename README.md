# 🧠 DocMind — AI Document Intelligence Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-38B2AC?logo=tailwindcss)](https://tailwindcss.com)

> Build intelligent AI chatbots from your documents using Retrieval-Augmented Generation (RAG).

DocMind is a full-stack AI document intelligence platform that transforms documents into intelligent chatbots. Upload files, automatically categorize content, configure chunking and embeddings, connect vector databases, and instantly create AI assistants capable of answering questions using your knowledge base.

---

## 🌟 Overview

DocMind allows users to:

* Upload documents in multiple formats
* Automatically classify content
* Create document-specific AI chatbots
* Configure retrieval settings
* Connect different vector databases
* Select embedding and LLM providers
* Query documents with source citations
* Manage multiple chatbots and knowledge bases

Perfect for:

* 📚 Research Papers
* ⚖️ Legal Documents
* 🏥 Medical Records
* 💰 Financial Reports
* 📰 News Archives
* 📖 Company Knowledge Bases
* 🎓 Educational Materials

---

## ✨ Features

### 📄 Document Processing

Supported Formats:

* PDF
* DOCX
* TXT
* CSV
* XLSX
* JSON
* PPTX
* Markdown (MD)

Features:

* Multi-file upload
* Automatic metadata extraction
* Content indexing
* File management dashboard

---

### 🤖 AI Chatbot Builder

Create a dedicated chatbot for each document.

Supported Chunking Methods:

* Fixed Size Chunking
* Recursive Chunking
* Semantic Chunking
* Graph-Based Chunking

Supported Embedding Models:

* OpenAI Ada-002
* OpenAI text-embedding-3-large
* BAAI BGE-M3
* Cohere Embeddings

Supported LLMs:

* GPT-4o
* Claude 3.5
* Gemini 1.5 Pro
* Llama 3.1

---

### 🗄️ Vector Database Support

Choose your preferred vector store:

* ChromaDB
* Pinecone
* Qdrant
* Weaviate

Each chatbot can use its own vector database configuration.

---

### 🔍 Smart Retrieval

* Source-aware responses
* Chunk citations
* Configurable Top-K retrieval
* Similarity search
* Semantic search

---

### 🧠 Auto Categorization

Documents are automatically classified into:

* Medical
* Legal
* Research
* Financial
* Political
* News
* Education
* Other

---

### 👤 User Management

Subscription Tiers:

| Plan       | Storage  | Chatbots  |
| ---------- | -------- | --------- |
| Free       | Limited  | Limited   |
| Pro        | Extended | More Bots |
| Enterprise | Custom   | Unlimited |

Features:

* JWT Authentication
* API Key Management
* User Dashboard
* Usage Analytics

---

### 📊 Dashboard

Track:

* Uploaded files
* Storage consumption
* Chatbot statistics
* Processing progress
* API usage

---

### ⚙️ Advanced RAG Configuration

Per-chatbot settings:

* Chunk Size
* Chunk Overlap
* Embedding Model
* LLM Selection
* Temperature
* Top-K Retrieval
* Vector Store Selection

---

## 🏗️ Architecture

```text
Document Upload
      │
      ▼
Document Processing
      │
      ▼
Auto Categorization
      │
      ▼
Chunking Strategy
      │
      ▼
Embeddings
      │
      ▼
Vector Database
      │
      ▼
RAG Retrieval
      │
      ▼
AI Chatbot
```

---

# 🛠 Technology Stack

| Layer          | Technology                         |
| -------------- | ---------------------------------- |
| Backend        | FastAPI                            |
| Language       | Python 3.10+                       |
| ORM            | SQLAlchemy                         |
| Validation     | Pydantic                           |
| Authentication | JWT + bcrypt                       |
| Database       | SQLite / PostgreSQL                |
| Frontend       | HTML5                              |
| Styling        | Tailwind CSS                       |
| JavaScript     | Vanilla JS                         |
| Vector DB      | Chroma, Pinecone, Weaviate, Qdrant |
| AI Providers   | OpenAI, Anthropic, Google, Cohere  |

---

# 🚀 Quick Start

## Prerequisites

Install:

* Python 3.10+
* pip
* Git

---

## 1️⃣ Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/docmind.git

cd docmind
```

---

## 2️⃣ Create Virtual Environment

### Linux / macOS

```bash
python -m venv venv

source venv/bin/activate
```

### Windows

```powershell
python -m venv venv

venv\Scripts\activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Configure Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-super-secure-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

DATABASE_URL=sqlite:///./docmind.db

UPLOAD_DIR=uploads

MAX_FILE_SIZE_MB=50
```

### Important

Never use the default secret key in production.

Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## 5️⃣ Run Application

### Standard Run

```bash
python main.py
```

### Uvicorn Development Mode

```bash
uvicorn main:app --reload --port 8000
```

---

## 6️⃣ Open Application

Visit:

```text
http://localhost:8000
```

Workflow:

1. Register an account
2. Upload a document
3. Wait for processing
4. Create a chatbot
5. Ask questions
6. View citations

---

# 📁 Project Structure

```text
docmind/
│
├── main.py
├── requirements.txt
├── .env
├── docmind.db
│
├── uploads/
├── vectorstore/
│
├── app/
│   ├── config.py
│   ├── database.py
│   ├── auth.py
│   ├── schemas.py
│   │
│   └── routers/
│       ├── auth.py
│       ├── files.py
│       ├── chatbots.py
│       └── users.py
│
├── static/
│   ├── js/
│   │   └── api.js
│   │
│   └── pages/
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html
│       ├── chatbots.html
│       └── user.html
│
└── README.md
```

---

# 🔌 API Endpoints

### Authentication

| Method | Endpoint             |
| ------ | -------------------- |
| POST   | `/api/auth/register` |
| POST   | `/api/auth/login`    |
| POST   | `/api/auth/logout`   |
| GET    | `/api/auth/me`       |

### File Management

| Method | Endpoint                   |
| ------ | -------------------------- |
| POST   | `/api/files/upload`        |
| GET    | `/api/files`               |
| PATCH  | `/api/files/{id}/category` |
| DELETE | `/api/files/{id}`          |

### Chatbots

| Method | Endpoint                     |
| ------ | ---------------------------- |
| POST   | `/api/chatbots`              |
| GET    | `/api/chatbots`              |
| POST   | `/api/chatbots/{id}/chat`    |
| GET    | `/api/chatbots/{id}/history` |
| DELETE | `/api/chatbots/{id}/history` |

### User Management

| Method | Endpoint                 |
| ------ | ------------------------ |
| GET    | `/api/users/me/stats`    |
| GET    | `/api/users/me/api-keys` |
| POST   | `/api/users/me/api-keys` |
| DELETE | `/api/users/me`          |

---

# 📖 API Documentation

Swagger UI:

```text
http://localhost:8000/api/docs
```

Interactive API testing is available directly through Swagger.

---

# 🧪 Real RAG Integration

The current implementation includes a demonstration RAG pipeline.

To enable production-grade RAG:

Install:

```bash
pip install langchain langchain-openai chromadb
```

Possible Integrations:

* LangChain
* LlamaIndex
* ChromaDB
* Pinecone
* Qdrant
* Weaviate

Supported Providers:

* OpenAI
* Anthropic
* Google Gemini
* Cohere
* Local LLMs via Ollama

---

# 📦 Deployment

Deploy on:

* Railway
* Render
* DigitalOcean
* AWS EC2
* VPS Servers
* Docker

### Production Start Script

```bash
#!/bin/bash

uvicorn main:app \
  --host 0.0.0.0 \
  --port $PORT \
  --workers 2
```

---

# 🔒 Production Checklist

Before deploying:

* Use PostgreSQL instead of SQLite
* Configure HTTPS
* Generate secure SECRET_KEY
* Enable backups
* Configure Nginx
* Enable rate limiting
* Configure monitoring

---

# ⚡ Roadmap

### Upcoming Features

* Multi-document chatbots
* GraphRAG integration
* Public chatbot sharing
* Slack integration
* Discord integration
* Teams integration
* PDF citation viewer
* User analytics dashboard
* Fine-tuned retrieval settings
* Local LLM support via Ollama

---

# 🤝 Contributing

Contributions are welcome.

```bash
# Fork repository

git checkout -b feature/amazing-feature

git commit -m "Add amazing feature"

git push origin feature/amazing-feature
```

Then create a Pull Request.

---

# 📄 License

Licensed under the MIT License.

You are free to use, modify, and distribute this software.

---

# 🙏 Acknowledgements

Special thanks to:

* FastAPI
* Tailwind CSS
* LangChain
* LlamaIndex
* OpenAI
* Anthropic
* Google Gemini
* Cohere
* ChromaDB

---

## 🚀 Build AI-Powered Knowledge Assistants From Any Document

Transform static documents into intelligent conversational experiences with DocMind.
