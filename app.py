"""
DocuSummarize - PDF Summarizer API
FastAPI backend service for PDF upload, processing, and AI-powered summarization
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from pathlib import Path
from dotenv import load_dotenv
import shutil
import tempfile
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="DocuSummarize - PDF Summarizer API",
    description="AI-powered PDF document summarization using LangChain, FastAPI, and LLMs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables!")

llm = ChatGroq(
    model="mixtral-8x7b-32768",
    groq_api_key=api_key,
    temperature=0.3,
    max_tokens=1024
)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Text splitter configuration
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", " ", ""]
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Pydantic models
class SummaryResponse(BaseModel):
    """Response model for summarization"""
    filename: str
    total_pages: int
    total_chunks: int
    summary: str
    status: str = "success"


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str


# Utility functions
def extract_text_from_pdf(file_path: str) -> tuple[list, int]:
    """
    Extract text from PDF file using LangChain
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Tuple of (list of text chunks, number of pages)
    """
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        total_pages = len(docs)
        
        # Split documents into chunks
        chunks = text_splitter.split_documents(docs)
        
        return chunks, total_pages
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")


def generate_summary(documents: list, summary_type: str = "map_reduce") -> str:
    """
    Generate summary using LLM
    
    Args:
        documents: List of document chunks
        summary_type: Type of summarization chain to use
        
    Returns:
        Generated summary text
    """
    try:
        if not documents:
            raise ValueError("No documents to summarize")
        
        # Define prompt template for summarization
        prompt_template = """
        Please provide a comprehensive and concise summary of the following text.
        Focus on key points, main ideas, and important information.
        Make the summary informative yet easy to understand.
        
        Text:
        {text}
        
        Summary:
        """
        
        # Combine document contents
        combined_text = "\n\n".join([doc.page_content for doc in documents[:10]])  # Use first 10 chunks for summary
        
        if len(combined_text) > 8000:  # Limit token count
            combined_text = combined_text[:8000]
        
        # Create the prompt
        system_msg = SystemMessage(content="You are an expert at summarizing documents. Provide clear, concise, and informative summaries.")
        human_msg = HumanMessage(content=prompt_template.format(text=combined_text))
        
        result = llm.invoke([system_msg, human_msg])
        
        return result.content if hasattr(result, 'content') else str(result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


# API Routes

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.post("/summarize", response_model=SummaryResponse)
async def summarize_pdf(
    file: UploadFile = File(...),
    summary_type: Optional[str] = "map_reduce"
):
    """
    Upload PDF file and get summarization
    
    Args:
        file: PDF file to upload
        summary_type: Type of summarization ("map_reduce", "stuff", "refine")
        
    Returns:
        SummaryResponse with filename, pages, chunks, and summary
    """
    
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    temp_file_path = None
    
    try:
        # Save uploaded file to temporary location
        temp_file_path = UPLOAD_DIR / file.filename
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Step 1: Extract text from PDF
        documents, total_pages = extract_text_from_pdf(str(temp_file_path))
        total_chunks = len(documents)
        
        if total_chunks == 0:
            raise HTTPException(status_code=400, detail="No text found in PDF")
        
        # Step 2: Generate summary
        summary = generate_summary(documents, summary_type)
        
        return SummaryResponse(
            filename=file.filename,
            total_pages=total_pages,
            total_chunks=total_chunks,
            summary=summary,
            status="success"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_file_path}: {e}")


@app.post("/summarize-detailed")
async def summarize_pdf_detailed(
    file: UploadFile = File(...),
    summary_type: Optional[str] = "map_reduce",
    include_chunks: bool = False
):
    """
    Advanced summarization endpoint with optional chunk details
    
    Args:
        file: PDF file to upload
        summary_type: Summarization chain type
        include_chunks: Whether to include individual chunk summaries
        
    Returns:
        Detailed summary with optional chunk information
    """
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    temp_file_path = None
    
    try:
        temp_file_path = UPLOAD_DIR / file.filename
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text
        documents, total_pages = extract_text_from_pdf(str(temp_file_path))
        total_chunks = len(documents)
        
        if total_chunks == 0:
            raise HTTPException(status_code=400, detail="No text found in PDF")
        
        # Generate summary
        summary = generate_summary(documents, summary_type)
        
        response = {
            "filename": file.filename,
            "total_pages": total_pages,
            "total_chunks": total_chunks,
            "summary": summary,
            "status": "success"
        }
        
        # Include chunk details if requested
        if include_chunks:
            response["chunks"] = [
                {
                    "id": idx,
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "source": doc.metadata.get("source", "unknown")
                }
                for idx, doc in enumerate(documents[:10])  # Limit to first 10 for performance
            ]
        
        return JSONResponse(response)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as e:
                print(f"Warning: Could not delete temp file: {e}")


@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "name": "DocuSummarize - PDF Summarizer API",
        "version": "1.0.0",
        "description": "AI-powered PDF document summarization using FastAPI and LangChain",
        "endpoints": {
            "health": "/health",
            "summarize": "/summarize (POST)",
            "summarize-detailed": "/summarize-detailed (POST)",
            "docs": "/docs"
        }
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status": "error"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status": "error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
