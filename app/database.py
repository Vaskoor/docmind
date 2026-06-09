from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import enum
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite only
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_uuid():
    return str(uuid.uuid4())


# ── Enums ────────────────────────────────────────────────────────────────────

class PlanEnum(str, enum.Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"

class FileCategoryEnum(str, enum.Enum):
    medical = "medical"
    legal = "legal"
    research = "research"
    news = "news"
    political = "political"
    financial = "financial"
    other = "other"

class FileStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    error = "error"

class ChunkingEnum(str, enum.Enum):
    fixed = "fixed"
    semantic = "semantic"
    recursive = "recursive"
    graph = "graph"

class EmbeddingEnum(str, enum.Enum):
    openai_ada = "openai-ada-002"
    openai_large = "openai-text-3-large"
    bge_m3 = "bge-m3"
    cohere = "cohere-embed-v3"

class VectorDBEnum(str, enum.Enum):
    chroma = "chroma"
    pinecone = "pinecone"
    weaviate = "weaviate"
    qdrant = "qdrant"

class BotStatusEnum(str, enum.Enum):
    building = "building"
    active = "active"
    error = "error"
    idle = "idle"


# ── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=True)
    plan = Column(String(20), default="free")
    email_notify = Column(Boolean, default=True)
    auto_categorize = Column(Boolean, default=True)
    weekly_digest = Column(Boolean, default=True)
    analytics_opt_in = Column(Boolean, default=False)
    storage_used_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    chatbots = relationship("Chatbot", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="owner", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    @property
    def storage_limit_bytes(self):
        limits = {"free": 5 * 1024**3, "pro": 50 * 1024**3, "enterprise": 500 * 1024**3}
        return limits.get(self.plan, 5 * 1024**3)


class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    original_name = Column(String(500), nullable=False)
    stored_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, csv, docx, etc.
    file_size = Column(Integer, default=0)  # bytes
    category = Column(String(20), default="other")
    status = Column(String(20), default="pending")
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="files")
    chatbots = relationship("Chatbot", back_populates="source_file")


class Chatbot(Base):
    __tablename__ = "chatbots"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    file_id = Column(String, ForeignKey("files.id"), nullable=True)
    name = Column(String(255), nullable=False)
    chunking_strategy = Column(String(20), default="fixed")
    chunk_size = Column(Integer, default=512)
    chunk_overlap = Column(Integer, default=64)
    embedding_model = Column(String(50), default="openai-ada-002")
    vector_db = Column(String(20), default="chroma")
    llm_model = Column(String(50), default="gpt-4o-mini")
    top_k = Column(Integer, default=5)
    temperature = Column(Float, default=0.3)
    status = Column(String(20), default="building")
    total_queries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="chatbots")
    source_file = relationship("File", back_populates="chatbots")
    messages = relationship("ChatMessage", back_populates="chatbot", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    chatbot_id = Column(String, ForeignKey("chatbots.id"), nullable=False)
    role = Column(String(10), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON string of source chunks
    created_at = Column(DateTime, default=datetime.utcnow)

    chatbot = relationship("Chatbot", back_populates="messages")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(20), nullable=False)   # shown in UI
    hashed_key = Column(String(255), nullable=False)  # stored securely
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="api_keys")


def create_tables():
    Base.metadata.create_all(bind=engine)
