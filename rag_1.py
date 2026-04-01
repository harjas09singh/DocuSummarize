"""
RAG (Retrieval-Augmented Generation) Utility Module
Handles PDF loading, embeddings, and vector store operations for semantic search
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document

load_dotenv()


class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline for document processing and semantic search
    """
    
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "documents",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize RAG Pipeline
        
        Args:
            qdrant_url: Qdrant vector store URL
            collection_name: Collection name in Qdrant
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize LLM
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables!")
        
        self.llm = ChatGroq(
            model="mixtral-8x7b-32768",
            groq_api_key=api_key,
            temperature=0.3,
            max_tokens=1024
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize vector store
        try:
            self.vector_store = QdrantVectorStore.from_existing_collection(
                url=qdrant_url,
                collection_name=collection_name,
                embedding=self.embeddings
            )
        except Exception as e:
            print(f"Warning: Could not connect to Qdrant: {e}")
            self.vector_store = None
    
    def load_pdf(self, file_path: str) -> tuple[List[Document], int]:
        """
        Load PDF file and extract documents
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (documents, total_pages)
        """
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        return docs, len(docs)
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks
        
        Args:
            documents: List of documents
            
        Returns:
            List of chunked documents
        """
        return self.text_splitter.split_documents(documents)
    
    def add_to_vector_store(self, documents: List[Document]) -> Optional[QdrantVectorStore]:
        """
        Add documents to vector store
        
        Args:
            documents: List of documents to add
            
        Returns:
            Updated vector store or None if connection failed
        """
        if self.vector_store is None:
            print("Vector store not available. Initializing new collection...")
            self.vector_store = QdrantVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings,
                url=self.qdrant_url,
                collection_name=self.collection_name
            )
        else:
            self.vector_store.add_documents(documents)
        
        return self.vector_store
    
    def semantic_search(
        self,
        query: str,
        k: int = 4
    ) -> List[Document]:
        """
        Perform semantic search using vector store
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if self.vector_store is None:
            raise RuntimeError("Vector store not initialized. Connect to Qdrant first.")
        
        return self.vector_store.similarity_search(query, k=k)
    
    def process_pdf_end_to_end(
        self,
        file_path: str,
        query: Optional[str] = None,
        add_to_store: bool = True
    ) -> dict:
        """
        Complete PDF processing pipeline
        
        Args:
            file_path: Path to PDF file
            query: Optional query for semantic search
            add_to_store: Whether to add documents to vector store
            
        Returns:
            Dictionary with processing results
        """
        # Load PDF
        docs, total_pages = self.load_pdf(file_path)
        
        # Chunk documents
        chunks = self.chunk_documents(docs)
        
        # Add to vector store
        if add_to_store:
            self.add_to_vector_store(chunks)
        
        result = {
            "filename": Path(file_path).name,
            "total_pages": total_pages,
            "total_chunks": len(chunks),
            "documents": chunks
        }
        
        # Perform semantic search if query provided
        if query:
            relevant_docs = self.semantic_search(query)
            result["search_query"] = query
            result["relevant_documents"] = relevant_docs
        
        return result


# Example usage
if __name__ == "__main__":
    # Initialize RAG pipeline
    rag = RAGPipeline()
    
    # Process a PDF file
    pdf_file = Path(__file__).parent / "sample.pdf"
    
    if pdf_file.exists():
        # Process PDF
        result = rag.process_pdf_end_to_end(
            file_path=str(pdf_file),
            query="What is the main topic?",
            add_to_store=True
        )
        
        print(f"Processed: {result['filename']}")
        print(f"Pages: {result['total_pages']}")
        print(f"Chunks: {result['total_chunks']}")
        
        if 'relevant_documents' in result:
            print(f"Found {len(result['relevant_documents'])} relevant documents")
    else:
        print(f"Sample PDF not found at {pdf_file}")
