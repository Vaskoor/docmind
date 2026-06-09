from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
import random
from datetime import datetime

from app.database import get_db, User, Chatbot, ChatMessage, File as FileModel
from app.schemas import (
    BuildChatbotRequest, UpdateChatbotRequest,
    ChatbotResponse, ChatRequest, ChatResponse,
    MessageResponse
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/chatbots", tags=["chatbots"])


def build_chatbot_background(bot_id: str):
    """
    Background task: simulate index building.
    Replace with real LangChain/LlamaIndex pipeline.
    """
    import time
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        bot = db.query(Chatbot).filter(Chatbot.id == bot_id).first()
        if not bot:
            return

        bot.status = "building"
        db.commit()

        # Simulate build time
        time.sleep(3)

        bot.status = "active"
        db.commit()

    except Exception as e:
        bot = db.query(Chatbot).filter(Chatbot.id == bot_id).first()
        if bot:
            bot.status = "error"
            db.commit()
    finally:
        db.close()


def generate_rag_response(question: str, bot: Chatbot, file: FileModel) -> tuple[str, list]:
    """
    Stub RAG response generator.
    Replace this with real LangChain/LlamaIndex retrieval + LLM call.

    In production:
      1. Load vector store for this bot
      2. Embed question using bot.embedding_model
      3. Retrieve top-K chunks
      4. Build prompt with context
      5. Call LLM (bot.llm_model) and return answer + sources
    """
    category = file.category if file else "general"
    chunking = bot.chunking_strategy
    embedding = bot.embedding_model
    vdb = bot.vector_db

    demo_responses = {
        "medical": [
            f"Based on the clinical document, the analysis reveals statistically significant results (p < 0.001). The study used {chunking} chunking with {bot.chunk_size}-token chunks, retrieving top-{bot.top_k} relevant passages via {vdb}.",
            "The document outlines several key findings: patient cohort showed 34% improvement in primary endpoints, adverse events were within acceptable CTCAE Grade 1-2 limits.",
            "According to indexed medical records, the treatment protocol follows WHO guidelines with dosage adjusted per BMI and renal function markers.",
        ],
        "legal": [
            f"The legal document specifies that under Section 4.2, all confidential information is subject to a 3-year non-disclosure obligation. Retrieved via {embedding} embeddings.",
            "Based on the contract terms, liability is capped at the total contract value. The indemnification clause (Section 8) covers direct damages only.",
            "The agreement requires 30-day written notice for termination. Arbitration is the exclusive dispute resolution mechanism per Section 12.",
        ],
        "research": [
            f"The paper's methodology section describes a transformer-based architecture achieving SOTA performance on benchmark tasks. Using {chunking} chunking preserved the semantic integrity of technical passages.",
            "Key findings from the research: the proposed approach outperforms baseline by 12.3% on F1 score. Results are reproducible with the provided hyperparameter configuration.",
            "The abstract states that the model was trained on 1.2B parameters with a context window of 8192 tokens. Ablation studies confirm the importance of the attention mechanism.",
        ],
        "financial": [
            f"Q4 revenue totaled $4.2M, representing a 23% YoY growth. EBITDA margin improved to 18.4%. Retrieved {bot.top_k} relevant data chunks from {vdb}.",
            "The financial report indicates cash reserves of $12.8M with a runway of approximately 18 months at current burn rate.",
            "Operating expenses increased 15% driven by R&D investment. Gross margin remained stable at 67.2% across all product lines.",
        ],
        "news": [
            "The news feed covers recent developments in the sector. Key highlights: regulatory changes announced last quarter are expected to impact operations in H2.",
            "According to retrieved articles, market sentiment has shifted following recent announcements. Analyst consensus remains cautiously optimistic.",
            "Breaking coverage from the indexed feed: three major developments identified — policy update, market movement, and strategic partnership announcement.",
        ],
        "political": [
            "The legislative document outlines proposed amendments to existing statute. Key provisions include expanded compliance requirements for digital platforms.",
            "Senate Bill analysis: bipartisan support identified across 3 key provisions. Opposition concentrated on Section 7 funding mechanism.",
            "Policy brief summary: the proposed framework aligns with international standards while introducing novel data sovereignty requirements.",
        ],
        "other": [
            f"Based on the document analysis, I found relevant information matching your query. The {chunking} chunking strategy with {embedding} embeddings retrieved {bot.top_k} relevant passages.",
            "The document contains detailed information on this topic. Key points extracted from the indexed content address your question directly.",
        ]
    }

    answers = demo_responses.get(category, demo_responses["other"])
    answer = random.choice(answers)

    # Generate fake source citations
    chunk_count = file.chunk_count if file else 50
    sources = []
    num_sources = min(bot.top_k, random.randint(2, 4))
    seen_chunks = set()
    for _ in range(num_sources):
        chunk_id = random.randint(1, max(1, chunk_count))
        while chunk_id in seen_chunks:
            chunk_id = random.randint(1, max(1, chunk_count))
        seen_chunks.add(chunk_id)
        sources.append({
            "chunk_id": f"chunk_{chunk_id:04d}",
            "page": random.randint(1, 50),
            "score": round(random.uniform(0.72, 0.98), 3),
            "preview": f"...relevant passage from chunk {chunk_id}..."
        })

    return answer, sources


@router.post("", response_model=ChatbotResponse, status_code=201)
async def build_chatbot(
    payload: BuildChatbotRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file belongs to user
    file = db.query(FileModel).filter(
        FileModel.id == payload.file_id,
        FileModel.user_id == current_user.id
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if file.status != "ready":
        raise HTTPException(status_code=400, detail="File is still processing. Please wait.")

    # Check chatbot limit per plan
    bot_count = db.query(Chatbot).filter(Chatbot.user_id == current_user.id).count()
    limits = {"free": 5, "pro": 999, "enterprise": 9999}
    limit = limits.get(current_user.plan, 5)
    if bot_count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Chatbot limit reached ({limit} for {current_user.plan} plan). Please upgrade."
        )

    bot = Chatbot(
        user_id=current_user.id,
        file_id=payload.file_id,
        name=payload.name,
        chunking_strategy=payload.chunking_strategy,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        embedding_model=payload.embedding_model,
        vector_db=payload.vector_db,
        llm_model=payload.llm_model,
        top_k=payload.top_k,
        temperature=payload.temperature,
        status="building"
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)

    # Build index in background
    background_tasks.add_task(build_chatbot_background, bot.id)

    # Load relationship for response
    db.refresh(bot)
    return bot


@router.get("", response_model=List[ChatbotResponse])
async def list_chatbots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bots = db.query(Chatbot).filter(
        Chatbot.user_id == current_user.id
    ).order_by(Chatbot.created_at.desc()).all()
    return bots


@router.get("/{bot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = db.query(Chatbot).filter(
        Chatbot.id == bot_id,
        Chatbot.user_id == current_user.id
    ).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    return bot


@router.patch("/{bot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    bot_id: str,
    payload: UpdateChatbotRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = db.query(Chatbot).filter(
        Chatbot.id == bot_id,
        Chatbot.user_id == current_user.id
    ).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")

    needs_rebuild = False
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(bot, field, value)
        if field in ["chunking_strategy", "chunk_size", "chunk_overlap", "embedding_model", "vector_db"]:
            needs_rebuild = True

    if needs_rebuild:
        bot.status = "building"
        background_tasks.add_task(build_chatbot_background, bot.id)

    db.commit()
    db.refresh(bot)
    return bot


@router.delete("/{bot_id}")
async def delete_chatbot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = db.query(Chatbot).filter(
        Chatbot.id == bot_id,
        Chatbot.user_id == current_user.id
    ).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    db.delete(bot)
    db.commit()
    return {"deleted": bot_id, "message": "Chatbot deleted"}


@router.post("/{bot_id}/chat", response_model=ChatResponse)
async def chat(
    bot_id: str,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = db.query(Chatbot).filter(
        Chatbot.id == bot_id,
        Chatbot.user_id == current_user.id
    ).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")

    if bot.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Chatbot is currently {bot.status}. Please wait for it to become active."
        )

    file = db.query(FileModel).filter(FileModel.id == bot.file_id).first()

    # Generate response (replace with real RAG in production)
    answer, sources = generate_rag_response(payload.question, bot, file)

    # Save messages to history
    user_msg = ChatMessage(
        chatbot_id=bot.id,
        role="user",
        content=payload.question,
    )
    bot_msg = ChatMessage(
        chatbot_id=bot.id,
        role="assistant",
        content=answer,
        sources=json.dumps(sources),
    )
    db.add(user_msg)
    db.add(bot_msg)

    # Update query count
    bot.total_queries += 1
    db.commit()

    return ChatResponse(
        answer=answer,
        sources=sources,
        tokens_used=len(answer.split()) * 2  # rough estimate
    )


@router.get("/{bot_id}/history", response_model=List[MessageResponse])
async def get_chat_history(
    bot_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = db.query(Chatbot).filter(
        Chatbot.id == bot_id,
        Chatbot.user_id == current_user.id
    ).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.chatbot_id == bot_id
    ).order_by(ChatMessage.created_at.asc()).limit(limit).all()

    return messages


@router.delete("/{bot_id}/history")
async def clear_chat_history(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = db.query(Chatbot).filter(
        Chatbot.id == bot_id,
        Chatbot.user_id == current_user.id
    ).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")

    db.query(ChatMessage).filter(ChatMessage.chatbot_id == bot_id).delete()
    db.commit()
    return {"message": "Chat history cleared"}
