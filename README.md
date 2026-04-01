# DocuSummarize - PDF Summarizer API

## Overview

**DocuSummarize** is a powerful FastAPI-based backend service for PDF document processing and AI-powered summarization. It leverages modern LLMs, LangChain, and vector databases to provide intelligent document analysis and concise summary generation.

### Key Features

✨ **PDF Upload & Processing** - Seamless document ingestion with validation
✨ **Intelligent Text Extraction** - LangChain-based PDF parsing and preprocessing
✨ **AI-Powered Summarization** - LLM-driven summaries with prompt engineering
✨ **Scalable Architecture** - Built on FastAPI for high-performance async processing
✨ **RESTful API** - Clean, well-documented endpoints with Swagger UI
✨ **Error Handling** - Comprehensive exception handling and validation
✨ **Vector Storage** - Optional Qdrant integration for semantic search and RAG

---

## Technology Stack

- **Framework**: FastAPI
- **LLM**: Groq (Mixtral 8x7B)
- **Document Processing**: LangChain
- **Embeddings**: HuggingFace Sentence Transformers
- **Vector Store**: Qdrant (optional)
- **Server**: Uvicorn
- **Language**: Python 3.10+

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Groq API Key (get it from [console.groq.com](https://console.groq.com))
- pip or conda package manager

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/docusummarize.git
cd docusummarize
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

5. **Run the application**
```bash
python app.py
```

The API will be available at `http://localhost:8000`

---

## API Endpoints

### 1. Health Check
```bash
GET /health
```
Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Summarize PDF
```bash
POST /summarize
```
Upload a PDF file and get AI-generated summary.

**Parameters:**
- `file` (file, required): PDF file to summarize
- `summary_type` (string, optional): "map_reduce" (default), "stuff", or "refine"

**Response:**
```json
{
  "filename": "document.pdf",
  "total_pages": 15,
  "total_chunks": 45,
  "summary": "This document discusses...",
  "status": "success"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/summarize" \
  -H "accept: application/json" \
  -F "file=@document.pdf"
```

### 3. Detailed Summarization
```bash
POST /summarize-detailed
```
Advanced endpoint with optional chunk details.

**Parameters:**
- `file` (file, required): PDF file
- `summary_type` (string, optional): Summarization strategy
- `include_chunks` (boolean, optional): Include chunk details in response

**Response:**
```json
{
  "filename": "document.pdf",
  "total_pages": 15,
  "total_chunks": 45,
  "summary": "...",
  "chunks": [
    {
      "id": 0,
      "content": "First 200 characters of chunk...",
      "source": "document.pdf"
    }
  ],
  "status": "success"
}
```

---

## Processing Workflow

```
PDF Upload
    ↓
File Validation
    ↓
Text Extraction (PyPDFLoader)
    ↓
Document Chunking (RecursiveCharacterTextSplitter)
    ↓
Preprocessing & Cleaning
    ↓
Embeddings Generation (HuggingFace)
    ↓
LLM Summarization (Groq)
    ↓
Response Delivery
```

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM access | ✅ Yes |
| `QDRANT_URL` | Qdrant vector store URL | ❌ No |
| `QDRANT_COLLECTION_NAME` | Qdrant collection name | ❌ No |
| `GEMINI_API_KEY` | Google Gemini API (alternative LLM) | ❌ No |
| `SERVER_HOST` | Uvicorn host (default: 0.0.0.0) | ❌ No |
| `SERVER_PORT` | Uvicorn port (default: 8000) | ❌ No |

---

## Usage Examples

### Python Using Requests
```python
import requests

url = "http://localhost:8000/summarize"
files = {"file": open("document.pdf", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

### JavaScript/Node.js
```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

fetch("http://localhost:8000/summarize", {
  method: "POST",
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

### Interactive API Documentation
Open your browser and navigate to:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Performance Optimization

### Chunking Strategy
The system uses `RecursiveCharacterTextSplitter` with:
- Chunk size: 1000 tokens
- Overlap: 200 tokens
- Separators: "\n\n", "\n", " ", ""

### Summarization Methods
- **map_reduce** (default): Best for large documents, splits into chunks and summarizes each
- **stuff**: Simpler method, fits all text in one prompt (good for small docs)
- **refine**: Iterative refinement, best for detailed summaries

---

## Troubleshooting

### Issue: "GROQ_API_KEY not found"
**Solution**: Ensure `.env` file exists with valid Groq API key
```bash
cp .env.example .env
# Edit .env and add your key
```

### Issue: PDF Processing Fails
**Possible causes:**
- Corrupted PDF file
- PDF is image-based (scanned document)
- Insufficient permissions to read file

### Issue: Slow Summarization
**Solutions:**
- Use smaller PDFs for testing
- Adjust chunk size in configuration
- Use faster LLM model (e.g., "gemma-7b-it")

---

## Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application              │
│  ┌───────────────────────────────────┐   │
│  │     PDF Upload Endpoint            │   │
│  │  ┌──────────────────────────────┐ │   │
│  │  │   File Validation            │ │   │
│  │  │   Temporary Storage          │ │   │
│  │  └──────────────────────────────┘ │   │
│  └───────────────────────────────────┘   │
│                ↓                         │
│  ┌───────────────────────────────────┐   │
│  │   Text Extraction Pipeline       │   │
│  │  ┌──────────────────────────────┐ │   │
│  │  │  LangChain PyPDFLoader       │ │   │
│  │  │  Document Preprocessing      │ │   │
│  │  │  Text Splitting              │ │   │
│  │  └──────────────────────────────┘ │   │
│  └───────────────────────────────────┘   │
│                ↓                         │
│  ┌───────────────────────────────────┐   │
│  │   LLM Processing Pipeline        │   │
│  │  ┌──────────────────────────────┐ │   │
│  │  │  Embeddings Generation       │ │   │
│  │  │  Prompt Engineering          │ │   │
│  │  │  LLM Chain Execution         │ │   │
│  │  └──────────────────────────────┘ │   │
│  └───────────────────────────────────┘   │
│                ↓                         │
│  ┌───────────────────────────────────┐   │
│  │   Response Formatting            │   │
│  │   (JSON with Summary)             │   │
│  └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see LICENSE file for details.

---

## Support

For questions or issues:
- 📧 Email: support@docusummarize.com
- 🐛 GitHub Issues: [Report Bug](https://github.com/yourusername/docusummarize/issues)
- 📚 Documentation: [Full Docs](https://docusummarize.readthedocs.io)

---

## Acknowledgments

- **LangChain** - Document processing framework
- **FastAPI** - Modern web framework
- **Groq** - Fast LLM API
- **HuggingFace** - Embedding models
- **Qdrant** - Vector database

---

**Made with ❤️ by the DocuSummarize Team**
