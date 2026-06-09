from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ── Auth Schemas ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str
    organization: Optional[str] = None
    plan: str = "free"

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("plan")
    @classmethod
    def valid_plan(cls, v):
        if v not in ["free", "pro", "enterprise"]:
            raise ValueError("Invalid plan")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    organization: Optional[str]
    plan: str
    initials: str
    storage_used_bytes: int
    storage_limit_bytes: int
    email_notify: bool
    auto_categorize: bool
    weekly_digest: bool
    analytics_opt_in: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class UpdatePreferencesRequest(BaseModel):
    email_notify: Optional[bool] = None
    auto_categorize: Optional[bool] = None
    weekly_digest: Optional[bool] = None
    analytics_opt_in: Optional[bool] = None


# ── File Schemas ─────────────────────────────────────────────────────────────

class FileResponse(BaseModel):
    id: str
    original_name: str
    file_type: str
    file_size: int
    category: str
    status: str
    chunk_count: int
    uploaded_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class UpdateFileCategoryRequest(BaseModel):
    category: str

    @field_validator("category")
    @classmethod
    def valid_category(cls, v):
        valid = ["medical", "legal", "research", "news", "political", "financial", "other"]
        if v not in valid:
            raise ValueError(f"Category must be one of {valid}")
        return v


# ── Chatbot Schemas ───────────────────────────────────────────────────────────

class BuildChatbotRequest(BaseModel):
    file_id: str
    name: str
    chunking_strategy: str = "fixed"
    chunk_size: int = 512
    chunk_overlap: int = 64
    embedding_model: str = "openai-ada-002"
    vector_db: str = "chroma"
    llm_model: str = "gpt-4o-mini"
    top_k: int = 5
    temperature: float = 0.3

    @field_validator("chunking_strategy")
    @classmethod
    def valid_chunking(cls, v):
        if v not in ["fixed", "semantic", "recursive", "graph"]:
            raise ValueError("Invalid chunking strategy")
        return v

    @field_validator("chunk_size")
    @classmethod
    def valid_chunk_size(cls, v):
        if not (64 <= v <= 4096):
            raise ValueError("Chunk size must be between 64 and 4096")
        return v

    @field_validator("temperature")
    @classmethod
    def valid_temperature(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v


class UpdateChatbotRequest(BaseModel):
    name: Optional[str] = None
    chunking_strategy: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    embedding_model: Optional[str] = None
    vector_db: Optional[str] = None
    llm_model: Optional[str] = None
    top_k: Optional[int] = None
    temperature: Optional[float] = None


class ChatbotResponse(BaseModel):
    id: str
    name: str
    file_id: Optional[str]
    chunking_strategy: str
    chunk_size: int
    chunk_overlap: int
    embedding_model: str
    vector_db: str
    llm_model: str
    top_k: int
    temperature: float
    status: str
    total_queries: int
    created_at: datetime
    source_file: Optional[FileResponse] = None

    class Config:
        from_attributes = True


# ── Chat Schemas ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[dict]] = []

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []
    tokens_used: int = 0


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── API Key Schemas ────────────────────────────────────────────────────────────

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CreateAPIKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # full key, only shown once
    key_prefix: str
    created_at: datetime


# ── Stats Schema ──────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_files: int
    active_chatbots: int
    total_chunks: int
    storage_used_bytes: int
    storage_limit_bytes: int
    storage_used_gb: float
    files_by_category: dict
    files_by_type: dict
