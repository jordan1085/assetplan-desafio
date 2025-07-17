from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Response(BaseModel):
    data: dict


class TaskResponse(BaseModel):
    message: str
    task_id: str
    
class CollectionBase(BaseModel):
    name: str
    metadata: Optional[Dict[str, Any]] = None

class HNSWConfig(BaseModel):
    """
    Model for HNSW index configuration parameters.
    These defaults provide a good balance for general-purpose use cases,
    especially with text embeddings.
    """
    space: Optional[str] = "cosine"
    ef_construction: Optional[int] = 256
    ef_search: Optional[int] = 128
    max_neighbors: Optional[int] = 32
    num_threads: Optional[int] = None # Let ChromaDB decide based on system resources
    batch_size: Optional[int] = 100
    sync_threshold: Optional[int] = 1000
    resize_factor: Optional[float] = 1.2

class CollectionCreate(CollectionBase):
    embedding_function_name: str = "openai" # e.g., "default", "openai", "cohere"
    hnsw_config: Optional[HNSWConfig] = None # Nested HNSW config

class CollectionResponse(BaseModel):
    message: str
    collection_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class CollectionInfo(BaseModel):
    name: str
    id: str # ChromaDB collection ID is a UUID
    count: int
    metadata: Optional[Dict[str, Any]] = None

class BaseDocumentMetadata(BaseModel):
    user_id: str
    file_id: str = Field(..., description="Unique UUID for the uploaded file.")
    file_name: str
    file_extension: str
    file_size: int = Field(..., description="File size in bytes.")
    file_token_count: int = Field(..., description="Total tokens in the entire document.")

class DocumentBase(BaseModel):
    ids: List[str]
    documents: Optional[List[str]] = None
    metadatas: Optional[List[Dict[str, Any]]] = None
    embeddings: Optional[List[List[float]]] = None

class DocumentAdd(BaseModel):
    collection_name: str
    documents: List[str]
    ids: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None

class DocumentsGetResponse(BaseModel):
    ids: List[str]
    documents: Optional[List[str]] = None
    metadatas: Optional[List[Dict[str, Any]]] = None

class DocumentOperationResponse(BaseModel):
    message: str
    processed_ids: Optional[List[str]] = None

class QueryRequest(BaseModel):
    collection_name: str
    query_texts: List[str]
    n_results: int = 5
    where: Optional[Dict[str, Any]] = None
    where_document: Optional[Dict[str, Any]] = None
    include: List[str] = Field(default_factory=lambda: ["metadatas", "documents", "distances"])
    user_id: Optional[str] = None # For multi-tenancy filtering

class QueryResult(BaseModel):
    ids: List[List[str]]
    distances: Optional[List[List[float]]] = None
    metadatas: Optional[List[List[Optional[Dict[str, Any]]]]] = None
    embeddings: Optional[List[List[Optional[List[float]]]]] = None
    documents: Optional[List[List[Optional[str]]]] = None
    uris: Optional[List[List[Optional[str]]]] = None
    data: Optional[List[List[Any]]] = None # ChromaDB can store raw data

class PeekResponse(BaseModel):
    ids: List[str]
    embeddings: Optional[List[List[float]]] = None
    documents: Optional[List[str]] = None
    metadatas: Optional[List[Dict[str, Any]]] = None

class CountResponse(BaseModel):
    collection_name: str
    count: int

class JobStatusResponse(BaseModel):
    task_id: str
    file_name: str
    total_tokens: Optional[int] = None
    status: str
    error_message: Optional[str] = None